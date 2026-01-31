from langgraph.prebuilt import create_react_agent
import os
from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from agent.tools import ToolManager
from core.tool_wrapper import get_langchain_tools


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next: str


MODEL_NAME = os.getenv("MODEL_NAME", "ziva-base:latest")
TOOL_MODEL_NAME = os.getenv("TOOL_MODEL_NAME", "qwen2.5-coder:7b")

supervisor_llm = ChatOllama(model=MODEL_NAME, temperature=0)
coder_llm = ChatOllama(model=TOOL_MODEL_NAME, temperature=0)
researcher_llm = ChatOllama(model=MODEL_NAME, temperature=0)

members = ["Researcher", "Coder"]
options = ["FINISH"] + members

system_prompt = (
    "You are the Supervisor of a team of AI agents: {members}.\n"
    "Your goal is to orchestrate the team to solve the user's request.\n"
    "1. RESEARCHER: For gathering information or web search.\n"
    "2. CODER: For writing code, fixing bugs, or executing commands.\n"
    "\n"
    "Given the conversation below, who should act next?\n"
    "Select one of: {options}\n"
    "If the task is complete, select FINISH.")

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="messages"),
    ("system",
     "Who should act next? Return ONLY the name of the role: {options}")
]).partial(options=str(options), members=", ".join(members))


def supervisor_node(state: AgentState):
    chain = prompt | supervisor_llm
    response = chain.invoke(state)
    content = response.content.strip().replace("'", "").replace('"', "")
    selected = "FINISH"
    for option in options:
        if option.upper() in content.upper():
            selected = option
            break
    if selected == "FINISH" and "FINISH" not in content.upper():
        selected = "Researcher"
    return {"next": selected}


def create_agent_node(agent_llm, name: str, tools: list = []):
    """
    Factory to create a node for a specific agent.
    """
    role_prompt = f"You are {name}. Solve the user's request with your tools."
    agent_executor = create_react_agent(agent_llm, tools, prompt=role_prompt)

    def agent_node(state: AgentState):
        result = agent_executor.invoke(state)
        old_len = len(state["messages"])
        new_messages = result["messages"][old_len:]
        return {"messages": new_messages}
    return agent_node


tool_manager = ToolManager()
all_tools = get_langchain_tools(tool_manager)

research_keywords = ["search", "read", "weather", "currency", "rag"]
coding_keywords = ["code", "file", "command", "usb", "bluetooth"]

research_tools = [t for t in all_tools if any(
    k in t.name.lower() for k in research_keywords)]
coding_tools = [t for t in all_tools if any(
    k in t.name.lower() for k in coding_keywords)]

if not research_tools:
    research_tools = all_tools
if not coding_tools:
    coding_tools = all_tools

research_node = create_agent_node(
    researcher_llm, "Researcher", research_tools)
coder_node = create_agent_node(coder_llm, "Coder", coding_tools)

workflow = StateGraph(AgentState)
workflow.add_node("Supervisor", supervisor_node)
workflow.add_node("Researcher", research_node)
workflow.add_node("Coder", coder_node)
workflow.set_entry_point("Supervisor")


def route_supervisor(state: AgentState):
    return state["next"]


workflow.add_conditional_edges(
    "Supervisor",
    route_supervisor,
    {
        "Researcher": "Researcher",
        "Coder": "Coder",
        "FINISH": END
    }
)

workflow.add_edge("Researcher", "Supervisor")
workflow.add_edge("Coder", "Supervisor")

supervisor_app = workflow.compile()