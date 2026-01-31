"""
Routing node for specialized searches.
"""
from typing import Dict, Any
from core.agent.state import AgentState
from core.agent.router import route_query


def route_search(state: AgentState) -> Dict[str, Any]:
    """
    Route query to appropriate search based on content analysis.

    Routes to:
    - anime_search: Anime/manga queries
    - sherlock_search: OSINT/username queries
    - web_search: Default fallback

    Args:
        state: Current agent state

    Returns:
        Next node name to execute
    """
    print("---ROUTE SEARCH---")
    question = state["question"]

    # Determine routing
    next_node = route_query(question)

    print(f"  🎯 Routing to: {next_node}")

    # Return the routing decision
    # This will be used by conditional edges in the graph
    state["route_decision"] = next_node

    return {"route_decision": next_node}
