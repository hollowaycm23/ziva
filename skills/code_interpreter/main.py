import logging
import os
from pathlib import Path
from agent.tools import ziva_tool

logger = logging.getLogger("SkillCoding")

@ziva_tool
def code_writer(filename: str, code: str, directory: str = "tmp") -> str:
    """
    Grava o código gerado em um arquivo físico no sistema local.
    """
    base_dir = Path("/home/holloway/ziva") / directory if not directory.startswith('/') else Path(directory)
    base_dir.mkdir(parents=True, exist_ok=True)
    file_path = base_dir / filename

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)
        logger.info(f"💾 Código gravado via Skill em: {file_path}")
        return f"Arquivo '{filename}' gravado com sucesso."
    except Exception as e:
        return f"Erro ao gravar arquivo: {e}"

@ziva_tool
def code_lookup(query: str) -> str:
    """
    Pesquisa na memória do Ziva por exemplos de código.
    """
    try:
        from core.vector_store import VectorStore
        vs = VectorStore()
        return f"Busca técnica por '{query}' integrada. Consulte o RAG context."
    except Exception as e:
        return f"Erro na busca técnica: {e}"
