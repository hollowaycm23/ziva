from agent.tools import ziva_tool
from network.remote import RemoteExecutor


@ziva_tool
def remote_shell(node: str, command: str) -> str:
    """
    Executa um comando shell em um nó remoto via SSH (Tailscale).
    NÃO USE para comandos no próprio nó (Ziva/Node07). Use local_shell para isso.

    Args:
        node (str): Nome do host remoto (ex: 'node08', 'gabrielle').
        command (str): Comando a ser executado (ex: 'uptime', 'df -h').

    Returns:
        str: Saída do comando (stdout) ou erro.
    """
    if not command or len(command) > 200:
        return "Erro: Comando vazio ou muito longo (max 200 chars)."

    args_node = node.lower()

    # Resolver nome amigável para ID real (ex: 'Gabrielle' -> 'falcon')
    from core.registry import NodeRegistry
    registry = NodeRegistry()

    target_host = node
    # Tenta encontrar no registro pelo nome ou ID
    for nid, data in registry.nodes.items():
        if data.get('name', '').lower() == args_node or nid == args_node:
            target_host = data.get('id', nid)
            break

    executor = RemoteExecutor(remote_host=target_host)

    # Check connection first
    # Poderíamos pular isso se performance for crítica
    if not executor.check_connection():
        return f"Erro: Nó {node} inacessível via SSH."

    result = executor.run_command(command)

    if result['success']:
        return f"Sucesso:\n{result['stdout']}"
    else:
        return f"Falha (Code {
            result['exit_code']}):\n{
            result['stderr'] or result['error']}"
