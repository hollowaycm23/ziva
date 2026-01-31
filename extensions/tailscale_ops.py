from agent.tools import ziva_tool
from core.tailscale import TailscaleManager


@ziva_tool
def tailscale_control(action: str) -> str:
    """
    Gerencia a rede Tailscale do nó.

    Args:
        action (str): 'status' para ver rede, 'login_url' para obter link de auth.

    Returns:
        str: Status ou URL formatada.
    """
    if action == "status":
        status = TailscaleManager.get_status()
        state = status.get("BackendState", "Unknown")
        if state == "Running":
            return f"Tailscale Conectado. IP: {
                status.get(
                    'Self', {}).get('TailscaleIPs')}"
        return f"Tailscale Estado: {state}"

    elif action == "login_url":
        url = TailscaleManager.get_login_url()
        if url:
            return f"Por favor, autentique em: {url}"
        return "Erro ao obter URL ou já autenticado."

    return "Ação inválida. Use 'status' ou 'login_url'."
