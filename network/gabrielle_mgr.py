import logging
import time
from network.remote import RemoteExecutor

logger = logging.getLogger("GabrielleMgr")


class GabrielleManager:
    """
    Orquestrador especializado para o nó Gabrielle (falcon).
    Gerencia o ciclo de vida dos serviços Ollama, SearxNG, Kiwix e API.
    """

    def __init__(self, hostname="falcon"):
        self.hostname = hostname
        # Obtém IP físico do registro se disponível para redundância
        from core.registry import NodeRegistry
        registry = NodeRegistry()
        node_info = registry.get_node(hostname)
        fallback = node_info.get("physical_ip") if node_info else None

        self.executor = RemoteExecutor(
            remote_host=hostname, fallback_ip=fallback)

    def start_core_services(self):
        """
        Inicia recursivamente todos os serviços necessários na Gabrielle.
        Assume que os serviços estão instalados e configurados como systemd ou docker.
        """
        logger.info(
            f"Iniciando Core Services na Gabrielle ({
                self.hostname})...")

        results = {}

        # 1. Ollama
        results["ollama"] = self.executor.run_command(
            "sudo systemctl start ollama || ollama serve > /dev/null 2>&1 & ")

        # 2. SearxNG (Assume Docker ou Systemd)
        results["searxng"] = self.executor.run_command(
            "sudo docker start searxng || sudo systemctl start searxng")

        # 3. Kiwix (Assume server rodando em porta específica)
        results["kiwix"] = self.executor.run_command(
            "sudo systemctl start kiwix-serve")

        # 4. Qwen Coder (Garante carregamento no Ollama)
        results["qwen"] = self.executor.run_command(
            "ollama run qwen2.5-coder:7b 'echo hello' > /dev/null 2>&1 &")

        return results

    def send_raw_command(self, command):
        """Passa um comando direto para a Gabrielle."""
        return self.executor.run_command(command)

    def check_health(self):
        """Verifica se os serviços estão respondendo."""
        health = {}
        # Checks simples via shell remota
        health["ssh"] = self.executor.check_connection()
        health["ollama"] = self.executor.run_command(
            "pgrep ollama").get("success", False)
        health["searxng"] = self.executor.run_command(
            "curl -s http://localhost:8080 > /dev/null && echo ok").get("stdout") == "ok"
        return health
