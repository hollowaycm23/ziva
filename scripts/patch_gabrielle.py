#!/usr/bin/env python3
import os
import sys

# Target file on Gabrielle
TARGET_FILE = "/home/holloway/ziva/api/server.py"


def patch_server():
    print("🦅 Gabrielle P2P Patcher")
    print("========================")

    if not os.path.exists(TARGET_FILE):
        print(f"❌ Arquivo não encontrado: {TARGET_FILE}")
        print("Verifique se o Ziva está instalado em /home/holloway/ziva")
        sys.exit(1)

    with open(TARGET_FILE, 'r') as f:
        content = f.read()

    if "def get_knowledge(min_quality: float = 0.8):" in content:
        print("✅ O endpoint 'get_knowledge' já parece existir.")
        sys.exit(0)

    print("🔧 Aplicando patch em api/server.py...")

    # Define o código do novo endpoint
    new_endpoint = '''

# --- P2P Endpoint Patch (Added by Ziva) ---
@app.get("/api/p2p/get_knowledge")
async def get_knowledge(min_quality: float = 0.8):
    """
    Endpoint para permitir que outros peers (ex: Ziva) façam PULL de conhecimento.
    """
    try:
        # Tenta usar o collector se disponível
        try:
            from core.training_data_collector import TrainingDataCollector
            collector = TrainingDataCollector()
            dataset = collector.get_training_dataset(min_quality=min_quality)

            return {
                "node_name": "gabrielle",
                "dataset": dataset,
                "count": len(dataset)
            }
        except ImportError:
            # Fallback simples se não tiver collector completo
            return {
                "node_name": "gabrielle",
                "dataset": [],
                "count": 0,
                "note": "Collector module missing"
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# ------------------------------------------
'''

    # Encontra um ponto seguro para inserir (antes do if __name__)
    if 'if __name__ == "__main__":' in content:
        new_content = content.replace(
            'if __name__ == "__main__":',
            new_endpoint + '\nif __name__ == "__main__":')
    else:
        # Se não achar main block, append no final
        new_content = content + new_endpoint

    # Backup
    os.rename(TARGET_FILE, TARGET_FILE + ".bak")

    # Write
    with open(TARGET_FILE, 'w') as f:
        f.write(new_content)

    print("✅ Patch aplicado com sucesso!")
    print("🔄 Reiniciando serviço (se rodando via start.sh)...")

    # Tenta reiniciar o processo python do server
    os.system("pkill -f 'uvicorn.*api.server'")
    print("⚠️  Serviço derrubado. O orquestrador deve reiniciar automaticamente ou execute ./start.sh novamente.")


if __name__ == "__main__":
    patch_server()
