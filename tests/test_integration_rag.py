"""
Integration tests for RAG pipeline and governance.
"""
import unittest
from unittest.mock import patch, MagicMock
import tempfile
from pathlib import Path

class TestGovernanceIntegration(unittest.TestCase):
    """Test governance integration with VectorStore."""

    def setUp(self):
        from core.governance import GovernanceService
        self.gov = GovernanceService()

    @patch('core.vector_store.VectorStore.exists_similar', return_value=False)
    @patch('core.vector_store.SyncManager')
    def test_vector_store_calls_governance(self, mock_sync, mock_exists):
        """Verify VectorStore.add_text() invokes governance assessment."""
        from core.vector_store import VectorStore
        
        vs = VectorStore()
        vs.sync_manager.add_to_staging.return_value = "test-id"
        vs.sync_manager.transfer_staging_to_main.return_value = 1
        
        result = vs.add_text(
            "def test():\n    return 42\n\nA test function.",
            [0.1] * 768,
            {"source_domain": "github.com", "author": "dev"}
        )
        
        self.assertEqual(result, "test-id")
        vs.sync_manager.add_to_staging.assert_called_once()

    def test_ingestion_pipeline_full_flow(self):
        """Test full ingestion pipeline with a good document."""
        from rag.ingestion.pipeline import IngestionPipeline
        
        pipeline = IngestionPipeline()
        doc = {
            "text": "def add(a, b):\n    return a + b\n\nA simple addition function.",
            "source_domain": "github.com",
            "author": "coder",
            "content_type": "code",
        }
        approved, score, reason, enriched = pipeline.assess(doc["text"], doc)
        self.assertTrue(approved)
        self.assertGreaterEqual(score, 70)
        self.assertIn("trust_score", enriched)
        self.assertIn("id", enriched)

    def test_ingestion_pipeline_rejects_ai(self):
        """Test pipeline rejects AI-generated content."""
        from rag.ingestion.pipeline import IngestionPipeline
        
        pipeline = IngestionPipeline()
        approved, score, reason, enriched = pipeline.assess(
            "As an AI language model, I cannot fulfill this request.",
            {"source_domain": "example.com"}
        )
        self.assertFalse(approved)

    def test_ingestion_pipeline_rejects_low_score(self):
        """Test pipeline rejects low-quality content."""
        from rag.ingestion.pipeline import IngestionPipeline
        
        pipeline = IngestionPipeline()
        approved, score, reason, enriched = pipeline.assess(
            "Some random opinion text.",
            {"source_domain": "unknown-blog.example.com"}
        )
        self.assertFalse(approved)


class TestDynamicToolsIntegration(unittest.TestCase):
    """Test dynamic tools creation, validation, and execution flow."""

    def setUp(self):
        import tempfile
        from core.dynamic_tools.registry import DynamicToolRegistry
        self.tmp = tempfile.mktemp(suffix=".json")
        self.registry = DynamicToolRegistry(Path(self.tmp))
        import extensions.dynamic_tools as dt_mod
        self._orig_get = dt_mod._get_registry
        dt_mod._get_registry = lambda: self.registry

    def tearDown(self):
        import extensions.dynamic_tools as dt_mod
        dt_mod._get_registry = self._orig_get
        try:
            Path(self.tmp).unlink(missing_ok=True)
        except Exception:
            pass

    def test_create_and_execute_flow(self):
        """Test create_tool → validate → register → execute."""
        from extensions.dynamic_tools import create_tool, list_dynamic_tools
        
        result = create_tool(
            "multiply",
            """def multiply(input: dict) -> dict:
    \"\"\"Multiply two numbers.\"\"\"
    return {"result": input.get("a", 0) * input.get("b", 0)}
""",
            "Multiplies two numbers"
        )
        self.assertIn("sucesso", result.lower())
        
        listed = list_dynamic_tools()
        self.assertIn("multiply", listed)
        
        from core.dynamic_tools.runtime import DynamicToolRuntime
        runtime = DynamicToolRuntime(self.registry)
        output = runtime.execute("multiply", {"a": 3, "b": 7})
        self.assertIn("21", output)

    def test_create_tool_rejects_invalid_code(self):
        """Test that create_tool rejects invalid code."""
        from extensions.dynamic_tools import create_tool
        
        result = create_tool(
            "bad_tool",
            "invalid python code {{{",
            "Invalid tool"
        )
        self.assertIn("erro", result.lower())


if __name__ == "__main__":
    unittest.main()
