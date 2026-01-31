import socket
import logging
import subprocess
from core.database import DatabaseManager

logger = logging.getLogger("ConnectionManager")


class ConnectionManager:
    """
    Gerencia a conectividade robusta com nós remotos (ex: Gabrielle).
    Implementa failover: TCP Socket (Binary) -> Tailscale SSH -> Direct SSH.
    """

    def __init__(self, target_node="node08", target_host="gabrielle",
                 target_port=9000, fallback_ip=None):
        self.target_node = target_node
        self.target_host = target_host
        self.target_port = target_port
        self.fallback_ip = fallback_ip
        self.db = DatabaseManager()

        self.active_channel = None
        self.last_heartbeat = 0

    def check_connectivity(self):
        """
        Verifica todos os canais e estabelece o melhor disponível.
        """
        if self._check_tcp_socket(self.target_host, self.target_port):
            self.active_channel = 'binary'
            logger.info(
                f"Canal Binário (TCP/{self.target_port}) ATIVO.")
            return True

        if self._check_ssh(self.target_host):
            self.active_channel = 'tailscale_ssh'
            logger.info(f"Canal Tailscale SSH ATIVO com {self.target_host}.")
            return True

        if self.fallback_ip and self._check_tcp_socket(self.fallback_ip, 2222):
            if self._check_ssh(self.fallback_ip):
                self.active_channel = 'direct_ssh'
                logger.warning(
                    f"Failover: Canal Direct SSH ATIVO com {self.fallback_ip}.")
                return True

        self.active_channel = 'none'
        logger.critical(
            f"Todos os canais com {self.target_node} falharam.")
        return False

    def get_transport_method(self):
        """Retorna o método de transporte ideal baseada na verificação."""
        if not self.active_channel or self.active_channel == 'none':
            self.check_connectivity()

        return self.active_channel

    def _check_tcp_socket(self, host, port, timeout=3):
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False

    def _check_ssh(self, host, user="holloway"):
        try:
            cmd = [
                "ssh",
                "-p",
                "2222",
                "-o",
                "ConnectTimeout=3",
                "-o",
                "StrictHostKeyChecking=no",
                f"{user}@{host}",
                "echo 'pong'"]
            res = subprocess.run(cmd, capture_output=True)
            return res.returncode == 0
        except BaseException:
            return False