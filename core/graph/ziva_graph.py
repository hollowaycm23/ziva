from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from rag.retrieval.research_augmenter import get_research_augmenter
from core.reranker import get_reranker
import logging
from core.memory.ziva_memory import ZivaMemory
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph.message import add_messages
import json
import os
from core.auditor import Auditor
from agent.tools import ToolManager
from core.tool_wrapper import get_langchain_tools
from core.gate.cognitive_check import EulerPoinsotGate
import re
from core.runtime_client import runtime
import time
from core.config import config
from core.agent.context_node import contextualize_node

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

def analyze_node(state: AgentState):
    node_name = "analyze_node"
    try:
        formatted_context = state.get("rag_context", "")
        augmenter = get_research_augmenter()
        current_query = state["input"]
        
        # Determine if we need more context
        is_context_useful = formatted_context.strip() and "[Nota:" not in formatted_context
        
        if not is_context_useful:
             logger.info("🔍 Local context empty/weak. Triggering Web Search...")
             additional_info = augmenter.research(current_query, ['sources'])
             formatted_context = augmenter.format_additional_info(additional_info)
        
        if state.get("tool_output"):
            formatted_context += f"\n\n[PREVIOUS TOOL OUTPUT]:\n{state['tool_output']}"

        # Setup reasoning environment
        llm_with_tools = tool_llm.bind_tools(ziva_tools)
        long_term_summary = state.get("long_term_summary", "Sem histórico relevante.")
        
        system_prompt = f"""You are Ziva, an Elite AI Assistant.
        CONTEXT: {formatted_context}
        LONG-TERM MEMORY: {long_term_summary}
        
        INSTRUCTIONS:
        1. If CONTEXT has the answer, synthesize it completely and technically.
        2. If CONTEXT contains 'Sem descrição' or is insufficient, YOU MUST USE web_search.
        3. Do NOT give just links. EXPLAIN and SYNTHESIZE knowledge.
        4. ANSWER IN PORTUGUESE (pt-BR).
        """
        
        ai_response = llm_with_tools.invoke([HumanMessage(content=system_prompt + f"\n\nUser: {current_query}")])
        
        # Heuristic for Physics
        physics_params = {}
        if any(k in current_query.lower() for k in ["euler", "gate", "rigid body"]):
            physics_params = {"I": [1,2,3], "omega0": [1,1,1], "dt": 0.01, "total_time": 5.0}

        return {
            "messages": [ai_response],
            "rag_context": formatted_context,
            "tool_needed": len(ai_response.tool_calls) > 0,
            "physics_params": physics_params
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
    response_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are ZIVA, a high-authority Autonomous Intelligence.
        
        CORE DIRECTIVES:
        1. SYNTHESIZE EVERYTHING: Use RAG Context + Tool Output to build a complete answer.
        2. BE PRECISE AND DETAILED: Avoid superficial responses. Use facts, dates, and technical details.
        3. AUTHORITATIVE STYLE: Answer with confidence. Support claims with the provided context.
        4. LANGUAGE: ALWAYS Portuguese (pt-BR).
        
        [CONTEXT]
        {rag_context}
        [TOOL OUTPUT]
        {tool_output}
        """),
        ("human", "{input}")
    ])
    chain = response_prompt | llm
    res = chain.invoke({
        "input": state["input"],
        "rag_context": state["rag_context"],
        "tool_output": state.get("tool_output", "Nenhum resultado de ferramenta.")
    })
    return {"response": res.content}

def cognitive_gate_node(state: AgentState):
    params = state.get("physics_params", {})
    if not params: return {"gate_result": {"passed": True}}
    gate = EulerPoinsotGate()
    result = gate.check_physics(params["I"], params["omega0"], params["dt"], params["total_time"])
    return {"gate_result": result}

def summarization_node(state: AgentState):
    # Auto-summarization implementation can be restored here later
    return {}

def learning_node(state: AgentState):
    # Auto-learning implementation can be restored here later
    return {}

def metacognition_node(state: AgentState):
    return {}

# Graph Workflow Construction
workflow = StateGraph(AgentState)
workflow.add_node("input_node", input_node)
workflow.add_node("contextualize_node", contextualize_node)
workflow.add_node("analyze_node", analyze_node)
workflow.add_node("execute_tool_node", execute_tool_node)
workflow.add_node("respond_node", respond_node)
workflow.add_node("cognitive_gate_node", cognitive_gate_node)
workflow.add_node("summarization_node", summarization_node)
workflow.add_node("learning_node", learning_node)
workflow.add_node("metacognition_node", metacognition_node)

workflow.set_entry_point("input_node")
workflow.add_edge("input_node", "contextualize_node")
workflow.add_edge("contextualize_node", "analyze_node")

def router(state: AgentState):
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