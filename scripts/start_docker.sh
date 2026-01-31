#!/bin/bash
# Script de entrada para Docker (Foreground)

echo "🐳 Ziva Container Starting..."

# Ativar ambiente virtual
source /opt/venv/bin/activate

# Garantir PYTHONPATH na raiz para imports de core/ e agent/
export PYTHONPATH=/app
cd /app

# Criar diretórios inbox/outbox e data se não existirem
mkdir -p /app/inbox /app/outbox /app/data
chmod -R 777 /app/data /app/inbox /app/outbox

# Iniciar Message Daemon em background
echo "📨 Iniciando Message Daemon (P2P Sync)..."
python3 -c "from network.daemon import MessageDaemon; daemon = MessageDaemon(); daemon.run()" &
DAEMON_PID=$!
echo "✅ Message Daemon iniciado (PID: $DAEMON_PID)"

# Iniciar Binary Server em background (P2P Channel)
echo "💎 Iniciando Binary Server (Canal P2P)..."
python3 core/binary_server.py &
BINARY_PID=$!
echo "✅ Binary Server iniciado (PID: $BINARY_PID)"

# Iniciar Go Runtime (The Body) para execução de código
echo "🛡️ Iniciando Go Runtime (The Body)..."
/app/core/runtime/ziva_runtime &
RUNTIME_PID=$!
echo "✅ Go Runtime iniciado (PID: $RUNTIME_PID)"


# Aguardar 2 segundos para daemons inicializarem
sleep 2

# Iniciar API Server em foreground (mantém container vivo)
echo "🚀 Iniciando API Server..."
exec python3 -m uvicorn api.server:app --host 0.0.0.0 --port 8000 --log-level info
