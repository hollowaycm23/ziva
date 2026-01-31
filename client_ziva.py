#!/usr/bin/env python3
import requests
import json
import sys

# Configuração
API_URL = "http://localhost:8000"
API_KEY = "sk-ziva-local-dev-key"  # Chave gerada para uso local

def check_health():
    try:
        resp = requests.get(f"{API_URL}/api/health", timeout=5)
        if resp.status_code == 200:
            print(f"✅ API Online: {resp.json().get('agent', 'Unknown')}")
            return True
        else:
            print(f"❌ API retornou status {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erro ao conectar na API: {e}")
        return False

def chat():
    print("\n--- Ziva API Client (Interativo) ---")
    print("Digite 'sair' para encerrar.")
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

    while True:
        try:
            user_input = input("\nVocê: ")
        except EOFError:
            break
            
        if user_input.lower() in ["sair", "exit"]:
            break
        
        if not user_input.strip():
            continue

        payload = {
            "message": user_input,
            "mode": "standard"  # ou "supervisor"
        }

        try:
            print("Ziva (pensando)...")
            response = requests.post(f"{API_URL}/chat", headers=headers, json=payload, timeout=300)
            
            if response.status_code == 200:
                data = response.json()
                # A resposta pode variar dependendo da estrutura do retorno do /chat
                # Baseado no código lido, retorna um dict com ou sem chaves específicas dependendo se é stream ou invoke direto no server.py
                # O server.py usa app.invoke() e retorna o final_state ou uma lista de mensagens.
                # Vamos imprimir o JSON bruto se não acharmos a resposta clara, ou tentar extrair.
                
                # No server.py linha 250+, ele retorna `return final_state` direto se não for supervisor?
                # Se for graph_app.invoke, retorna o state.
                # State geralmente tem "messages".
                
                print(f"Status: {response.status_code}")
                # print(json.dumps(data, indent=2)) # Debug
                
                # Tentar extrair a última mensagem do assistente
                if "messages" in data:
                    last_msg = data["messages"][-1]
                    # LangGraph messages structure: {"type": "ai", "content": "..."}
                    if isinstance(last_msg, dict):
                        print(f"Ziva: {last_msg.get('content', '')}")
                        if "tool_calls" in last_msg and last_msg["tool_calls"]:
                            print(f"[Tool Calls: {last_msg['tool_calls']}]")
                    else:
                         print(f"Ziva: {last_msg}")
                elif "response" in data:
                    print(f"Ziva: {data['response']}")
                else:
                    print(f"Resposta da API: {data}")

            else:
                print(f"❌ Erro {response.status_code}: {response.text}")

        except Exception as e:
            print(f"❌ Erro na requisição: {e}")

if __name__ == "__main__":
    if check_health():
        chat()
