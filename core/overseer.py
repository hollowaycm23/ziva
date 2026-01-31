
import json
import os
from typing import Dict, List, Any
from dataclasses import dataclass
from collections import defaultdict
import glob

@dataclass
class HealthReport:
    total_tool_calls: int
    tool_success_rate: Dict[str, float]
    avg_latency_ms: Dict[str, float]
    critical_errors: List[str]
    vitals: Dict[str, Any] # Memory, CPU, Disk
    status: str # "HEALTHY", "DEGRADED", "CRITICAL"

class Overseer:
    """
    Internal Auditor (Phase C).
    Analyzes system telemetry to determine health and suggest improvements.
    """
    
    
    def __init__(self, log_dir: str = "/home/holloway/ziva/logs"):
        self.log_dir = log_dir
        # Lazy load worker
        self.kgc_worker = None

    def _get_worker(self):
        if not self.kgc_worker:
            from core.workers.kgc_worker import KGCompletionWorker
            self.kgc_worker = KGCompletionWorker()
        return self.kgc_worker

    def trigger_gardener(self, specific_topic: str = None):
        """
        Aciona o ciclo do jardineiro (KGC) para preencher lacunas.
        """
        try:
            worker = self._get_worker()
            topic = specific_topic or "General Knowledge"
            print(f"🌱 Overseer: Acionando Gardener para '{topic}'...")
            
            facts = worker.process_topic(topic, limit=3)
            
            if facts:
                print(f"✅ Overseer: Gardener colheu {len(facts)} novos fatos.")
                # Futuro: worker.synthesize_to_memory(facts)
            else:
                print("🍂 Overseer: Nenhuma nova informação extraída.")
                
        except Exception as e:
            print(f"❌ Overseer: Falha no Gardener: {e}")

        
    def analyze_telemetry(self, last_n_lines: int = 1000) -> HealthReport:
        """
        Parses telemetry logs and generates a health report.
        """
        log_file = os.path.join(self.log_dir, "telemetry.jsonl")
        
        if not os.path.exists(log_file):
            return HealthReport(0, {}, {}, [], {}, "HEALTHY")
            
        tool_counts = defaultdict(int)
        tool_errors = defaultdict(int)
        tool_latency = defaultdict(list)
        critical_errs = []
        
        # SINAIS VITAIS (ECLSS - Life Support)
        import psutil
        vitals = {
            "ram_percent": psutil.virtual_memory().percent,
            "cpu_percent": psutil.cpu_percent(),
            "disk_percent": psutil.disk_usage('/').percent,
            "processes_count": len(psutil.pids())
        }
        
        try:
            with open(log_file, 'r') as f:
                # Read all lines (in production, use `tail` logic for efficiency)
                lines = f.readlines()[-last_n_lines:]
                
            for line in lines:
                try:
                    event = json.loads(line)
                    # We only care about tool usage for now
                    if "tool_name" in event:
                        t_name = event["tool_name"]
                        tool_counts[t_name] += 1
                        tool_latency[t_name].append(event.get("duration_ms", 0))
                        
                        if event["status"] == "error":
                            tool_errors[t_name] += 1
                            if event.get("error_message"):
                                msg = event['error_message']
                                critical_errs.append(f"{t_name}: {msg}")
                                
                                # FASE D: AUTO-TRIGGER GARDENER
                                # Se o erro for de recusa de conhecimento, acionar KGC
                                if t_name == "knowledge_retrieval" and "REFUSAL" in msg:
                                    # Extrair a pergunta original do input_summary (se possível)
                                    topic = event.get("input_summary", "General")
                                    self.trigger_gardener(specific_topic=topic)

                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            critical_errs.append(f"Overseer Log Read Error: {e}")
            
        # Synthesize Metrics
        success_rates = {}
        avg_latencies = {}
        
        for tool, total in tool_counts.items():
            errs = tool_errors[tool]
            success_rates[tool] = round(((total - errs) / total) * 100, 2)
            
            lats = tool_latency[tool]
            avg_latencies[tool] = round(sum(lats) / len(lats), 2) if lats else 0
            
        # Determine Overall Status
        status = "HEALTHY"
        for rate in success_rates.values():
            if rate < 80:
                status = "DEGRADED"
            if rate < 50:
                status = "CRITICAL"
                
        return HealthReport(
            total_tool_calls=sum(tool_counts.values()),
            tool_success_rate=success_rates,
            avg_latency_ms=avg_latencies,
            critical_errors=critical_errs[-5:], # Keep last 5 errors
            vitals=vitals,
            status=status
        )

    def print_report(self):
        report = self.analyze_telemetry()
        print(f"\nExample Overseer Report (Reflecting on Phase A Telemetry):")
        print(f"===========================================================")
        print(f"System Status: {report.status}")
        print(f"Total Tool Calls: {report.total_tool_calls}")
        print(f"-----------------------------------------------------------")
        print(f"Tool Performance:")
        for tool, rate in report.tool_success_rate.items():
            latency = report.avg_latency_ms.get(tool, 0)
            print(f"  - {tool}: {rate}% Success | Avg Latency: {latency}ms")
        
        if report.critical_errors:
            print(f"-----------------------------------------------------------")
            print(f"Recent Critical Errors:")
            for err in report.critical_errors:
                print(f"  ! {err}")
        print(f"===========================================================\n")

if __name__ == "__main__":
    # Self-test
    o = Overseer()
    o.print_report()
    
    # Teste Fase D
    print("\n--- Teste Fase D: The Gardener Cycle ---")
    o.trigger_gardener(specific_topic="Ziva Architecture")
