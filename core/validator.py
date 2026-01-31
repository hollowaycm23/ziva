import socket
import importlib.metadata
import logging
from pathlib import Path

logger = logging.getLogger("SystemValidator")


class SystemValidator:
    """
    Validador de integridade do sistema e ambiente.

    Verifica disponibilidade de portas de rede e conflitos de dependências
    antes da inicialização dos serviços críticos.
    """

    @staticmethod
    def is_port_free(port, host="127.0.0.1"):
        """
        Verifica se uma porta TCP está livre para uso.

        Args:
            port (int): Porta a ser verificada.
            host (str): Endereço de bind.

        Returns:
            bool: True se a porta estiver livre, False caso contrário.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            try:
                s.bind((host, port))
                return True
            except OSError:
                return False

    @staticmethod
    def check_dependencies(requirements_path):
        """
        Verifica se as dependências listadas no requirements.txt estão satisfeitas.

        Args:
            requirements_path (str): Caminho para o arquivo requirements.txt.

        Returns:
            list[str]: Lista de pacotes ausentes ou conflitantes.
        """
        missing = []
        if not Path(requirements_path).exists():
            logger.warning(
                f"Arquivo de requisitos não encontrado: {requirements_path}")
            return missing

        with open(requirements_path, 'r') as f:
            requirements = [
                line.strip() for line in f if line.strip() and not line.startswith('#')]

        for req in requirements:
            # Simplificação: assume formato 'package>=version' ou 'package'
            pkg_name = req.split('>=')[0].split('==')[0].split('<')[0]
            try:
                importlib.metadata.version(pkg_name)
            except importlib.metadata.PackageNotFoundError:
                missing.append(req)
            except Exception as e:
                logger.warning(f"Erro ao verificar {pkg_name}: {e}")

        return missing

    @staticmethod
    def get_pid_on_port(port):
        """
        Identifica o PID do processo ocupando a porta (Linux).
        Requer comando 'lsof' ou 'ss' ou 'fuser'.
        Usaremos 'ss' por ser padrão.
        """
        import subprocess
        try:
            # ss -lptn 'sport = :<port>'
            cmd = ["ss", "-lptn", f"sport = :{port}"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            # Saida ex: LISTEN 0 128 127.0.0.1:8080 0.0.0.0:*
            # users:(("python3",pid=1234,fd=3))
            import re
            match = re.search(r'pid=(\d+)', result.stdout)
            if match:
                return int(match.group(1))
        except Exception as e:
            logger.error(f"Erro ao buscar PID na porta {port}: {e}")
        return None

    @staticmethod
    def get_process_name(pid):
        """
        Recupera o nome do processo pelo PID.
        """
        try:
            with open(f"/proc/{pid}/cmdline", "r") as f:
                cmdline = f.read().replace('\0', ' ').strip()
                return cmdline
        except Exception:
            return None

    @staticmethod
    def release_port(port):
        """
        Tenta liberar a porta matando o processo que a ocupa, COM SEGURANÇA.

        Args:
            port (int): Porta a ser liberada.

        Returns:
            bool: True se conseguiu liberar ou já estava livre.
        """
        if SystemValidator.is_port_free(port):
            return True

        pid = SystemValidator.get_pid_on_port(port)
        if pid:
            proc_name = SystemValidator.get_process_name(pid)
            logger.warning(
                f"Porta {port} ocupada pelo PID {pid} ({proc_name}).")

            # SAFEGUARD: Whitelist de processos que podemos matar
            # Evita matar processo do sistema ou outros críticos
            safe_processes = [
                "llama-server",
                "python",
                "python3",
                "start_agent",
                "ziva"]
            is_safe = False
            if proc_name:
                for safe in safe_processes:
                    # Contém o nome (ex: /usr/bin/python3 ziva.py)
                    if safe in proc_name:
                        is_safe = True
                        break

            if not is_safe:
                logger.error(
                    f"ABORTADO: Processo '{proc_name}' (PID {pid}) não está na whitelist de segurança. Não será encerrado.")
                return False

            logger.info(f"Tentando encerrar processo seguro: {proc_name}")
            import os
            import signal
            try:
                os.kill(pid, signal.SIGTERM)
                import time
                time.sleep(1)  # Espera morrer
                if SystemValidator.is_port_free(port):
                    return True
                # Force kill if needed?
                os.kill(pid, signal.SIGKILL)
                return True
            except PermissionError:
                logger.error(f"Sem permissão para matar PID {pid}.")
                return False
            except Exception as e:
                logger.error(f"Erro ao matar PID {pid}: {e}")
                return False

        return False

    @staticmethod
    def find_free_port(start_port=8080, max_port=8090, host="127.0.0.1"):
        """
        Busca a próxima porta livre em um intervalo.

        Args:
            start_port (int): Porta inicial.
            max_port (int): Porta limite.

        Returns:
            int: Porta livre encontrada ou None.
        """
        for port in range(start_port, max_port + 1):
            if SystemValidator.is_port_free(port, host):
                return port
        return None
