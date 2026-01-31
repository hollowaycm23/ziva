#!/usr/bin/env python3
"""
Teste direto do RAG Helper
Debug de embeddings e busca
"""

import sys
sys.path.insert(0, '/home/holloway/ziva')

print("🔍 Debug RAG Helper")
print("=" * 60)

# Teste 1: Import
print("\n1️⃣ Importando RAG Helper...")
try:
    from core.rag_helper import RAGHelper
    print("   ✅ Import OK")
except Exception as e:
    print(f"   ❌ Erro: {e}")
    sys.exit(1)

# Teste 2: Inicializar
print("\n2️⃣ Inicializando...")
try:
    rag = RAGHelper()
    print("   ✅ Inicializado")
except Exception as e:
    print(f"   ❌ Erro: {e}")
    sys.exit(1)

# Teste 3: Gerar embedding
print("\n3️⃣ Gerando embedding...")
try:
    embedding = rag.get_embedding("test")
    if embedding:
        print(f"   ✅ Embedding gerado ({len(embedding)} dims)")
    else:
        print("   ❌ Embedding vazio")
except Exception as e:
    print(f"   ❌ Erro: {e}")

# Teste 4: Buscar memórias
print("\n4️⃣ Buscando memórias...")
try:
    memories = rag.search_memories("JavaScript async await", limit=3)
    print(f"   Encontradas: {len(memories)} memórias")

    if memories:
        for i, mem in enumerate(memories, 1):
            score = mem.get('score', 0)
            text = mem.get('text', '')[:100]
            print(f"   {i}. Score: {score:.3f} - {text}...")
    else:
        print("   ⚠️  Nenhuma memória encontrada")

except Exception as e:
    print(f"   ❌ Erro: {e}")

# Teste 5: Enhance prompt
print("\n5️⃣ Testando enhance_prompt...")
try:
    enhanced, count = rag.enhance_prompt("Como usar TypeScript?", limit=2)
    print(f"   Memórias usadas: {count}")
    print(f"   Prompt length: {len(enhanced)} chars")

    if count > 0:
        print(f"\n   Preview:\n   {enhanced[:200]}...")

except Exception as e:
    print(f"   ❌ Erro: {e}")

print("\n" + "=" * 60)
print("✅ Debug concluído")
