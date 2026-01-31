from agent.tools import ziva_tool
from core.tools.sherlock import SherlockClient
import logging

logger = logging.getLogger("SherlockTool")

# Instância global do cliente
_client = None


def _get_client():
    global _client
    if _client is None:
        _client = SherlockClient()
    return _client


@ziva_tool
def search_username(username: str):
    """
    Pesquisa por um nome de usuário em centenas de sites e redes sociais (OSINT).
    Útil para encontrar perfis digitais de uma pessoa ou verificar a existência de um handle.

    Args:
        username (str): O nome de usuário para pesquisar (ex: "johndoe123").

    Returns:
        dict: Lista de sites onde o usuário foi encontrado.
    """
    logger.info(f"Sherlock Tool invocada para: {username}")
    client = _get_client()
    return client.search(username)
