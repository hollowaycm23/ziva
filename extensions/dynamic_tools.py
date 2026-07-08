import logging
from core.dynamic_tools.validator import DynamicToolValidator
import core.dynamic_tools.registry as _registry_mod

logger = logging.getLogger("DynamicTools")


def create_tool(name: str, code: str, description: str) -> str:
    """
    Cria uma nova ferramenta Python que será validada, registrada e disponibilizada para uso futuro.
    A ferramenta deve ser uma função Python com assinatura 'def nome(input: dict) -> dict:' e um docstring.

    Args:
        name: Nome da ferramenta (usado para chamá-la depois, ex: 'converter_temperatura')
        code: Código Python completo da função (com docstring explicando parâmetros e retorno)
        description: Descrição curta do que a ferramenta faz (para o LLM saber quando usá-la)

    Returns:
        Mensagem de sucesso ou erro
    """
    validator = DynamicToolValidator()
    result = validator.validate(code)
    if not result:
        return f"Erro de validação: {result.reason}"

    try:
        registry = _get_registry()
        version = registry.register(name, code, description)
    except RuntimeError as e:
        return f"Erro: {e}"

    return (
        f"Ferramenta '{name}' criada com sucesso (v{version})! "
        f"Ela já está disponível para uso em conversas futuras. "
        f"Descrição: {description}"
    )


create_tool._is_ziva_tool = True


def _get_registry():
    return _registry_mod.get_registry()


def list_dynamic_tools() -> str:
    """
    Lista todas as ferramentas criadas dinamicamente pelo usuário.
    Retorna nome, descrição, versão, taxa de sucesso e número de usos de cada ferramenta.

    Returns:
        Lista formatada de ferramentas dinâmicas
    """
    registry = _get_registry()
    tools = registry.list_tools()
    if not tools:
        return "Nenhuma ferramenta dinâmica registrada ainda."

    lines = ["Ferramentas Dinâmicas disponíveis:"]
    for name, meta in sorted(tools.items()):
        success_pct = round(meta.success_rate * 100)
        lines.append(
            f"  - {name} (v{meta.version}): {meta.description} "
            f"[usos: {meta.usage_count}, sucesso: {success_pct}%]"
        )
    return "\n".join(lines)


def delete_tool(name: str) -> str:
    """
    Remove uma ferramenta dinâmica pelo nome.

    Args:
        name: Nome da ferramenta a ser removida

    Returns:
        Mensagem de sucesso ou erro
    """
    registry = _get_registry()
    if registry.delete(name):
        return f"Ferramenta '{name}' removida com sucesso."
    return f"Ferramenta '{name}' não encontrada."


list_dynamic_tools._is_ziva_tool = True
delete_tool._is_ziva_tool = True
