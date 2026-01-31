import socket
import struct
import math
import logging

logger = logging.getLogger("NetworkOptimizer")

class NetworkOptimizer:
    """
    Utilitário para otimização de rede e compressão de dados.
    """
    
    # Comandos para otimização via sysctl (Linux)
    OPTIMIZATION_COMMANDS = [
        "sudo sysctl -w net.ipv4.tcp_rmem='4096 87380 134217728'",
        "sudo sysctl -w net.ipv4.tcp_wmem='4096 65536 134217728'"
    ]

    @staticmethod
    def optimize_socket(sock):
        """
        Aplica configurações de otimização em um socket TCP.
        """
        try:
            # Desabilitar algoritmo de Nagle (menor latência)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            
            # Aumentar buffers se possível (pode falhar dependendo do OS/Permissões)
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024 * 1024)
            except Exception:
                pass
                
            return sock
        except Exception as e:
            logger.warning(f"Falha ao otimizar socket: {e}")
            return sock

    @staticmethod
    def quantize_int8(vector):
        """
        Converte vetor de floats para int8 + scale.
        Retorna (bytes, float).
        """
        if not vector:
            return b'', 0.0

        # Encontrar max abs para escala
        max_val = max(abs(x) for x in vector)
        if max_val == 0:
            scale = 1.0
        else:
            scale = max_val / 127.0

        # Quantizar
        q_vals = []
        for x in vector:
            val = int(x / scale)
            # Clamp -127 to 127
            val = max(-127, min(127, val))
            q_vals.append(val)

        # Pack into bytes (signed char)
        q_bytes = struct.pack(f'{len(q_vals)}b', *q_vals)
        
        return q_bytes, scale

    @staticmethod
    def dequantize_int8(q_bytes, scale):
        """
        Reconstroi vetor de floats a partir de int8 bytes + scale.
        """
        if not q_bytes:
            return []

        count = len(q_bytes)
        q_vals = struct.unpack(f'{count}b', q_bytes)
        
        return [float(x) * scale for x in q_vals]