import logging
from pathlib import Path
from agent.tools import ziva_tool

logger = logging.getLogger("FileTools")


@ziva_tool
def file_reader(filepath: str) -> str:
    """
    Lê o conteúdo de um arquivo existente.
    
    DELEGATED TO: Go Runtime (Body) via JSON Protocol.

    Args:
        filepath (str): Caminho completo do arquivo.

    Returns:
        str: Conteúdo do arquivo ou mensagem de erro.
    """
    # Import inside function to avoid circular deps if any, though core should be fine
    from core.runtime_client import runtime
    
    # 1. Normalize path logic can stay here OR move to Go (Go has sandbox).
    # Ideally, we send the raw intention to Go and let it decide.
    # But for backward compatibility with Ziva's relative paths:
    path_str = filepath
    if not path_str.startswith('/'):
        path_str = str(Path("/home/holloway/ziva") / filepath)

    # 2. Call Go Runtime
    result = runtime.execute_tool("read_file", {"path": path_str})
    
    # 3. Handle Response
    if result["status"] == "success":
        logger.info(f"Go Runtime read file: {path_str}")
        return f"Conteúdo de {path_str}:\n\n{result['result']}"
    else:
        logger.error(f"Go Runtime error reading {path_str}: {result.get('error')}")
        return f"Erro ao ler arquivo (Go Runtime): {result.get('error')}"


@ziva_tool
def file_editor(filepath: str, content: str, mode: str = "overwrite") -> str:
    """
    Modifica ou cria um arquivo com novo conteúdo.
    
    DELEGATED TO: Go Runtime (Body).

    Args:
        filepath (str): Caminho completo.
        content (str): Conteúdo.
        mode (str): 'overwrite' (padrão) ou 'append'.

    Returns:
        str: Status da operação.
    """
    from core.runtime_client import runtime
    
    path_str = filepath
    if not path_str.startswith('/'):
        path_str = str(Path("/home/holloway/ziva") / filepath)

    # Validate mode (client-side pre-check, though server checks too strictly speaking server blindly accepts strings)
    if mode not in ["overwrite", "append", "create"]:
        return f"Erro: Modo '{mode}' inválido. Use 'overwrite', 'append' ou 'create' (create mapeia para overwrite no Go por enquanto)."

    # Go runtime "write_file" handles overwrite and append. "create" is essentially overwrite if not exists, but let's map it.
    go_mode = mode
    if mode == "create":
        go_mode = "overwrite"

    result = runtime.execute_tool("write_file", {
        "path": path_str,
        "content": content,
        "mode": go_mode
    })
    
    if result["status"] == "success":
        logger.info(f"Go Runtime wrote file: {path_str}")
        return f"Arquivo modificado via Go Runtime: {result['result']}"
    else:
        logger.error(f"Go Runtime error writing {path_str}: {result.get('error')}")
        return f"Erro ao modificar arquivo (Go Runtime): {result.get('error')}"


@ziva_tool
def file_deleter(filepath: str) -> str:
    """
    Remove um arquivo do sistema.

    Args:
        filepath (str): Caminho completo do arquivo (absoluto ou relativo a /home/holloway/ziva/).

    Returns:
        str: Status da operação.
    """
    # Permitir caminhos absolutos
    if filepath.startswith('/'):
        file_path = Path(filepath)
    else:
        file_path = Path("/home/holloway/ziva") / filepath

    if not file_path.exists():
        return f"Erro: Arquivo '{filepath}' não encontrado."

    try:
        file_path.unlink()
        logger.info(f"Arquivo removido: {file_path}")
        return f"Arquivo {file_path} removido com sucesso."
    except Exception as e:
        logger.error(f"Erro ao remover arquivo: {e}")
        return f"Falha ao remover '{filepath}': {e}"
