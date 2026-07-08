import logging
import uuid
import time
from datetime import datetime
from typing import Dict, Optional, Tuple

from rag.ingestion.trust_scorer import TrustScorer
from rag.ingestion.content_detector import ContentDetector

logger = logging.getLogger("Governance")


class GovernanceService:
    """
    Central authority for document governance:
    1. AI content detection (9.4)
    2. Trust scoring (9.2) with full criteria
    3. Metadata enrichment (9.6)
    4. Ingestion decision
    """

    def __init__(self):
        self.trust_scorer = TrustScorer()
        self.content_detector = ContentDetector()
        self.min_trust_score = 70

    def assess(self, text: str, metadata: Optional[Dict] = None) -> Tuple[bool, int, str]:
        """
        Assess a document for ingestion.

        Args:
            text: The document text
            metadata: Document metadata (source, author, date, content_type, etc.)

        Returns:
            (approved: bool, score: int, reason: str)
        """
        metadata = metadata or {}

        if not text or not text.strip():
            return False, 0, "Empty text"

        # 1. AI Content Detection (9.4)
        if self.content_detector.detect_ai_content(text):
            return False, 0, "AI-generated content detected"

        # 2. Trust Scoring (9.2)
        score = self.trust_scorer.calculate_trust_score(text, metadata)
        if score < self.min_trust_score:
            return False, score, f"Trust score {score} below minimum {self.min_trust_score}"

        return True, score, "Approved"

    def enrich_metadata(self, metadata: Optional[Dict], score: int, text: str) -> Dict:
        """Add governance audit metadata."""
        enriched = dict(metadata or {})
        enriched.update({
            "trust_score": score,
            "governance_assessed_at": datetime.now().isoformat(),
            "governance_assessed_by": "GovernanceService",
            "id": str(uuid.uuid4()),
            "ingested_at": time.time(),
        })
        return enriched


_governance_instance = None


def get_governance():
    global _governance_instance
    if _governance_instance is None:
        _governance_instance = GovernanceService()
    return _governance_instance
