#!/bin/bash
#
# Ziva AI System - Restart Script
# Para e reinicia todos os serviços
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🔄 Restarting Ziva AI System..."
echo ""

# Stop
bash "$SCRIPT_DIR/stop.sh"

#!/bin/bash
echo "⚠️  AVISO: Este script (restart.sh) está depreciado."
echo "➡️  Por favor, use: python3 scripts/control_ziva.py restart"
echo ""
echo "🚀 Redirecionando para o novo gerenciador..."
export PYTHONPATH=$PYTHONPATH:$(pwd)
python3 scripts/control_ziva.py restart
