#!/usr/bin/env python3
"""
Teste de Integração RAG
Verifica se o chat está usando contexto do Qdrant
"""

import requests
import json

API_URL = "http://localhost:8000/chat"

print("🧪 Teste de Integração RAG")
print("=" * 60)

# Teste 1: Pergunta sobre JavaScript
print("\n1️⃣ Teste: Pergunta sobre JavaScript")
print("-" * 60)

test_query = "Como usar async/await em JavaScript?"
print(f"Pergunta: {test_query}")

try:
    response = requests.post(
        API_URL,
        json={"message": test_query},
        timeout=30
    )

    if response.status_code == 200:
        data = response.json()
        answer = data.get("response", "")
        context_count = data.get("context_used", 0)

        print(f"\n✅ Resposta recebida ({len(answer)} chars)")
        print(f"🧠 Contexto usado: {context_count} memórias")
        print(f"\nResposta:\n{answer[:300]}...")

    else:
        print(f"❌ Erro: Status {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"❌ Erro: {e}")

# Teste 2: Pergunta sobre TypeScript
print("\n\n2️⃣ Teste: Pergunta sobre TypeScript")
print("-" * 60)

test_query2 = "O que é TypeScript e por que usar?"
print(f"Pergunta: {test_query2}")

try:
    response = requests.post(
        API_URL,
        json={"message": test_query2},
        timeout=30
    )

    if response.status_code == 200:
        data = response.json()
        answer = data.get("response", "")

        print(f"\n✅ Resposta recebida ({len(answer)} chars)")
        print(f"\nResposta:\n{answer[:300]}...")

    else:
        print(f"❌ Erro: Status {response.status_code}")

except Exception as e:
    print(f"❌ Erro: {e}")

# Teste 3: Verificar Qdrant diretamente
print("\n\n3️⃣ Teste: Verificar Qdrant")
print("-" * 60)

try:
    qdrant_response = requests.get(
        "http://localhost:6333/collections/ziva_knowledge")
    if qdrant_response.status_code == 200:
        data = qdrant_response.json()
        points = data["result"]["points_count"]
        print(f"✅ Qdrant online: {points} memórias disponíveis")
    else:
        print(f"⚠️  Qdrant status: {qdrant_response.status_code}")
except Exception as e:
    print(f"❌ Qdrant erro: {e}")

print("\n" + "=" * 60)
print("✅ Testes concluídos!")
