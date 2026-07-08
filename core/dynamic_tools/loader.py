import logging
from langchain_core.tools import StructuredTool
from core.dynamic_tools.runtime import DynamicToolRuntime

logger = logging.getLogger("DynamicToolLoader")
_runtime = DynamicToolRuntime()


def _make_dynamic_tool(meta):
    def _run(args: dict) -> str:
        return _runtime.execute(meta.name, args)

    _run.__name__ = meta.name
    _run.__doc__ = meta.description or f"Dynamic tool: {meta.name}"
    return StructuredTool.from_function(
        func=_run,
        name=meta.name,
        description=meta.description or f"Dynamic tool: {meta.name}",
    )


def load_dynamic_tools_into(ziva_tools_list: list):
    from core.dynamic_tools.registry import get_registry
    registry = get_registry()
    existing_names = {t.name for t in ziva_tools_list}
    added = 0
    for name, meta in registry.list_tools().items():
        if name not in existing_names:
            tool = _make_dynamic_tool(meta)
            ziva_tools_list.append(tool)
            logger.info(f"Loaded dynamic tool: {name}")
            added += 1
    return added
