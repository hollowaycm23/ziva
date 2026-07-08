import logging
import re
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger("TrustScorer")


class TrustScorer:
    """
    Calculates trust score for a document based on metadata.
    Score range: 0-100. Minimum for ingestion: 70.

    Criteria (Section 9.2):
    - Source credibility (+30)
    - Author identification (+10)
    - Date recency (+10)
    - Language objectivity (+10)
    - Technical structure (+20)
    - Local consistency (+20)
    - AI content penalty (-30)
    """

    def calculate_trust_score(self, text: str, metadata: Dict[str, Any]) -> int:
        score = 0

        # 1. Source Credibility (+30 max)
        source = metadata.get("source_domain", "")
        if isinstance(source, str):
            source = source.lower()
        else:
            source = str(source) if source else ""

        trusted_domains = [
            "python.org", "mozilla.org", "github.com",
            "arxiv.org", "wikipedia.org", "stackoverflow.com",
            "docker.com", "postgresql.org", "nginx.org",
            "redis.io", "elastic.co", "kubernetes.io",
        ]
        if any(d in source for d in trusted_domains):
            score += 30
        elif source.endswith(".edu") or source.endswith(".gov"):
            score += 25
        elif source.endswith(".org") or source.endswith(".io"):
            score += 15
        elif source:
            score += 5

        # 2. Author Identification (+10)
        if metadata.get("author"):
            score += 10

        # 3. Recency (+10 max)
        date_str = metadata.get("date")
        if date_str:
            try:
                doc_date = datetime.fromisoformat(str(date_str))
                age_days = (datetime.now() - doc_date).days
                if age_days < 365:
                    score += 10
                elif age_days < 365 * 3:
                    score += 5
            except (ValueError, TypeError):
                pass

        # 4. Language Objectivity (+10)
        if self._is_objective_language(text):
            score += 10

        # 5. Technical Structure (+20)
        if self._has_technical_structure(text, metadata):
            score += 20
        elif "code_blocks" in metadata and metadata["code_blocks"] > 0:
            score += 15

        # 6. Local Consistency (+20)
        # Checks if document contradicts verified local knowledge
        consistency = self._check_local_consistency(text, metadata)
        score += consistency

        # 7. AI Content Penalty (-30)
        if self._is_likely_ai_generated(text):
            score -= 30

        return max(0, min(100, score))

    def _is_objective_language(self, text: str) -> bool:
        opinionative = [
            r"\bin my opinion\b", r"\bi think\b", r"\bi believe\b",
            r"\bin my view\b", r"\bpersonally\b", r"\barguably\b",
            r"\bunquestionably\b", r"\bclearly the best\b",
            r"\bwithout a doubt\b", r"\bits safe to say\b",
            r"\bnotably\b",
        ]
        opinion_count = sum(1 for p in opinionative if re.search(p, text, re.IGNORECASE))
        if opinion_count > 3:
            return False
        return True

    def _has_technical_structure(self, text: str, metadata: Dict) -> bool:
        content_type = metadata.get("content_type", "")
        if content_type in ("code", "documentation", "rfc", "spec", "api"):
            return True

        technical_indicators = [
            r"```[\w]*\n", r"def \w+\(", r"class \w+", r"import \w+",
            r"from \w+ import", r"return \w+", r"const \w+", r"function \w+",
            r"int main\(", r"public class", r"SELECT .* FROM",
            r"HTTP/\d\.\d", r"Content-Type:", r"Status: \d{3}",
            r"^\s*-\s+\w+", r"^\d+\.\s+\w+",
            r"RFC \d{4}", r"IEEE \d+",
        ]
        code_hits = sum(1 for p in technical_indicators if re.search(p, text, re.MULTILINE))
        return code_hits >= 2

    def _check_local_consistency(self, text: str, metadata: Dict) -> int:
        try:
            from core.vector_stores.factory import get_vector_store
            from core.llm import LLMService

            llm = LLMService()
            embedding = llm.embedding(text[:2000])
            if not embedding:
                return 0

            vs = get_vector_store()
            results = vs.search(embedding, limit=3, filters=None)
            if not results:
                return 0

            contradictions = 0
            for r in results:
                stored = r.get("text", "")
                if stored and self._detect_contradiction(text[:500], stored[:500]):
                    contradictions += 1

            if contradictions >= 2:
                return -20
            elif contradictions == 1:
                return 0
            return 20
        except Exception:
            return 0

    def _detect_contradiction(self, a: str, b: str) -> bool:
        try:
            from sentence_transformers import SentenceTransformer
            encoder = SentenceTransformer("all-MiniLM-L6-v2")
            emb_a = encoder.encode(a)
            emb_b = encoder.encode(b)
            import numpy as np
            sim = np.dot(emb_a, emb_b) / (np.linalg.norm(emb_a) * np.linalg.norm(emb_b))
            return sim < -0.3
        except Exception:
            return False

    def _is_likely_ai_generated(self, text: str) -> bool:
        patterns = [
            r"\bas an ai\b", r"\bI'm an AI\b", r"\bI am an AI\b",
            r"\bas a language model\b", r"\bI don't have personal\b",
            r"\bmy cutoff\b", r"\bI cannot access\b", r"\bI don't have access to\b",
            r"\bregenerate\b", r"\bAs an AI assistant\b",
        ]
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)
