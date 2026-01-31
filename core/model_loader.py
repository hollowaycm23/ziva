#!/usr/bin/env python3
"""
ModelLoader - Intelligent LLM model loading/unloading for multi-agent system.
"""

import logging
import requests
from typing import Optional, Dict
from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import Lock

logger = logging.getLogger("ModelLoader")


@dataclass
class ModelSpec:
    """Specification for an LLM model."""
    name: str
    vram_mb: int
    context_window: int = 4096
    description: str = ""


MODEL_REGISTRY = {
    "deepseek-coder:6.7b": ModelSpec(
        "deepseek-coder:6.7b", 3800, 4096, "Code generation specialist"),
    "qwen2.5-coder:7b": ModelSpec(
        "qwen2.5-coder:7b", 4200, 8192, "Advanced code generation"),
    "qwen2.5:7b": ModelSpec(
        "qwen2.5:7b", 4200, 8192, "General reasoning and debugging"),
    "llama3.2:3b": ModelSpec(
        "llama3.2:3b", 1900, 4096, "Lightweight planning and research"),
    "llama3.1:8b": ModelSpec(
        "llama3.1:8b", 4800, 8192, "General purpose LLM"),
}


class ModelLoader:
    """
    Intelligent model loading/unloading.
    """

    def __init__(self, ollama_url: str = "http://127.0.0.1:11434",
                 idle_timeout_seconds: int = 30):
        self.ollama_url = ollama_url
        self.idle_timeout = timedelta(seconds=idle_timeout_seconds)
        self.loaded_model: Optional[str] = None
        self.loaded_by_agent: Optional[str] = None
        self.last_used: Optional[datetime] = None
        self.load_queue: list = []
        self.lock = Lock()
        logger.info(
            f"ModelLoader initialized (Ollama: {ollama_url}, "
            f"idle timeout: {idle_timeout_seconds}s)")

    def _check_ollama_available(self) -> bool:
        try:
            requests.get(self.ollama_url, timeout=2)
            return True
        except Exception as e:
            logger.error(f"Ollama not available: {e}")
            return False

    def _get_loaded_models(self) -> list:
        try:
            resp = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return [model["name"] for model in data.get("models", [])]
            return []
        except Exception as e:
            logger.error(f"Error getting loaded models: {e}")
            return []

    def _load_model_ollama(self, model_name: str) -> bool:
        try:
            payload = {"model": model_name,
                       "prompt": "Hello", "stream": False}
            logger.info(f"Loading model {model_name} via Ollama...")
            resp = requests.post(
                f"{self.ollama_url}/api/generate", json=payload, timeout=60)
            if resp.status_code == 200:
                logger.info(f"Model {model_name} loaded successfully")
                return True
            else:
                logger.error(
                    f"Failed to load model {model_name}: "
                    f"{resp.status_code} {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {e}")
            return False

    def _unload_model_ollama(self, model_name: str):
        logger.info(f"Marking model {model_name} as unloaded")

    def load_model(self, model_name: str, agent_id: str) -> bool:
        with self.lock:
            if not self._check_ollama_available():
                logger.error("Ollama service not available")
                return False
            if self.loaded_model == model_name:
                logger.info(
                    f"Model {model_name} already loaded, reusing for {agent_id}")
                self.loaded_by_agent = agent_id
                self.last_used = datetime.now()
                return True
            if self.loaded_model:
                logger.info(
                    f"Unloading model {self.loaded_model} for {model_name}")
                self._unload_model_ollama(self.loaded_model)
                self.loaded_model = None
                self.loaded_by_agent = None
            success = self._load_model_ollama(model_name)
            if success:
                self.loaded_model = model_name
                self.loaded_by_agent = agent_id
                self.last_used = datetime.now()
                from core.resource_monitor import get_monitor
                monitor = get_monitor()
                vram_mb = self.estimate_vram_required(model_name)
                monitor.update_model_loaded(agent_id, model_name, vram_mb)
            return success

    def unload_model(self, agent_id: str):
        with self.lock:
            if self.loaded_by_agent != agent_id:
                logger.warning(
                    f"Agent {agent_id} tried to unload model, "
                    f"but it's loaded by {self.loaded_by_agent}")
                return
            if self.loaded_model:
                logger.info(f"Unloading model {self.loaded_model}")
                self._unload_model_ollama(self.loaded_model)
                from core.resource_monitor import get_monitor
                monitor = get_monitor()
                monitor.update_model_loaded(agent_id, None, 0)
                self.loaded_model = None
                self.loaded_by_agent = None
                self.last_used = None

    def get_loaded_model(self) -> Optional[str]:
        return self.loaded_model

    def estimate_vram_required(self, model_name: str) -> int:
        if model_name in MODEL_REGISTRY:
            return MODEL_REGISTRY[model_name].vram_mb
        if "3b" in model_name.lower():
            return 2000
        elif "7b" in model_name.lower():
            return 4200
        elif "13b" in model_name.lower():
            return 7500
        else:
            return 5000

    def queue_model_load(
            self,
            model_name: str,
            agent_id: str,
            priority: int = 5):
        with self.lock:
            self.load_queue.append((model_name, agent_id, priority))
            self.load_queue.sort(key=lambda x: x[2], reverse=True)
            logger.info(
                f"Queued model load: {model_name} for {agent_id} "
                f"(priority {priority})")

    def process_queue(self):
        with self.lock:
            if not self.load_queue:
                return
            if self.loaded_model and self.last_used:
                idle_time = datetime.now() - self.last_used
                if idle_time < self.idle_timeout:
                    logger.debug(f"Current model still active")
                    return
            model_name, agent_id, priority = self.load_queue.pop(0)
            logger.info(f"Processing queued load: {model_name} for {agent_id}")
            self.load_model(model_name, agent_id)

    def check_idle_unload(self):
        with self.lock:
            if not self.loaded_model or not self.last_used:
                return
            idle_time = datetime.now() - self.last_used
            if idle_time > self.idle_timeout:
                logger.info(f"Model {self.loaded_model} idle, unloading")
                self.unload_model(self.loaded_by_agent)

    def get_status(self) -> Dict:
        return {
            "loaded_model": self.loaded_model,
            "loaded_by_agent": self.loaded_by_agent,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "idle_seconds": (datetime.now() - self.last_used).seconds
            if self.last_used else None,
            "queue_length": len(self.load_queue),
            "queue": [{"model": m, "agent": a, "priority": p}
                      for m, a, p in self.load_queue]
        }


_loader_instance: Optional[ModelLoader] = None


def get_loader() -> ModelLoader:
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = ModelLoader()
    return _loader_instance