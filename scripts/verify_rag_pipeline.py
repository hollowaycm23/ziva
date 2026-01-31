
import logging
from rag.ingestion.pipeline import IngestionPipeline
# Mock ZivaMemory to avoid actual Qdrant calls during strictly unit testing script
# But since we want to verify integration, we might want real calls or a mock class.
# Let's use a mock for speed and safety in this script.


class MockMemory:
    def __init__(self):
        self.saved = []

    def recall(self, text, limit=1, min_score=0.5):
        if "duplicate" in text:
            # Fake a return object
            class MockEntry:
                metadata = {"id": "123"}
            return [MockEntry()]
        return []

    def save(self, text, quadrant, metadata, importance):
        self.saved.append({"text": text, "metadata": metadata})


print("Starting RAG Pipeline Verification...")

pipeline = IngestionPipeline(memory_system=MockMemory())

# Test 1: Trusted Document
print("Test 1: Trusted Document...")
doc_trusted = {
    "text": "The Python programming language syntax is designed to be readable.",
    "source_domain": "python.org",
    "author": "Guido",
    "date": "2024-01-01",
    "content_type": "documentation"}
if pipeline.process_document(doc_trusted):
    print("SUCCESS: Trusted document accepted.")
else:
    print("FAILED: Trusted document rejected.")
    exit(1)

# Test 2: Low Trust Document
print("Test 2: Low Trust Document...")
doc_untrusted = {
    "text": "Some random blog post opinion.",
    "source_domain": "random-blog.xyz",
    "date": "2020-01-01"
}
if not pipeline.process_document(doc_untrusted):
    print("SUCCESS: Untrusted document rejected.")
else:
    print("FAILED: Untrusted document accepted.")
    exit(1)

# Test 3: AI Content
print("Test 3: AI Content...")
doc_ai = {
    "text": "As an AI language model, I cannot provide that information.",
    "source_domain": "unknown.com"
}
if not pipeline.process_document(doc_ai):
    print("SUCCESS: AI content rejected.")
else:
    print("FAILED: AI content accepted.")
    exit(1)

print("\nALL RAG PIPELINE CHECKS PASSED.")
