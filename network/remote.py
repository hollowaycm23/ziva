import subprocess
import logging
import shutil

logger = logging.getLogger("RemoteExecutor")


class RemoteExecutor:
    """
    Gerencia execução de comandos remotos via SSH (Tailscale).
    """

    def __init__(self, remote_host, fallback_ip=None):
        """
        Args:
            remote_host (str): Hostname ou IP do nó remoto (ex: 'gabrielle', '100.x.y.z').
            fallback_ip (str, optional): IP físico para failover se o host principal falhar.
        """
        self.primary_host = remote_host
        self.fallback_ip = fallback_ip
        self.active_host = self.primary_host

        self.ssh_bin = shutil.which("ssh")

        if not self.ssh_bin:
            logger.error(
                "Binário 'ssh' não encontrado. Execução remota indisponível.")

    def run_command(self, command, timeout=30):
        """
        Executa um comando no host remoto via SSH.
        """
        if not self.ssh_bin:
            return {"success": False, "error": "SSH binary missing"}

        # Construção segura do comando SSH
        ssh_cmd = [
            self.ssh_bin,
            "-p", "2222",  # Porta customizada solicitada pelo usuário
            "-o", "BatchMode=yes",
            "-o", "ConnectTimeout=5",
            self.active_host,  # Use active host
            command
        ]

        try:
            logger.info(f"Executando remoto em {self.active_host}: {command}")
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            success = (result.returncode == 0)
            if not success:
                logger.warning(
                    f"Comando remoto falhou (Exit {
                        result.returncode}): {
                        result.stderr.strip()}")

            return {
                "success": success,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "exit_code": result.returncode
            }

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout ao executar comando em {self.active_host}")
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            logger.error(f"Erro na execução remota: {e}")
            return {"success": False, "error": str(e)}

    def check_connection(self):
        """Verifica se o host é acessível via SSH com Failover."""
        hosts_to_try = [self.primary_host]
        if self.fallback_ip:
            hosts_to_try.append(self.fallback_ip)

        for host in hosts_to_try:
            res = self._try_ping(host)
            if res.get("success", False) and res.get("stdout") == "ping":
                self.active_host = host
                if host != self.primary_host:
                    logger.info(f"Conectado via IP alternativo: {host}")
                return True
        return False

    def _try_ping(self, host):
        # Helper interno para ping sem alterar active_host prematuramente
        if not self.ssh_bin:
            return {}
        cmd = [
            self.ssh_bin,
            "-p",
            "2222",
            "-o",
            "BatchMode=yes",
            "-o",
            "ConnectTimeout=5",
            host,
            "echo 'ping'"]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return {"success": (r.returncode == 0), "stdout": r.stdout.strip()}
        except BaseException:
            return {}
