#!/bin/bash
# ZIVA Interactive Chat Wrapper
# Garante a ativação do ambiente virtual correto para o chat interativo

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# 1. Tentar localizar e ativar o ambiente virtual (VENV) funcional
activate_and_validate() {
    local venv_path="$1"
    if [ -f "$venv_path/bin/activate" ]; then
        source "$venv_path/bin/activate"
        if python3 -c "import rich, requests, qdrant_client" &>/dev/null; then
            return 0
        else
            deactivate 2>/dev/null
            return 1
        fi
    fi
    return 1
}

if activate_and_validate "$PROJECT_ROOT/venv"; then
    VENV_MSG="venv local"
elif activate_and_validate "$PROJECT_ROOT/agent_venv"; then
    VENV_MSG="agent_venv local"
elif activate_and_validate "$HOME/.venv"; then
    VENV_MSG="venv global"
else
    echo "⚠️ Nenhum ambiente virtual FUNCIONAL (com qdrant-client) detectado."
    echo "Tente rodar: pip install qdrant-client rich requests"
fi

# 2. Configurar PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# 3. Verificar se Ollama está rodando
if ! pgrep -x "ollama" > /dev/null; then
    echo "🦙 Iniciando servidor Ollama em background..."
    nohup ollama serve > /dev/null 2>&1 &
    echo "⏳ Aguardando Ollama inicializar (5s)..."
    sleep 5
else
    echo "✅ Servidor Ollama detectado."
fi

# 4. Chamar o chat interativo
echo "✨ Iniciando Chat Interativo (usando $VENV_MSG)..."
# Usar exec para substituir o shell atual pelo python, economizando recursos
exec python3 scripts/interactive_ziva.py "$@"
