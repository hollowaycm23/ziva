import logging
import time
import os
from pathlib import Path
from network.local import LocalExecutor

logger = logging.getLogger("ZivaMgr")


class ZivaManager:
    """
    Orquestrador local para o nó Ziva.
    Gerencia o ciclo de vida dos serviços via Docker Compose.
    """

    def __init__(self, project_root="/home/holloway/ziva"):
        self.project_root = project_root
        self.executor = LocalExecutor()
        self.compose_file = os.path.join(project_root, "docker-compose.yml")

        if not os.path.exists(self.compose_file):
            logger.error(f"FATAL: docker-compose.yml not found at {self.compose_file}")

    def _run_compose(self, cmd):
        """Helper para comandos docker compose."""
        full_cmd = f"docker compose -f {self.compose_file} {cmd}"
        return self.executor.run_command(full_cmd, cwd=self.project_root, timeout=300)

    def start_services(self):
        """
        Inicia a stack Ziva completa.
        """
        logger.info("Iniciando Serviços Ziva (Docker Compose)...")
        
        # Garante que as variáveis de ambiente corretas estão setadas se não estiverem no .env
        # Mas assumimos que docker-compose.yml já tem o que precisa ou usa .env
        
        res = self._run_compose("up -d")
        if res["success"]:
            logger.info("✅ Stack Ziva iniciada com sucesso.")
        else:
            logger.error(f"❌ Falha ao iniciar Ziva: {res['stderr']}")
        return res

    def stop_services(self):
        """
        Para a stack Ziva.
        """
        logger.info("Parando Serviços Ziva...")
        res = self._run_compose("down")
        if res["success"]:
            logger.info("✅ Stack Ziva parada.")
        else:
            logger.error(f"❌ Falha ao parar Ziva: {res['stderr']}")
        return res

    def restart_services(self):
        """
        Reinicia a stack Ziva.
        """
        logger.info("Reiniciando Serviços Ziva...")
        self.stop_services()
        time.sleep(2) # Give Docker time to cleanup networks
        return self.start_services()

    def check_health(self):
        """
        Verifica saúde dos containers e APIs.
        """
        health_report = {}
        
        # 1. Check Docker Containers
        ps_res = self.executor.run_command("docker ps --format '{{.Names}}'")
        running_containers = ps_res["stdout"].splitlines() if ps_res["success"] else []
        
        expected_services = ["ziva-core", "ziva-qdrant", "ziva-openwebui"]
        status = {}
        all_up = True
        
        for svc in expected_services:
            is_up = any(svc in c for c in running_containers)
            status[svc] = "UP" if is_up else "DOWN"
            if not is_up: all_up = False

        health_report["services"] = status
        health_report["overall_status"] = "HEALTHY" if all_up else "DEGRADED"

        # 2. Check API Health (se core estiver UP)
        if status.get("ziva-core") == "UP":
            api_res = self.executor.run_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/api/health")
            health_report["api_response"] = api_res["stdout"]
        
        return health_report

    def get_logs(self, service="ziva-core", lines=50):
        """
        Obtém logs recentes de um serviço.
        """
        return self.executor.run_command(f"docker logs {service} --tail {lines}")
