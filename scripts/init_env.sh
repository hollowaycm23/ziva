#!/bin/bash
# scripts/init_env.sh - Generate secure secrets for .env

set -e

ENV_FILE=".env"

if [ -f "$ENV_FILE" ]; then
    echo "✅ .env já existe, pulando criação"
    exit 0
fi

echo "🔐 Gerando .env com secrets seguros..."

# Copiar de template
cp .env.production "$ENV_FILE"

# Gerar secrets aleatórios
SEARXNG_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || echo "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0")
WEBUI_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(16))" 2>/dev/null || echo "webui_secret_key_placeholder")
LETTA_PASSWORD=$(python3 -c "import secrets; print(secrets.token_hex(16))" 2>/dev/null || echo "letta_password_placeholder")
HASH_SALT=$(python3 -c "import secrets; print(secrets.token_hex(16))" 2>/dev/null || echo "hash_salt_placeholder")

# Atualizar .env com secrets gerados
echo "📝 Atualizando secrets no .env..."

# Usar sed ou awk dependendo do sistema
if command -v sed &> /dev/null; then
    sed -i.bak "s/SEARXNG_SECRET_KEY=.*/SEARXNG_SECRET_KEY=$SEARXNG_SECRET/" "$ENV_FILE" || true
    sed -i.bak "s/WEBUI_SECRET_KEY=.*/WEBUI_SECRET_KEY=$WEBUI_SECRET/" "$ENV_FILE" || true
    sed -i.bak "s/LETTA_DB_PASSWORD=.*/LETTA_DB_PASSWORD=$LETTA_PASSWORD/" "$ENV_FILE" || true
    sed -i.bak "s/HASH_SALT=.*/HASH_SALT=$HASH_SALT/" "$ENV_FILE" || true
fi

echo "✅ .env criado com secrets:"
echo "   - SEARXNG_SECRET_KEY: ${SEARXNG_SECRET:0:16}..."
echo "   - WEBUI_SECRET_KEY: ${WEBUI_SECRET:0:16}..."
echo "   - LETTA_DB_PASSWORD: ${LETTA_PASSWORD:0:16}..."
echo "   - HASH_SALT: ${HASH_SALT:0:16}..."
echo ""
echo "⚠️  Edite .env para adicionar valores personalizados (OPENAI_API_KEY, etc.)"
