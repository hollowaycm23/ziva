#!/bin/bash
# ZIVA Start Wrapper - Orquestrador Unificado
# Delega toda a lógica para o script Python que já possui auto-cura e gestão de ambiente.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "🚀 Iniciando Ziva Environment..."
# Configuração LM Studio (Opcionais, prioridade para o .env)
export LLM_BASE_URL="http://127.0.0.1:1234/v1"
exec python3 scripts/start_ziva.py "$@"
