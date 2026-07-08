from langchain_openai import ChatOpenAI
from rag.retrieval.research_augmenter import get_research_augmenter
import logging
import time
import threading
from datetime import datetime
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List, Callable, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.graph.message import add_messages
from agent.tools import ToolManager
from core.tool_wrapper import get_langchain_tools
from core.gate.cognitive_check import EulerPoinsotGate
from core.config import config
from core.agent.context_node import contextualize_node
from core.classifier.query_classifier import get_query_classifier

from core.memory.summarizer import MemorySummarizer
from core.episodic_memory import EpisodicMemory
from core.reflection import ReflectionManager
from core.graph_metrics import track_node
from core.logging_setup import log_event
from core.dynamic_tools.loader import load_dynamic_tools_into

# rough token estimation (4 chars per token)
MAX_CONTEXT_TOKENS = 28000


def _trim_messages(messages, max_tokens=MAX_CONTEXT_TOKENS):
    """Truncate oldest messages when approaching context limit."""
    total_chars = sum(len(m.content) if hasattr(m, 'content') else 0 for m in messages)
    if total_chars // 4 <= max_tokens:
        return messages
    kept = [messages[0]] if messages else []
    for m in reversed(messages[1:]):
        char_cost = len(m.content) if hasattr(m, 'content') else 0
        if (sum(len(x.content) if hasattr(x, 'content') else 0 for x in kept) + char_cost) // 4 <= max_tokens:
            kept.insert(1 if kept else 0, m)
        else:
            break
    return kept


logger = logging.getLogger(__name__)


def _run_with_timeout(fn: Callable, timeout: int = 60, default: Any = None):
    """Run fn in a daemon thread with total timeout. Abandons thread on timeout."""
    result = []
    exception = []
    done = threading.Event()

    def worker():
        try:
            result.append(fn())
        except Exception as e:
            exception.append(e)
        finally:
            done.set()

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    finished = done.wait(timeout=timeout)
    if not finished:
        logger.warning("⏱️ _run_with_timeout: timed out after %ds", timeout)
        return default
    if exception:
        raise exception[0]
    return result[0] if result else default

tool_manager = ToolManager()
ziva_tools = get_langchain_tools(tool_manager)


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    input: str
    analysis: str
    rag_context: str
    tool_needed: bool
    tool_output: str
    response: str
    retry_count: int
    tool_found: bool
    physics_params: dict
    gate_result: dict
    long_term_summary: str
    task_type: str
    task_confidence: float
    allowed_tools: list
    graph_start_time: float
    graph_node_times: dict


# LLM Configuration (lazy init for degraded mode)
llm = None
tool_llm = None
_llm_initialized = False


def _init_llm():
    global llm, tool_llm, _llm_initialized
    if _llm_initialized:
        return True
    primary_model_config = config.get_llm_provider("agent.primary_model")
    if not primary_model_config:
        logger.error("No LLM configuration found in ziva.yaml — running in degraded mode")
        return False
    logger.info(f"🔌 Initializing Graph LLMs for {primary_model_config['model_name']}...")
    llm = ChatOpenAI(
        model=primary_model_config["model_name"],
        openai_api_base=primary_model_config["base_url"],
        openai_api_key=primary_model_config["api_key"],
        temperature=0.3,
        request_timeout=300,
        max_tokens=1024,
        max_retries=0,
    )
    coder_config = config.get_llm_provider("agent.coder_model")
    tool_llm = ChatOpenAI(
        model=coder_config["model_name"] if coder_config else primary_model_config["model_name"],
        openai_api_base=coder_config["base_url"] if coder_config else primary_model_config["base_url"],
        openai_api_key=coder_config["api_key"] if coder_config else primary_model_config["api_key"],
        temperature=0.0,
        request_timeout=300,
        max_tokens=1024,
        max_retries=0,
    )
    _llm_initialized = True
    return True


_init_llm()


@track_node("input_node")
def input_node(state: AgentState):
    log_event("graph_state", node="input_node", input_len=len(state.get("input", "")))
    return {"input": state.get("input", ""), "graph_start_time": time.time(), "graph_node_times": {}}


@track_node("classify_node")
def classify_node(state: AgentState):
    classifier = get_query_classifier()
    query = state.get("input", "")
    task_type, confidence, _ = classifier.classify(query)
    allowed = classifier.get_allowed_tools(task_type)
    log_event("graph_state", node="classify_node", task_type=task_type, confidence=round(confidence, 2))
    return {
        "task_type": task_type,
        "task_confidence": confidence,
        "allowed_tools": allowed,
    }


@track_node("analyze_node")
def analyze_node(state: AgentState):
    try:
        if not _init_llm():
            return {"tool_needed": False, "response": "LLM não configurado. Verifique ziva.yaml."}
        formatted_context = state.get("rag_context", "")
        current_query = state["input"]
        task_type = state.get("task_type", "general_knowledge")
        is_price_query = any(kw in current_query.lower() for kw in ["preço", "preco", "valor", "custa", "quanto", "comprar", "promoção", "promocao", "melhor", "barato", "caro", "mais em conta"])
        is_comparison_query = any(kw in current_query.lower() for kw in ["comparativo", "comparação", "comparar", "vs", "versus", "diferença", "qual a diferença", "ou"])

        # Fast path for simple queries
        fast_responses = {
            "oi": "Olá! Como posso ajudar você hoje?",
            "ola": "Olá! Como posso ajudar você hoje?",
            "olá": "Olá! Como posso ajudar você hoje?",
            "hey": "Olá! Como posso ajudar você hoje?",
            "hi": "Hi there! How can I help?",
            "hello": "Hello! How can I help you today?",
            "bom dia": "Bom dia! Como posso ajudar?",
            "boa tarde": "Boa tarde! Como posso ajudar?",
            "boa noite": "Boa noite! Como posso ajudar?",
            "tudo bem": "Tudo bem! E você? Como posso ajudar?",
        }
        normalized = current_query.strip().lower().rstrip("?!.,")
        if task_type in ("greeting", "chitchat") and len(current_query) < 20:
                logger.info(f"Fast path: returning cached greeting for '{normalized}'")
                return {
                    "messages": [AIMessage(content=fast_responses[normalized])],
                    "tool_needed": False,
                    "response": fast_responses[normalized],
                }

        # Fast path for conversational/personal questions (no search needed)
        CONVERSATIONAL_PATTERNS = (
            "quem sou eu", "quem é você", "quem e voce", "quem e vc",
            "como você está", "como vc esta", "como vai",
            "oque voce faz", "o que você faz", "o que vc faz",
            "vc gosta", "você gosta", "qual seu nome", "qual o seu nome",
        )
        if task_type in ("greeting",) and normalized in fast_responses:
            pass
        elif normalized in CONVERSATIONAL_PATTERNS or any(normalized.startswith(p) for p in CONVERSATIONAL_PATTERNS):
            logger.info("💬 Conversational fast path for '%s'", normalized)
            system_prompt = f"""You are Ziva, an AI assistant.
Answer concisely in Portuguese (pt-BR). Do NOT use tools or search.
Current date/time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
            msg = [SystemMessage(content=system_prompt), HumanMessage(content=current_query)]
            ai_response = _run_with_timeout(lambda: llm.invoke(msg), timeout=180)
            if ai_response is None:
                return {"tool_needed": False, "response": "Desculpe, não consegui encontrar a resposta para sua pergunta.", "retry_count": state.get("retry_count", 0)}
            response_text = ai_response.content if hasattr(ai_response, 'content') else str(ai_response)
            return {
                "messages": [AIMessage(content=response_text)],
                "tool_needed": False,
                "response": response_text,
            }

        # Decide search strategy based on task type
        task_confidence = state.get("task_confidence", 0)
        NO_SEARCH_TASKS = {"greeting", "sentiment", "chitchat", "off_topic"}
        SEARCH_DIRECT_TASKS = {"web_search", "time_sensitive", "research", "general_knowledge"}

        has_history = len(state.get("messages", [])) > 1
        search_empty = False
        should_search = (
            task_type in SEARCH_DIRECT_TASKS
            or (is_price_query and task_type not in NO_SEARCH_TASKS)
            or (is_comparison_query and task_type not in NO_SEARCH_TASKS)
        )
        if should_search and not state.get("tool_output"):
            logger.info("🔍 Web search for '%s' (task=%s, price=%s, comp=%s)", current_query[:50], task_type, is_price_query, is_comparison_query)
            try:
                from extensions.unified_search import unified_web_search
                search_result = unified_web_search(current_query, 10, deep_scrape=False)
                if search_result and search_result.get("results"):
                    snippets = []
                    key_terms = [w for w in current_query.lower().split() if len(w) > 2 and w not in ("preço", "preco", "valor", "custa", "quanto", "comprar", "promoção", "promocao", "melhor", "barato", "caro", "para", "mais", "com", "brasil", "loja", "entre", "qual", "diferença", "quero", "obter", "sobre", "incluindo", "como", "uma", "por", "ser", "dos", "das", "ter", "muito", "tambem", "também", "quando", "onde", "que", "pode", "tem", "sao", "são", "esta", "está", "esse", "essa", "isto", "isso", "aquele", "aquela")]
                    for r in search_result["results"][:10]:
                        title = r.get("title", "")
                        url = r.get("url", "")
                        desc = r.get("description", "")
                        snippets.append(f"- {title}: {desc} ({url})")
                    formatted_context = "\n".join(snippets)
                    logger.info("✅ Search found %d results", len(search_result["results"]))
                    # Fetch top 2 result pages via HTTP for richer content (fast, no browser)
                    try:
                        import requests as req
                        from bs4 import BeautifulSoup
                        page_texts = []
                        for url in [r.get("url") for r in search_result["results"][:2] if r.get("url")]:
                            try:
                                resp = req.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
                                if resp.status_code == 200:
                                    soup = BeautifulSoup(resp.text, "html.parser")
                                    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                                        tag.decompose()
                                    text = soup.get_text(separator="\n", strip=True)[:3000]
                                    page_texts.append(f"--- CONTEÚDO ({url}) ---\n{text}")
                            except Exception:
                                pass
                        if page_texts:
                            formatted_context += "\n\n" + "\n\n".join(page_texts)
                            logger.info("📄 Fetched %d pages via HTTP for richer context", len(page_texts))
                    except ImportError:
                        pass
                    # Check if key product terms from query appear in results
                    product_terms = [w.strip("()[]{}.,;:!?") for w in current_query.split() if any(c.isdigit() for c in w) and len(w) > 1]
                    missing = [t for t in product_terms if t.lower() not in formatted_context.lower()]
                    if missing:
                        logger.info("⚠️ Products not found in search results: %s", missing)
                        formatted_context += f"\n\n[NOT FOUND IN SEARCH: {', '.join(missing)}]"
                elif is_price_query:
                    formatted_context = ""
                    search_empty = True
            except Exception as e:
                logger.warning("Search failed: %s", e)
        elif task_type in NO_SEARCH_TASKS or task_confidence < 0.3:
            if task_confidence < 0.3:
                logger.info("🔇 Skipping RAG (low confidence task=%.2f)", task_confidence)
            else:
                logger.info("🔇 Skipping RAG search for task '%s'", task_type)
        elif not is_price_query and not is_comparison_query:
            augmenter = get_research_augmenter()
            is_context_useful = formatted_context.strip() and "[Nota:" not in formatted_context
            if not is_context_useful:
                logger.info("🔍 Local context empty/weak. Triggering Web Search...")
                additional_info = augmenter.research(current_query, ['completeness', 'accuracy', 'sources', 'relevance'])
                formatted_context = augmenter.format_additional_info(additional_info)

        if state.get("tool_output"):
            tool_out = state["tool_output"]
            formatted_context += f"\n\n[PREVIOUS TOOL OUTPUT]:\n{tool_out}"
            if "NÃO ENCONTREI" in tool_out or "Nenhum resultado encontrado" in tool_out:
                search_empty = True
        if not formatted_context.strip() or "[Nota:" in formatted_context:
            search_empty = True

        # Load any dynamic tools created by the LLM
        load_dynamic_tools_into(ziva_tools)

        # Filter tools based on task classification
        task_type = state.get("task_type", "general_knowledge")
        SEARCH_DIRECT_TASKS = {"web_search", "time_sensitive", "research", "general_knowledge"}
        has_direct_context = (task_type in SEARCH_DIRECT_TASKS or is_price_query or is_comparison_query) and formatted_context.strip() and not state.get("tool_output")
        allowed_names = state.get("allowed_tools", [])
        filtered_tools = []
        if allowed_names:
            filtered_tools = [t for t in ziva_tools if t.name in allowed_names]
            logger.info("🔧 Using %d/%d tools for task '%s'",
                        len(filtered_tools), len(ziva_tools), task_type)
        else:
            logger.info("🔧 No tools needed for task '%s'", task_type)

        # Prevent tool loop: if tools already executed, unbind tools
        tools_already_executed = bool(state.get("tool_output"))
        if tools_already_executed or has_direct_context:
            llm_with_tools = tool_llm
            if has_direct_context:
                logger.info("🔇 Direct context available — tools disabled, single LLM call")
            else:
                logger.info("🔇 Tools already executed. Using tool LLM without tools.")
        else:
            llm_with_tools = tool_llm.bind_tools(filtered_tools) if filtered_tools else tool_llm

        long_term_summary = state.get("long_term_summary", "Sem histórico relevante.")

        # Hierarchical memory enrichment
        try:
            from core.memory.hierarchical_memory import get_hierarchical_memory
            hm = get_hierarchical_memory()
            memory_context = hm.get_working_context(current_query)
            if memory_context and memory_context != "Nenhum contexto relevante encontrado.":
                formatted_context = f"{formatted_context}\n\n[MEMORY]:\n{memory_context}" if formatted_context else f"[MEMORY]:\n{memory_context}"
        except Exception as e:
            logger.debug(f"Hierarchical memory enrichment failed: {e}")

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        weekday = datetime.now().strftime('%A')

        # Hard guard: if search found nothing for a product/price query, short-circuit to prevent hallucination
        if search_empty and is_price_query:
            logger.warning("⛔ Anti-hallucination guard: empty search for price/product query")
            safe_response = f"Não encontrei informações sobre '{current_query}' nas buscas realizadas. Pode ser que o termo esteja incorreto ou o produto não esteja disponível no mercado brasileiro atualmente. Tente verificar a grafia ou buscar por um modelo similar."
            return {
                "messages": [AIMessage(content=safe_response)],
                "tool_needed": False,
                "response": safe_response,
            }

        if tools_already_executed or has_direct_context:
            price_instruction = ""
            if is_price_query:
                price_instruction = """
FORMATTING RULE: The search results contain product prices from multiple stores. Extract ALL prices found and present them as a MARKDOWN TABLE with columns: Loja | Preço | Link. Order by preço ascending. Bold the lowest price. Include ALL stores found, even if the price is similar. If a store appears multiple times with different prices, include the lowest one for that store. Add a row for each unique store/price combination."""

            no_results_warning = ""
            if search_empty:
                no_results_warning = "\nIMPORTANTE: A busca não encontrou resultados específicos. Se o produto ou informação não foi encontrado, diga claramente que não encontrou. NÃO invente produtos, preços, avaliações ou links. NÃO simule resultados que não existem."
            system_prompt = f"""You are Ziva, an AI assistant with REAL-TIME WEB SEARCH.
CURRENT DATE AND TIME: {now}
CURRENT WEEKDAY: {weekday}
LONG-TERM MEMORY: {long_term_summary}

You already performed a web search and the results are below.
Use these results to answer the user. DO NOT call any tools.
{no_results_warning}

CRITICAL RULES - VIOLATION WILL CAUSE HALLUCINATION:
1. ONLY use information that literally appears in SEARCH RESULTS below.
2. NEVER say "presumivelmente", "provavelmente", "deve ter", "ou mais alto" - those are lies.
3. NEVER fabricate clock speeds, cores, cache, cores, threads, TDP, preços, ou qualquer especificação numérica.
4. NEVER claim ProductA = ProductB with overclocking. Different model numbers mean different products.
5. Extract and present ALL relevant information found in the search snippets. If snippets mention specs, prices, or comparisons, include them.
6. If search results have relevant pages but lack full details, list the page titles and links found so the user can access them.

Answer in Portuguese (pt-BR).
{price_instruction}
SEARCH RESULTS:
{formatted_context}
"""
        else:
            no_results_warning = ""
            if search_empty:
                no_results_warning = "\nIMPORTANTE: A busca não encontrou resultados. Se você usou a ferramenta de busca e não encontrou o produto, diga claramente que não encontrou. NÃO invente produtos, preços, avaliações ou links."
            system_prompt = f"""You are Ziva, an AI assistant with REAL-TIME WEB SEARCH.
CURRENT DATE AND TIME: {now}
CURRENT WEEKDAY: {weekday}
LONG-TERM MEMORY: {long_term_summary}
{no_results_warning}

REASONING PROCESS:
1. Analyze the user's question carefully
2. Check if CONTEXT has the answer
3. If CONTEXT has the answer: synthesize it into a clear response, citing sources
4. If CONTEXT is empty or insufficient: CALL web_search tool NOW. Do NOT explain how to search. Do NOT give step-by-step instructions. Actually call the function.
5. For greetings/simple chat: respond directly without searching

Answer in Portuguese (pt-BR). Be concise, accurate, and helpful. Never invent product information. Never tell the user to search manually — you search for them.

CONTEXT (web results):
{formatted_context}
"""

        # Build message history + current query
        history_messages = state.get("messages", [])
        system_message = SystemMessage(content=system_prompt)
        current_message = HumanMessage(content=current_query)
        all_messages = [system_message] + history_messages + [current_message] if history_messages else [system_message, current_message]
        all_messages = _trim_messages(all_messages)

        ai_response = _run_with_timeout(lambda: llm_with_tools.invoke(all_messages), timeout=300)
        if ai_response is None:
            return {"tool_needed": False, "response": "Desculpe, não consegui encontrar a resposta para sua pergunta.", "retry_count": state.get("retry_count", 0)}

        physics_params = {}
        if any(k in current_query.lower() for k in ["euler", "gate", "rigid body"]):
            physics_params = {"I": [1, 2, 3], "omega0": [1, 1, 1], "dt": 0.01, "total_time": 5.0}

        tool_needed = len(ai_response.tool_calls) > 0
        log_event("graph_state", node="analyze_node", tool_needed=tool_needed,
                  retry=state.get("retry_count", 0), task_type=task_type)
        return {
            "messages": [ai_response],
            "rag_context": formatted_context,
            "tool_needed": tool_needed,
            "response": ai_response.content if not tool_needed else "",
            "physics_params": physics_params,
            "retry_count": state.get("retry_count", 0) + (1 if tool_needed else 0)
        }
    except Exception as e:
        logger.error(f"Error in analyze_node: {e}")
        return {"tool_needed": False, "response": state.get("response", "")}


@track_node("execute_tool_node")
def execute_tool_node(state: AgentState):
    new_messages = []
    last_message = state["messages"][-1]
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return {}

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_id = tool_call["id"]

        logger.info(f"⚙️ Executing Tool: {tool_name}")
        content = "Tool execution failed."
        for tool in ziva_tools:
            if tool.name == tool_name:
                try:
                    content = str(tool.invoke(tool_args))
                except Exception as e:
                    content = f"Error: {e}"
                break
        new_messages.append(ToolMessage(content=content, tool_call_id=tool_id, name=tool_name))

    tool_names = [tc["name"] for tc in last_message.tool_calls]
    log_event("graph_state", node="execute_tool_node", tools=tool_names)
    return {"messages": new_messages, "tool_output": "\n".join([m.content for m in new_messages])}


@track_node("respond_node")
def respond_node(state: AgentState):
    if not _init_llm():
        return {"response": "LLM não configurado. Verifique ziva.yaml."}
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    weekday = datetime.now().strftime('%A')
    input_text = state["input"]
    rag_context = state.get("rag_context", "")
    tool_output = state.get("tool_output", "Nenhum resultado de ferramenta.")
    is_product_query = any(kw in input_text.lower() for kw in ["preço", "preco", "valor", "custa", "quanto", "comprar", "promoção", "promocao", "produto", "modelo", "celular", "smartphone", "comparativo", "comparação", "comparar", "vs", "versus", "diferença"])
    empty_context = not rag_context.strip() or "NÃO ENCONTREI" in rag_context or "Nenhum resultado encontrado" in rag_context
    no_invent = ""
    if empty_context and is_product_query:
        no_invent = "\nIMPORTANTE: The search returned no results for this product. Do NOT invent prices, stores, or links. Say 'Não encontrei informações sobre esse produto.'"
    system_text = f"""You are ZIVA - answer from the data below.
CURRENT DATE AND TIME: {now}
CURRENT WEEKDAY: {weekday}{no_invent}

RESPONSE GUIDELINES:
1. If CONTEXT has the answer: use it, synthesize clearly, cite sources
2. If CONTEXT is empty: use general knowledge for factual/simple queries
3. If the user asks for an image: describe in text and provide source links
4. Be concise and direct — avoid unnecessary preamble
5. For complex topics: break down into clear steps
6. Explicitly cite the source text that supports your answer
7. Never invent product prices, store names, or URLs.

[CONTEXT - Web Search Results]
{rag_context}

[TOOL OUTPUT]
{tool_output}
"""
    messages = [SystemMessage(content=system_text), HumanMessage(content=input_text)]
    messages = _trim_messages(messages)
    res = _run_with_timeout(lambda: llm.invoke(messages), timeout=180)
    if res is not None:
        log_event("graph_state", node="respond_node", response_len=len(res.content))
        return {"response": res.content}
    logger.warning("⏱️ respond_node LLM timed out after 180s")
    return {"response": "Não consegui encontrar a resposta para sua pergunta."}


@track_node("cognitive_gate_node")
def cognitive_gate_node(state: AgentState):
    params = state.get("physics_params", {})
    if not params:
        return {"gate_result": {"passed": True}}
    gate = EulerPoinsotGate()
    result = gate.check_physics(params["I"], params["omega0"], params["dt"], params["total_time"])
    return {"gate_result": result}


@track_node("summarization_node")
def summarization_node(state: AgentState):
    try:
        response = state.get("response", "")
        query = state.get("input", "")
        history = state.get("messages", [])
        existing_summary = state.get("long_term_summary", "")

        recent = []
        for m in history[-4:]:
            if hasattr(m, 'content') and m.content:
                recent.append(m)
        recent.append(HumanMessage(content=query))
        recent.append(AIMessage(content=response))

        summarizer = MemorySummarizer()
        new_summary = summarizer.summarize_conversation(existing_summary, recent)
        if new_summary and new_summary != existing_summary:
            logger.info(f"📝 Summary updated ({len(new_summary)} chars)")
            return {"long_term_summary": new_summary}
    except Exception as e:
        logger.error(f"Summarization error: {e}")
    return {"long_term_summary": state.get("long_term_summary", "")}


@track_node("learning_node")
def learning_node(state: AgentState):
    try:
        query = state.get("input", "")
        response = state.get("response", "")
        if not query or not response or len(response) < 5:
            return {}

        episodic = EpisodicMemory()
        episodic.remember(query, response, source="ziva_graph")

        rag_context = state.get("rag_context", "")
        if rag_context and len(rag_context) > 20:
            from core.vector_store import VectorStore
            from core.llm import LLMService
            llm_svc = LLMService()
            embedding = llm_svc.embedding(query)
            if embedding:
                vs = VectorStore()
                vs.add_text(
                    f"Q: {query}\nA: {response}",
                    embedding,
                    {"source": "graph_learning", "type": "interaction", "timestamp": time.time()}
                )
                logger.info("🧠 Learned from graph interaction")
    except Exception as e:
        logger.debug(f"Learning node error: {e}")
    return {}


@track_node("metacognition_node")
def metacognition_node(state: AgentState):
    try:
        query = state.get("input", "")
        response = state.get("response", "")
        if not query or not response or len(response) < 10:
            return {}

        rag_context = state.get("rag_context", "")
        context_list = [rag_context] if rag_context else []

        reflection = ReflectionManager()
        result = reflection.reflect(query, context_list, response)
        if result and result.get("score", 0) > 0:
            reflection.save_reflection(result, query, response)
            logger.info(f"🔍 Reflection: score={result.get('score')}/5, lesson='{result.get('lesson', '')[:60]}'")
    except Exception as e:
        logger.debug(f"Metacognition error: {e}")
    return {}


# Graph Workflow Construction
workflow = StateGraph(AgentState)
workflow.add_node("input_node", input_node)
workflow.add_node("contextualize_node", contextualize_node)
workflow.add_node("classify_node", classify_node)
workflow.add_node("analyze_node", analyze_node)
workflow.add_node("execute_tool_node", execute_tool_node)
workflow.add_node("respond_node", respond_node)
workflow.add_node("cognitive_gate_node", cognitive_gate_node)
workflow.add_node("summarization_node", summarization_node)
workflow.add_node("learning_node", learning_node)
workflow.add_node("metacognition_node", metacognition_node)

workflow.set_entry_point("input_node")
workflow.add_edge("input_node", "contextualize_node")
workflow.add_edge("contextualize_node", "classify_node")
workflow.add_edge("classify_node", "analyze_node")


def router(state: AgentState):
    retry_count = state.get("retry_count", 0)
    graph_start = state.get("graph_start_time", 0)
    elapsed = time.time() - graph_start if graph_start else 0

    if retry_count >= 3 or elapsed > 240:
        if elapsed > 240:
            log_event("loop_timeout", elapsed_seconds=round(elapsed, 1), retry_count=retry_count)
            logger.warning(f"⏱️ Graph timeout after {elapsed:.0f}s, forcing respond")
        log_event("graph_transition", from_node="analyze_node", to="respond_node", reason="max_retries_or_timeout")
        return "respond_node"
    if state.get("physics_params") and not state.get("gate_result"):
        log_event("graph_transition", from_node="analyze_node", to="cognitive_gate_node")
        return "cognitive_gate_node"
    if state.get("tool_needed"):
        log_event("graph_transition", from_node="analyze_node", to="execute_tool_node")
        return "execute_tool_node"
    if state.get("response"):
        log_event("graph_transition", from_node="analyze_node", to=END)
        return END
    log_event("graph_transition", from_node="analyze_node", to="respond_node", reason="default")
    return "respond_node"


workflow.add_conditional_edges("analyze_node", router, {
    "execute_tool_node": "execute_tool_node",
    "respond_node": "respond_node",
    "cognitive_gate_node": "cognitive_gate_node",
    "summarization_node": "summarization_node",
    END: END
})

workflow.add_edge("cognitive_gate_node", "respond_node")
workflow.add_edge("execute_tool_node", "analyze_node")
workflow.add_edge("respond_node", END)
# Cognitive nodes (summarization, learning, metacognition) run asynchronously
# outside the main graph to avoid blocking the user response

app = workflow.compile()
