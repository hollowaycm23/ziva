#!/usr/bin/env python3
import sys
import os

# Ensure we can import core modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from extensions.file_ops import file_editor
from extensions.execution import local_shell, bash_runner
import logging

# Configure Logger to show info
logging.basicConfig(level=logging.INFO)

def main():
    print("--- 🧪 STARTING END-TO-END GO RUNTIME TEST ---\n")

    # 1. Create a Node.js file (Tests 'write_file' via Go)
    js_content = """
    console.log("Hello from NodeJS running inside Ziva's Safe Shell!");
    console.log("Time: " + new Date().toISOString());
    """
    js_path = "core/runtime/hello.js"
    
    print(f"📝 Creating file '{js_path}'...")
    write_result = file_editor(js_path, js_content, mode="overwrite")
    print(f"   Result: {write_result}\n")

    if "Erro" in write_result:
        print("❌ Write Failed. Aborting.")
        return

    # 2. Execute it via local_shell -> Go Runtime -> node (Tests 'execute_shell' + Whitelist)
    print(f"🚀 Executing 'node {js_path}'...")
    # We use local_shell which delegates to 'execute_shell'
    exec_result = local_shell(f"node {js_path}")
    
    print(f"   Output:\n{exec_result}\n")

    if "Hello from NodeJS" in exec_result:
        print("✅ TEST PASSED: Node.js executed successfully via Go Runtime!")
    else:
        print("❌ TEST FAILED: Expected output not found.")

if __name__ == "__main__":
    main()
