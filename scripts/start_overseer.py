
import time
import sys
import os

# Ensure core is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.overseer import Overseer
from network.telegram_bridge import get_telegram_bridge

def run_background_monitor(interval_seconds=60):
    print(f"👁️ Overseer Service Started. Monitoring every {interval_seconds}s...")
    overseer = Overseer()
    telegram = get_telegram_bridge()
    
    last_status = "UNKNOWN"
    
    try:
        while True:
            report = overseer.analyze_telemetry()
            
            # ECLSS: Atuar sobre Sinais Vitais
            vitals = report.vitals
            if vitals["ram_percent"] > 90:
                msg = f"🚨 ECLSS CRITICAL: RAM usage at {vitals['ram_percent']}%. Triggering purging protocols..."
                print(msg)
                telegram.send_message(msg)
                # Clearing python cache as a simple action
                os.system("find . -name '__pycache__' -type d -exec rm -rf {} +")
                
            if report.status == "CRITICAL":
                msg = "🆘 SYSTEM FAILURE DETECTED. Executing Emergency Restart Protocols..."
                print(msg)
                telegram.send_message(msg)
            
            # Only print if status changes or is critical, to avoid spam
            if report.status != last_status or report.status == "CRITICAL":
                msg = f"👁️ [OVERSEER] System Status Change: {last_status} -> {report.status}\nVitals: RAM {vitals['ram_percent']}% | CPU {vitals['cpu_percent']}%"
                print(f"\n{msg}")
                telegram.send_message(msg)
                
                if report.status != "HEALTHY":
                    print("⚠️ WARNING: System health is degraded. ECLSS protocols active.")
                    
                last_status = report.status
            
            time.sleep(interval_seconds)
            
    except KeyboardInterrupt:
        print("\nStopping Overseer.")

if __name__ == "__main__":
    run_background_monitor()
