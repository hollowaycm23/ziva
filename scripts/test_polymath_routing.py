import requests
import json
import sys


def test_routing():
    url = "http://localhost:8000/chat"

    # 1. Teste de Raciocínio (Esperado: deepseek-r1)
    # Uma pergunta lógica que force a classificação 'reasoning'
    reasoning_query = "If I have 5 apples, eat 2, and buy 3 more, how many do I have? Explain the logic step by step."

    print(f"🤖 Enviando query de raciocínio: '{reasoning_query}'")

    try:
        resp = requests.post(
            url,
            json={
                "message": reasoning_query,
                "compact": True})
        if resp.status_code == 200:
            data = resp.json()
            model = data.get('model_used', 'unknown')
            task = data.get('task_type', 'unknown')
            print(f"✅ Sucesso!")
            print(f"   Task Type Detected: {task}")
            print(f"   Model Selected: {model}")

            if "deepseek" in model and task == "reasoning":
                print("   🎉 ROUTING CORRETO!")
            else:
                print(
                    "   ⚠️ Routing diferente do esperado (pode ser normal dependendo da config)")
        else:
            print(f"❌ Erro API: {resp.text}")

    except Exception as e:
        print(f"❌ Falha na conexão: {e}")


if __name__ == "__main__":
    test_routing()
