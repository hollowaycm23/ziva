import subprocess
import logging
import shutil
import json

logger = logging.getLogger("TailscaleManager")


class TailscaleManager:
    """
    Gerencia a instalação, autenticação e status do Tailscale.
    """

    @staticmethod
    def is_installed():
        """Verifica se o binário do tailscale está no PATH."""
        return shutil.which("tailscale") is not None

    @staticmethod
    def install():
        """
        Tenta instalar o Tailscale usando o script oficial.
        """
        logger.info("Iniciando tentativa de instalação do Tailscale...")
        try:
            cmd = "curl -fsSL https://tailscale.com/install.sh | sh"
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("Comando de instalação executado com sucesso.")
                return True, result.stdout
            else:
                logger.error(f"Falha na instalação: {result.stderr}")
                return False, result.stderr
        except Exception as e:
            logger.error(f"Erro durante instalação: {e}")
            return False, str(e)

    @staticmethod
    def get_login_url():
        """
        Inicia o processo de login e retorna a URL de autenticação.
        """
        try:
            cmd = ["tailscale", "up", "--qr"]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10)
            output = result.stderr + result.stdout
            import re
            url_match = re.search(
                r'https://login\.tailscale\.com/a/\S+', output)
            if url_match:
                return url_match.group(0)
            return None
        except subprocess.TimeoutExpired as e:
            output = e.stderr.decode() if e.stderr else ""
            import re
            url_match = re.search(
                r'https://login\.tailscale\.com/a/\S+', output)
            if url_match:
                return url_match.group(0)
            return None
        except Exception as e:
            logger.error(f"Erro ao obter URL de login: {e}")
            return None

    @staticmethod
    def get_status():
        """Retorna o status atual da rede em JSON."""
        if not TailscaleManager.is_installed():
            return {"status": "not_installed"}
        try:
            result = subprocess.run(
                ["tailscale", "status", "--json"], capture_output=True, text=True)
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                return {"status": "down", "error": result.stderr}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @staticmethod
    def ensure_connected():
        """
        Loop de verificação/reparação rápida.
        """
        if not TailscaleManager.is_installed():
            logger.warning(
                "Tailscale não instalado. Ziva operando em modo local apenas.")
            return False
        status = TailscaleManager.get_status()
        backend_state = status.get("BackendState", "Unknown")
        if backend_state == "Running":
            logger.info("Tailscale conectado e operacional.")
            return True
        else:
            logger.info(
                f"Tailscale em estado: {backend_state}. Necessário intervenção.")
            return False