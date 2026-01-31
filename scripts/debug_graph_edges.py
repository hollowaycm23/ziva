from core.graph.ziva_graph import workflow


def debug_graph():
    print("Nodes:", workflow.nodes.keys())
    # Accessing edges in StateGraph is tricky as they are internal,
    # but we can check if compiling works and runs a simple path.

    app = workflow.compile()
    print("Graph compiled successfully.")

    # Test path: Input with tool need
    initial_state = {
        "input": "test request",
        "tool_needed": True  # Mocking previous step
    }

    # We can't easily mock the internal state transition without running it.
    # But we can check if the node function is correct.
    from core.graph.nodes.lookup_tool import lookup_tool_node
    print(f"Lookup Node Function: {lookup_tool_node}")


if __name__ == "__main__":
    debug_graph()
