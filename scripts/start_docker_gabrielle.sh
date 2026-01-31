#!/bin/bash
set -e

echo "🐳 Gabrielle Container Starting..."

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

# Aguardar 2 segundos para daemons inicializarem
sleep 2

# Iniciar API Server em foreground
echo "🚀 Iniciando API Server..."
exec uvicorn api.server:app --host 0.0.0.0 --port 8000
