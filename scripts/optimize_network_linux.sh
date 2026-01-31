#!/bin/bash
# Otimizações de Rede - Linux (WSL)
# Execute com sudo para aplicar

echo "🚀 Aplicando Otimizações de Rede..."
echo "===================================="

# Verificar se é root
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  Este script precisa ser executado como root (sudo)"
    echo "Mostrando comandos que seriam executados:"
    echo ""
fi

# Aumentar buffers TCP
echo "📊 Configurando buffers TCP..."
sudo sysctl -w net.core.rmem_max=134217728 2>/dev/null || echo "  sudo sysctl -w net.core.rmem_max=134217728"
sudo sysctl -w net.core.wmem_max=134217728 2>/dev/null || echo "  sudo sysctl -w net.core.wmem_max=134217728"
sudo sysctl -w net.ipv4.tcp_rmem='4096 87380 134217728' 2>/dev/null || echo "  sudo sysctl -w net.ipv4.tcp_rmem='4096 87380 134217728'"
sudo sysctl -w net.ipv4.tcp_wmem='4096 65536 134217728' 2>/dev/null || echo "  sudo sysctl -w net.ipv4.tcp_wmem='4096 65536 134217728'"

# TCP window scaling
echo "🪟 Habilitando Window Scaling..."
sudo sysctl -w net.ipv4.tcp_window_scaling=1 2>/dev/null || echo "  sudo sysctl -w net.ipv4.tcp_window_scaling=1"

# TCP timestamps
echo "⏰ Habilitando Timestamps..."
sudo sysctl -w net.ipv4.tcp_timestamps=1 2>/dev/null || echo "  sudo sysctl -w net.ipv4.tcp_timestamps=1"

# TCP SACK
echo "📦 Habilitando SACK..."
sudo sysctl -w net.ipv4.tcp_sack=1 2>/dev/null || echo "  sudo sysctl -w net.ipv4.tcp_sack=1"

# Aumentar backlog
echo "🔧 Configurando Backlog..."
sudo sysctl -w net.core.netdev_max_backlog=5000 2>/dev/null || echo "  sudo sysctl -w net.core.netdev_max_backlog=5000"

# TCP Fast Open
echo "⚡ Habilitando TCP Fast Open..."
sudo sysctl -w net.ipv4.tcp_fastopen=3 2>/dev/null || echo "  sudo sysctl -w net.ipv4.tcp_fastopen=3"

# Congestion control
echo "🚦 Configurando Congestion Control..."
sudo sysctl -w net.ipv4.tcp_congestion_control=bbr 2>/dev/null || echo "  sudo sysctl -w net.ipv4.tcp_congestion_control=bbr"

echo ""
echo "✅ Otimizações aplicadas!"
echo ""
echo "📋 Verificar configurações atuais:"
echo "  sysctl net.ipv4.tcp_rmem"
echo "  sysctl net.ipv4.tcp_wmem"
echo "  sysctl net.core.rmem_max"
echo "  sysctl net.core.wmem_max"
