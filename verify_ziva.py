import requests
import json
import time

url = "http://localhost:8000/chat"
headers = {
    "X-API-Key": "ziva_secret_key_2026",
    "Content-Type": "application/json"
}

# Pergunta que antes confundia o modelo (Guerra vs Drogas)
payload = {
    "message": "Olá, teste de sistema. Responda 'OK' se receber.",
    "compact": False
}

print(f"Sending request to {url}...")
try:
    response = requests.post(url, headers=headers, json=payload, timeout=300)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
