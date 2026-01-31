#!/bin/bash
# Helper script para executar comandos sudo automaticamente usando senha do .env

# Carregar .env
if [ -f "/home/holloway/ziva/.env" ]; then
    export $(grep -v '^#' /home/holloway/ziva/.env | xargs)
fi

# Verificar se a senha está definida
if [ -z "$SUDO_PASSWORD" ]; then
    echo "Erro: SUDO_PASSWORD não está definida no .env"
    exit 1
fi

# Executar comando com sudo usando a senha
echo "$SUDO_PASSWORD" | sudo -S "$@"
