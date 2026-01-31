
from langchain_core.messages import HumanMessage
from core.graph.ziva_graph import analyze_node, AgentState
import sys
import os
import logging

# Setup paths and logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DebugToolSelection")


def test_tool_selection(query):
    logger.info(f"Testing query: '{query}'")

    # Mock initial state
    state: AgentState = {
        "input": query,
        "messages": [HumanMessage(content=query)],
        "rag_context": "",
        "tool_needed": False,
        "analysis": "",
        "retry_count": 0,
        "validation_errors": []
    }

    try:
        result = analyze_node(state)
        tool_needed = result.get("tool_needed", False)
        analysis = result.get("analysis", "No analysis")

        logger.info(f"Result: tool_needed={tool_needed}")
        logger.info(f"Analysis: {analysis}")

        # Check messages for tool calls
        messages = result.get("messages", [])
        if messages:
            last_msg = messages[-1]
            if hasattr(last_msg, 'tool_calls'):
                logger.info(f"Tool Calls found: {len(last_msg.tool_calls)}")
                for tc in last_msg.tool_calls:
                    logger.info(f" - Tool: {tc['name']}, Args: {tc['args']}")
            else:
                logger.info("No tool_calls in last message.")
        else:
            logger.info("No messages returned.")

        return tool_needed

    except Exception as e:
        logger.error(f"Error executing analyze_node: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    query = "qual o valor do bitcoin hoje"
    if len(sys.argv) > 1:
        query = sys.argv[1]

    test_tool_selection(query)
