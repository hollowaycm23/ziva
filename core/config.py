import yaml
import os
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class Config:
    _instance = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        config_path = os.getenv("ZIVA_CONFIG_PATH", "ziva.yaml")
        
        # Fallback path if running inside Docker vs Local
        if not os.path.exists(config_path):
            fallback = "/app/ziva.yaml"
            if os.path.exists(fallback):
                config_path = fallback
        
        try:
            with open(config_path, 'r') as f:
                self._config = yaml.safe_load(f)
            logger.info(f"✅ Configuration loaded from {config_path}")
        except FileNotFoundError:
            logger.warning(f"⚠️ Config file not found at {config_path}. Using Environment defaults.")
            self._config = {}
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
            self._config = {}

    @classmethod
    def get(cls, path: str, default: Any = None) -> Any:
        """
        Retrieves a value from config using dot notation (e.g. 'agent.primary_model')
        """
        instance = cls()
        keys = path.split('.')
        value = instance._config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    @classmethod
    def get_llm_provider(cls, alias_path: str) -> Dict[str, Any]:
        """
        Resolves a model alias (e.g., 'lm-studio/primary') to its full config.
        """
        # 1. Get the alias string
        # If the input is just "lm-studio/primary", split it.
        # If input is "agent.primary_model", resolve it first.
        full_alias = cls.get(alias_path)
        if not full_alias:
            full_alias = alias_path # Assume direct string was passed if lookup failed
            
        try:
            provider_name, model_alias = full_alias.split('/')
            
            # 2. Get Provider Config
            provider_config = cls.get(f"models.providers.{provider_name}")
            if not provider_config:
                raise ValueError(f"Provider '{provider_name}' not found in config.")
                
            # 3. Find Model in Provider
            target_model = None
            for model in provider_config.get("models", []):
                if model["alias"] == model_alias:
                    target_model = model
                    break
                    
            if not target_model:
                raise ValueError(f"Model alias '{model_alias}' not found in provider '{provider_name}'.")
                
            # 4. Resolve API Key
            api_key = provider_config.get("api_key")
            if not api_key and "api_key_env" in provider_config:
                env_var = provider_config["api_key_env"]
                api_key = os.getenv(env_var)
                
            return {
                "base_url": provider_config["base_url"],
                "api_key": api_key,
                "model_name": target_model["id"],
                "context_window": target_model.get("context_window", 8192)
            }
            
        except Exception as e:
            logger.error(f"Failed to resolve LLM provider for '{alias_path}': {e}")
            return None

# Global helper
config = Config()
