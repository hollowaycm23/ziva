import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from .trust_scorer import TrustScorer
from .content_detector import ContentDetector

logger = logging.getLogger("IngestionPipeline")


class IngestionPipeline:
    """
    Orchestrates the ingestion of documents into Qdrant.
    Steps: Filter -> Trust Score -> AI Detect -> Deduplicate -> Ingest.
    """

    def __init__(self):
        self.trust_scorer = TrustScorer()
        self.content_detector = ContentDetector()
        self.min_trust_score = 70

    def assess(self, text: str, metadata: Optional[Dict] = None) -> tuple:
        """
        Assess a document without ingesting it.

        Args:
            text: Document text
            metadata: Document metadata

        Returns:
            (approved: bool, score: int, reason: str, enriched_metadata: dict)
        """
        metadata = metadata or {}

        if not text or not text.strip():
            return False, 0, "Empty text", metadata

        if self.content_detector.detect_ai_content(text):
            return False, 0, "AI-generated content detected", metadata

        score = self.trust_scorer.calculate_trust_score(text, metadata)
        metadata["trust_score"] = score

        if score < self.min_trust_score:
            return False, score, f"Trust score {score} below minimum {self.min_trust_score}", metadata

        enriched = dict(metadata)
        enriched.setdefault("source", "")
        enriched.setdefault("author", "")
        enriched.setdefault("date", "")
        enriched.setdefault("content_type", "")
        enriched["trust_score"] = score
        enriched["ingested_at"] = datetime.now().isoformat()
        enriched["id"] = str(uuid.uuid4())

        return True, score, "Approved", enriched
