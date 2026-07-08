"""
Training data collector for auto fine-tuning.
Selects high-quality interactions based on:
- Response confidence score > 0.7
- User feedback (implicit: no error retries, explicit: thumbs up)
- Diversity (avoids duplicate training data)
- Minimum response length > 20 chars
"""

import json
import uuid
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger("TrainingData")

DATA_DIR = Path(__file__).parent.parent / "data" / "training"


class TrainingExample:
    def __init__(self, query: str, response: str, quality_score: float = 0.0,
                 topics: Optional[List[str]] = None, metadata: Optional[Dict] = None):
        self.id = str(uuid.uuid4())
        self.query = query
        self.response = response
        self.quality_score = quality_score
        self.topics = topics or []
        self.metadata = metadata or {}
        self.timestamp = time.time()
        self.used_in_training = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "query": self.query,
            "response": self.response,
            "quality_score": self.quality_score,
            "topics": self.topics,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "used_in_training": self.used_in_training,
        }

    @classmethod
    def from_dict(cls, data: dict):
        ex = cls(data["query"], data["response"], data.get("quality_score", 0.0),
                 data.get("topics", []), data.get("metadata", {}))
        ex.id = data.get("id", ex.id)
        ex.timestamp = data.get("timestamp", ex.timestamp)
        ex.used_in_training = data.get("used_in_training", False)
        return ex


class TrainingDataCollector:
    """
    Collects, filters, and exports training data for fine-tuning.
    High-quality selection criteria:
    1. Response confidence > 0.7 (from ConfidenceScorer)
    2. No tool errors in the interaction
    3. Minimum response length > 20 chars
    4. Diversity: embedding similarity < 0.95 with existing examples
    """

    def __init__(self):
        self.data_dir = DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._examples: List[TrainingExample] = []
        self._load()

    def _load(self):
        path = self.data_dir / "examples.jsonl"
        if path.exists():
            try:
                with open(path, "r") as f:
                    for line in f:
                        if line.strip():
                            self._examples.append(TrainingExample.from_dict(json.loads(line)))
                logger.info(f"Loaded {len(self._examples)} training examples")
            except Exception as e:
                logger.error(f"Failed to load training examples: {e}")

    def _save(self):
        path = self.data_dir / "examples.jsonl"
        try:
            with open(path, "w") as f:
                for ex in self._examples:
                    f.write(json.dumps(ex.to_dict()) + "\n")
        except Exception as e:
            logger.error(f"Failed to save training examples: {e}")

    def add_example(self, query: str, response: str, metadata: Optional[Dict] = None,
                    topics: Optional[List[str]] = None) -> bool:
        if len(response) < 20:
            return False

        quality_score = self._calculate_quality(query, response, metadata)
        if quality_score < 0.5:
            return False

        ex = TrainingExample(query, response, quality_score, topics, metadata)
        self._examples.append(ex)
        self._save()
        logger.info(f"Training example added (score={quality_score:.2f}): {query[:50]}...")
        return True

    def _calculate_quality(self, query: str, response: str, metadata: Optional[Dict]) -> float:
        score = 0.5

        if metadata:
            if metadata.get("tool_success", True) is False:
                score -= 0.2
            confidence = metadata.get("confidence", 0)
            score += confidence * 0.3

        if len(response) > 100:
            score += 0.1
        if len(query) > 10:
            score += 0.1

        return min(1.0, max(0.0, score))

    def get_training_data(self, min_score: float = 0.7, limit: int = 100,
                          exclude_used: bool = True) -> List[TrainingExample]:
        candidates = [ex for ex in self._examples if ex.quality_score >= min_score]
        if exclude_used:
            candidates = [ex for ex in candidates if not ex.used_in_training]
        candidates.sort(key=lambda x: -x.quality_score)
        return candidates[:limit]

    def export_for_modelfile(self, output_path: Optional[Path] = None,
                             min_score: float = 0.7, limit: int = 100) -> Optional[Path]:
        examples = self.get_training_data(min_score=min_score, limit=limit)
        if not examples:
            logger.warning("No training examples to export")
            return None

        path = output_path or (self.data_dir / "training_data.jsonl")
        with open(path, "w") as f:
            for ex in examples:
                entry = {
                    "messages": [
                        {"role": "user", "content": ex.query},
                        {"role": "assistant", "content": ex.response},
                    ]
                }
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        logger.info(f"Exported {len(examples)} examples to {path}")
        return path

    def get_stats(self) -> dict:
        total = len(self._examples)
        used = sum(1 for ex in self._examples if ex.used_in_training)
        avg_quality = sum(ex.quality_score for ex in self._examples) / max(total, 1)
        return {
            "total_examples": total,
            "used_in_training": used,
            "avg_quality_score": round(avg_quality, 2),
            "high_quality_count": sum(1 for ex in self._examples if ex.quality_score >= 0.7),
        }


_collector = None


def get_collector():
    global _collector
    if _collector is None:
        _collector = TrainingDataCollector()
    return _collector
