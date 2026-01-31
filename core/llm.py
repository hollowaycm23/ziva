import os
import requests
import logging
import json

logger = logging.getLogger("ZivaLLM")

# Configuration via Environment
# Valid Choices: "openai", "gemini", "deepseek", "groq", "custom"
PROVIDER = os.getenv("LLM_PROVIDER", "custom") 
API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("ZIVA_LLM_KEY") or "ziva_secret_key_2026"
# Use ZIVA_LLM_BASE_URL (configured in docker-compose.yml for LM Studio)
API_BASE = os.getenv("ZIVA_LLM_BASE_URL") or os.getenv("LLM_BASE_URL", "http://localhost:1234/v1") 
MODEL_NAME = os.getenv("ZIVA_LLM_MODEL") or os.getenv("MODEL_NAME", "qwen3-14b")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "qwen/qwen3-vl-4b")


class LLMService:
    """
    Service Wrapper for External LLM Inference (OpenAI Compatible).
    """

    def __init__(self, model=None, base_url=None, api_key=None):
        self.model = model or MODEL_NAME
        self.embedding_model = EMBEDDING_MODEL_NAME
        self.api_key = api_key or API_KEY
        self.api_base = (base_url or API_BASE).rstrip('/')
        
        if not self.api_key:
            logger.warning("⚠️ No API Key found for External LLM. Set OPENAI_API_KEY or ZIVA_LLM_KEY.")

    def is_running(self):
        """Always true for external APIs unless we want to ping."""
        return True

    def completion(self, prompt, temperature=0.7,
                   max_tokens=512, model=None, images=None):
        """
        Generate completion using External API.
        """
        target_model = model if model else self.model
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # OpenAI Compatible Payload
        payload = {
            "model": target_model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }

        # Image handling (Multimodal)
        if images:
            # Transform prompt to content array with image_url
            content = [{"type": "text", "text": prompt}]
            for img_b64 in images:
                content.append({
                    "type": "image_url", 
                    "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
                })
            payload["messages"][0]["content"] = content

        try:
            url = f"{self.api_base}/chat/completions"
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            
            if resp.status_code == 200:
                data = resp.json()
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                return ""
            else:
                logger.error(f"LLM API Error ({resp.status_code}): {resp.text}")
                return f"Error: {resp.status_code} - {resp.text}"
                
        except Exception as e:
            logger.error(f"Connection Error to External LLM: {e}")
            return ""

    def embedding(self, text, model=None):
        """
        Generate embeddings.
        Note: Requires an embedding-capable model/endpoint.
        """
        # Use configured embedding model if not provided
        target_model = model if model else self.embedding_model
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            # Enforce model limit of 2048 (characters for safety, though it is usually 2048 tokens)
            # Adding a newline to help with some GGUF tokenizers that expect a separator
            safe_text = text[:2048] + "\n"
            payload = {
                "model": target_model,
                "input": safe_text
            }
            
            # Primary attempt: OpenAI Compatible
            url = f"{self.api_base}/embeddings"
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if resp.status_code == 200:
                data = resp.json()
                if "data" in data and len(data["data"]) > 0:
                    return data["data"][0]["embedding"]
            
            logger.error(f"Embedding failed. Status: {resp.status_code}, Response: {resp.text}")
            return []

        except Exception as e:
            logger.error(f"Embedding API Error: {e}")
            return []

    # Local Management Stubs (Deprecated/Removed)
    def start_server(self): pass
    def stop_server(self): pass
    def health_check(self): return True
    def update_model(self, path): return True