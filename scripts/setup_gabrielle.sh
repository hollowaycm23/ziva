#!/bin/bash
# Auto-setup script para Gabrielle
# Executa configuração P2P automaticamente

echo "🦅 Gabrielle P2P Auto-Setup"
echo "=============================="

cd /home/holloway/ziva || exit 1

# 1. Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado"
    exit 1
fi
echo "✅ Python3 OK"

# 2. Matar processos antigos e liberar porta 9000
pkill -f binary_server 2>/dev/null
lsof -ti:9000 | xargs kill -9 2>/dev/null
echo "🔄 Processos antigos terminados e porta 9000 liberada"

# 3. Iniciar servidor P2P com PYTHONPATH e Otimizações de Hardware
export PYTHONPATH=/home/holloway/ziva
export OLLAMA_NUM_THREAD=4      # Otimizado para i3-4005U (4 threads)
export MODEL_NAME=qwen2.5-coder:3b # Modelo leve para 8GB RAM

# Garantir que Ollama está rodando
if ! pgrep -x "ollama" > /dev/null; then
    echo "🔄 Iniciando Ollama..."
    nohup ollama serve > /tmp/ollama.log 2>&1 &
    sleep 5
fi

nohup python3 -m core.binary_server > /tmp/binary_server.log 2>&1 &
PID=$!

sleep 2

# 4. Verificar se iniciou
if ps -p $PID > /dev/null; then
    echo "✅ Binary Server iniciado (PID: $PID)"
    echo "📄 Logs: /tmp/binary_server.log"
    
    # Mostrar últimas linhas do log
    echo ""
    echo "--- Últimas linhas do log ---"
    tail -5 /tmp/binary_server.log
    
    exit 0
else
    echo "❌ Falha ao iniciar servidor"
    echo "Log de erro:"
    cat /tmp/binary_server.log
    exit 1
fi
