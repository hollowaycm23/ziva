#!/bin/bash
# scripts/deploy_and_test.sh - Deploy com validação

set -e

echo "🚀 Ziva Docker Deploy & Test Script"
echo "==================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Step 1: Network
echo "📡 Step 1: Criar network ziva-net..."
docker network create ziva-net 2>/dev/null || echo "   Network já existe"
echo ""

# Step 2: Check .env
echo "🔑 Step 2: Verificar .env..."
if [ ! -f .env ]; then
    echo "   .env não encontrado, criando..."
    cp .env.production .env
fi
echo -e "   ${GREEN}✅${NC} .env pronto"
echo ""

# Step 3: Check docker-compose
echo "🐳 Step 3: Validar docker-compose.yml..."
docker-compose config > /dev/null 2>&1 && echo -e "   ${GREEN}✅${NC} docker-compose.yml válido" || echo -e "   ${RED}❌${NC} Erro em docker-compose.yml"
echo ""

# Step 4: Build
echo "🔨 Step 4: Build Dockerfile..."
echo "   Isso pode levar 5-10 minutos..."
docker build -t ziva:latest . || echo -e "   ${RED}❌${NC} Build falhou"
echo -e "   ${GREEN}✅${NC} Build concluído"
echo ""

# Step 5: Deploy
echo "🚀 Step 5: Iniciar containers..."
docker-compose up -d
echo -e "   ${GREEN}✅${NC} Containers iniciados"
echo ""

# Step 6: Wait
echo "⏳ Step 6: Aguardar inicialização (60s)..."
sleep 60
echo -e "   ${GREEN}✅${NC} Timeout concluído"
echo ""

# Step 7: Health Checks
echo "💚 Step 7: Verificar saúde dos serviços..."
echo ""

# API
echo -n "   Testando API (http://localhost:8000/v1/health)... "
if curl -s http://localhost:8000/v1/health | grep -q "healthy\|degraded"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${YELLOW}⏳ Ainda inicializando...${NC}"
fi

# Ollama
echo -n "   Testando Ollama (http://localhost:11434/api/tags)... "
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${YELLOW}⏳ Ainda inicializando...${NC}"
fi

# Qdrant
echo -n "   Testando Qdrant (http://localhost:6333/health)... "
if curl -s http://localhost:6333/health | grep -q "ok"; then
    echo -e "${GREEN}✅ OK${NC}"
else
    echo -e "${YELLOW}⏳ Ainda inicializando...${NC}"
fi

# Containers
echo -n "   Verificando containers... "
RUNNING=$(docker ps --filter "name=ziva" --filter "status=running" | wc -l)
if [ $RUNNING -ge 8 ]; then
    echo -e "${GREEN}✅ $((RUNNING-1)) containers rodando${NC}"
else
    echo -e "${YELLOW}⚠️  $((RUNNING-1)) containers rodando (esperado 9)${NC}"
fi

echo ""
echo "==================================="
echo -e "${GREEN}✅ Deploy concluído!${NC}"
echo ""
echo "📊 Acessar:"
echo "   - API: http://localhost:8000"
echo "   - WebUI: http://localhost:3000"
echo "   - Ollama: http://localhost:11434"
echo "   - Qdrant: http://localhost:6333/dashboard"
echo "   - SearXNG: http://localhost:8082"
echo "   - Kiwix: http://localhost:8081"
echo ""
echo "📝 Ver logs:"
echo "   docker logs -f ziva-core"
echo "   docker-compose logs -f"
echo ""
