import json
import time
import logging
import threading
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger("DynamicToolRegistry")

REGISTRY_PATH = Path(__file__).parent.parent.parent / "data" / "dynamic_tools.json"
MAX_USER_TOOLS = 30


class ToolMetadata:
    def __init__(self, name: str, code: str, description: str, version: int = 1,
                 created_at: float = 0, usage_count: int = 0, success_count: int = 0):
        self.name = name
        self.code = code
        self.description = description
        self.version = version
        self.created_at = created_at or time.time()
        self.usage_count = usage_count
        self.success_count = success_count

    @property
    def success_rate(self) -> float:
        if self.usage_count == 0:
            return 1.0
        return self.success_count / self.usage_count

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "code": self.code,
            "description": self.description,
            "version": self.version,
            "created_at": self.created_at,
            "usage_count": self.usage_count,
            "success_count": self.success_count,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            name=data["name"],
            code=data["code"],
            description=data.get("description", ""),
            version=data.get("version", 1),
            created_at=data.get("created_at", 0),
            usage_count=data.get("usage_count", 0),
            success_count=data.get("success_count", 0),
        )


class DynamicToolRegistry:
    def __init__(self, path: Path = REGISTRY_PATH):
        self.path = path
        self._tools: Dict[str, ToolMetadata] = {}
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self):
        try:
            if self.path.exists():
                with open(self.path, "r") as f:
                    data = json.load(f)
                for item in data:
                    meta = ToolMetadata.from_dict(item)
                    self._tools[meta.name] = meta
                logger.info(f"Loaded {len(self._tools)} dynamic tools from {self.path}")
        except Exception as e:
            logger.error(f"Failed to load dynamic tools: {e}")

    def _save(self):
        try:
            data = [meta.to_dict() for meta in self._tools.values()]
            with open(self.path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save dynamic tools: {e}")

    def register(self, name: str, code: str, description: str) -> int:
        with self._lock:
            if name in self._tools:
                existing = self._tools[name]
                if existing.code == code:
                    return existing.version
                existing.version += 1
                existing.code = code
                existing.description = description
                logger.info(f"Updated dynamic tool: {name} (v{existing.version})")
            else:
                if len(self._tools) >= MAX_USER_TOOLS:
                    logger.warning(f"Tool creation rejected: maximum {MAX_USER_TOOLS} tools reached")
                    raise RuntimeError(
                        f"Limite de {MAX_USER_TOOLS} ferramentas dinâmicas atingido. "
                        f"Remova ferramentas antigas com delete_tool() antes de criar novas."
                    )
                self._tools[name] = ToolMetadata(
                    name=name, code=code, description=description
                )
                logger.info(f"Registered dynamic tool: {name} (v1)")
            self._save()
            return self._tools[name].version

    def get(self, name: str) -> Optional[ToolMetadata]:
        return self._tools.get(name)

    def record_usage(self, name: str, success: bool):
        with self._lock:
            tool = self._tools.get(name)
            if tool:
                tool.usage_count += 1
                if success:
                    tool.success_count += 1
                self._save()

    def delete(self, name: str) -> bool:
        with self._lock:
            if name in self._tools:
                del self._tools[name]
                self._save()
                logger.info(f"Deleted dynamic tool: {name}")
                return True
            return False

    def list_tools(self) -> Dict[str, ToolMetadata]:
        with self._lock:
            return dict(self._tools)

    def get_all_code(self) -> Dict[str, str]:
        with self._lock:
            return {n: t.code for n, t in self._tools.items()}


_registry = None
_registry_lock = threading.Lock()


def get_registry() -> DynamicToolRegistry:
    global _registry
    if _registry is None:
        with _registry_lock:
            if _registry is None:
                _registry = DynamicToolRegistry()
    return _registry
