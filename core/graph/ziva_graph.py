from langchain_openai import ChatOpenAI
from rag.retrieval.research_augmenter import get_research_augmenter
import logging
from datetime import datetime
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langgraph.graph.message import add_messages
from agent.tools import ToolManager
from core.tool_wrapper import get_langchain_tools
from core.gate.cognitive_check import EulerPoinsotGate
from core.config import config
from core.agent.context_node import contextualize_node
from core.classifier.query_classifier import get_query_classifier

logger = logging.getLogger(__name__)

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


# LLM Configuration
primary_model_config = config.get_llm_provider("agent.primary_model")
if primary_model_config:
    logger.info(f"🔌 Initializing Graph LLMs for {primary_model_config['model_name']}...")
    llm = ChatOpenAI(
        model=primary_model_config["model_name"],
        openai_api_base=primary_model_config["base_url"],
        openai_api_key=primary_model_config["api_key"],
        temperature=0.3,
        request_timeout=120
    )
    coder_config = config.get_llm_provider("agent.coder_model")
    tool_llm = ChatOpenAI(
        model=coder_config["model_name"] if coder_config else primary_model_config["model_name"],
        openai_api_base=coder_config["base_url"] if coder_config else primary_model_config["base_url"],
        openai_api_key=coder_config["api_key"] if coder_config else primary_model_config["api_key"],
        temperature=0.0,
        request_timeout=120
    )
else:
    raise RuntimeError("Critical: No LLM configuration found in ziva.yaml")


def input_node(state: AgentState):
    return {"input": state.get("input", "")}


def classify_node(state: AgentState):
    classifier = get_query_classifier()
    query = state.get("input", "")
    task_type, confidence, _ = classifier.classify(query)
    allowed = classifier.get_allowed_tools(task_type)
    logger.info("📋 Task classified as '%s' (conf=%.2f) with %d allowed tools",
                task_type, confidence, len(allowed))
    return {
        "task_type": task_type,
        "task_confidence": confidence,
        "allowed_tools": allowed,
    }


def analyze_node(state: AgentState):
    try:
        formatted_context = state.get("rag_context", "")
        current_query = state["input"]
        task_type = state.get("task_type", "general_knowledge")

        # Skip RAG search for simple task types that don't need external data
        NO_SEARCH_TASKS = {"greeting", "sentiment", "chitchat", "off_topic"}
        if task_type in NO_SEARCH_TASKS:
            logger.info("🔇 Skipping RAG search for task '%s'", task_type)
        else:
            augmenter = get_research_augmenter()
            is_context_useful = formatted_context.strip() and "[Nota:" not in formatted_context
            if not is_context_useful:
                logger.info("🔍 Local context empty/weak. Triggering Web Search...")
                additional_info = augmenter.research(current_query, ['completeness', 'accuracy', 'sources', 'relevance'])
                formatted_context = augmenter.format_additional_info(additional_info)

        if state.get("tool_output"):
            formatted_context += f"\n\n[PREVIOUS TOOL OUTPUT]:\n{state['tool_output']}"

        # Filter tools based on task classification
        task_type = state.get("task_type", "general_knowledge")
        allowed_names = state.get("allowed_tools", [])
        filtered_tools = []
        if allowed_names:
            filtered_tools = [t for t in ziva_tools if t.name in allowed_names]
            logger.info("🔧 Using %d/%d tools for task '%s'",
                        len(filtered_tools), len(ziva_tools), task_type)
        else:
            logger.info("🔧 No tools needed for task '%s'", task_type)
        llm_with_tools = tool_llm.bind_tools(filtered_tools) if filtered_tools else tool_llm
        long_term_summary = state.get("long_term_summary", "Sem histórico relevante.")

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        weekday = datetime.now().strftime('%A')
        system_prompt = f"""You are Ziva, an AI assistant with REAL-TIME WEB SEARCH.
CURRENT DATE AND TIME: {now}
CURRENT WEEKDAY: {weekday}
LONG-TERM MEMORY: {long_term_summary}

CRITICAL INSTRUCTION:
CONTEXT below contains REAL-TIME web search results.
Use CONTEXT when it has the answer. If CONTEXT is empty or insufficient, call web_search or get_current_datetime.
If unsure after searching, say "Não encontrei na busca."
Answer in Portuguese (pt-BR).

CONTEXT (web results):
{formatted_context}
"""

        ai_response = llm_with_tools.invoke([HumanMessage(content=system_prompt + f"\n\nUser: {current_query}")])

        physics_params = {}
        if any(k in current_query.lower() for k in ["euler", "gate", "rigid body"]):
            physics_params = {"I": [1, 2, 3], "omega0": [1, 1, 1], "dt": 0.01, "total_time": 5.0}

        return {
            "messages": [ai_response],
            "rag_context": formatted_context,
            "tool_needed": len(ai_response.tool_calls) > 0,
            "physics_params": physics_params,
            "retry_count": state.get("retry_count", 0) + (1 if len(ai_response.tool_calls) > 0 else 0)
        }
    except Exception as e:
        logger.error(f"Error in analyze_node: {e}")
        return {"tool_needed": False}


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

    return {"messages": new_messages, "tool_output": "\n".join([m.content for m in new_messages])}


def respond_node(state: AgentState):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    weekday = datetime.now().strftime('%A')
    response_prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are ZIVA - answer from the data below.
CURRENT DATE AND TIME: {now}
CURRENT WEEKDAY: {weekday}

RULES:
- If CONTEXT has the answer, use it and cite sources.
- If CONTEXT is empty, you MAY use your general knowledge for factual/time/simple queries.
- If the user asks for an image: describe in text and provide source links.
- Explicitly cite the source text that supports your answer.

[CONTEXT - Web Search Results]
{{rag_context}}

[TOOL OUTPUT]
{{tool_output}}
"""),
        ("human", "{input}")
    ])
    chain = response_prompt | llm
    res = chain.invoke({
        "input": state["input"],
        "rag_context": state.get("rag_context", ""),
        "tool_output": state.get("tool_output", "Nenhum resultado de ferramenta.")
    })
    return {"response": res.content}


def cognitive_gate_node(state: AgentState):
    params = state.get("physics_params", {})
    if not params:
        return {"gate_result": {"passed": True}}
    gate = EulerPoinsotGate()
    result = gate.check_physics(params["I"], params["omega0"], params["dt"], params["total_time"])
    return {"gate_result": result}


def summarization_node(state: AgentState):
    return {}


def learning_node(state: AgentState):
    return {}


def metacognition_node(state: AgentState):
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
    if retry_count >= 3:
        return "respond_node"
    if state.get("physics_params") and not state.get("gate_result"):
        return "cognitive_gate_node"
    if state.get("tool_needed"):
        return "execute_tool_node"
    return "respond_node"


workflow.add_conditional_edges("analyze_node", router, {
    "execute_tool_node": "execute_tool_node",
    "respond_node": "respond_node",
    "cognitive_gate_node": "cognitive_gate_node"
})

workflow.add_edge("cognitive_gate_node", "respond_node")
workflow.add_edge("execute_tool_node", "analyze_node")
workflow.add_edge("respond_node", "summarization_node")
workflow.add_edge("summarization_node", "learning_node")
workflow.add_edge("learning_node", "metacognition_node")
workflow.add_edge("metacognition_node", END)

app = workflow.compile()
