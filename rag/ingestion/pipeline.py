import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from .trust_scorer import TrustScorer
from .content_detector import ContentDetector
# Assuming ZivaMemory is available from core.memory.ziva_memory
from core.memory.ziva_memory import ZivaMemory

logger = logging.getLogger("IngestionPipeline")


class IngestionPipeline:
    """
    Orchestrates the ingestion of documents into Qdrant.
    Steps: Filter -> Trust Score -> AI Detect -> Deduplicate -> Ingest.
    """

    def __init__(self, memory_system: Optional[ZivaMemory] = None):
        self.trust_scorer = TrustScorer()
        self.content_detector = ContentDetector()
        self.memory = memory_system if memory_system else ZivaMemory()
        self.min_trust_score = 70

    def process_document(self, document: Dict[str, Any]) -> bool:
        """
        Process a single document for ingestion.

        Args:
            document: Dict containing 'text', 'source_domain', 'author', 'date', 'content_type'.

        Returns:
            True if ingested, False if rejected.
        """
        text = document.get("text", "")
        if not text:
            logger.warning("Ingestion skipped: Empty text.")
            return False

        # 1. AI Content Detection
        if self.content_detector.detect_ai_content(text):
            logger.warning(
                f"Ingestion rejected: AI content detected from {
                    document.get('source_domain')}")
            return False

        # 2. Trust Scoring
        score = self.trust_scorer.calculate_trust_score(document)
        document['trust_score'] = score

        if score < self.min_trust_score:
            logger.warning(
                f"Ingestion rejected: Low trust score ({score}) for {
                    document.get('source_domain')}")
            return False

        # 3. Deduplication (Simplified using Memory Recall)
        # Check if similar content exists with high score
        similar = self.memory.recall(text, limit=1, min_score=0.95)
        if similar:
            logger.info(
                f"Ingestion skipped: Duplicate content found (id: {
                    similar[0].metadata.get(
                        'id', 'unknown')})")
            return False

        # 4. Ingestion
        metadata = {
            "source": document.get("source_domain"),
            "author": document.get("author"),
            "date": document.get("date"),
            "trust_score": score,
            "ingested_at": datetime.now().isoformat(),
            "id": str(uuid.uuid4())
        }

        self.memory.save(
            text,
            quadrant="Q5_SKILLS",
            metadata=metadata,
            importance=0.8)
        logger.info(
            f"Ingestion success: {
                document.get('source_domain')} (Score: {score})")
        return True
