
import os
from typing import Dict, Any, List, Optional
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from core.llm import LLMService
from core.config import config

class ReflectionSchema(BaseModel):
    score: int = Field(description="Score from 1 to 5 representing response quality")
    success: bool = Field(description="Whether the user's intent was fulfilled")
    critique: str = Field(description="Critical analysis of the answer")
    lesson: str = Field(description="One sentence lesson learned for future interactions")

class ReflectionManager:
    """
    Analyzes agent interactions to extract lessons and improve future performance.
    Phase B of Evolutionary Architecture.
    """
    
    def __init__(self, llm_backend=None):
        self.llm = llm_backend 
        # Note: If llm_backend is None, we should initialize one or rely on injection.
        # For now, we will expect it to be passed or lazily init.
        self.client = None
        self.embedder = None
        
        self.parser = JsonOutputParser(pydantic_object=ReflectionSchema)
        
        self.prompt = PromptTemplate(
            template="""You are an AI Quality Assurance Auditor. Analyze the following interaction.

            Question: {question}
            Context Provided: {context}
            Generated Answer: {answer}

            Evaluate the answer based on:
            1. Accuracy (Does it answer the question?)
            2. Grounding (Is it supported by context?)
            3. Helpfulness (Is it direct and clear?)

            Return a JSON with:
            - score (1-5)
            - success (true/false)
            - critique (short criticism)
            - lesson (one rule to remember)

            {format_instructions}
            """,
            input_variables=["question", "context", "answer"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )

    def reflect(self, question: str, context: List[str], answer: str) -> Dict[str, Any]:
        """
        Executes the reflection process.
        """
        if not self.llm:
            # Fallback lazy init if not provided
            from langchain_ollama import ChatOllama
            import os
            # Reuse logic from nodes.py or similar (simplified here)
            # Ideally this should be centralized
            model_name = os.getenv("ZIVA_LLM_MODEL", "batiai/qwen3.6-35b:iq3")
            self.llm = ChatOllama(model=model_name, temperature=0)

        chain = self.prompt | self.llm | self.parser
        
        try:
            # Truncate context to avoid token limits in reflection
            context_str = "\n".join(context)[:2000]
            
            result = chain.invoke({
                "question": question,
                "context": context_str,
                "answer": answer
            })
            return result
        except Exception as e:
            print(f"Reflection failed: {e}")
            return {
                "score": 0, 
                "success": False, 
                "critique": f"Error: {str(e)}", 
                "lesson": "Fix reflection module."
            }

    
    def _ensure_collection(self, vector_dim=None):
        """Ensures the reflections collection exists."""
        vec_size = vector_dim or int(os.getenv("QDRANT_VECTOR_SIZE", "768"))
        try:
            self.client.get_collection(self.collection_name)
            info = self.client.get_collection(self.collection_name)
            existing_dim = info.config.params.vectors.size
            if existing_dim != vec_size:
                print(f"⚠️ Collection dim mismatch: {existing_dim} vs {vec_size}, deleting and recreating")
                self.client.delete_collection(self.collection_name)
                raise Exception("recreate")
        except Exception:
            from qdrant_client.models import VectorParams, Distance
            print(f"Creating collection: {self.collection_name} (dim={vec_size})")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=vec_size, distance=Distance.COSINE)
            )

    def save_reflection(self, reflection: Dict[str, Any], question: str, answer: str):
        """
        Saves the reflection to Qdrant.
        """
        if not self.client:
            from qdrant_client import QdrantClient
            import os
            from core.llm import LLMService 

            url = os.getenv("QDRANT_URL", "http://localhost:6333")
            self.client = QdrantClient(url=url)
            self.collection_name = "evolutionary_reflections"
            emb_config = config.get_llm_provider("agent.embedding_model")
            model_name = emb_config["model_name"] if emb_config else "text-embedding-qwen2.5-0.5b-instruct"
            self.embedder = LLMService(model=model_name)

        try:
            vector = self.embedder.embedding(question)
            if not vector:
                print("Failed to embed reflection question.")
                return

            # Ensure collection with correct dimension from actual embedding
            self._ensure_collection(vector_dim=len(vector))

            import uuid
            import time
            from qdrant_client.models import PointStruct

            point_id = str(uuid.uuid4())

            payload = reflection.copy()
            payload["original_question"] = question
            payload["original_answer"] = answer
            payload["timestamp"] = time.time()
            payload["type"] = "self_reflection"

            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=payload
                    )
                ]
            )
            print(f"✅ Reflection saved to Qdrant (Score: {reflection.get('score')})")

        except Exception as e:
            print(f"Failed to save reflection: {e}")
