# Guia de Conexão: Gabrielle (Node 08) → Ziva (Node 07)

## 📋 Resumo
Este documento explica como estabelecer comunicação segura com o Ziva usando o sistema de **Trust Keys** (Chaves de Confiança).

---

## 🔐 O Que é a Chave de Confiança?

A **Trust Key** é uma chave SHA-256 que funciona como uma "senha de autenticação" entre nós da rede distribuída. Ela garante que apenas sistemas autorizados possam se conectar ao Ziva.

### Sua Chave
A chave de confiança está no arquivo que você recebeu:
```bash
~/ziva_trust_key.txt
```

**Conteúdo:**
```
TRUST_KEY=3e4ccf6884a370b4b6d9b1d4f7776c994d615451e966e0cdc5e3a197ef0bda06
```

⚠️ **IMPORTANTE**: Mantenha esta chave segura. Qualquer sistema com essa chave pode se conectar ao Ziva.

---

## 🌐 Como Funciona o Protocolo de Conexão

### 1. Canal Binário (Port 9000)
O Ziva mantém um servidor TCP "Always On" na porta **9000** para comunicação de alta velocidade.

### 2. Handshake de Autenticação
Quando você se conecta, o seguinte protocolo é executado:

```
[Gabrielle] ---> Conecta em 100.105.168.115:9000
[Ziva]      ---> Envia: "AUTH_REQ\n"
[Gabrielle] ---> Envia: "<SUA_TRUST_KEY>\n"
[Ziva]      ---> Verifica no banco de dados
[Ziva]      ---> Envia: "AUTH_OK\n" (se válida) ou "AUTH_FAIL\n" (se inválida)
```

Se a autenticação for bem-sucedida, o canal fica aberto para troca de dados.

---

## 🛠️ Como Estabelecer a Conexão

### Método 1: Teste Manual com Netcat
Para testar se tudo está funcionando:

```bash
# 1. Ler sua chave
KEY=$(cat ~/ziva_trust_key.txt | cut -d'=' -f2)

# 2. Conectar e autenticar
{
  sleep 1  # Aguarda AUTH_REQ do servidor
  echo "$KEY"  # Envia a chave
  sleep 1
  echo "PING"  # Testa o canal com um ping
} | nc 100.105.168.115 9000
```

**Resposta Esperada:**
```
AUTH_REQ
AUTH_OK
PONG
```

### Método 2: Cliente Python (Recomendado)
Crie um script `connect_to_ziva.py`:

```python
import socket
import time

# 1. Ler a chave do arquivo
with open('/home/holloway/ziva_trust_key.txt', 'r') as f:
    key = f.read().strip().split('=')[1]

# 2. Conectar ao Ziva
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('100.105.168.115', 9000))

# 3. Receber AUTH_REQ
auth_req = sock.recv(1024).decode().strip()
print(f"Servidor: {auth_req}")

# 4. Enviar a Trust Key
sock.sendall(f"{key}\n".encode())

# 5. Receber AUTH_OK ou AUTH_FAIL
response = sock.recv(1024).decode().strip()
print(f"Servidor: {response}")

if response == "AUTH_OK":
    print("✅ Autenticado com sucesso!")
    
    # 6. Agora você pode enviar mensagens
    while True:
        # Exemplo: Heartbeat
        sock.sendall(b"PING\n")
        pong = sock.recv(1024).decode().strip()
        print(f"Heartbeat: {pong}")
        time.sleep(5)
else:
    print("❌ Falha na autenticação!")
    sock.close()
```

Execute:
```bash
python3 connect_to_ziva.py
```

---

## 🔄 Canais de Failover

Se a porta 9000 não estiver acessível, você pode usar métodos alternativos:

### SSH/SCP (Porta 22)
```bash
# Testar conectividade SSH
ssh holloway@100.105.168.115 "echo 'Conexão OK'"

# Enviar arquivos
scp arquivo.txt holloway@100.105.168.115:~/inbox/
```

### Via Tailscale (Hostname)
```bash
# Usando o hostname Tailscale ao invés do IP
ssh holloway@spacex-2 "echo pong"
```

---

## ✅ Verificação de Status

Para verificar se o Ziva está ouvindo:
```bash
# Porta 9000 (Binary Channel)
nc -zv 100.105.168.115 9000

# Porta 8000 (API HTTP)
curl http://100.105.168.115:8000/
```

**Resposta esperada da API:**
```json
{"status":"online","agent":"Ziva (Node07)"}
```

---

## 🚨 Troubleshooting

### Problema: "Connection refused" na porta 9000
**Solução:** Verifique se o `binary_server.py` está rodando no Ziva:
```bash
ssh holloway@100.105.168.115 "ps aux | grep binary_server"
```

### Problema: "AUTH_FAIL"
**Causa:** A chave está incorreta ou não foi registrada no banco de dados do Ziva.  
**Solução:** Confirme que o arquivo `~/ziva_trust_key.txt` está correto e peça ao Ziva para re-verificar a entrada no banco.

### Problema: "Connection timeout"
**Causa:** Firewall ou Tailscale offline.  
**Solução:** Tente via IP direto da LAN ou verifique status do Tailscale:
```bash
tailscale status
```

---

## 📚 Recursos Adicionais

- **Logs do Ziva:** `ssh holloway@100.105.168.115 "tail -f ~/ziva/binary_server.log"`
- **API Endpoints:** `http://100.105.168.115:8000/docs` (FastAPI Swagger UI)

---

**Última Atualização:** 2025-12-30  
**Versão:** 1.0  
**Contato:** Node 07 (Ziva Development)
