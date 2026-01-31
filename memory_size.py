#!/usr/bin/env python3
"""
Script para mostrar quantidade de dados na memória Qdrant
"""
import requests

try:
    # Conectar ao Qdrant
    response = requests.get("http://localhost:6333/collections/ziva_knowledge")
    data = response.json()

    if data.get("status") == "ok":
        result = data.get("result", {})
        points_count = result.get("points_count", 0)

        print(f"📊 Memória Qdrant:")
        print(f"   Collection: ziva_knowledge")
        print(f"   Total de memórias: {points_count}")
        print(f"   Status: ✅ Online")
    else:
        print("❌ Erro ao acessar Qdrant")

except Exception as e:
    print(f"❌ Erro: {e}")
    print("💡 Certifique-se que Qdrant está rodando:")
    print("   docker ps | grep qdrant")
