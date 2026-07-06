import os
import requests
import logging

logger = logging.getLogger("ZivaLLM")

PROVIDER = os.getenv("LLM_PROVIDER", "custom")
_DEFAULT_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("ZIVA_LLM_KEY") or os.getenv("LLM_KEY", "ziva_secret_key_2026")
_DEFAULT_API_BASE = os.getenv("ZIVA_LLM_BASE_URL") or os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
_DEFAULT_MODEL = os.getenv("ZIVA_LLM_MODEL") or os.getenv("MODEL_NAME", "deepseek-coder-v2:16b")


class LLMService:
    """
    Service Wrapper for External LLM Inference (OpenAI Compatible).
    """

    def __init__(self, model=None, base_url=None, api_key=None):
        self.model = model or os.getenv("ZIVA_LLM_MODEL") or os.getenv("MODEL_NAME", _DEFAULT_MODEL)
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text:latest")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("ZIVA_LLM_KEY") or os.getenv("LLM_KEY", "ziva_secret_key_2026")
        self.api_base = (base_url or os.getenv("ZIVA_LLM_BASE_URL") or os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")).rstrip('/')

        if not self.api_key:
            logger.warning("⚠️ No API Key found for External LLM. Set OPENAI_API_KEY, ZIVA_LLM_KEY or LLM_KEY.")

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
            safe_text = text.encode('utf-8')[:2048].decode('utf-8', errors='ignore') + "\n"
            payload = {"model": target_model, "input": safe_text}

            # Try Ollama /api/embed first (fast, direct)
            ollama_base = self.api_base.replace("/v1", "").replace("/api", "")
            ollama_url = f"{ollama_base}/api/embed"
            resp = requests.post(ollama_url, json=payload, timeout=120)
            if resp.status_code == 200:
                data = resp.json()
                if "embeddings" in data and len(data["embeddings"]) > 0:
                    return data["embeddings"][0]

            # Fallback: OpenAI Compatible /v1/embeddings
            url = f"{self.api_base}/embeddings"
            resp2 = requests.post(url, headers=headers, json=payload, timeout=30)
            if resp2.status_code == 200:
                data2 = resp2.json()
                if "data" in data2 and len(data2["data"]) > 0:
                    return data2["data"][0]["embedding"]

            logger.error(f"Embedding failed. Status: {resp.status_code}, Response: {resp.text}")
            return []

        except Exception as e:
            logger.error(f"Embedding API Error: {e}")
            return []

    def start_server(self):
        logger.warning("start_server() is deprecated. Use external LLM provider.")

    def stop_server(self):
        logger.warning("stop_server() is deprecated. Use external LLM provider.")

    def health_check(self) -> bool:
        try:
            url = f"{self.api_base}/models"
            resp = requests.get(url, headers={"Authorization": f"Bearer {self.api_key}"}, timeout=5)
            return resp.status_code == 200
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False

    def update_model(self, path):
        logger.warning("update_model() is deprecated. Configure model in ziva.yaml or env vars.")
        return True
