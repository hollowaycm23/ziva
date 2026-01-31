import subprocess
import os
import logging
from pathlib import Path

logger = logging.getLogger("ZivaTransfer")


class TransferManager:
    """
    Gerenciador de transferências de arquivos P2P via SSH/SCP.

    Facilita a comunicação segura e cópia de arquivos entre nós da Tailscale
    (ex: Node07 <-> Node08).
    """

    def __init__(self, local_user="holloway", remote_user="holloway",
                 remote_host="100.114.201.84", fallback_ip=None):
        """
        Inicializa configurações de conexão remota.

        Args:
            local_user (str): Usuário local.
            remote_user (str): Usuário no host remoto.
            remote_host (str): Hostname ou IP do nó remoto (Tailscale).
            fallback_ip (str, optional): IP Físico/LAN para tentativa de conexão se Tailscale falhar.
        """
        self.local_user = local_user
        self.remote_user = remote_user
        self.primary_host = remote_host
        self.fallback_ip = fallback_ip

        # Current active host (starts with primary)
        self.active_host = self.primary_host

        self.common_options = [
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "ConnectTimeout=5"
        ]

    def _get_ssh_cmd(self, host, command):
        """Constrói o comando SSH com a porta correta (-p)."""
        return ["ssh", "-p", "22"] + self.common_options + \
               [f"{self.remote_user}@{host}", command]

    def _get_scp_cmd(self, source, dest):
        """Constrói o comando SCP com a porta correta (-P)."""
        return ["scp", "-P", "22"] + self.common_options + [source, dest]

    def check_connection(self):
        """
        Verifica se o host remoto está acessível via SSH.
        Tenta Primary -> Fallback se necessário.
        """
        hosts_to_try = [self.primary_host]
        if self.fallback_ip:
            hosts_to_try.append(self.fallback_ip)

        for host in hosts_to_try:
            try:
                cmd = self._get_ssh_cmd(host, "echo 'pong'")
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    self.active_host = host  # Update active
                    if host != self.primary_host:
                        logger.info(
                            f"Conectado via IP alternativo/físico: {host}")
                    return True
            except Exception as e:
                logger.warning(f"Falha ao conectar em {host}: {e}")

        return False

    def send_file(self, local_path, remote_path):
        """
        Envia um arquivo local para o host remoto via SCP.

        Args:
            local_path (str): Caminho do arquivo origem.
            remote_path (str): Caminho de destino no host remoto.

        Returns:
            bool: True se a transferência for bem-sucedida.
        """
        if not Path(local_path).exists():
            logger.error(f"Arquivo local não encontrado: {local_path}")
            return False

        try:
            # scp -o ... local_file user@host:remote_path
            # Ensure remote directory exists
            remote_dir = os.path.dirname(remote_path)
            mkdir_cmd = self._get_ssh_cmd(self.active_host, f"mkdir -p {remote_dir}")
            subprocess.run(mkdir_cmd, capture_output=True, timeout=5)

            target = f"{self.remote_user}@{self.active_host}:{remote_path}"
            cmd = self._get_scp_cmd(str(local_path), target)
            logger.info(f"Iniciando transferência: {local_path} -> {target}")

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info("Transferência concluída com sucesso.")
                return True
            else:
                logger.error(f"Falha na transferência: {result.stderr}")
                return False
        except FileNotFoundError:
            logger.warning("Binário 'scp' ou 'ssh' não encontrado. Transferência abortada.")
            return False
        except Exception as e:
            logger.error(f"Erro na execução do SCP: {e}")
            return False

    def fetch_file(self, remote_path, local_path):
        """
        Busca um arquivo do host remoto via SCP (Download).

        Args:
            remote_path (str): Caminho do arquivo origem no host remoto.
            local_path (str): Caminho de destino local.

        Returns:
            bool: True se o download for bem-sucedido.
        """
        try:
            source = f"{self.remote_user}@{self.active_host}:{remote_path}"
            cmd = self._get_scp_cmd(source, str(local_path))
            logger.info(f"Buscando arquivo: {source} -> {local_path}")

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info("Download concluído com sucesso.")
                return True
            else:
                logger.error(f"Falha no download: {result.stderr}")
                return False
        except FileNotFoundError:
            logger.warning("Binário 'scp' ou 'ssh' não encontrado. Download abortado.")
            return False
        except Exception as e:
            logger.error(f"Erro na execução do SCP: {e}")
            return False
