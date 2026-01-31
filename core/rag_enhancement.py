"""
RAG Enhancement - Active Recall Logic
"""
import logging
from typing import List, Dict, Optional

logger = logging.getLogger("RAGEnhancement")


class ActiveRecallEnhancer:
    """
    Enhances RAG search results by boosting learned lessons.
    """

    def __init__(self, boost_factor: float = 1.25):
        """
        Initialize Active Recall Enhancer
        """
        self.boost_factor = boost_factor
        logger.info(f"🧠 Active Recall initialized (boost: {boost_factor}x)")

    def enhance_results(self, results: List[Dict]) -> List[Dict]:
        """
        Apply Active Recall boost to search results.
        """
        if not results:
            return results
        boosted_count = 0
        for res in results:
            metadata = res.get('metadata', {})
            if self._is_learned_lesson(metadata):
                original_score = res.get('score', 0)
                res['score'] = original_score * self.boost_factor
                boosted_count += 1
                logger.info(
                    f"🚀 Active Recall: '{res.get('text', '')[:40]}...' "
                    f"boosted {original_score:.3f} → {res['score']:.3f}"
                )
        results.sort(key=lambda x: x.get('score', 0), reverse=True)
        if boosted_count > 0:
            logger.info(
                f"✅ Active Recall applied to {boosted_count}/{len(results)} results")
        return results

    def _is_learned_lesson(self, metadata: Dict) -> bool:
        """
        Determine if metadata indicates a learned lesson.
        """
        if metadata.get('type') == 'learned_lesson':
            return True
        source = metadata.get('source', '')
        if source in ['thought_police', 'error_correction', 'hallucination_fix']:
            return True
        tags = metadata.get('tags', [])
        if isinstance(tags, list) and 'hallucination' in tags:
            return True
        return False


class LessonTracker:
    """
    Tracks and stores learned lessons for Active Recall.
    """

    def __init__(self, vector_store=None):
        """
        Initialize Lesson Tracker
        """
        self.vector_store = vector_store
        logger.info("📚 Lesson Tracker initialized")

    def record_lesson(
        self,
        lesson_text: str,
        context: str,
        error_type: str = "hallucination",
        embedding: Optional[List[float]] = None
    ) -> bool:
        """
        Record a learned lesson to prevent future errors.
        """
        if not self.vector_store:
            logger.warning("No vector store available for lesson recording")
            return False
        try:
            metadata = {
                'type': 'learned_lesson',
                'source': 'error_correction',
                'error_type': error_type,
                'context': context[:200],
                'tags': ['hallucination'] if error_type == 'hallucination' else []
            }
            self.vector_store.add(
                text=lesson_text,
                metadata=metadata,
                embedding=embedding
            )
            logger.info(f"✅ Learned lesson: '{lesson_text[:50]}...' ")
            return True
        except Exception as e:
            logger.error(f"Failed to record lesson: {e}")
            return False

    def get_lessons_count(self) -> int:
        """Get total number of learned lessons"""
        if not self.vector_store:
            return 0
        try:
            return 0
        except BaseException:
            return 0


_recall_enhancer = None
_lesson_tracker = None


def get_recall_enhancer(boost_factor: float = 1.25) -> ActiveRecallEnhancer:
    """Get or create singleton Active Recall Enhancer"""
    global _recall_enhancer
    if _recall_enhancer is None:
        _recall_enhancer = ActiveRecallEnhancer(boost_factor=boost_factor)
    return _recall_enhancer


def get_lesson_tracker(vector_store=None) -> LessonTracker:
    """Get or create singleton Lesson Tracker"""
    global _lesson_tracker
    if _lesson_tracker is None:
        _lesson_tracker = LessonTracker(vector_store=vector_store)
    return _lesson_tracker


if __name__ == "__main__":
    enhancer = get_recall_enhancer()
    test_results = [
        {'text': 'Atlas 950 is NOT the most powerful AI chip',
         'score': 0.75,
         'metadata': {'type': 'learned_lesson', 'source': 'error_correction'}},
        {'text': 'Regular search result about AI',
         'score': 0.80,
         'metadata': {}}
    ]
    enhanced = enhancer.enhance_results(test_results)
    print("\n🧪 Test Results:")
    for r in enhanced:
        print(f"  Score: {r['score']:.3f} - {r['text'][:50]}")