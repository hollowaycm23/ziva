#!/bin/bash
# scripts/check_docker_config.sh - Diagnosticar configuração Docker

echo "🔍 Ziva Docker Configuration Diagnostics"
echo "======================================="
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅${NC} $2"
    else
        echo -e "${RED}❌${NC} $2"
        return 1
    fi
}

warn_status() {
    echo -e "${YELLOW}⚠️${NC}  $1"
}

# 1. Check Docker
echo "1️⃣ Verificando Docker..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | cut -d ' ' -f3 | cut -d ',' -f1)
    check_status 0 "Docker instalado: v$DOCKER_VERSION"
else
    check_status 1 "Docker NÃO encontrado - instale Docker"
fi

# 2. Check Docker Compose
echo ""
echo "2️⃣ Verificando Docker Compose..."
if command -v docker-compose &> /dev/null; then
    DC_VERSION=$(docker-compose --version | cut -d ' ' -f3 | cut -d ',' -f1)
    check_status 0 "Docker Compose instalado: v$DC_VERSION"
else
    check_status 1 "Docker Compose NÃO encontrado - instale Docker Compose"
fi

# 3. Check .env
echo ""
echo "3️⃣ Verificando arquivos de configuração..."
if [ -f .env ]; then
    check_status 0 ".env existe"
else
    check_status 1 ".env NÃO encontrado"
    warn_status "Execute: cp .env.production .env"
fi

if [ -f docker-compose.yml ]; then
    check_status 0 "docker-compose.yml existe"
else
    check_status 1 "docker-compose.yml NÃO encontrado"
fi

if [ -f Dockerfile ]; then
    check_status 0 "Dockerfile existe"
else
    check_status 1 "Dockerfile NÃO encontrado"
fi

# 4. Check Network
echo ""
echo "4️⃣ Verificando network Docker..."
if docker network inspect ziva-net > /dev/null 2>&1; then
    check_status 0 "Network 'ziva-net' existe"
else
    check_status 1 "Network 'ziva-net' NÃO existe"
    warn_status "Execute: docker network create ziva-net"
fi

# 5. Check Services Status
echo ""
echo "5️⃣ Verificando status dos containers..."
RUNNING=$(docker ps --format "{{.Names}}" | grep -c "ziva-" || echo 0)
TOTAL=9

if [ $RUNNING -eq 0 ]; then
    warn_status "Nenhum container Ziva está rodando"
    echo "   Execute: docker-compose up -d"
else
    echo "   Containers rodando: $RUNNING/$TOTAL"
    docker ps --filter "name=ziva" --format "table {{.Names}}\t{{.Status}}"
fi

# 6. Check Ollama
echo ""
echo "6️⃣ Verificando Ollama..."
if docker ps --filter "name=ziva-ollama" --filter "status=running" | grep -q ziva-ollama; then
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        check_status 0 "Ollama está pronto"
    else
        check_status 1 "Ollama não responde na porta 11434"
    fi
else
    warn_status "Container ziva-ollama não está rodando"
fi

# 7. Check Qdrant
echo ""
echo "7️⃣ Verificando Qdrant..."
if docker ps --filter "name=ziva-qdrant" --filter "status=running" | grep -q ziva-qdrant; then
    if curl -s http://localhost:6333/health > /dev/null 2>&1; then
        check_status 0 "Qdrant está pronto"
    else
        check_status 1 "Qdrant não responde na porta 6333"
    fi
else
    warn_status "Container ziva-qdrant não está rodando"
fi

# 8. Check API
echo ""
echo "8️⃣ Verificando API Server..."
if docker ps --filter "name=ziva-core" --filter "status=running" | grep -q ziva-core; then
    if curl -s http://localhost:8000/v1/health > /dev/null 2>&1; then
        check_status 0 "API Server está pronto na porta 8000"
    else
        warn_status "API Server não responde ainda na porta 8000"
    fi
else
    warn_status "Container ziva-core não está rodando"
fi

# 9. Check Memory
echo ""
echo "9️⃣ Verificando recursos..."
TOTAL_MEM=$(free -h 2>/dev/null | awk '/^Mem:/ {print $2}' || echo "?")
if [ "$TOTAL_MEM" != "?" ]; then
    if [ "$(echo $TOTAL_MEM | grep -oE '^[0-9]+' || echo 0)" -ge 16 ]; then
        check_status 0 "RAM disponível: $TOTAL_MEM (mínimo 16GB OK)"
    else
        check_status 1 "RAM insuficiente: $TOTAL_MEM (mínimo 16GB necessário)"
    fi
else
    warn_status "Não foi possível verificar RAM"
fi

# 10. Check Disk
echo ""
echo "🔟 Verificando espaço em disco..."
DISK_FREE=$(df -h . | awk 'NR==2 {print $4}')
DISK_PERCENT=$(df . | awk 'NR==2 {print $5}' | tr -d '%')
if [ "$DISK_PERCENT" -lt 80 ]; then
    check_status 0 "Espaço em disco: ${DISK_FREE} livres (${DISK_PERCENT}% usado)"
else
    check_status 1 "Pouco espaço em disco: ${DISK_FREE} livres (${DISK_PERCENT}% usado)"
fi

# Summary
echo ""
echo "======================================="
echo "🎯 Próximos passos:"
echo ""
echo "1. Inicializar network (se necessário):"
echo "   docker network create ziva-net 2>/dev/null || true"
echo ""
echo "2. Iniciar containers:"
echo "   docker-compose up -d"
echo ""
echo "3. Aguardar inicialização (30-60s):"
echo "   sleep 60"
echo ""
echo "4. Verificar saúde:"
echo "   docker logs ziva-core"
echo ""
echo "5. Acessar:"
echo "   - API: http://localhost:8000"
echo "   - WebUI: http://localhost:3000"
echo "   - Ollama: http://localhost:11434"
echo ""
