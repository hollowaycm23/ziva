import subprocess
import logging
import shutil
import os

logger = logging.getLogger("LocalExecutor")


class LocalExecutor:
    """
    Gerencia execução de comandos locais mantendo interface compatível com RemoteExecutor.
    """

    def __init__(self):
        """
        Inicializa o executor local.
        """
        self.hostname = "localhost"

    def run_command(self, command, timeout=30, cwd=None):
        """
        Executa um comando localmente via subprocess.
        
        Args:
            command (str): Comando a ser executado.
            timeout (int): Timeout em segundos.
            cwd (str, optional): Diretório de trabalho.

        Returns:
            dict: {success, stdout, stderr, exit_code}
        """
        try:
            logger.debug(f"Executando local: {command}")
            
            # Usamos shell=True para compatibilidade com os comandos complexos (pipes, etc)
            # que geralmente são enviados para o RemoteExecutor
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd
            )

            success = (result.returncode == 0)
            if not success:
                logger.warning(
                    f"Comando local falhou (Exit {result.returncode}): {result.stderr.strip()}"
                )

            return {
                "success": success,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "exit_code": result.returncode
            }

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout ao executar comando local: {command}")
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            logger.error(f"Erro na execução local: {e}")
            return {"success": False, "error": str(e)}

    def check_connection(self):
        """
        Verifica se o ambiente local está funcional (sempre True para local).
        """
        return True
