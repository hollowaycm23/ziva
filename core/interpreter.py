import logging
import multiprocessing
import sys
import io
import contextlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Interpreter")


def _worker(code, result_queue):
    """
    Worker function running in a separate process.
    Captures stdout.
    """
    # Safety: Disable dangerous modules in this process
    sys.modules['os'] = None
    sys.modules['subprocess'] = None
    sys.modules['shutil'] = None

    # Capture stdout
    f = io.StringIO()
    try:
        with contextlib.redirect_stdout(f):
            exec(code, {'__builtins__': __builtins__}, {})
        result_queue.put({"success": True, "output": f.getvalue()})
    except Exception as e:
        result_queue.put({"success": False, "error": str(e)})


class SafeInterpreter:
    """
    Sandboxed Python Interpreter for LLM code execution.
    """

    def execute(self, code: str, timeout: int = 2) -> str:
        """
        Executes Python code safely with a timeout.

        Args:
            code: The python code string.
            timeout: Max execution time in seconds.

        Returns:
            String containing stdout or error message.
        """
        logger.info("🔧 Executing Code Snippet...")

        queue = multiprocessing.Queue()
        p = multiprocessing.Process(target=_worker, args=(code, queue))
        p.start()
        p.join(timeout)

        if p.is_alive():
            p.terminate()
            p.join()
            logger.warning("⏱️ Code Execution Timed Out.")
            return "ERROR: Execution timed out."

        if not queue.empty():
            res = queue.get()
            if res["success"]:
                return res["output"].strip()
            else:
                return f"ERROR: {res['error']}"
        return "ERROR: No output produced."


if __name__ == "__main__":
    interp = SafeInterpreter()
    print(interp.execute("print(1 + 1)"))
    print(interp.execute("import time; time.sleep(5); print('fail')"))
