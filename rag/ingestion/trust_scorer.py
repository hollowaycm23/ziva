import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger("TrustScorer")


class TrustScorer:
    """
    Calculates trust score for a document based on metadata.
    Score range: 0-100. Minimum for ingestion: 70.
    """

    def calculate_trust_score(self, metadata: Dict[str, Any]) -> int:
        score = 0

        # 1. Source Credibility (+30 max)
        source = metadata.get("source_domain", "").lower()
        trusted_domains = [
            "python.org",
            "mozilla.org",
            "github.com",
            "arxiv.org",
            "wikipedia.org",
            "stackoverflow.com"]
        if any(d in source for d in trusted_domains):
            score += 30
        elif source.endswith(".edu") or source.endswith(".gov"):
            score += 25

        # 2. Author Identification (+10)
        if metadata.get("author"):
            score += 10

        # 3. Recency (+10 max)
        date_str = metadata.get("date")
        if date_str:
            try:
                doc_date = datetime.fromisoformat(date_str)
                age_days = (datetime.now() - doc_date).days
                if age_days < 365:  # < 1 year
                    score += 10
                elif age_days < 365 * 3:  # < 3 years
                    score += 5
            except ValueError:
                pass  # Invalid date format

        # 4. Technical Structure (+20)
        content_type = metadata.get("content_type", "")
        if content_type in ["code", "documentation", "rfc"]:
            score += 20
        elif "code_blocks" in metadata and metadata["code_blocks"] > 0:
            score += 15

        # 5. Local Consistency check (placeholder) (+20)
        # In a real system, we'd check if it contradicts verified facts.
        # For now, we assume neutral/positive if source is good.
        if score >= 30:
            score += 20

        return min(100, score)
