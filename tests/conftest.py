import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)

@pytest.fixture
def mock_llm():
    """Mock LLMService that returns predictable embeddings and completions."""
    with patch('core.llm.LLMService') as mock:
        instance = mock.return_value
        instance.embedding.return_value = [0.1] * 768
        instance.completion.return_value = "Mocked response"
        yield instance

@pytest.fixture
def mock_vector_store():
    """Mock VectorStore that stores in memory."""
    with patch('core.vector_store.VectorStore') as mock:
        instance = mock.return_value
        instance.add_text.return_value = "mock-id-123"
        instance.search.return_value = [
            {"text": "Mock result", "score": 0.95, "metadata": {"source": "test"}}
        ]
        yield instance

@pytest.fixture
def mock_qdrant_client():
    """Mock QdrantClient."""
    with patch('qdrant_client.QdrantClient') as mock:
        instance = mock.return_value
        instance.get_collection.side_effect = Exception("Not found")
        instance.create_collection.return_value = None
        instance.upsert.return_value = None
        instance.query_points.return_value = MagicMock(points=[])
        instance.count.return_value = MagicMock(count=0)
        yield instance

@pytest.fixture
def sample_document():
    return {
        "text": "def hello():\n    return 'world'\n\nA Python function.",
        "source_domain": "github.com",
        "author": "developer",
        "date": "2026-01-15",
        "content_type": "code",
    }
