import logging
import os
import json
import requests
from typing import Optional, List, Dict, Any
from letta_client import Client, LettaError
from letta_client.types import CreateBlockParam

logger = logging.getLogger("LettaAgent")

class LettaAgentWrapper:
    """
    Wrapper for interacting with the Letta (MemGPT) Server.
    Ensures a stateful agent exists and handles message exchange with robust extraction.
    """
    
    def __init__(self, base_url: str = "http://localhost:8283", agent_name: str = "Ziva_Auto"):
        self.base_url = base_url.rstrip("/")
        self.agent_name = agent_name
        self.client = None
        self.agent_id = None
        self._connect()

    def _connect(self):
        """Initializes the Letta Client and finds/creates the agent."""
        try:
            self.client = Client(base_url=self.base_url)
            logger.info(f"✅ Connected to Letta Server at {self.base_url}")
            self._ensure_agent()
        except Exception as e:
            logger.error(f"❌ Failed to connect to Letta Server: {e}")
            self.client = None

    def _ensure_agent(self):
        """Finds or creates the Letta agent with auto-approval philosophy."""
        if not self.client:
            return

        try:
            # List agents
            agents = self.client.agents.list()
            target = next((a for a in agents if a.name == self.agent_name), None)

            if target:
                self.agent_id = target.id
                logger.info(f"🧠 Connected to existing Letta Agent: {self.agent_name} (ID: {self.agent_id})")
            else:
                logger.info(f"✨ Creating new Letta Agent: {self.agent_name}...")
                self.agent_id = self._create_agent_raw(self.agent_name)
                if self.agent_id:
                    logger.info(f"✅ Created new Letta Agent (ID: {self.agent_id})")
        except Exception as e:
            logger.error(f"❌ Error ensuring Letta agent: {e}")

    def _create_agent_raw(self, name: str) -> Optional[str]:
        """Raw HTTP fallback for agent creation with explicit tool-less system prompt."""
        url = f"{self.base_url}/v1/agents"
        headers = {"Content-Type": "application/json"}
        
        # System prompt explicitly forbids tools to avoid ApprovalResponseMessage hang
        system_prompt = (
            "You are Ziva, a long-term memory assistant. "
            "Your ONLY job is to remember facts about the user and provide context. "
            "DO NOT use tools or search functions. Reply only with text. "
            "NEVER request approvals."
        )

        payload = {
            "name": name,
            "system": system_prompt,
            "memory": {
                "blocks": [
                    {"label": "human", "value": "User is Holloway, an AI Developer."},
                    {"label": "persona", "value": "I am Ziva, a memory assistant."}
                ]
            },
            "llm_config": {
                "model": "gpt-4",
                "model_endpoint": "http://100.104.242.35:1234/v1",
                "model_endpoint_type": "openai",
                "context_window": 8192
            },
            "embedding_config": {
                "embedding_model": "text-embedding-qwen2.5-0.5b-instruct",
                "embedding_endpoint": "http://100.104.242.35:1234/v1",
                "embedding_endpoint_type": "openai",
                "context_window": 2048
            }
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code in [200, 201]:
                return resp.json().get("id")
            logger.error(f"Raw creation failed: {resp.status_code} - {resp.text}")
            return None
        except Exception as e:
            logger.error(f"Network error during agent creation: {e}")
            return None

    def send_message(self, message: str) -> str:
        """Sends a message and robustly extracts text from varied response objects."""
        if not self.client or not self.agent_id:
            return "Error: Letta memory system is offline."

        try:
            response = self.client.agents.messages.create(
                agent_id=self.agent_id,
                messages=[{"role": "user", "text": message}]
            )
            
            bot_response = ""
            for msg_obj in response.messages:
                # v1.x SDK objects: check all possible text fields
                if hasattr(msg_obj, 'text') and msg_obj.text:
                    bot_response += msg_obj.text
                elif hasattr(msg_obj, 'content') and msg_obj.content:
                    bot_response += msg_obj.content
                elif hasattr(msg_obj, 'description') and msg_obj.description:
                    bot_response += msg_obj.description
                elif isinstance(msg_obj, dict):
                    bot_response += msg_obj.get("text", msg_obj.get("content", ""))
            
            if bot_response:
                return bot_response.strip()

            # Handle potential approval hang by notifying logs
            logger.warning(f"No text extracted. Agent might be stuck in approval. Type: {type(response.messages[0]).__name__ if response.messages else 'Empty'}")
            return "..."
        except Exception as e:
            logger.error(f"Letta send_message error: {e}")
            return f"Error: {e}"
