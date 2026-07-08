import logging
import json
from typing import Dict, Any, Optional
from pathlib import Path
from langchain_core.prompts import PromptTemplate
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import JsonOutputParser
from tools.registry.tool_registry import ToolRegistry
from core.auditor import Auditor

logger = logging.getLogger("LookupTool")

PATTERN_RULES = {}
try:
    pattern_file = Path("/home/holloway/ziva/data/training/tool_patterns.json")
    if pattern_file.exists():
        with open(pattern_file, 'r') as f:
            PATTERN_RULES = json.load(f)
        logger.info(f"Loaded {len(PATTERN_RULES)} pattern rules")
except Exception as e:
    logger.warning(f"Could not load pattern rules: {e}")


def match_tool_by_pattern(query: str) -> Optional[tuple]:
    """
    Match tool using pattern rules.
    """
    query_lower = query.lower()

    for tool_name, patterns in PATTERN_RULES.items():
        for pattern in patterns:
            if pattern in query_lower:
                confidence = 0.9 if len(pattern) > 10 else 0.85
                logger.info(
                    f"Pattern match: '{pattern}' → {tool_name} "
                    f"(confidence: {confidence})")
                return (tool_name, confidence)

    return None


def lookup_tool_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Checks if an existing tool can fulfill the user's request.
    """
    node_name = "lookup_tool_node"
    Auditor.log_event(
        "NODE_START", {"node": node_name, "input": state.get("input")})

    try:
        full_input = state.get("input", "")
        current_query = full_input
        if "User Request:" in full_input:
            current_query = full_input.split("User Request:")[-1].strip()
        elif "\nUser:" in full_input:
            parts = full_input.split("\nUser:")
            if len(parts) > 1:
                current_query = parts[-1].split("\n")[0].strip()

        logger.info(f"🔎 Looking up tool for: '{current_query[:50]}...'")
        registry = ToolRegistry()
        tools = registry.list_tools()
        if not tools:
            return {"tool_found": False}
        tool_list = []
        for name, versions in tools.items():
            latest = versions[-1]
            tool_list.append(f"- {name}: {latest['description']}")
        tools_str = "\n".join(tool_list)
        llm = ChatOllama(model="qwen2.5-coder:7b")
        pattern_match = match_tool_by_pattern(current_query)
        if pattern_match:
            tool_name, confidence = pattern_match
            tool_data = registry.get_tool(tool_name)
            if tool_data and confidence >= 0.85:
                logger.info(
                    f"✅ Pattern match found: {tool_name} "
                    f"(confidence: {confidence})")
                res = {"tool_found": True, "tool_name": tool_name,
                       "tool_code": tool_data["code"],
                       "tool_description": tool_data["description"],
                       "tool_input_schema": tool_data["input_schema"],
                       "tool_output_schema": tool_data["output_schema"],
                       "tool_registered": True}
                Auditor.log_event("NODE_END", {
                    "node": node_name, "output": {
                        "tool_found": True, "tool_name": tool_name,
                        "method": "pattern_match"}})
                return res
        prompt = PromptTemplate.from_template(
            """
            You are a tool selection expert. Select the BEST tool for the CURRENT query.

            CURRENT User Query: {input}

            Available Tools:
            {tools}

            Respond with JSON:
            {{
                "found": true/false,
                "tool_name": "tool_name" or null,
                "confidence": 0.0-1.0,
                "reasoning": "why this tool"
            }}
            """
        )
        chain = prompt | llm | JsonOutputParser()
        result = chain.invoke({"input": state["input"], "tools": tools_str})
        Auditor.log_event(
            "LLM_CALL",
            {"node": node_name, "model": "qwen2.5-coder:7b", "result": result})
        if result.get("found") and result.get("confidence", 0) > 0.8:
            tool_name = result["tool_name"]
            tool_data = registry.get_tool(tool_name)
            if tool_data:
                res = {"tool_found": True, "tool_name": tool_name,
                       "tool_code": tool_data["code"],
                       "tool_description": tool_data["description"],
                       "tool_input_schema": tool_data["input_schema"],
                       "tool_output_schema": tool_data["output_schema"],
                       "tool_registered": True}
                Auditor.log_event("NODE_END", {
                    "node": node_name, "output": {
                        "tool_found": True, "tool_name": tool_name}})
                return res
        Auditor.log_event(
            "NODE_END", {"node": node_name, "output": {"tool_found": False}})
        return {"tool_found": False}
    except Exception as e:
        logger.error(f"Error in lookup_tool_node: {e}")
        Auditor.log_event(
            "NODE_ERROR",
            {"node": node_name, "error": str(e)}, level="ERROR")
        return {"tool_found": False}
