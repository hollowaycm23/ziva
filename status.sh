#!/bin/bash
#
# Ziva AI System - Status Check
# Verifica status de todos os serviços
#

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m'

echo -e "${MAGENTA}╔════════════════════════════════════════╗${NC}"
echo -e "${MAGENTA}║     ZIVA AI SYSTEM STATUS              ║${NC}"
echo -e "${MAGENTA}╚════════════════════════════════════════╝${NC}"
echo ""

# Check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo -e "${GREEN}✓ Online${NC}"
        return 0
    else
        echo -e "${RED}✗ Offline${NC}"
        return 1
    fi
}

# Check HTTP endpoint
check_http() {
    local url=$1
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200\|404" ; then
        echo -e "${GREEN}✓ Responding${NC}"
        return 0
    else
        echo -e "${RED}✗ Not responding${NC}"
        return 1
    fi
}

echo -e "${BLUE}Core Services:${NC}"
echo -n "  LM Studio (1234):      "
if curl -s --connect-timeout 2 --max-time 5 -o /dev/null "http://100.104.242.35:1234/v1/models" ; then
    echo -e "${GREEN}✓ Online${NC}"
else
    echo -e "${RED}✗ Offline${NC}"
fi

echo -n "  Kiwix (8081):          "
check_port 8081

echo -n "  SearxNG (8080):        "
check_port 8080

echo -n "  Ziva API (8000):       "
check_port 8000

echo -n "  P2P Binary (9000):     "
check_port 9000

echo -n "  Qdrant (6333):         "
check_port 6333

echo ""
echo -e "${BLUE}API Endpoints:${NC}"
echo -n "  /health:               "
check_http "http://localhost:8000/health"

echo -n "  /api/v1/chat:          "
check_http "http://localhost:8000/api/v1/chat"

echo ""
echo -e "${BLUE}Docker Containers:${NC}"
if command -v docker &> /dev/null; then
    RUNNING=$(docker ps --format "table {{.Names}}\t{{.Status}}" 2>/dev/null | grep -v NAMES || echo "None")
    if [ "$RUNNING" = "None" ]; then
        echo -e "  ${YELLOW}No containers running${NC}"
    else
        echo "$RUNNING" | while read line; do
            echo "  $line"
        done
    fi
else
    echo -e "  ${YELLOW}Docker not installed${NC}"
fi

echo ""
