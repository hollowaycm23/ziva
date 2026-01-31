#!/usr/bin/env python3
import sys
import os
import time

# Ensure we can import core modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from extensions.file_ops import file_editor
from extensions.docker_ops import run_docker_container
import logging

logging.basicConfig(level=logging.INFO)

def main():
    print("--- ⚔️ STARTING C++ COMPILATION DROID TEST ---\n")

    # 1. Write C++ Source
    cpp_content = """
#include <iostream>
int main() {
    std::cout << "Greetings from Compiled C++ Code!" << std::endl;
    return 0;
}
    """
    cpp_path = "tmp/hello.cpp"
    print(f"📝 [1/3] Creating source file '{cpp_path}'...")
    file_editor(cpp_path, cpp_content, mode="overwrite")

    # 2. Compile via Docker (GCC Image)
    # We use 'gcc:latest' or 'gcc:12'. Let's use 'gcc:latest' (it might need pulling).
    # If not present, it will verify pulling capabilities too.
    print(f"🔨 [2/3] Compiling via GCC Container...")
    
    # Command: g++ -o hello hello.cpp
    # Input is /workspace/hello.cpp (mapped from tmp/hello.cpp)
    # Output is /workspace/hello (mapped to tmp/hello)
    compile_out = run_docker_container(
        image="gcc:latest",
        command="g++ -o hello hello.cpp"
    )
    print(f"   Compiler Output:\n{compile_out}\n")
    
    if "Erro" in compile_out:
        print("❌ Compilation Failed.")
        return

    # 3. Execute Binary via Docker (Same or different image)
    # We can use 'gcc:latest' again or 'ubuntu:latest'.
    # Note: compiled binary depends on libc. 'alpine' uses musl, so glibc binary might not run on alpine.
    # Safe bet: use 'gcc:latest' or 'debian'.
    print(f"🚀 [3/3] Executing Binary './hello' via Container...")
    
    exec_out = run_docker_container(
        image="gcc:latest", 
        command="./hello"
    )
    print(f"   Execution Output:\n{exec_out}\n")

    if "Greetings from Compiled C++ Code" in exec_out:
        print("✅ TEST PASSED: C++ code compiled and executed across ephemeral containers!")
        # Clean up binary ensures we don't pollute too much
        # But we leave it for inspection if user wants
    else:
        print("❌ TEST FAILED: Expected output not found.")

if __name__ == "__main__":
    main()
