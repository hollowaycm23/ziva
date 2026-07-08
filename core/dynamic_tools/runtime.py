import logging
import threading
from typing import Any, Dict

from core.dynamic_tools.validator import DynamicToolValidator

logger = logging.getLogger("ToolRuntime")

TOOL_TIMEOUT = 30


class RuntimeError(Exception):
    pass


def _execute_in_thread(code: str, func_name: str, args: dict, result_container: list,
                       error_container: list):
    try:
        safe_globals = DynamicToolValidator.get_safe_globals()
        local_ns = {}
        exec(code, safe_globals, local_ns)
        func = local_ns.get(func_name)
        if func is None:
            error_container.append(RuntimeError(f"Function '{func_name}' not found after exec"))
            return
        result = func(args)
        result_container.append(result)
    except Exception as e:
        error_container.append(e)


class DynamicToolRuntime:
    def __init__(self, registry=None):
        from core.dynamic_tools.registry import get_registry
        self.registry = registry or get_registry()

    def execute(self, tool_name: str, args: Dict[str, Any], timeout: int = TOOL_TIMEOUT) -> str:
        meta = self.registry.get(tool_name)
        if not meta:
            return f"Error: tool '{tool_name}' not found"

        success = False
        try:
            result_container = []
            error_container = []
            func_name = meta.name

            thread = threading.Thread(
                target=_execute_in_thread,
                args=(meta.code, func_name, args, result_container, error_container),
                daemon=True
            )
            thread.start()
            thread.join(timeout=timeout)

            if thread.is_alive():
                return f"Error: tool '{tool_name}' timed out after {timeout}s"

            if error_container:
                exc = error_container[0]
                return f"Error in '{tool_name}': {exc}"

            if result_container:
                result = result_container[0]
                success = True
                if isinstance(result, dict):
                    return str(result)
                return str(result)

            return f"Error: tool '{tool_name}' returned no result"

        except Exception as e:
            return f"Error executing '{tool_name}': {e}"
        finally:
            self.registry.record_usage(tool_name, success)
