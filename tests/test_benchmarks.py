"""
Benchmark tests for Ziva AI agent.
Measures latency, throughput, and resource usage of key components.
"""
import time
import unittest
import logging

logging.disable(logging.CRITICAL)


class TestEmbeddingCacheBenchmark(unittest.TestCase):
    """Benchmark embedding cache performance."""

    def setUp(self):
        from core.embedding_cache import EmbeddingCache
        import tempfile
        self.tmpdir = tempfile.mkdtemp()
        self.cache = EmbeddingCache(cache_dir=self.tmpdir)
        import numpy as np
        self.test_texts = [f"Test query number {i}" for i in range(50)]
        self.test_vectors = [np.random.rand(768) for _ in range(50)]

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_cache_hit_latency(self):
        """Measure latency of cache hit."""
        for text, vec in zip(self.test_texts[:10], self.test_vectors[:10]):
            self.cache.set(text, vec)

        start = time.perf_counter()
        for _ in range(100):
            self.cache.get(self.test_texts[0])
        elapsed = time.perf_counter() - start

        avg_latency = elapsed / 100
        self.assertLess(avg_latency, 0.001, f"Cache too slow: {avg_latency*1000:.2f}ms")

    def test_cache_miss_latency(self):
        """Measure latency of cache miss."""
        start = time.perf_counter()
        for _ in range(100):
            self.cache.get("nonexistent_text_xyz")
        elapsed = time.perf_counter() - start

        avg_latency = elapsed / 100
        self.assertLess(avg_latency, 0.001, f"Cache miss too slow: {avg_latency*1000:.2f}ms")

    def test_cache_set_latency(self):
        """Measure latency of cache set."""
        import numpy as np
        start = time.perf_counter()
        for i in range(100):
            self.cache.set(f"text_{i}", np.random.rand(768))
        elapsed = time.perf_counter() - start

        avg_latency = elapsed / 100
        self.assertLess(avg_latency, 0.005, f"Cache set too slow: {avg_latency*1000:.2f}ms")


class TestTrustScorerBenchmark(unittest.TestCase):
    """Benchmark trust scorer static criteria (no API calls)."""

    def setUp(self):
        from rag.ingestion.trust_scorer import TrustScorer
        self.scorer = TrustScorer()
        # Mock local consistency to return 0 (avoids embedding API call)
        self.scorer._check_local_consistency = lambda text, meta: 0
        self.test_docs = [
            ("def hello(): pass",
             {"source_domain": "github.com", "author": "dev",
              "date": "2026-01-01", "content_type": "code"})
            for _ in range(100)
        ]

    def test_scorer_throughput(self):
        """Measure throughput of trust scoring (static criteria only)."""
        start = time.perf_counter()
        for _ in range(10):
            for text, meta in self.test_docs:
                self.scorer.calculate_trust_score(text, meta)
        elapsed = time.perf_counter() - start

        throughput = (10 * len(self.test_docs)) / elapsed
        self.assertGreater(throughput, 50, f"Low throughput: {throughput:.0f} docs/sec")


class TestValidatorBenchmark(unittest.TestCase):
    """Benchmark tool validator performance."""

    def setUp(self):
        from core.dynamic_tools.validator import DynamicToolValidator
        self.validator = DynamicToolValidator()
        self.valid_code = '''def test_tool(input: dict) -> dict:
    """A valid test tool."""
    import math
    return {"result": math.sqrt(input.get("x", 0))}
'''

    def test_validator_throughput(self):
        """Measure throughput of code validation."""
        start = time.perf_counter()
        for _ in range(500):
            self.validator.validate(self.valid_code)
        elapsed = time.perf_counter() - start

        throughput = 500 / elapsed
        self.assertGreater(throughput, 100, f"Low throughput: {throughput:.0f} validations/sec")


class TestInputSanitizationBenchmark(unittest.TestCase):
    """Benchmark input sanitization performance."""

    def setUp(self):
        from core.security_config import sanitize_input

    def test_sanitization_latency(self):
        """Measure latency of input sanitization."""
        from core.security_config import sanitize_input
        texts = [
            "Hello, how are you?" * 100,
            "Normal input with no special chars",
            "Bad\x00input\x01with\x02control chars",
            "A" * 5000,
        ]

        start = time.perf_counter()
        for _ in range(100):
            for text in texts:
                sanitize_input(text)
        elapsed = time.perf_counter() - start

        avg_latency = elapsed / (100 * len(texts))
        self.assertLess(avg_latency, 0.001, f"Sanitization too slow: {avg_latency*1000:.2f}ms")


class TestRateLimiterBenchmark(unittest.TestCase):
    """Benchmark rate limiter performance."""

    def setUp(self):
        from core.security_config import RateLimiter
        self.limiter = RateLimiter(max_requests=1000, window=60)

    def test_rate_limiter_throughput(self):
        """Measure throughput of rate limiter checks."""
        start = time.perf_counter()
        for i in range(1000):
            self.limiter.check(f"client_{i % 10}")
        elapsed = time.perf_counter() - start

        throughput = 1000 / elapsed
        self.assertGreater(throughput, 10000, f"Low throughput: {throughput:.0f} checks/sec")


if __name__ == "__main__":
    unittest.main()
