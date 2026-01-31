from langchain_core.tools import StructuredTool
from agent.tools import ToolManager
import logging

logger = logging.getLogger("ToolWrapper")


def get_langchain_tools(tool_manager: ToolManager) -> list[StructuredTool]:
    """
    Converte ferramentas do ToolManager (funções Python puras)
    para StructuredTools do LangChain, preservando docstrings e types.
    """
    lc_tools = []

    # Carregar ferramentas se ainda não estiverem carregadas
    if not tool_manager.loaded_tools:
        tool_manager.load_tools()

    for name, func in tool_manager.loaded_tools.items():
        try:
            # Criar StructuredTool a partir da função
            # O LangChain lê automaticamente type hints e docstrings para criar
            # o schema JSON
            tool = StructuredTool.from_function(
                func=func,
                name=name,
                description=func.__doc__ or f"Tool: {name}",
            )
            lc_tools.append(tool)
            logger.debug(f"Converted {name} to LangChain Tool")
        except Exception as e:
            logger.error(f"Failed to convert tool {name}: {e}")

    return lc_tools
