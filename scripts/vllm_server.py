import os
import subprocess
import sys

# Configuration for RTX 4070 (12GB VRAM)
# We use AWQ quantization to fit 14B model in <10GB
MODEL_ID = "Qwen/Qwen2.5-14B-Instruct-AWQ"
PORT = 8000

def start_vllm():
    cmd = [
        sys.executable, "-m", "vllm.entrypoints.openai.api_server",
        "--model", MODEL_ID,
        "--port", str(PORT),
        "--gpu-memory-utilization", "0.90", # Leave some room for OS
        "--max-model-len", "4096", # Reduce context slightly to save VRAM if needed
        "--dtype", "float16", # AWQ usually runs as fp16 with int4 weights
        "--quantization", "awq",
        "--trust-remote-code"
    ]
    
    print(f"🚀 Starting vLLM Server...")
    print(f"Model: {MODEL_ID}")
    print(f"Port: {PORT}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Stopping vLLM Server...")
    except Exception as e:
        print(f"\n🔴 Error: {e}")

if __name__ == "__main__":
    start_vllm()
