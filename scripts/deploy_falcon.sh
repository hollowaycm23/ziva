#!/bin/bash
# Script de Deploy para Nó Secundário (Falcon)
# Uso: ./deploy_falcon.sh [usuario@ip_destino]

TARGET=${1:-"holloway@falcon"} # Default target
IMAGE_FILE="ziva_core.tar"
COMPOSE_FILE="docker-compose.yml"
REMOTE_DIR="~/ziva_deploy"

echo "🦅 Iniciando Deploy Ziva para $TARGET..."

# 1. Verificar se a imagem exportada existe
if [ ! -f "$IMAGE_FILE" ]; then
    echo "❌ Erro: Arquivo $IMAGE_FILE não encontrado."
    echo "💡 Execute: docker save -o $IMAGE_FILE ziva-ziva-core:latest"
    exit 1
fi

# 2. Criar diretório remoto
echo "📂 Criando diretório remoto..."
ssh -p 2222 $TARGET "mkdir -p $REMOTE_DIR"

# 3. Transferir arquivos (Rsync com progresso)
# Excluímos 'models/' se estiverem na imagem, mas transferimos o compose
echo "🚀 Transferindo imagem e configurações (Isso pode demorar)..."
rsync -avP -e "ssh -p 2222" $IMAGE_FILE $COMPOSE_FILE $TARGET:$REMOTE_DIR/

# 4. Executar setup remoto
echo "⚙️ Configurando nó remoto..."
ssh -p 2222 $TARGET << EOF
    cd $REMOTE_DIR
    
    echo "🐳 Carregando imagem Docker..."
    docker load -i $IMAGE_FILE
    
    echo "🚀 Iniciando containers..."
    # Ajuste para Worker Node se necessário (e.g. override env vars)
    export ZIVA_NODE_TYPE="worker"
    docker compose up -d
    
    echo "✅ Ziva Falcon Node está online!"
EOF

echo "🎉 Deploy concluído com sucesso!"
