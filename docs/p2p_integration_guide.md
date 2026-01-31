# Guia de Integração P2P com Ziva
**Para Sistemas Externos (como Mita)**

Este documento explica como integrar qualquer sistema com a rede P2P da Ziva sem precisar instalar todo o stack.

---

## 📡 Protocolo Binário Ziva

**Porta:** 9000 (TCP)  
**Autenticação:** Chave PSK (Pre-Shared Key)  
**Encoding:** UTF-8 para texto, Big Endian para números

---

## 🔐 Handshake de Autenticação

### Servidor (Mita) deve:
1. Aceitar conexão na porta 9000
2. Enviar: `AUTH_REQ\n`
3. Aguardar chave do cliente
4. Se chave correta: enviar `AUTH_OK\n`
5. Se incorreta: enviar `AUTH_FAIL\n` e fechar

**Chave Configurada:** `admin`

---

## 🔑 CHAVE DE AUTENTICAÇÃO (PRÉ-CONFIGURADA)

> **IMPORTANTE:** A Ziva já está configurada para aceitar conexões da Mita usando esta chave:

```
Chave: admin
```

**No código do servidor, use exatamente:**
```python
AUTH_KEY = b"admin"  # Não mudar! Já configurado na Ziva
```

Esta chave já está cadastrada no peer store da Ziva. Não precisa alterar nada lá.

---

## 📋 Comandos Suportados

### 1. PING (Health Check)
**Cliente envia:** `PING`  
**Servidor responde:** `PONG`

### 2. RPC_LLM (Query LLM Remoto)
**Cliente envia:** `RPC_LLM`  
**Servidor responde:** `READY`  
**Cliente envia:** `<4 bytes length><prompt UTF-8>`  
**Servidor responde:** `<4 bytes length><response UTF-8>`

**Length:** Big Endian, unsigned int (>I em struct)

### 3. REQUEST_DATA (Requisitar Dataset)
**Cliente envia:** `REQUEST_DATA`  
**Servidor responde:** `<4 bytes length><JSON dataset>`

### 4. SYNC_DATA (Enviar Dataset)
**Cliente envia:** `SYNC_DATA`  
**Servidor responde:** `READY`  
**Cliente envia:** `<4 bytes length><JSON dataset>`  
**Servidor responde:** `ACK: N items received`

---

## 🐍 Exemplo: Servidor Mínimo em Python

```python
#!/usr/bin/env python3
"""
Servidor P2P Mínimo - Compatível com Ziva
Porta: 9000
"""
import socket
import struct
import json
import threading

AUTH_KEY = b"admin"  # Chave combinada com Ziva
PORT = 9000

def handle_client(conn, addr):
    print(f"Conexão de {addr}")
    
    # 1. Handshake
    conn.sendall(b"AUTH_REQ\n")
    key = conn.recv(1024).strip()
    
    if key != AUTH_KEY:
        conn.sendall(b"AUTH_FAIL\n")
        conn.close()
        return
    
    conn.sendall(b"AUTH_OK\n")
    print(f"✅ Autenticado: {addr}")
    
    # 2. Loop de comandos
    while True:
        try:
            cmd = conn.recv(1024)
            if not cmd:
                break
            
            cmd = cmd.strip()
            
            if cmd == b"PING":
                conn.sendall(b"PONG")
            
            elif cmd == b"RPC_LLM":
                conn.sendall(b"READY")
                # Ler prompt
                raw_len = conn.recv(4)
                prompt_len = struct.unpack('>I', raw_len)[0]
                prompt = conn.recv(prompt_len).decode('utf-8')
                
                # Processar com seu LLM/sistema
                response = process_query(prompt)
                
                # Enviar resposta
                resp_bytes = response.encode('utf-8')
                conn.sendall(struct.pack('>I', len(resp_bytes)))
                conn.sendall(resp_bytes)
            
            elif cmd == b"REQUEST_DATA":
                # Enviar dados do seu projeto
                data = get_project_info()
                payload = json.dumps(data).encode('utf-8')
                conn.sendall(struct.pack('>I', len(payload)))
                conn.sendall(payload)
            
            else:
                print(f"Comando desconhecido: {cmd}")
        
        except Exception as e:
            print(f"Erro: {e}")
            break
    
    conn.close()

def process_query(prompt):
    """
    Processa query usando seu sistema.
    Retorna string com resposta.
    """
    # SUBSTITUA AQUI com chamada ao seu LLM/chatbot
    # Exemplo com resposta estática:
    return f"Recebi a query: {prompt}. Sistema Mita v1.0"

def get_project_info():
    """
    Retorna informações sobre seu projeto
    """
    return {
        "project_name": "Mita",
        "version": "1.0",
        "tech_stack": ["Python", "FastAPI", "PostgreSQL"],
        "status": "Em desenvolvimento"
    }

# Servidor principal
def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', PORT))
    server.listen(5)
    
    print(f"🚀 Servidor P2P rodando na porta {PORT}")
    print(f"🔑 Chave de autenticação: {AUTH_KEY.decode()}")
    
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == "__main__":
    start_server()
```

---

## 🚀 Como Usar

### No sistema da Mita (Lucas):
```bash
# Salvar como p2p_server.py
python3 p2p_server.py
```

### Na Ziva (você):
```bash
# Testar conexão
python3 scripts/knowledge_exchange.py --host 100.73.184.97 --action status

# Analisar projeto
python3 scripts/analyze_project.py --host 100.73.184.97 --depth quick
```

---

## 💡 Dicas de Implementação

1. **LLM Integration**: Substitua `process_query()` para chamar seu chatbot/LLM real
2. **Project Info**: Customize `get_project_info()` com dados reais do projeto
3. **Async**: Use asyncio para melhor performance
4. **Logging**: Adicione logs para debug
5. **Firewall**: Libere porta 9000 ou use Tailscale (já libera automaticamente)

---

## 🔒 Segurança

- ✅ Autenticação obrigatória
- ✅ Chave PSK privada (não commitar)
- ✅ Tailscale fornece encryption automática
- ⚠️ Para produção: adicione rate limiting

---

## 📞 Suporte

Se tiver dúvidas, o protocolo completo está em:
`/home/holloway/ziva/core/binary_server.py` (servidor)
`/home/holloway/ziva/core/p2p_learning.py` (cliente)
