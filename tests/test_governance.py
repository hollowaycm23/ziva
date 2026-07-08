import unittest
from unittest.mock import patch, MagicMock


class TestGovernanceService(unittest.TestCase):
    def setUp(self):
        from core.governance import GovernanceService
        self.gov = GovernanceService()

    def test_approve_good_document(self):
        text = "def hello():\n    return 'world'\n\nThis is a technical document about Python."
        metadata = {
            "source_domain": "python.org",
            "author": "Guido van Rossum",
            "date": "2026-01-01",
            "content_type": "documentation",
        }
        approved, score, reason = self.gov.assess(text, metadata)
        self.assertTrue(approved, f"Expected approved, got: {reason} (score={score})")
        self.assertGreaterEqual(score, 70)

    def test_reject_empty_text(self):
        approved, score, reason = self.gov.assess("", {})
        self.assertFalse(approved)
        self.assertIn("empty", reason.lower())

    def test_reject_ai_content(self):
        text = "As an AI language model, I cannot fulfill this request."
        approved, score, reason = self.gov.assess(text, {"source_domain": "example.com"})
        self.assertFalse(approved)
        self.assertIn("AI", reason)

    def test_reject_low_score(self):
        text = "Some random opinion text without any technical value."
        metadata = {
            "source_domain": "unknown-blog.example.com",
            "author": "",
            "date": "2010-01-01",
            "content_type": "",
        }
        approved, score, reason = self.gov.assess(text, metadata)
        self.assertFalse(approved)
        self.assertIn("below minimum", reason)

    def test_enrich_metadata(self):
        enriched = self.gov.enrich_metadata({"source": "test"}, 85, "some text")
        self.assertIn("trust_score", enriched)
        self.assertEqual(enriched["trust_score"], 85)
        self.assertIn("governance_assessed_at", enriched)
        self.assertIn("governance_assessed_by", enriched)
        self.assertIn("id", enriched)
        self.assertIn("ingested_at", enriched)


class TestTrustScorer(unittest.TestCase):
    def setUp(self):
        from rag.ingestion.trust_scorer import TrustScorer
        self.scorer = TrustScorer()

    def test_source_credibility_top(self):
        score = self.scorer.calculate_trust_score("text", {"source_domain": "python.org"})
        self.assertGreaterEqual(score, 30)

    def test_source_credibility_edu(self):
        score = self.scorer.calculate_trust_score("text", {"source_domain": "mit.edu"})
        self.assertGreaterEqual(score, 25)

    def test_author_bonus(self):
        score_with = self.scorer.calculate_trust_score("text", {"source_domain": "x.org", "author": "John"})
        score_without = self.scorer.calculate_trust_score("text", {"source_domain": "x.org", "author": ""})
        self.assertGreater(score_with, score_without)

    def test_recency_recent(self):
        score = self.scorer.calculate_trust_score("text", {"date": "2026-06-01", "source_domain": "example.com"})
        self.assertGreaterEqual(score, 5)

    def test_recency_old(self):
        old_with = self.scorer.calculate_trust_score("text", {"date": "2000-01-01", "source_domain": "example.com"})
        recent_with = self.scorer.calculate_trust_score("text", {"date": "2026-01-01", "source_domain": "example.com"})
        self.assertGreater(recent_with, old_with)

    def test_technical_structure_code(self):
        text = "```python\ndef hello():\n    pass\n```"
        score = self.scorer.calculate_trust_score(text, {"source_domain": "example.com"})
        self.assertGreaterEqual(score, 10)

    def test_ai_penalty(self):
        score = self.scorer.calculate_trust_score(
            "As an AI, I think this is the best approach.",
            {"source_domain": "example.com"}
        )
        self.assertLess(score, 50)

    def test_objective_language(self):
        objective = "This technical document describes the implementation of a sorting algorithm."
        score = self.scorer.calculate_trust_score(objective, {"source_domain": "example.com"})
        self.assertGreaterEqual(score, 5)

    def test_full_pipeline_high_score(self):
        text = """def quicksort(arr):
    \"\"\"Implementation of quicksort algorithm.\"\"\"
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)
"""
        metadata = {
            "source_domain": "python.org",
            "author": "Guido van Rossum",
            "date": "2026-01-15",
            "content_type": "code",
        }
        score = self.scorer.calculate_trust_score(text, metadata)
        self.assertGreaterEqual(score, 70)


class TestContentDetector(unittest.TestCase):
    def setUp(self):
        from rag.ingestion.content_detector import ContentDetector
        self.detector = ContentDetector()

    def test_detect_ai_flag(self):
        self.assertTrue(self.detector.detect_ai_content("As an AI language model, I cannot fulfill this request."))

    def test_detect_normal_text(self):
        self.assertFalse(self.detector.detect_ai_content("This is a normal human-written article."))

    def test_detect_hedging(self):
        text = "Moreover, this is therefore consequently a furthermore important however note."
        self.assertTrue(self.detector.detect_ai_content(text))

    def test_empty_text(self):
        self.assertFalse(self.detector.detect_ai_content(""))


class TestToolCreationLimit(unittest.TestCase):
    def setUp(self):
        import tempfile
        from pathlib import Path
        from core.dynamic_tools.registry import DynamicToolRegistry
        self.tmp = tempfile.mktemp(suffix=".json")
        self.registry = DynamicToolRegistry(Path(self.tmp))

    def tearDown(self):
        try:
            from pathlib import Path
            Path(self.tmp).unlink(missing_ok=True)
        except Exception:
            pass

    @patch("core.dynamic_tools.registry.MAX_USER_TOOLS", 3)
    def test_limit_reached(self):
        from core.dynamic_tools.registry import MAX_USER_TOOLS
        self.registry.register("a", "def a(i): pass", "tool a")
        self.registry.register("b", "def b(i): pass", "tool b")
        self.registry.register("c", "def c(i): pass", "tool c")
        with self.assertRaises(RuntimeError):
            self.registry.register("d", "def d(i): pass", "tool d")

    @patch("core.dynamic_tools.registry.MAX_USER_TOOLS", 5)
    def test_under_limit(self):
        self.registry.register("a", "def a(i): pass", "tool a")
        self.registry.register("b", "def b(i): pass", "tool b")
        version = self.registry.register("c", "def c(i): pass", "tool c")
        self.assertEqual(version, 1)


class TestIngestionPipeline(unittest.TestCase):
    def setUp(self):
        from rag.ingestion.pipeline import IngestionPipeline
        self.pipeline = IngestionPipeline()

    def test_assess_approve(self):
        text = "def add(a, b):\n    return a + b\n\nA simple Python function."
        metadata = {
            "source_domain": "github.com",
            "author": "dev",
            "content_type": "code",
        }
        approved, score, reason, enriched = self.pipeline.assess(text, metadata)
        self.assertTrue(approved, f"Expected approved: {reason}")
        self.assertGreaterEqual(score, 70)

    def test_assess_reject_empty(self):
        approved, score, reason, enriched = self.pipeline.assess("", {})
        self.assertFalse(approved)

    def test_assess_reject_ai(self):
        text = "As an AI language model, I cannot fulfill this request."
        approved, score, reason, enriched = self.pipeline.assess(text, {"source_domain": "example.com"})
        self.assertFalse(approved)
        self.assertIn("AI", reason)

    def test_assess_enriches_metadata(self):
        text = "Technical documentation about APIs."
        metadata = {"source_domain": "example.com"}
        approved, score, reason, enriched = self.pipeline.assess(text, metadata)
        if approved:
            self.assertIn("trust_score", enriched)
            self.assertIn("ingested_at", enriched)
            self.assertIn("id", enriched)


if __name__ == "__main__":
    unittest.main()
