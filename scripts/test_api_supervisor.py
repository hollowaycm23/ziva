
import requests
import json
import time
import hashlib
import os

API_URL = "http://localhost:8000/chat"
TEST_KEY = "ziva_supervisor_test_key"
SECRETS_FILE = "secrets.json"


def setup_auth():
    print("🔐 Configurando autenticação de teste...")

    # 1. Calculate Hash
    key_hash = hashlib.sha256(TEST_KEY.encode()).hexdigest()

    # 2. Read Secrets
    if os.path.exists(SECRETS_FILE):
        with open(SECRETS_FILE, "r") as f:
            data = json.load(f)
    else:
        data = {"api_keys": {}, "users": {}}

    # 3. Add Key if not present
    if "api_keys" not in data:
        data["api_keys"] = {}

    data["api_keys"]["supervisor_test"] = key_hash

    # 4. Save
    with open(SECRETS_FILE, "w") as f:
        json.dump(data, f, indent=4)

    print(f"✅ Chave de teste injetada: {TEST_KEY[:4]}***")


def test_api():
    print("🧪 Testando API Ziva (Modo Supervisor)...")

    # Payload
    payload = {
        "message": "Qual é a capital da França e qual a moeda usada lá? Use suas tools.",
        "mode": "supervisor",
        "stream": False}

    # Correct Header for Ziva: X-API-Key
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": TEST_KEY
    }

    try:
        start = time.time()
        print(f"📡 Enviando request para {API_URL}...")
        response = requests.post(API_URL, json=payload, headers=headers)

        print(f"⏱️ Tempo: {time.time() - start:.2f}s")
        print(f"🔢 Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("\n✅ Resposta Recebida:")
            print(json.dumps(data, indent=2, ensure_ascii=False))

            # Additional Validation
            if "response" in data:
                print("\n📝 Validação: Resposta contém campo 'response'.")
            else:
                print("\n⚠️ Validação: Campo 'response' faltando.")

        else:
            print(f"\n❌ Erro: {response.text}")

    except Exception as e:
        print(f"\n❌ Falha na conexão: {e}")


if __name__ == "__main__":
    setup_auth()
    time.sleep(1)  # Wait a bit for file sync if needed (usually immediate)
    test_api()
