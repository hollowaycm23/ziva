from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from core.llm import LLMService
from core.config import config
import uuid
import time
import logging
import numpy as np

logger = logging.getLogger("EpisodicMemory")

class EpisodicMemory:
    def __init__(self, collection_name="episodic_experiences"):
        import os
        url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.client = QdrantClient(url=url)
        self.collection = collection_name
        # Embedding Model Initialization via Config
        emb_config = config.get_llm_provider("agent.embedding_model")
        model_name = emb_config["model_name"] if emb_config else "text-embedding-qwen2.5-0.5b-instruct"
        self.embedder = LLMService(model=model_name)
        self._init_collection()

    def _init_collection(self):
        try:
            self.client.get_collection(self.collection)
            logger.info(f"Connected to episodic collection: {self.collection}")
        except Exception:
            logger.info(f"Creating episodic collection: {self.collection}")
            import os
            vector_size = int(os.getenv("QDRANT_VECTOR_SIZE", "768"))
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )

    def recall(self, query: str, threshold: float = 0.90):
        """
        Search for a highly similar past experience.
        Returns the answer if similarity > threshold.
        """
        try:
            vector = self.embedder.embedding(query)
            if isinstance(vector, np.ndarray):
                vector = vector.tolist()
            if not vector:
                return None

            results = self.client.query_points(
                collection_name=self.collection,
                query=vector,
                limit=1,
                with_payload=True
            ).points

            if results:
                top_match = results[0]
                if top_match.score >= threshold:
                    logger.info(f"🧠 Episodic Cache Hit! Score: {top_match.score:.4f} | Query: '{query}'")
                    return {
                        "answer": top_match.payload.get("answer"),
                        "original_query": top_match.payload.get("query"),
                        "score": top_match.score,
                        "timestamp": top_match.payload.get("timestamp")
                    }
            
            return None

        except Exception as e:
            logger.error(f"Episodic recall failed: {e}")
            return None

    def remember(self, query: str, answer: str, source: str = "ziva_agent"):
        """
        Store a validated QA pair, ensuring no duplicates.
        """
        try:
            vector = self.embedder.embedding(query)
            if isinstance(vector, np.ndarray):
                vector = vector.tolist()
            if not vector:
                return False

            # Check for duplicates before saving
            existing = self.client.query_points(
                collection_name=self.collection,
                query=vector,
                limit=1,
                score_threshold=0.98  # Extremely high similarity means it's the same question/knowledge
            ).points

            if existing:
                logger.info(f"⚠️ Memory already exists (Score: {existing[0].score:.4f}). Skipping save to prevent pollution.")
                return True # Treat as success

            point_id = str(uuid.uuid4())
            payload = {
                "query": query,
                "answer": answer,
                "timestamp": time.time(),
                "source": source
            }

            self.client.upsert(
                collection_name=self.collection,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=payload
                    )
                ]
            )
            logger.info(f"💾 Stored NEW episodic memory: '{query}'")
            return True

        except Exception as e:
            logger.error(f"Failed to store episodic memory: {e}")
            return False