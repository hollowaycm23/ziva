import logging
import subprocess
from pathlib import Path
from agent.tools import ziva_tool

logger = logging.getLogger("ExecutionTools")


@ziva_tool
def code_runner(filename: str = None, directory: str = "tmp",
                args: str = "", script_path: str = None) -> str:
    """
    Executa um script Python previamente criado.
    
    DELEGATED TO: Go Runtime (Body).

    Args:
        filename (str): Nome do arquivo.
        directory (str): Diretório.
        script_path (str): Caminho alternativo.
        args (str): Argumentos.

    Returns:
        str: Saída da execução.
    """
    from core.runtime_client import runtime
    import shlex

    # Resolve Path Logic
    file_path = None
    cwd = "/home/holloway/ziva"
    
    if script_path:
        f = Path(script_path)
        # Normalize relative logic similar to original
        if str(script_path).startswith('/tmp') or str(script_path).startswith('/scripts'):
             file_path = Path("/home/holloway/ziva") / script_path.lstrip('/')
        elif not f.is_absolute():
             file_path = Path("/home/holloway/ziva") / script_path
        else:
             file_path = f
        cwd = str(file_path.parent)
    elif filename:
        if directory.startswith('/'):
            base_dir = Path(directory)
        else:
            base_dir = Path("/home/holloway/ziva") / directory
        file_path = base_dir / filename
        cwd = str(base_dir)
    else:
        return "Erro: Forneça 'filename' ou 'script_path'."
        
    cmd_args = [str(file_path)]
    if args:
        cmd_args.extend(shlex.split(args))
        
    result = runtime.execute_tool("execute_shell", {
        "command": "python3",
        "args": cmd_args,
        "cwd": cwd
    })
    
    if result["status"] == "success":
        logger.info(f"Go Runtime executed python: {file_path}")
        return f"=== SAÍDA (Go Runtime) ===\n{result['result']}"
    else:
        logger.error(f"Go Runtime error executing python {file_path}: {result.get('error')}")
        return f"Erro ao executar script (Go Runtime): {result.get('error')}"


@ziva_tool
def bash_runner(filename: str, directory: str = "tmp", args: str = "") -> str:
    """
    Executa um script Bash/Shell previamente criado.
    
    DELEGATED TO: Go Runtime (Body).

    Args:
        filename (str): Nome do arquivo a executar (ex: 'install.sh').
        directory (str): Caminho relativo ou absoluto.
        args (str): Argumentos opcionais.

    Returns:
        str: Saída da execução do script.
    """
    from core.runtime_client import runtime
    import shlex

    # Resolve Path Logic (Client side for now)
    if directory.startswith('/'):
        base_dir = Path(directory)
    else:
        base_dir = Path("/home/holloway/ziva") / directory
    
    file_path = base_dir / filename
    
    # We call "bash" explicitly
    cmd_args = [str(file_path)]
    if args:
        cmd_args.extend(shlex.split(args))
        
    result = runtime.execute_tool("execute_shell", {
        "command": "bash",
        "args": cmd_args,
        "cwd": str(base_dir)
    })
    
    if result["status"] == "success":
        logger.info(f"Go Runtime executed bash: {filename}")
        return f"=== SAÍDA (Go Runtime) ===\n{result['result']}"
    else:
        logger.error(f"Go Runtime error executing bash {filename}: {result.get('error')}")
        return f"Erro ao executar script (Go Runtime): {result.get('error')}"


@ziva_tool
def local_shell(command: str) -> str:
    """
    Executa um comando shell LOCALMENTE no nó atual (Node07/Ziva) via Go Runtime.
    Ferramenta PADRÃO para comandos de sistema (date, ls, df, cat, grep, etc).
    
    SECURITY: Delegated to Go Runtime. Only whitelisted commands allowed.
    NO PIPES (|) or CHAINING (&&, ;) allowed.

    Args:
        command (str): Comando bash a ser executado.

    Returns:
        str: Saída do comando (stdout + stderr).
    """
    from core.runtime_client import runtime
    import shlex

    if not command or len(command) > 500:
        return "Erro: Comando muito longo ou vazio."

    try:
        # Split command into parts safely
        parts = shlex.split(command)
        if not parts:
            return "Erro: Comando vazio."
            
        cmd_name = parts[0]
        cmd_args = parts[1:] if len(parts) > 1 else []
        
        result = runtime.execute_tool("execute_shell", {
            "command": cmd_name,
            "args": cmd_args,
            "cwd": "/home/holloway/ziva"
        })
        
        if result["status"] == "success":
            return result["result"]
        else:
            return f"Erro (Go Runtime): {result.get('error')}"
            
    except Exception as e:
        return f"Erro local ao processar comando: {e}"
