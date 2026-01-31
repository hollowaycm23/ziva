#!/bin/bash
# Script para entrar no ambiente virtual do Agente (agent_venv)
# Ele inicia um novo shell bash com o ambiente ativado.

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -d "$DIR/agent_venv" ]; then
    echo "✅ Encontrado agent_venv."
    echo "🚀 Ativando ambiente..."
    source "$DIR/agent_venv/bin/activate"
    
    # Inicia um novo bash mantendo o ambiente
    exec bash --rcfile <(echo '. ~/.bashrc; . '"$DIR/agent_venv/bin/activate")
else
    echo "❌ Erro: agent_venv não encontrado em $DIR."
    exit 1
fi
