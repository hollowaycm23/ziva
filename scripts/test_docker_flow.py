#!/usr/bin/env python3
import sys
import os
import json

# Ensure we can import core modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from extensions.file_ops import file_editor
from extensions.docker_ops import run_docker_container
import logging

logging.basicConfig(level=logging.INFO)

def main():
    print("--- 🐳 STARTING DOCKER PROTOCOL DROID TEST ---\n")

    # 1. Create a Python script in 'tmp' (Mapped to /workspace)
    py_content = """
import os
print("Hello from inside the Container!")
print(f"Working Directory: {os.getcwd()}")
print(f"Env Var CHECK: {os.environ.get('CHECK')}")
    """
    py_path = "tmp/test_container.py"
    
    print(f"📝 Creating host file '{py_path}'...")
    file_editor(py_path, py_content, mode="overwrite")

    # 2. Execute via Docker (Python Image)
    print(f"🚀 Launching Container (python:3.10-slim)...")
    
    # We execute 'python3 test_container.py'. 
    # Since workdir is /workspace and tmp is mapped to /workspace, the file 'test_container.py' is in CWD.
    output = run_docker_container(
        image="python:3.10-slim",
        command="python3 test_container.py",
        env=json.dumps({"CHECK": "VERIFIED"})
    )
    
    print(f"   Output:\n{output}\n")

    if "Hello from inside" in output and "VERIFIED" in output:
        print("✅ TEST PASSED: Container executed script from volume and read env vars!")
    else:
        print("❌ TEST FAILED: Output mismatch.")

if __name__ == "__main__":
    main()
