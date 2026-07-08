import dspy
import os
from typing import List, Union, Optional
from core.vector_store import VectorStore
from core.llm import LLMService
from core.config import config

class ZivaRetriever(dspy.Retrieve):
    """
    Custom Retriever wrapper for Ziva's VectorStore (Qdrant) + LLMService (Embedding).
    """
    def __init__(self, k: int = 3):
        super().__init__(k=k)
        self.vs = VectorStore()
        # Ensure we use an embedding model
        # Ensure we use an embedding model from config
        emb_config = config.get_llm_provider("agent.embedding_model")
        if emb_config:
            self.embedder = LLMService(
                model=emb_config["model_name"],
                base_url=emb_config["base_url"],
                api_key=emb_config["api_key"]
            )
        else:
            self.embedder = LLMService(model="text-embedding-qwen2.5-0.5b-instruct")

    def forward(self, query_or_queries: Union[str, List[str]], k: Optional[int] = None) -> List[str]:
        """
        Retrieves passages for the given query/queries.
        """
        k = k if k else self.k
        queries = [query_or_queries] if isinstance(query_or_queries, str) else query_or_queries
        
        all_passages = []
        for query in queries:
            # Generate embedding
            emb = self.embedder.embedding(query)
            if emb:
                # Search in Qdrant
                results = self.vs.search(embedding=emb, limit=k)
                # Extract text
                # We return a list of strings (passages)
                passages = [r["text"] for r in results]
                all_passages.extend(passages)
            else:
                print(f"  ⚠️ DSPy Retrieval Warning: Could not embed query '{query}'")
        
        # Deduplicate if multiple queries returned same docs
        return list(set(all_passages))

def configure_dspy():
    """
    Configures the global DSPy settings (LM and RM).
    """
    # --- LLM CONFIGURATION via Config Class ---
    # We resolve the primary model configuration
    llm_config = config.get_llm_provider("agent.primary_model")
    
    if llm_config:
        print(f"🔌 DSPy connecting to {llm_config['base_url']}...")
        # LM Studio / OpenAI Compatible Logic
        # We assume standard OpenAI compatibility for now based on config
        lm = dspy.LM(
            model=f"openai/{llm_config['model_name']}",
            api_base=llm_config["base_url"],
            api_key=llm_config["api_key"],
            response_format={"type": "text"},
            timeout=120
        )
        lm_model_name = llm_config['model_name'] # Define for the final print statement
    else:
        # Fallback Legacy Logic
        backend = os.getenv("ZIVA_LLM_BACKEND", "lm_studio").lower()
        
        if backend == "lm_studio":
            base_url = os.getenv("ZIVA_LLM_BASE_URL", "http://localhost:1234/v1")
            lm_model_name = os.getenv("ZIVA_LLM_MODEL", "batiai/qwen3.6-35b:iq3")
            lm = dspy.LM(
                model=f"openai/{lm_model_name}",
                api_base=base_url,
                api_key=os.getenv("ZIVA_LLM_KEY", "lm-studio"),
                response_format={"type": "text"},
                timeout=120
            ) 
        elif backend == "vllm":
            base_url = os.getenv("ZIVA_LLM_BASE_URL", "http://localhost:8000/v1")
            lm_model_name = "Qwen/Qwen2.5-14B-Instruct-AWQ" # Define for the final print statement
            lm = dspy.LM(
                model=lm_model_name,
                api_base=base_url,
                api_key="vllm",
                response_format={"type": "text"},
                timeout=120
            )
        else:
             # Default fallback
            base_url = os.getenv("ZIVA_LLM_BASE_URL", "http://100.104.242.35:1234/v1")
            lm_model_name = os.getenv("ZIVA_LLM_MODEL", "batiai/qwen3.6-35b:iq3")
            lm = dspy.LM(
                model=f"openai/{lm_model_name}",
                api_base=base_url,
                api_key="lm-studio",
                response_format={"type": "text"},
                timeout=120
           )

    # 2. Setup Retriever
    rm = ZivaRetriever(k=3)

    # 3. Configure Global Settings
    dspy.settings.configure(lm=lm, rm=rm)
    
    print(f"✅ DSPy Configured: LM={lm_model_name}, RM=ZivaRetriever(Qdrant)")
    return lm, rm

if __name__ == "__main__":
    # Test configuration when run directly
    configure_dspy()
