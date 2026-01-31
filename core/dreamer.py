import logging
from typing import List, Dict
from core.llm import LLMService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Dreamer")


class Dreamer:
    """
    Offline Memory Consolidation System.
    """

    def __init__(self):
        self.llm = LLMService(model="ziva-base:latest")
        from core.rag_helper import get_rag_helper
        self.rag = get_rag_helper()

    def dream(self):
        """
        Executes the dream cycle: Retrieve -> Synthesize -> Prune.
        """
        logger.info("💤 Entering Dream Phase (Consolidating Memories)...")

        try:
            from qdrant_client.http import models

            filter_condition = models.Filter(
                must=[
                    models.FieldCondition(
                        key="type",
                        match=models.MatchValue(value="learned_lesson")
                    )
                ]
            )

            scroll_result, _ = self.rag.vector_store.client.scroll(
                collection_name=self.rag.vector_store.collection_name,
                scroll_filter=filter_condition,
                limit=50,
                with_payload=True
            )

            lesson_cluster = []
            for point in scroll_result:
                payload = point.payload
                item = {
                    "text": payload.get('text'),
                    "metadata": payload.get('metadata', payload)
                }
                lesson_cluster.append(item)

        except Exception as e:
            logger.error(f"Scroll failed: {e}")
            return

        if len(lesson_cluster) < 2:
            logger.info(
                f"Not enough lessons ({len(lesson_cluster)}) to synthesize.")
            return

        logger.info(
            f"Found {len(lesson_cluster)} lessons for synthesis.")

        insight = self._synthesize_cluster(lesson_cluster)

        if insight:
            logger.info("✨ Created Macro-Memory. Saving...")
            emb = self.rag.get_embedding(insight)
            if emb:
                self.rag.vector_store.add_text(
                    text=insight,
                    embedding=emb,
                    metadata={
                        "type": "macro_insight",
                        "source": "dreamer_v1"}
                )
                logger.info(
                    "✂️  [Pruning] Marking lessons for deletion (Simulated).")

    def _synthesize_cluster(self, cluster: List[Dict]) -> str:
        """
        Uses LLM to merge multiple learned lessons into one universal rule.
        """
        content_block = "\n".join([f"- {m['text']}" for m in cluster])

        prompt = f"""
        Below are several 'lessons' I have learned recently:

        {content_block}

        TASK: Synthesize these into a SINGLE, high-level universal principle.
        It should be abstract enough to apply broadly but specific enough to
        be useful.

        OUTPUT: Only the synthesized insight.
        """

        response = self.llm.completion(prompt)
        return f"MACRO-INSIGHT: {response.strip()}"


if __name__ == "__main__":
    d = Dreamer()
    d.dream()