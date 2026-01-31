#!/bin/bash

echo "🛑 Parando Sistema Ziva..."
echo "================================"

# 1. Parar Qdrant
echo ""
echo "🧠 Parando Qdrant..."
if docker ps | grep -q ziva-qdrant; then
    docker stop ziva-qdrant
    echo "   ✅ Qdrant parado"
else
    echo "   ℹ️  Qdrant não estava rodando"
fi

# 2. Parar Servidor P2P
echo ""
echo "🌐 Parando Servidor P2P..."
pkill -f "binary_server.py"
if [ $? -eq 0 ]; then
    echo "   ✅ Servidor P2P parado"
else
    echo "   ℹ️  Servidor P2P não estava rodando"
fi

# 3. Parar API
echo ""
echo "🔌 Parando API..."
pkill -f "uvicorn.*server:app"
if [ $? -eq 0 ]; then
    echo "   ✅ API parada"
else
    echo "   ℹ️  API não estava rodando"
fi

# 4. Parar Ollama (opcional - comentado por padrão)
# echo ""
# echo "🤖 Parando Ollama..."
# pkill -f "ollama serve"

echo ""
echo "================================"
echo "✅ Sistema Ziva parado!"
echo "================================"
echo ""
echo -e "${YELLOW}🧹 Clearing Python cache...${NC}"
find "$PROJECT_ROOT" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$PROJECT_ROOT" -type f -name "*.pyc" -delete 2>/dev/null || true
echo -e "${MAGENTA}✅ Python cache cleared${NC}"

echo ""
echo -e "${MAGENTA}✅ Ziva AI System stopped${NC}"
echo ""
