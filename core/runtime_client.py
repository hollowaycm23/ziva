import requests
import json
import logging
import os
import time

logger = logging.getLogger(__name__)

class GoRuntimeClient:
    """
    Client for the Ziva Go Runtime (The Body).
    Delegates execution of unsafe tools to the Sandboxed Go process.
    """
    
    BASE_URL = "http://localhost:8090/execute"
    
    @staticmethod
    def execute_tool(tool_name: str, arguments: dict, timeout: int = 10) -> dict:
        """
        Sends a tool execution request to the Go Runtime.
        
        Args:
            tool_name: Name of the tool (e.g., "read_file")
            arguments: Dictionary of arguments for the tool
            timeout: Timeout in seconds
            
        Returns:
            Dict containing 'status', 'result', and 'error'
        """
        
        # Ensure Runtime usage is enabled via env var (Safety switch)
        if os.getenv("ZIVA_USE_GO_RUNTIME", "true").lower() != "true":
            logger.warning(f"Go Runtime bypass active. Tool '{tool_name}' blocked or needs fallback.")
            return {"status": "error", "error": "Go Runtime disabled via config."}

        payload = {
            "id": f"py-{int(time.time()*1000)}",
            "tool_name": tool_name,
            "arguments": arguments
        }
        
        try:
            logger.info(f"⚡ Delegating '{tool_name}' to Go Runtime...")
            resp = requests.post(GoRuntimeClient.BASE_URL, json=payload, timeout=timeout)
            resp.raise_for_status()
            
            data = resp.json()
            
            if data.get("status") == "success":
                return {"status": "success", "result": data.get("result")}
            else:
                return {"status": "error", "error": data.get("error")}
                
        except requests.exceptions.ConnectionError:
            error_msg = "Go Runtime unreachable (Is 'ziva_runtime' running on port 8090?)"
            logger.error(error_msg)
            return {"status": "error", "error": error_msg}
        except Exception as e:
            logger.error(f"Runtime Client Error: {e}")
            return {"status": "error", "error": str(e)}

# Global Instance
runtime = GoRuntimeClient()
