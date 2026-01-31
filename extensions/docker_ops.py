import logging
import shlex
from agent.tools import ziva_tool
import json

logger = logging.getLogger("DockerTools")

@ziva_tool
def run_docker_container(image: str, command: str, env: str = "{}", allow_network: bool = False) -> str:
    """
    Executa um comando dentro de um Container Docker EFÊMERO.
    
    DELEGATED TO: Go Runtime (Protocol Droids).
    SECURITY:
    - Network: Default NONE. Se allowed=True, usa bridge (com internet).
    - Storage: Read-Only root, Volume /workspace mapeado para /home/holloway/ziva/tmp.
    - Lifecycle: Container é destruído após execução (--rm).

    Args:
        image (str): Imagem Docker (ex: 'python:3.10-slim').
        command (str): Comando a executar (ex: 'python3 script.py').
        env (str): JSON string com variáveis de ambiente.
        allow_network (bool): Se True, permite acesso à internet (para pip install, etc).

    Returns:
        str: STDOUT + STDERR da execução.
    """
    from core.runtime_client import runtime

    try:
        env_dict = json.loads(env)
    except:
        return "Erro: 'env' deve ser um JSON válido."

    # Parse command safely
    args = shlex.split(command)
    
    result = runtime.execute_tool("run_container", {
        "image": image,
        "args": args,
        "env": env_dict,
        "allow_network": allow_network
    }, timeout=600)


    if result["status"] == "success":
        logger.info(f"Container '{image}' executed successfully.")
        return f"=== CONTAINER OUTPUT ===\n{result['result']}"
    else:
        err_msg = result.get('error', 'Unknown Error')
        res_out = result.get('result', '')
        logger.error(f"Container error: {err_msg}")
        return f"=== CONTAINER OUTPUT ===\nErro na execução do Container: {err_msg}\n{res_out}"
