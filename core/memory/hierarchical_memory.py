"""
Multi-level hierarchical memory system.
Level 0: Raw conversation messages (episodic memory)
Level 1: Session summaries (per conversation session)
Level 2: Topic clusters (grouped by extracted topics)
Level 3: Global knowledge (long-term learned facts)
"""

import time
import logging
from typing import Dict, List, Optional

logger = logging.getLogger("HierarchicalMemory")

# Topics are extracted by the LLM and stored here
# Each topic has: name, summary, first_seen, last_seen, message_count, importance


class TopicMemory:
    """Topic-level memory (Level 2)."""

    def __init__(self):
        self.topics: Dict[str, dict] = {}

    def update_topic(self, topic_name: str, summary: str, importance: float = 0.5):
        now = time.time()
        if topic_name in self.topics:
            self.topics[topic_name]["last_seen"] = now
            self.topics[topic_name]["message_count"] += 1
            self.topics[topic_name]["summary"] = self._merge_summaries(
                self.topics[topic_name]["summary"], summary
            )
            self.topics[topic_name]["importance"] = max(
                self.topics[topic_name]["importance"], importance
            )
        else:
            self.topics[topic_name] = {
                "name": topic_name,
                "summary": summary,
                "first_seen": now,
                "last_seen": now,
                "message_count": 1,
                "importance": importance,
            }

    def _merge_summaries(self, old: str, new: str) -> str:
        """Merge two summaries, keeping most relevant info."""
        merged = old + "\n" + new
        if len(merged) > 2000:
            merged = merged[-2000:]
        return merged

    def get_relevant_topics(self, query: str, limit: int = 5) -> List[dict]:
        """Get topics relevant to a query (simple keyword matching)."""
        query_lower = query.lower()
        scored = []
        for name, data in self.topics.items():
            score = 0
            if query_lower in name.lower():
                score += 10
            if any(word in name.lower() for word in query_lower.split()):
                score += 5
            if any(word in data.get("summary", "").lower() for word in query_lower.split()):
                score += 2
            score += data.get("importance", 0) * 3
            scored.append((score, data))
        scored.sort(key=lambda x: -x[0])
        return [s[1] for s in scored[:limit]]

    def get_all_topics(self) -> List[dict]:
        return sorted(
            self.topics.values(),
            key=lambda x: -x["importance"]
        )


class HierarchicalMemory:
    """
    Manages memory across all 4 levels.
    - Level 0: raw messages (via EpisodicMemory)
    - Level 1: session summaries (via MemorySummarizer)
    - Level 2: topic clusters (via TopicMemory)
    - Level 3: long-term knowledge (via Qdrant main_knowledge)
    """

    def __init__(self):
        self.topic_memory = TopicMemory()
        self._session_summaries: Dict[str, str] = {}
        self._initialized = False

    def _ensure_services(self):
        if self._initialized:
            return
        from core.memory.summarizer import MemorySummarizer
        from core.episodic_memory import EpisodicMemory
        from core.vector_stores.factory import get_vector_store
        self.summarizer = MemorySummarizer()
        self.episodic = EpisodicMemory()
        self.vector_store = get_vector_store()
        self._initialized = True

    def store_interaction(self, session_id: str, query: str, response: str,
                          topics: Optional[List[str]] = None):
        """
        Store an interaction across all memory levels.
        """
        self._ensure_services()
        # Level 0: Episodic memory
        self.episodic.remember(query, response, source=f"session:{session_id}")

        # Level 2: Topic memory
        if topics:
            for topic in topics:
                summary = f"Q: {query[:100]}... A: {response[:100]}..."
                self.topic_memory.update_topic(topic, summary)

    def recall(self, query: str, limit: int = 5) -> Dict[str, List]:
        """
        Recall from all memory levels for a given query.
        Returns combined results from all levels.
        """
        self._ensure_services()
        results = {
            "episodic": [],
            "topics": [],
            "knowledge": [],
        }

        # Level 0: Episodic recall
        try:
            episodic_results = self.episodic.recall(query, limit=limit)
            results["episodic"] = [
                {"query": r.query, "response": r.response, "score": r.similarity}
                for r in episodic_results
            ]
        except Exception as e:
            logger.debug(f"Episodic recall failed: {e}")

        # Level 2: Topic recall
        topic_results = self.topic_memory.get_relevant_topics(query, limit=limit)
        results["topics"] = [
            {
                "name": t["name"],
                "summary": t["summary"],
                "importance": t["importance"],
                "message_count": t["message_count"],
            }
            for t in topic_results
        ]

        # Level 3: Vector search
        try:
            from core.llm import LLMService
            llm = LLMService()
            embedding = llm.embedding(query)
            if embedding:
                vs_results = self.vector_store.search(embedding, limit=limit)
                results["knowledge"] = [
                    {"text": r["text"], "score": r["score"], "metadata": r.get("metadata", {})}
                    for r in vs_results
                ]
        except Exception as e:
            logger.debug(f"Vector recall failed: {e}")

        return results

    def get_working_context(self, query: str, max_tokens: int = 2000) -> str:
        """
        Build a compact working context string for the LLM prompt.
        """
        memory = self.recall(query, limit=3)
        parts = []

        if memory["topics"]:
            topics_str = "; ".join([t["name"] for t in memory["topics"][:3]])
            parts.append(f"[Tópicos relevantes]: {topics_str}")

        if memory["knowledge"]:
            for k in memory["knowledge"][:2]:
                parts.append(f"[Knowledge]: {k['text'][:300]}")

        if memory["episodic"]:
            for e in memory["episodic"][:2]:
                parts.append(f"[Anterior]: Q: {e['query'][:100]} | A: {e['response'][:100]}")

        context = "\n".join(parts)
        if len(context) > max_tokens * 4:
            context = context[:max_tokens * 4]
        return context or "Nenhum contexto relevante encontrado."

    def get_stats(self) -> dict:
        """Get memory statistics."""
        self._ensure_services()
        topics = self.topic_memory.get_all_topics()
        return {
            "topics_count": len(topics),
            "top_important_topics": [
                {"name": t["name"], "importance": t["importance"], "messages": t["message_count"]}
                for t in topics[:10]
            ],
        }

_hm_instance = None  # noqa: E305


def get_hierarchical_memory():  # noqa: E302
    global _hm_instance
    if _hm_instance is None:
        _hm_instance = HierarchicalMemory()
    return _hm_instance
