import requests
import time
import sys
import subprocess

SERVICES = {
    "Ollama": "http://localhost:11434/api/tags",
    "Qdrant": "http://localhost:6333/dashboard",
}

def check_services():
    print("🏥 Checking Core Services...")
    all_ok = True
    for name, url in SERVICES.items():
        try:
            resp = requests.get(url, timeout=2)
            if resp.status_code == 200:
                print(f"✅ {name}: UP")
            else:
                print(f"⚠️ {name}: UNSTABLE (Status {resp.status_code})")
                all_ok = False
        except Exception:
            print(f"🔴 {name}: DOWN")
            all_ok = False
            
            # Auto-Recovery
            if name == "Ollama":
                print(f"🚑 Attempting to restart {name}...")
                subprocess.run(["sudo", "systemctl", "restart", "ollama"])
                time.sleep(5)
    
    return all_ok

if __name__ == "__main__":
    if not check_services():
        sys.exit(1)
    print("All systems operational.")
