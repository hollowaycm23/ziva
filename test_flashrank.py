#!/usr/bin/env python3
"""
Teste direto do FlashRank - verifica se está funcionando corretamente.
"""

print("="*80)
print("TESTE DO FLASHRANK")
print("="*80)

print("\n1. Testando importação...")
try:
    from flashrank import Ranker, RerankRequest
    print("✅ FlashRank importado com sucesso")
except Exception as e:
    print(f"❌ Erro ao importar: {e}")
    exit(1)

print("\n2. Inicializando Ranker...")
try:
    ranker = Ranker()
    print("✅ Ranker inicializado")
except Exception as e:
    print(f"❌ Erro ao inicializar: {e}")
    exit(1)

print("\n3. Testando re-ranking...")
query = "Qual ave voa para trás?"
documents = [
    "O pinguim é uma ave que não voa, mas nada muito bem.",
    "A galinha pode voar curtas distâncias.",
    "O beija-flor é a única ave capaz de voar para trás.",
    "As águias são aves de rapina.",
    "O avestruz é a maior ave do mundo."
]

print(f"\nQuery: {query}")
print(f"Documentos: {len(documents)}")

try:
    passages = [{"id": i, "text": doc} for i, doc in enumerate(documents)]
    rerank_request = RerankRequest(query=query, passages=passages)
    results = ranker.rerank(rerank_request)
    
    print("\n✅ Re-ranking concluído!")
    print("\nResultados (ordenados por score):")
    print("="*80)
    
    sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)
    
    for i, res in enumerate(sorted_results):
        print(f"\nRANK {i+1}:")
        print(f"  Score: {res['score']:.4f}")
        print(f"  Texto: {res['text']}")
    
    # Verifica se o documento correto está em RANK 1
    if "beija-flor" in sorted_results[0]['text'].lower():
        print("\n" + "="*80)
        print("✅ SUCESSO: Documento correto em RANK 1!")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("❌ PROBLEMA: Documento correto NÃO está em RANK 1!")
        print(f"RANK 1 atual: {sorted_results[0]['text']}")
        print("="*80)
        
except Exception as e:
    print(f"❌ Erro no re-ranking: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
