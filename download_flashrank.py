#!/usr/bin/env python3
"""
Download manual do modelo FlashRank com timeout e retry.
"""

import os
import sys

print("="*80)
print("DOWNLOAD MANUAL DO MODELO FLASHRANK")
print("="*80)

# Configurar timeout para requests
os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '60'

print("\n1. Importando FlashRank...")
try:
    from flashrank import Ranker
    print("✅ Importado")
except Exception as e:
    print(f"❌ Erro: {e}")
    sys.exit(1)

print("\n2. Tentando inicializar Ranker (com timeout de 60s)...")
print("   Modelo: ms-marco-TinyBERT-L-2-v2 (~40MB)")
print("   Isso pode demorar alguns minutos na primeira vez...\n")

try:
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError("Download demorou mais de 120 segundos")
    
    # Set timeout de 120 segundos
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(120)
    
    ranker = Ranker()
    
    signal.alarm(0)  # Cancel timeout
    print("\n✅ Modelo baixado e carregado com sucesso!")
    print(f"   Cache: ~/.cache/huggingface/")
    
except TimeoutError as e:
    print(f"\n❌ TIMEOUT: {e}")
    print("   O download está demorando muito.")
    print("   Possíveis causas:")
    print("   - Conexão lenta")
    print("   - Problema no HuggingFace Hub")
    print("   - Firewall bloqueando")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Erro: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n3. Testando re-ranking...")
try:
    from flashrank import RerankRequest
    
    passages = [
        {"id": 1, "text": "O beija-flor é a única ave capaz de voar para trás."},
        {"id": 2, "text": "O pinguim não voa."}
    ]
    
    req = RerankRequest(query="ave que voa para trás", passages=passages)
    results = ranker.rerank(req)
    
    print(f"✅ Re-ranking funcionou!")
    print(f"   Resultado: {results[0]['text'][:50]}...")
    
except Exception as e:
    print(f"❌ Erro no teste: {e}")
    sys.exit(1)

print("\n" + "="*80)
print("✅ FLASHRANK ESTÁ FUNCIONANDO CORRETAMENTE!")
print("="*80)
