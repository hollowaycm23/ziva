#!/bin/bash

# Script para iniciar o sistema Ziva completo e o chat
# Uso: bash chat_iniciar.sh

cd /home/holloway/ziva

echo "🚀 Iniciando Sistema Ziva..."

# Verificar se o orquestrador já está rodando
if pgrep -f "bash start.sh" > /dev/null; then
    echo "✅ Orquestrador já está rodando"
else
    echo "🔧 Iniciando orquestrador em background..."
    nohup bash start.sh > /dev/null 2>&1 &
    echo "⏳ Aguardando serviços iniciarem (15 segundos)..."
    sleep 15
fi

# Verificar se a API está respondendo
echo "🔍 Verificando API..."
if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo "✅ API Online"
else
    echo "⚠️  API ainda não está pronta, aguardando mais 10 segundos..."
    sleep 10
fi

echo ""
echo "💬 Iniciando Chat Interativo..."
echo ""

# Iniciar o chat
source venv/bin/activate
python3 scripts/chat.py
