from core.agent.modes import get_mode_by_slug, MODES
from core.agent.prompts import get_system_prompt, GRADER_PROMPT, TRANSFORM_QUERY_PROMPT, CONTEXTUALIZE_QUERY_PROMPT, QUERY_EXPANSION_PROMPT
from core.agent.router import route_query
from core.agent.anime_node import anime_search
from core.llm import LLMService
from core.rag_helper import get_rag_helper
from core.p2p_learning import GabrielleConnector
from core.episodic_memory import EpisodicMemory
from typing import Dict, Any
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import re
from core.agent.state import AgentState
from qdrant_client import QdrantClient
from langchain_core.documents import Document
from core.dspy_config import configure_dspy
from core.dspy_modules.modules import (
    Contextualizer, Grader, Reworder, Generator, load_compiled_state
)
from core.hex_protocol import HEXCommandBuilder
from core.reflection import ReflectionManager
from core.letta_agent import LettaAgentWrapper
from core.rag.rerank import rerank_documents
import logging

import os
from core.config import config
# --- Configuration ---
# Verbosity Control (Default: False for clean UX)
VERBOSE = os.getenv("ZIVA_VERBOSE", "false").lower() == "true"

# --- GLOBAL LOGGING SILENCE ---
if not VERBOSE:
    # Silence all standard loggers
    logging.getLogger().setLevel(logging.WARNING)
    logging.getLogger("root").setLevel(logging.WARNING)
    logging.getLogger("RAGEnhancement").setLevel(logging.WARNING)
    logging.getLogger("EpisodicMemory").setLevel(logging.WARNING)
    logging.getLogger("ZivaRerank").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

# Configure DSPy Global Settings
configure_dspy()

# Initialize DSPy Modules
contextualizer_module = Contextualizer()
grader_module = Grader()
reworder_module = Reworder()
generator_module = Generator()

# Attempt to load optimized weights (if they exist)
# load_compiled_state(generator_module, "core/dspy_modules/compiled_generator.json")
# Connect to local Qdrant
client = QdrantClient(host="localhost", port=6333)
# Connect to local Ollama (Llama 3.2 or compatible)
# LLM Initialization via Config
llm_config = config.get_llm_provider("agent.primary_model")
if llm_config:
    print(f"🔌 Nodes connecting to {llm_config['base_url']}")
    llm = ChatOpenAI(
        model=llm_config["model_name"],
        openai_api_base=llm_config["base_url"],
        openai_api_key=llm_config["api_key"],
        temperature=0,
        request_timeout=120
    )
else:
    # Fallback/Legacy
    backend = os.getenv("ZIVA_LLM_BACKEND", "lm_studio").lower()
    if backend == "lm_studio":
        base_url = os.getenv("ZIVA_LLM_BASE_URL", "http://100.104.242.35:1234/v1")
        llm = ChatOpenAI(
            model=os.getenv("ZIVA_LLM_MODEL", "qwen3-14b"),
            openai_api_base=base_url,
            openai_api_key=os.getenv("ZIVA_LLM_KEY", "lm-studio"),
            temperature=0,
            request_timeout=120
        )
    else:
        llm = ChatOllama(model="qwen2.5:14b", temperature=0)


# Initialize Core Intelligence Modules
rag = get_rag_helper()
# Embedding Model Initialization via Config
emb_config = config.get_llm_provider("agent.embedding_model")
if emb_config:
    embedder = LLMService(
        model=emb_config["model_name"],
        base_url=emb_config["base_url"],
        api_key=emb_config["api_key"]
    )
else:
    embedder = LLMService(model="text-embedding-qwen2.5-0.5b-instruct")
episodic_mem = EpisodicMemory()
gabrielle = GabrielleConnector() # P2P Connection
reflector = ReflectionManager(llm_backend=llm)
letta = LettaAgentWrapper(base_url="http://localhost:8283") # Long-term Memory


def retrieve(state: AgentState) -> Dict[str, Any]:
    """
    Retrieve documents using Hybrid Intelligence (Local RAG + Remote Latent P2P).
    """

    if VERBOSE:
        print(HEXCommandBuilder.exec_cmd("RETRIEVE (HYBRID)"))
    question = state["question"]
    
    # --- RAG LEVEL 2: Metadata Filtering ---
    from core.agent.filters_extractor import extract_query_filters
    query_filters = extract_query_filters(question)
    
    # --- RAG LEVEL 3: Entity Linking ---
    from core.agent.entity_linker import EntityLinker
    linker = EntityLinker(llm)
    linked_entities = linker.extract_entities(question)
    entity_context = " ".join(linked_entities) if linked_entities else ""
    
    documents = []

    # 1. Episodic Memory (Fast Path)
    episodic_hit = episodic_mem.recall(question)
    if episodic_hit:
        print(HEXCommandBuilder.read(f"Episodic Hit! (Score: {episodic_hit['score']:.4f})"))
        mem_doc = f"FONTE: MEMÓRIA EPISÓDICA (VERDADE ABSOLUTA)\nPERGUNTA: {episodic_hit['original_query']}\nRESPOSTA: {episodic_hit['answer']}"
        documents.append(mem_doc)

    # 2. Local Semantic Search (via RAGHelper)
    # RAGHelper handles embedding generation, fetching, and ACTIVE RECALL boosting internally
    try:
        if VERBOSE:
             print(HEXCommandBuilder.think("Searching Local Memory (Deep RAG)..."))
             
        # Enhance query with entities
        search_query = f"{question} {entity_context}".strip()
        
        # Use RAGHelper to search (includes filtering and initial scoring)
        # Note: We retrieve extended candidates for Reranking later
        local_results = rag.search_memories(
            query=search_query, 
            limit=10, # Fetch more for reranking
            min_score=0.4 # Permissive initial filter
        )
        
        local_docs = [r["text"] for r in local_results]
        documents.extend(local_docs)
        
        if VERBOSE:
            print(HEXCommandBuilder.read(f"Local RAG found {len(local_results)} candidates"))

    except Exception as e:
        print(f"Local RAG Error: {e}")

    # 3. Long-term Context (Letta / MemGPT)
    # The Letta agent provides historical context and stateful memories
    try:
        if VERBOSE:
            print(HEXCommandBuilder.think("Querying Long-term Memory (Letta)..."))
        
        # We ask Letta what it remembers or how it sees the current context
        letta_context = letta.send_message(f"[INTERNAL RETRIEVAL] O que você lembra sobre isso ou sobre nossas conversas passadas relacionadas a: {question}")
        if letta_context and letta_context.strip() and not letta_context.startswith("Error"):
             if VERBOSE:
                 print(HEXCommandBuilder.read("✨ Historical Context found in Letta"))
             documents.append(f"FONTE: MEMÓRIA DE LONGO PRAZO (LETTA)\nCONTEXTO HISTÓRICO: {letta_context}")
    except Exception as e:
        if VERBOSE:
            print(f"Letta Retrieval Error: {e}")

    # 4. P2P Latent Search (Gabrielle Intelligence) - The "Missing Link"
    # If local results are weak/few, we ask the hive mind.
    # In V2, we ALWAYS ask for "hard" questions to get diverse perspectives.
    is_hard_question = len(question.split()) > 5 # Heuristic
    if not local_docs or is_hard_question:
         if VERBOSE:
             print(HEXCommandBuilder.think("📡 Initiating P2P Latent Search (Gabrielle)..."))
             
         try:
             # Generate embedding using RAG Helper to ensure compatibility
             query_vec = rag.get_embedding(question)
             if query_vec:
                 remote_context = gabrielle.search_remote_latent(query_vec)
                 if remote_context:
                     print(HEXCommandBuilder.read("✨ P2P Insight Received from Gabrielle"))
                     documents.append(f"FONTE: MENTE COLMEIA (GABRIELLE P2P)\nCONTEXTO: {remote_context}")
                 else:
                     if VERBOSE:
                        print("P2P Search returned no results.")
         except Exception as e:
             if VERBOSE:
                 print(f"P2P Search failed: {e}")

    # 4. Emergency Knowledge Injection (Hardcoded Patches)
    if "pikas" in question.lower() or "ochotona" in question.lower():
         pika_doc = """[INJEÇÃO MANUAL] Pikas (Ochotona) são mamíferos reais da ordem Lagomorpha, não ficção."""
         documents.append(pika_doc)

    # 5. Semantic Reranking (FlashRank via RAGHelper/Nodes)
    # Deduplicate first
    unique_docs = list(set(documents))
    
    if unique_docs:
        if VERBOSE:
            print(HEXCommandBuilder.think(f"Reranking {len(unique_docs)} candidates..."))
            
        # Rerank
        reranked_docs = rerank_documents(question, unique_docs, top_k=5)
        
        # Force Episodic to Top if it exists
        if episodic_hit and mem_doc in unique_docs:
             if mem_doc not in reranked_docs:
                 reranked_docs.insert(0, mem_doc)
        
        documents = reranked_docs
        
        if VERBOSE:
            print(HEXCommandBuilder.think(f"Top {len(documents)} selected for generation."))

    return {"documents": documents, "question": question}


def sherlock_search(state: AgentState):
    """
    Executes an OSINT search using Sherlock to find social media accounts.
    """

    if VERBOSE:
        print(HEXCommandBuilder.exec_cmd("SHERLOCK_SEARCH"))
    query = state["question"]

    # Simple extraction
    username = query.lower().replace("sherlock", "").strip()
    if not username:
        username = query.strip()

    if not username:
        username = query.strip()

    if not username:
        username = query.strip()

    if VERBOSE:
        print(HEXCommandBuilder.tool("sherlock", username))

    from core.tools.sherlock import SherlockClient
    sherlock_client = SherlockClient()
    results = sherlock_client.search(username)

    documents = []
    if "error" in results:
        documents.append(f"Shared Error: {results['error']}")
    elif results.get("found_count", 0) > 0:
        doc_str = f"Sherlock OSINT Report for '{results['username']}':\n"
        doc_str += f"Found {results['found_count']} accounts:\n"
        for site in results["sites"]:
            doc_str += f"- {site['site']}: {site['url']}\n"
        documents.append(doc_str)
    else:
        documents.append(
            f"Sherlock search for '{username}' returned no results.")

    return {"documents": documents, "question": query}


def get_memory_stats(state: AgentState):
    """
    Retrieves statistics about the internal Vector Database (Qdrant).
    """

    if VERBOSE:
        print(HEXCommandBuilder.exec_cmd("GET_MEMORY_STATS"))
    query = state["question"]

    stats = rag.vector_store.get_stats()

    documents = []
    if "error" in stats:
        documents.append(f"Erro ao acessar estatísticas da memória: {stats['error']}")
    else:
        doc_str = "Estatísticas da Memória Interna (Qdrant):\n"
        doc_str += f"- Total de Pontos (Chunks): {stats['total_points']}\n"
        doc_str += f"- Status da Coleção: {stats['status']}\n"
        doc_str += f"- Segmentos Otimizados: {stats['segments']}\n"
        doc_str += f"- Vetores Indexados: {stats['vectors_count']}\n"
        documents.append(doc_str)

    return {"documents": documents, "question": query}


def get_system_services(state: AgentState):
    """
    Lists all running services and their ports for Ziva's operation.
    """
    print(HEXCommandBuilder.exec_cmd("GET_SYSTEM_SERVICES"))
    query = state["question"]

    import socket

    def check_port(port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                return s.connect_ex(('127.0.0.1', port)) == 0
        except BaseException:
            return False

    services = [
        {"name": "SSH (Sistema)", "port": 22},
        {"name": "SSH Alternativo (Tailscale/Custom)", "port": 2222},
        {"name": "Ollama (LLM Backend)", "port": 11434},
        {"name": "Qdrant (Vector Database)", "port": 6333},
        {"name": "SearXNG (Web Search)", "port": 8082},
        {"name": "Kiwix (Offline Wikipedia)", "port": 8081},
        {"name": "Binary Server (P2P Sync)", "port": 9000},
        {"name": "Ziva API (FastAPI)", "port": 8000},
    ]

    doc_str = "Serviços do Sistema Ziva:\n\n"
    for svc in services:
        status = "🟢 Online" if check_port(svc["port"]) else "🔴 Offline"
        doc_str += f"- {svc['name']}: Porta {svc['port']} - {status}\n"

    documents = [doc_str]
    return {"documents": documents, "question": query}


def get_network_devices(state: AgentState):
    """
    Discovers devices on the Tailscale network.
    """
    print(HEXCommandBuilder.exec_cmd("GET_NETWORK_DEVICES"))
    query = state["question"]

    import subprocess

    try:
        # Run tailscale status to get network devices
        result = subprocess.run(
            ["tailscale", "status"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            doc_str = "Dispositivos na Rede Tailscale:\n\n"

            for line in lines:
                if line.strip():
                    # Parse tailscale status output
                    # Format: hostname IP [tags] [online/offline]
                    parts = line.split()
                    if len(parts) >= 2:
                        hostname = parts[0]
                        ip = parts[1]
                        doc_str += f"- {hostname}: {ip}\n"

            documents = [doc_str]
        else:
            documents = [
                "Erro ao acessar Tailscale. Verifique se o serviço está rodando."]

    except FileNotFoundError:
        documents = [
            "Tailscale não está instalado ou não está no PATH do sistema."]
    except subprocess.TimeoutExpired:
        documents = ["Timeout ao consultar Tailscale."]
    except Exception as e:
        documents = [f"Erro ao descobrir dispositivos: {str(e)}"]

    return {"documents": documents, "question": query}


def fetch_tech_news(state: AgentState):
    """
    Fetches latest tech news headlines from Brazilian sources and summarizes them.
    """
    print(HEXCommandBuilder.exec_cmd("FETCH_TECH_NEWS"))
    query = state["question"]

    from core.tools.tech_news import TechNewsClient

    client = TechNewsClient()
    headlines = client.fetch_headlines(max_sources=2)

    documents = []
    doc_str = "Últimas Notícias de Tecnologia:\n\n"

    for source, data in headlines.items():
        if "error" in data:
            doc_str += f"❌ {source.title()}: Erro ao buscar ({data['error']})\n\n"
        else:
            doc_str += f"📰 {source.title().replace('_', ' ')} ({data['url']}):\n"
            doc_str += f"{data['content']}\n\n"

    documents.append(doc_str)
    return {"documents": documents, "question": query}


def grade_documents(state: AgentState) -> Dict[str, Any]:
    """
    Determines whether the retrieved documents are relevant to the question.
    """

    if VERBOSE:
        print(HEXCommandBuilder.exec_cmd("GRADE_DOCUMENTS"))
    question = state["question"]
    documents = state["documents"]

    # DSPy Grader
    filtered_docs = []
    
    # Construct grading question from context
    grading_question = question
    expanded = state.get("expanded_queries", [])
    if expanded:
        grading_question = f"{question} (Intent Context: {', '.join(expanded)})"
        if VERBOSE:
            print(HEXCommandBuilder.think(f"Grading with expanded context: {grading_question}"))

    # FLASHRANK TRUST BYPASS: Auto-accept RANK 1 (first document)
    # The cross-encoder re-ranker is more reliable than the bi-encoder grader
    if documents:
        # Check if Rank 1 is Episodic
        is_episodic = "Memória Episódica" in documents[0]
        if is_episodic:
            if VERBOSE:
                print(HEXCommandBuilder.think("RANK 1 AUTO-ACCEPTED (Episodic Memory)"))
        else:
            if VERBOSE:
                print(HEXCommandBuilder.think("RANK 1 AUTO-ACCEPTED (FlashRank Trust)"))
        
        filtered_docs.append(documents[0])
        remaining_docs = documents[1:]
    else:
        remaining_docs = []

    # --- Grader Logic ---
    # LM Studio Crash Fix: DSPy/LiteLLM tries to enforce 'response_format' which LM Studio rejects.
    # We fallback to standard LangChain for Grading if backend is 'lm_studio'.
    backend = os.getenv("ZIVA_LLM_BACKEND", "ollama").lower()
    
    if backend == "lm_studio":
        # Fallback: Simple LangChain Grading
        prompt = PromptTemplate(
            template="""You are a grader assessing relevance of a retrieved document to a user question.
            
            Question: {question}
            Document: {document}
            
            If the document contains keyword(s) or semantic meaning related to the question, grade it as 'yes'.
            Otherwise, grade it as 'no'.
            
            Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question.""",
            input_variables=["question", "document"]
        )
        chain = prompt | llm | StrOutputParser()
        
        # Grade remaining documents using LangChain
        for doc in remaining_docs:
            # If contextualized exists, use it (it's better)
            current_grading_question = state.get("contextualized_question", grading_question)
                
            # Truncate doc for grading only (save tokens)
            grade_doc_content = doc[:2000] + "..." if len(doc) > 2000 else doc
            score = chain.invoke({"question": current_grading_question, "document": grade_doc_content})
            grade = score.strip().lower()
            
            if "yes" in grade:
                 if VERBOSE:
                    print(f"---GRADE: DOC RELEVANT (LangChain)---")
                 filtered_docs.append(doc)
            else:
                 if VERBOSE:
                    print(f"---GRADE: DOC NOT RELEVANT (LangChain)---")
                    
        return {"documents": filtered_docs, "question": question}

    # Default: DSPy Grading (Ollama)
    # Grade remaining documents
    for doc in remaining_docs:
        # returns prediction with .is_relevant
        pred = grader_module(question=grading_question, document=doc)
        grade = pred.is_relevant.lower()
        
        if "yes" in grade:
            if VERBOSE:
                print(HEXCommandBuilder.think("GRADE: DOCUMENT RELEVANT"))
            filtered_docs.append(doc)
        else:
            if VERBOSE:
                print(HEXCommandBuilder.think("GRADE: DOCUMENT NOT RELEVANT"))
            continue

    return {"documents": filtered_docs, "question": question}


def generate(state: AgentState) -> Dict[str, Any]:
    """
    Generates the answer using the retrieved documents.
    """

    if VERBOSE:
        print(HEXCommandBuilder.exec_cmd("GENERATE"))
    question = state["question"]
    documents = state["documents"]

    # Get System Date
    import datetime
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # DSPy Generation
    # Use top 3 documents (highest FlashRank score) to provide better coverage
    # while maintaining focus. The re-ranker already selected the most relevant candidates.
    if documents:
        context_str = "\n\n---\n\n".join(documents[:3])
        if VERBOSE:
            print(HEXCommandBuilder.think(f"Using top {min(3, len(documents))} documents for generation."))
    else:
        context_str = ""
    
    # Propagate intent to generator
    gen_question = question
    expanded = state.get("expanded_queries", [])
    if expanded:
        gen_question = f"{question} (Context Intent: {', '.join(expanded)})"
    
    pred = generator_module(context=context_str, question=gen_question)
    generation = pred.answer
    return {"generation": generation}


def transform_query(state: AgentState) -> Dict[str, Any]:
    """
    Transform the query to produce a better question.
    """

    if VERBOSE:
        print(HEXCommandBuilder.exec_cmd("TRANSFORM_QUERY"))
    question = state["question"]
    retry_count = state.get("retry_count", 0) + 1

    # DSPy Reworder
    pred = reworder_module(question=question)
    better_question = pred.better_question
    return {"question": better_question, "retry_count": retry_count}


def set_mode(state: AgentState) -> Dict[str, Any]:
    """
    Sets the agent's mode based on the user's request.
    """

    if VERBOSE:
        print(HEXCommandBuilder.exec_cmd("SET_MODE"))
    question = state["question"].lower()

    # Default to preserving current mode or general if not set
    current_mode = state.get("mode", "general")
    target_mode = current_mode

    # Check for mode switch keywords
    for mode in MODES:
        if mode.slug in question or mode.name.lower() in question:
            target_mode = mode.slug
            break

    # Check for "architect" specifically if not found (alias check)
    if "arquiteto" in question:
        target_mode = "architect"
    elif "programador" in question or "coder" in question:
        target_mode = "coder"

    if target_mode != current_mode:
        if VERBOSE:
            print(HEXCommandBuilder.exec_cmd(f"SWITCH_MODE:{current_mode}->{target_mode}"))
    else:
        if VERBOSE:
             print(HEXCommandBuilder.think(f"Keeping mode: {current_mode}"))

    return {"mode": target_mode, "question": question}


def contextualize_query(state: AgentState) -> Dict[str, Any]:
    """
    Rewrites the question based on chat history to make it standalone.
    """

    if VERBOSE:
        print(HEXCommandBuilder.exec_cmd("CONTEXTUALIZE_QUERY"))
    question = state["question"]
    chat_history = state.get("chat_history", [])

    if not chat_history:
        return {"question": question}

    # Format history for prompt
    history_str = "\n".join(chat_history[-4:])  # Keep last 4 turns

    # DSPy Contextualizer
    pred = contextualizer_module(chat_history=history_str, question=question)
    new_question = pred.standalone_question
    if VERBOSE:
        print(HEXCommandBuilder.think(f"Rewritten: {new_question}"))
    return {"question": new_question}


def expand_query(state: AgentState) -> Dict[str, Any]:
    """
    Expands the user query into multiple semantic variations using the LLM.
    """

    if VERBOSE:
        print(HEXCommandBuilder.exec_cmd("EXPAND_QUERY"))
    question = state["question"]
    
    # 0. Domain Knowledge Heuristics (Override)
    if "lhc" in question.lower():
        if VERBOSE:
            print(HEXCommandBuilder.think("Domain Knowledge: LHC -> Laboratório Hacker de Campinas"))
        return {"expanded_queries": ["Laboratório Hacker de Campinas", "Laboratório Hacker Campinas", "Large Hadron Collider"]}

    # Using the LLM to generate variations
    chain = QUERY_EXPANSION_PROMPT | llm | StrOutputParser()
    try:
        response = chain.invoke({"question": question})
        # Parse lines (Robust)
        lines = response.split('\n')
        variations = []
        for line in lines:
            clean = line.strip()
            # Remove numbering (1., 2., -)
            if clean and (clean[0].isdigit() or clean.startswith("-")):
                parts = clean.split(" ", 1)
                if len(parts) > 1:
                    clean = parts[1].strip()
            # Remove quotes
            clean = clean.replace('"', "").replace("'", "")
            if clean and "Here are" not in clean and "?" not in clean: # Filter conversational filler
                variations.append(clean)
        
        # Take up to 3
        variations = variations[:3]

        if VERBOSE:
            print(HEXCommandBuilder.think(f"Generated Variations: {variations}"))
        return {"expanded_queries": variations}
    except Exception as e:
        if VERBOSE:
             print(HEXCommandBuilder.think(f"Expansion failed: {e}"))
        return {"expanded_queries": []}

# from core.tools.weather import WeatherClient


def check_weather(state: AgentState) -> Dict[str, Any]:
    """
    Executes weather check and returns it as a document context.
    """
    """
    Executes weather check and returns it as a document context.
    """
    if VERBOSE:
        print(HEXCommandBuilder.exec_cmd("CHECK_WEATHER"))
    question = state["question"]
    lower_q = question.lower()

    # 0. Narrative/Fiction Guardrail
    # If query mentions fiction terms, abort weather/time check immediately.
    narrative_keywords = ["anime", "manga", "mangá", "filme", "série", "livro", "personagem", "episódio", "temporada", "vol", "volume", "capítulo"]
    if any(k in lower_q for k in narrative_keywords):
        if VERBOSE:
            print(HEXCommandBuilder.think("Narrative context detected. Skipping weather/time check."))
        return {
            "documents": ["N/A (Narrative Context)"],
            "question": question}

    # Extract location (heuristic for MVP)
    # Ideally use LLM to extract entity, but let's try keyword split or just
    # pass full query
    from core.tools.weather import WeatherClient
    client = WeatherClient()

    # Improved Entity Extraction (Heuristic)
    # 1. Try splitting by "em", "no", "na"
    lower_q = question.lower()
    location = ""

    delimiters = [" em ", " no ", " na ", " in ", " for ", " para "]
    for d in delimiters:
        if d in lower_q:
            parts = lower_q.split(d)
            if len(parts) > 1:
                location = parts[-1].replace("?", "").strip()
                break

    # 2. If no delimiter, fallback to cleaning
    if not location:
        stopwords = [
            "qual",
            "o",
            "a",
            "clima",
            "tempo",
            "temperatura",
            "previsão",
            "como",
            "está",
            "hoje",
            "agora",
            "para",
            "de"]
        words = lower_q.replace("?", "").split()
        clean_words = [w for w in words if w not in stopwords]
        location = " ".join(clean_words)

    # 3. Clean Date Words from Location (to prevent Geocoding errors)
    date_words = ["hoje", "amanhã", "amanha", "agora", "tomorrow", "today"]
    for dw in date_words:
        location = location.replace(dw, "").strip()

    print(HEXCommandBuilder.tool("weather_check", location))
    if len(location) < 2:
        return {
            "documents": ["Erro: Localização não detectada na pergunta."],
            "question": question}

    data = client.get_weather(location)

    documents = []
    if "result" in data:
        documents.append(data["result"])
    else:
        documents.append(f"Não foi possível obter o clima: {data.get('error')}")

    return {"documents": documents, "question": question}


def validate_answer(state: AgentState) -> Dict[str, Any]:
    """
    Checks if the generated answer is a refusal ("I don't know").
    """

    if VERBOSE:
        print(HEXCommandBuilder.exec_cmd("VALIDATE_ANSWER"))
    generation = state["generation"]
    question = state["question"] # Needed for remembering

    # Simple heuristic to start (save LLM call)
    refusals = [
        "i don't know",
        "não sei",
        "não tenho informações",
        "no information",
        "cannot answer",
        "não há informações",
        "a resposta não está disponível",
        "não encontrei informações",
        "desculpe",
        "sinto muito"]
    for r in refusals:

        if r in generation.lower():
            if VERBOSE:
                print(HEXCommandBuilder.think("DECISION: ANSWER IS REFUSAL"))
            
            # TELEMETRY: Log refusal as a failure of knowledge retrieval
            # This allows the Overseer to see "knowledge_retrieval" errors and trigger KGC
            from core.telemetry import TelemetryManager
            import time
            TelemetryManager.log_tool_execution(
                tool="knowledge_retrieval",
                start_time=time.time() - 1, # Approx
                status="error",
                input_val=question,
                error="REFUSAL: Insufficient Knowledge"
            )
            
            return {"generation": generation, "is_refusal": True}

    if VERBOSE:
        print(HEXCommandBuilder.think("DECISION: ANSWER IS VALID"))
    
    # Store Valid Answer in Episodic Memory
    try:
        episodic_mem.remember(query=question, answer=generation)
    except Exception as e:
        print(HEXCommandBuilder.think(f"Failed to store episodic memory: {e}"))
        
    # Sync with Letta (Long-term Persistence)
    try:
        # We send the finalized pair to Letta so it 'records' it in its memory blocks
        letta.send_message(f"Usuário: {question}\nZiva: {generation}")
    except Exception as e:
        if VERBOSE:
            print(f"Letta Persistence Error: {e}")
            
    return {"generation": generation, "is_refusal": False}

# from core.tools.kiwix import KiwixClient


def offline_search(state: AgentState) -> Dict[str, Any]:
    """
    Search offline verification (Kiwix).
    """
    print(HEXCommandBuilder.exec_cmd("OFFLINE_SEARCH"))
    question = state["question"]

    from core.tools.kiwix import KiwixClient
    kiwix = KiwixClient()
    results = kiwix.search(question, num_results=2)

    documents = []
    if results:
        print(HEXCommandBuilder.read(f"Found {len(results)} articles in Kiwix."))
        for r in results:
            # Fetch full content for the best result
            content = kiwix.get_page_content(r["url"])
            doc_str = f"Source: Kiwix (Offline)\nTitle: {r['title']}\nURL: {r['url']}\n\n{content}"
            documents.append(doc_str)
            print(HEXCommandBuilder.read(f"Read article: {r['title']}"))
    else:
        print(HEXCommandBuilder.think("No Kiwix results found."))

    retry_count = state.get("retry_count", 0) + 1
    return {"documents": documents,
            "question": question, "retry_count": retry_count}

# from core.tools.searxng import SearXNGClient
# from core.tools.scraper import PlaywrightScraper


def web_search(state: AgentState) -> Dict[str, Any]:
    """
    Search via SearXNG (Fast RAG Mode).
    Prioritizes direct summaries from search engine to match 'fast_rag.py' quality.
    """
    if VERBOSE:
        print(HEXCommandBuilder.exec_cmd("WEB_SEARCH (FAST MODE)"))
    question = state["question"]
    
    import json
    from core.tools.searxng import SearXNGClient
    from core.telemetry import TelemetryManager
    import time
    
    start_time = time.time()
    documents = []
    error_msg = None
    
    try:
        if VERBOSE:
             print(HEXCommandBuilder.tool("searxng_fast", question))
             
        client = SearXNGClient()
        # Use HTML scraping mode implicitly via the client
        results = client.search(question, num_results=3)
        
        if results:
            if VERBOSE:
                print(HEXCommandBuilder.read(f"Found {len(results)} results (SearXNG)."))
                
            # Combine into a single detailed context document (mimicking fast_rag.py)
            context_text = f"--- CONTEXTO WEB (SEARXNG) PARA: '{question}' ---\n"
            
            for i, result in enumerate(results): 
                title = result.get('title', 'Sem título')
                snippet = result.get('snippet', 'Sem resumo disponível')
                url = result.get('url', 'N/A')
                
                context_text += f"[{i+1}] Título: {title}\n    Resumo: {snippet}\n    Fonte: {url}\n\n"
                
            documents.append(context_text)
            
            # --- AUTO-INGESTION (Optional) ---
            try:
                if VERBOSE:
                     print(HEXCommandBuilder.think("Auto-ingesting search summary to vector store..."))
                emb = embedder.embedding(context_text)
                if emb:
                    rag.vector_store.add_text(context_text, emb, {
                        "source": "searxng_fast_rag", 
                        "title": f"Search: {question}",
                        "type": "web_search_summary"
                    })
            except Exception as e:
                if VERBOSE:
                    print(HEXCommandBuilder.think(f"Auto-ingestion failed (non-critical): {e}"))
                pass

        else:
             if VERBOSE:
                  print(HEXCommandBuilder.read("SearXNG returned no results."))
                  
    except Exception as e:
        error_msg = str(e)
        if VERBOSE:
             print(HEXCommandBuilder.think(f"SearXNG Error: {e}"))
        documents.append(f"Search Error: {e}")

    # Log Telemetry
    TelemetryManager.log_tool_execution(
        tool="web_search",
        start_time=start_time,
        status="error" if error_msg else "success",
        input_val=question,
        error=error_msg
    )

    retry_count = state.get("retry_count", 0) + 1
    return {"documents": documents,
            "question": question, "retry_count": retry_count}


def reflection_node(state: AgentState) -> Dict[str, Any]:
    """
    Analyzes the quality of the interaction and stores lessons.
    """
    if VERBOSE:
        print(HEXCommandBuilder.exec_cmd("REFLECTION"))
        
    question = state["question"]
    documents = state.get("documents", [])
    generation = state["generation"]
    
    # Skip reflection for refusals (nothing to learn except "I don't know")
    if state.get("is_refusal"):
        return {"reflection": None}

    # Execute Reflection
    try:
        if VERBOSE:
            print(HEXCommandBuilder.think("Analyzing interaction quality..."))
            
        result = reflector.reflect(question, documents, generation)
        
        if VERBOSE:
            print(HEXCommandBuilder.read(f"Reflection Score: {result.get('score')}/5"))
            print(HEXCommandBuilder.read(f"Critique: {result.get('critique')}"))
            print(HEXCommandBuilder.read(f"Lesson: {result.get('lesson')}"))
            
        # Persist Reflection
        reflector.save_reflection(result, question, generation)
            
        return {"reflection": result}
        
    except Exception as e:
        print(f"Reflection Node Error: {e}")
        return {"reflection": None}
