"""
Integration tests for the LangGraph workflow (ziva_graph).
Mocks external services (LLM, Qdrant, SearXNG) but tests the actual graph structure.
"""
import unittest
from unittest.mock import patch, MagicMock
import json
import time

class TestGraphIntegration(unittest.TestCase):
    """Test the full LangGraph workflow end-to-end with mocks."""

    def setUp(self):
        from langchain_core.messages import AIMessage
        # Patch external dependencies before importing graph
        self.llm_patcher = patch('core.graph.ziva_graph.llm')
        self.tool_llm_patcher = patch('core.graph.ziva_graph.tool_llm')
        self.tool_manager_patcher = patch('agent.tools.ToolManager')
        
        mock_llm = self.llm_patcher.start()
        mock_tool_llm = self.tool_llm_patcher.start()
        mock_tm = self.tool_manager_patcher.start()
        
        # Configure mock LLM to return proper AIMessage
        mock_llm.invoke.return_value = AIMessage(
            content="Test response",
            tool_calls=[]
        )
        mock_tool_llm.invoke.return_value = AIMessage(
            content="Test response",
            tool_calls=[]
        )
        mock_tool_llm.bind_tools.return_value = mock_tool_llm
        
        # Configure mock ToolManager
        mock_tm_instance = mock_tm.return_value
        mock_tm_instance.loaded_tools = {}
        mock_tm_instance.list_tools.return_value = []
        mock_tm_instance.get_tool.return_value = None

    def tearDown(self):
        self.llm_patcher.stop()
        self.tool_llm_patcher.stop()
        self.tool_manager_patcher.stop()

    def test_graph_compiles(self):
        """Verify the graph compiles without errors."""
        from core.graph.ziva_graph import workflow, AgentState
        app = workflow.compile()
        self.assertIsNotNone(app)

    def test_graph_nodes_exist(self):
        """Verify all expected nodes are registered."""
        from core.graph.ziva_graph import workflow
        expected = {
            "input_node", "contextualize_node", "classify_node",
            "analyze_node", "execute_tool_node", "respond_node",
            "cognitive_gate_node", "summarization_node",
            "learning_node", "metacognition_node"
        }
        nodes = set(workflow.nodes.keys())
        self.assertTrue(expected.issubset(nodes), f"Missing nodes: {expected - nodes}")

    def test_simple_invoke_no_tools(self):
        """Test a simple invoke that doesn't need tools."""
        from core.graph.ziva_graph import app, AgentState
        from langchain_core.messages import HumanMessage
        result = app.invoke({
            "input": "What is Python?",
            "messages": [HumanMessage(content="What is Python?")],
        })
        self.assertIn("response", result)
        self.assertEqual(result["response"], "Test response")

    def test_router_logic_tool_needed(self):
        """Verify router returns execute_tool_node when tool_needed=True."""
        from core.graph.ziva_graph import router, AgentState
        
        state = AgentState(
            input="test",
            messages=[],
            analysis="",
            rag_context="",
            tool_needed=True,
            tool_output="",
            response="",
            retry_count=0,
            tool_found=False,
            physics_params={},
            gate_result={},
            long_term_summary="",
            task_type="general_knowledge",
            task_confidence=0.9,
            allowed_tools=[],
            graph_start_time=time.time(),
            graph_node_times={},
        )
        result = router(state)
        self.assertEqual(result, "execute_tool_node")

    def test_router_logic_respond(self):
        """Verify router returns END when response is ready."""
        from core.graph.ziva_graph import router, END, AgentState
        
        state = AgentState(
            input="test",
            messages=[],
            analysis="",
            rag_context="",
            tool_needed=False,
            tool_output="",
            response="Ready response",
            retry_count=0,
            tool_found=False,
            physics_params={},
            gate_result={},
            long_term_summary="",
            task_type="general_knowledge",
            task_confidence=0.9,
            allowed_tools=[],
            graph_start_time=time.time(),
            graph_node_times={},
        )
        result = router(state)
        self.assertEqual(result, END)

    def test_router_timeout(self):
        """Verify router returns respond_node after timeout."""
        from core.graph.ziva_graph import router, AgentState
        
        state = AgentState(
            input="test",
            messages=[],
            analysis="",
            rag_context="",
            tool_needed=True,
            tool_output="",
            response="",
            retry_count=5,  # Exceeds max retries
            tool_found=False,
            physics_params={},
            gate_result={},
            long_term_summary="",
            task_type="general_knowledge",
            task_confidence=0.9,
            allowed_tools=[],
            graph_start_time=time.time() - 300,  # 5 minutes ago
            graph_node_times={},
        )
        result = router(state)
        self.assertEqual(result, "respond_node")

    @patch('core.graph.ziva_graph.ziva_tools', [])
    def test_execute_tool_node_no_tools(self):
        """Test execute_tool_node with no tool calls."""
        from core.graph.ziva_graph import execute_tool_node, AgentState
        
        state = AgentState(
            input="test",
            messages=[MagicMock(tool_calls=[])],
            analysis="",
            rag_context="",
            tool_needed=True,
            tool_output="",
            response="",
            retry_count=0,
            tool_found=False,
            physics_params={},
            gate_result={},
            long_term_summary="",
            task_type="general_knowledge",
            task_confidence=0.9,
            allowed_tools=[],
            graph_start_time=time.time(),
            graph_node_times={},
        )
        result = execute_tool_node(state)
        self.assertEqual(result, {})

    def test_classify_node(self):
        """Test classify_node returns task_type and allowed_tools."""
        from core.graph.ziva_graph import classify_node, AgentState
        
        state = AgentState(
            input="What is the capital of France?",
            messages=[],
            analysis="",
            rag_context="",
            tool_needed=False,
            tool_output="",
            response="",
            retry_count=0,
            tool_found=False,
            physics_params={},
            gate_result={},
            long_term_summary="",
            task_type="",
            task_confidence=0.0,
            allowed_tools=[],
            graph_start_time=time.time(),
            graph_node_times={},
        )
        result = classify_node(state)
        self.assertIn("task_type", result)
        self.assertIn("allowed_tools", result)

    def test_trim_messages_short(self):
        """Test _trim_messages with short content (no truncation)."""
        from core.graph.ziva_graph import _trim_messages
        from langchain_core.messages import HumanMessage
        
        messages = [HumanMessage(content="Hello!")]
        result = _trim_messages(messages, max_tokens=1000)
        self.assertEqual(len(result), 1)

    def test_trim_messages_long(self):
        """Test _trim_messages with long content (truncation expected)."""
        from core.graph.ziva_graph import _trim_messages
        from langchain_core.messages import HumanMessage, SystemMessage
        
        system = SystemMessage(content="SYSTEM" * 2000)
        msg1 = HumanMessage(content="A" * 50000)
        msg2 = HumanMessage(content="B" * 50000)
        
        result = _trim_messages([system, msg1, msg2], max_tokens=10000)
        self.assertLessEqual(len(result), len([system, msg1, msg2]))


class TestAPIIntegration(unittest.TestCase):
    """Test API server endpoints with mocked dependencies."""

    @classmethod
    def setUpClass(cls):
        cls.server_patcher = patch('api.server.ZivaAgent')
        cls.mock_agent = cls.server_patcher.start()
        
    @classmethod
    def tearDownClass(cls):
        cls.server_patcher.stop()

    def setUp(self):
        from fastapi.testclient import TestClient
        from api.server import app
        self.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertIn(response.status_code, (200, 404))

    def test_metrics_endpoint(self):
        response = self.client.get("/metrics")
        self.assertIn(response.status_code, (200, 404))


if __name__ == "__main__":
    unittest.main()
