#!/bin/bash
# Script para rodar o Dashboard da Ziva usando o ambiente virtual correto

# Pega o diretório do script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PATH="$PROJECT_ROOT/agent_venv"

if [ -d "$VENV_PATH" ]; then
    echo "🚀 Iniciando Dashboard da Ziva..."
    "$VENV_PATH/bin/python3" "$SCRIPT_DIR/dashboard.py"
else
    echo "❌ Erro: Ambiente virtual não encontrado em $VENV_PATH"
    echo "Certifique-se de que a Ziva foi instalada corretamente."
    exit 1
fi
