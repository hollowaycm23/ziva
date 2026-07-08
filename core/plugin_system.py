"""
Ziva Plugin System.
Allows third-party packages to extend Ziva with:
- New tools (functions with _is_ziva_tool)
- New memory backends (implementing VectorStoreBase)
- New LLM providers
- Lifecycle hooks (on_load, on_unload)

Plugin discovery:
1. Entry points (ziva_plugins) in installed packages
2. Directories in plugins/ folder
3. Config-file defined plugins
"""

import importlib
import importlib.metadata
import inspect
import logging
from pathlib import Path
from typing import Dict, List, Optional, Callable

logger = logging.getLogger("PluginSystem")


class PluginManifest:
    """Metadata about a loaded plugin."""

    def __init__(self, name: str, version: str = "0.1.0",
                 description: str = "", author: str = ""):
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.tools: List[str] = []
        self.hooks: Dict[str, Callable] = {}
        self.module = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "tools": self.tools,
            "hooks": list(self.hooks.keys()),
        }


class PluginSystem:
    """
    Discovers, loads, and manages plugins.
    """

    def __init__(self, tool_manager=None):
        self._manifests: Dict[str, PluginManifest] = {}
        self._tool_manager = tool_manager
        self._hooks: Dict[str, List[Callable]] = {
            "on_startup": [],
            "on_shutdown": [],
            "before_chat": [],
            "after_chat": [],
        }

    def discover_entry_points(self) -> List[str]:
        """Discover plugins via ziva_plugins entry point."""
        names = []
        try:
            eps = importlib.metadata.entry_points(group="ziva_plugins")
            for ep in eps:
                names.append(ep.name)
                logger.info(f"Discovered plugin via entry point: {ep.name}")
        except Exception as e:
            logger.debug(f"Entry point discovery failed: {e}")
        return names

    def discover_local(self) -> List[Path]:
        """Discover plugins in plugins/ directory."""
        plugins_dir = Path(__file__).parent.parent / "plugins"
        if not plugins_dir.exists():
            plugins_dir.mkdir(parents=True, exist_ok=True)
            return []

        found = []
        for entry in sorted(plugins_dir.iterdir()):
            if entry.is_dir() and (entry / "__init__.py").exists():
                found.append(entry)
            elif entry.suffix == ".py" and entry.stem != "__init__":
                found.append(entry)
        return found

    def load_plugin(self, name_or_path: str) -> Optional[PluginManifest]:
        """Load a plugin by name (entry point) or path."""
        # Try as entry point first
        try:
            eps = importlib.metadata.entry_points(group="ziva_plugins")
            for ep in eps:
                if ep.name == name_or_path:
                    module = ep.load()
                    return self._register_plugin(module, name_or_path)
        except Exception:
            pass

        # Try as file path
        path = Path(name_or_path)
        if not path.exists():
            path = Path(__file__).parent.parent / "plugins" / name_or_path
        if not path.exists():
            path = Path(__file__).parent.parent / "plugins" / f"{name_or_path}.py"

        if path.exists():
            try:
                spec = importlib.util.spec_from_file_location(path.stem, path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return self._register_plugin(module, path.stem)
            except Exception as e:
                logger.error(f"Failed to load plugin {path}: {e}")

        logger.warning(f"Plugin not found: {name_or_path}")
        return None

    def load_all(self):
        """Discover and load all plugins."""
        count = 0
        for name in self.discover_entry_points():
            if self.load_plugin(name):
                count += 1
        for path in self.discover_local():
            name = path.stem if path.is_file() else path.name
            if self.load_plugin(str(path)):
                count += 1
        logger.info(f"Loaded {count} plugins")
        return count

    def _register_plugin(self, module, name: str) -> Optional[PluginManifest]:
        manifest = PluginManifest(name)

        # Read metadata from module
        manifest.version = getattr(module, "__version__", "0.1.0")
        manifest.description = getattr(module, "__description__", "")
        manifest.author = getattr(module, "__author__", "")
        manifest.module = module

        # Register tools
        if self._tool_manager:
            for attr_name in dir(module):
                obj = getattr(module, attr_name)
                if inspect.isfunction(obj) and getattr(obj, "_is_ziva_tool", False):
                    self._tool_manager.loaded_tools[attr_name] = obj
                    manifest.tools.append(attr_name)
                    logger.info(f"  Loaded tool: {attr_name}")

        # Register hooks
        hook_map = {
            "on_startup": "on_startup",
            "on_shutdown": "on_shutdown",
            "before_chat": "before_chat",
            "after_chat": "after_chat",
        }
        for hook_name, attr in hook_map.items():
            func = getattr(module, attr, None)
            if func and callable(func):
                self._hooks[hook_name].append(func)
                manifest.hooks[hook_name] = func

        self._manifests[name] = manifest
        logger.info(f"Plugin registered: {name} v{manifest.version} ({len(manifest.tools)} tools)")
        return manifest

    def run_hook(self, hook_name: str, *args, **kwargs):
        """Run all registered hooks of a given type."""
        results = []
        for hook in self._hooks.get(hook_name, []):
            try:
                result = hook(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"Hook '{hook_name}' failed: {e}")
        return results

    def get_manifests(self) -> List[PluginManifest]:
        return list(self._manifests.values())

    def get_manifest(self, name: str) -> Optional[PluginManifest]:
        return self._manifests.get(name)


_system = None


def get_plugin_system(tool_manager=None):
    global _system
    if _system is None:
        _system = PluginSystem(tool_manager)
    return _system
