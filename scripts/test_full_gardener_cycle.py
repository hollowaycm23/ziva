
import time
import os
import sys
import logging

# Adicionar raiz ao path
sys.path.append(os.getcwd())

from core.telemetry import TelemetryManager
from core.overseer import Overseer

# Configurar logging para stdout para ver o que acontece
logging.basicConfig(level=logging.INFO)

print("--- 🧪 Teste de Integração: Gardener Cycle 🧪 ---")

# 1. Simular uma recusa (Ziva diz: "Não sei")
print("\n[Passo 1] Simulando Recusa da Ziva...")
test_topic = "Teoria das Cordas Avançada"
TelemetryManager.log_tool_execution(
    tool="knowledge_retrieval",
    start_time=time.time(),
    status="error",
    input_val=test_topic, 
    error="REFUSAL: Insufficient Knowledge detected during validation."
)
print(f"✅ Evento de 'REFUSAL' verificado em logs/telemetry.jsonl para o tópico: '{test_topic}'")

# Esperar um pouco para garantir escrita em disco
time.sleep(1)

# 2. Executar o Overseer
print("\n[Passo 2] Executando Análise do Overseer...")
overseer = Overseer()

# A mágica acontece dentro de analyze_telemetry -> trigger_gardener
# Vamos capturar o output
try:
    report = overseer.analyze_telemetry(last_n_lines=50)
    print(f"\n[Relatório Overseer]")
    print(f"Status: {report.status}")
    print(f"Erros Críticos Recentes: {len(report.critical_errors)}")
    for err in report.critical_errors:
        print(f"  - {err}")

    print("\n[Verificação]")
    print("Verifique no output acima se apareceu '🌱 Overseer: Acionando Gardener...'")

except Exception as e:
    print(f"❌ Erro ao rodar Overseer: {e}")

print("\n--- Fim do Teste ---")
