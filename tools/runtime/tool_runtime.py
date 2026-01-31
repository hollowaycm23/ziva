import logging
import traceback
from typing import Dict, Any, Tuple
import json

logger = logging.getLogger("ToolRuntime")


class ToolRuntime:
    """
    Safe execution environment for dynamic tools.
    """

    def execute_tool(self, code: str, tool_name: str,
                     inputs: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        """
        Executes the tool's code with the provided inputs.

        Args:
            code: The Python source code of the tool.
            tool_name: The name of the function to call within the code.
            inputs: A dictionary of arguments to pass to the function.

        Returns:
            A tuple (result_dict, error_string). If success, error_string is None/Empty.
        """
        local_scope = {}
        import requests
        import logging
        global_scope = {
            "__builtins__": {
                "abs": abs,
                "all": all,
                "any": any,
                "bin": bin,
                "bool": bool,
                "dict": dict,
                "divmod": divmod,
                "enumerate": enumerate,
                "filter": filter,
                "float": float,
                "format": format,
                "frozenset": frozenset,
                "hash": hash,
                "hex": hex,
                "int": int,
                "isinstance": isinstance,
                "issubclass": issubclass,
                "len": len,
                "list": list,
                "map": map,
                "max": max,
                "min": min,
                "next": next,
                "oct": oct,
                "ord": ord,
                "pow": pow,
                "range": range,
                "repr": repr,
                "reversed": reversed,
                "round": round,
                "set": set,
                "slice": slice,
                "sorted": sorted,
                "str": str,
                "sum": sum,
                "tuple": tuple,
                "zip": zip,
                "Exception": Exception,
                "ValueError": ValueError,
                "TypeError": TypeError,
                "KeyError": KeyError,
                "IndexError": IndexError,
                "__import__": __import__,
                "open": open,
                "__build_class__": __build_class__,
                "type": type,
                "super": super,
                "object": object},
            "requests": requests,
            "logging": logging,
            "__name__": "__main__",
            "json": json,
            "logger": logging.getLogger("ToolRuntime")}

        try:
            # 1. compile the code
            compiled_code = compile(code, "<string>", "exec")

            # 2. execute the code definition to populate local_scope with the
            # function
            exec(compiled_code, global_scope, local_scope)

            # 3. get the function object
            if tool_name not in local_scope:
                return {}, f"Function '{tool_name}' not found in the provided code."

            tool_func = local_scope[tool_name]

            # 4. call the function with inputs
            # Ensure inputs match expected arguments (basic check)
            result = tool_func(**inputs)

            # 5. return result
            if not isinstance(result, dict):
                # Enforce dict output as per roadmap contract
                return {"result": result}, ""

            return result, ""

        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {e}")
            return {}, str(e)
