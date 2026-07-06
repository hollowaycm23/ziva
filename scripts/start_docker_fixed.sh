#!/bin/bash
# Script de entrada para Docker (Corrigido)
# - Supervisiona processos background
# - Implementa trap para cleanup
# - Mantém logs em foreground

set -e  # Exit on error

echo "🐳 Ziva Container Starting..."

# Ativar ambiente virtual
source /opt/venv/bin/activate

# Garantir PYTHONPATH
export PYTHONPATH=/app
cd /app

# Criar diretórios se não existirem
mkdir -p /app/inbox /app/outbox /app/data /app/logs
chmod -R 777 /app/data /app/inbox /app/outbox /app/logs

# Trap para cleanup ao receber SIGTERM
cleanup() {
    echo "🛑 Shutdown signal received, stopping all processes..."
    kill $(jobs -p) 2>/dev/null || true
    exit 0
}
trap cleanup SIGTERM SIGINT

# Iniciar Message Daemon em background
echo "📨 Iniciando Message Daemon (P2P Sync)..."
python3 -c "
import logging
logging.basicConfig(level=logging.INFO)
from network.daemon import MessageDaemon
daemon = MessageDaemon()
try:
    daemon.run()
except Exception as e:
    logging.error(f'Message Daemon error: {e}')
" >> /app/logs/message_daemon.log 2>&1 &
DAEMON_PID=$!
echo "✅ Message Daemon iniciado (PID: $DAEMON_PID)"

# Iniciar Binary Server em background (P2P Channel)
echo "💎 Iniciando Binary Server (Canal P2P)..."
python3 core/binary_server.py >> /app/logs/binary_server.log 2>&1 &
BINARY_PID=$!
echo "✅ Binary Server iniciado (PID: $BINARY_PID)"

# Iniciar Go Runtime se existir (The Body)
if [ -f /app/core/runtime/ziva_runtime ]; then
    echo "🛡️ Iniciando Go Runtime (The Body)..."
    chmod +x /app/core/runtime/ziva_runtime
    /app/core/runtime/ziva_runtime >> /app/logs/go_runtime.log 2>&1 &
    RUNTIME_PID=$!
    echo "✅ Go Runtime iniciado (PID: $RUNTIME_PID)"
else
    echo "⚠️ Go Runtime não encontrado em /app/core/runtime/ziva_runtime (opcional)"
fi

# Aguardar subsistemas inicializarem
sleep 2

# Check se Message Daemon ainda está rodando
if ! ps -p $DAEMON_PID > /dev/null 2>&1; then
    echo "⚠️ Message Daemon falhou ao iniciar"
    tail -10 /app/logs/message_daemon.log
fi

# Iniciar API Server em foreground (mantém container vivo)
echo "🚀 Iniciando API Server na porta 8000..."
exec python3 -m uvicorn api.server:app \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level info \
    --access-log
