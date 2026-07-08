import importlib.util
import inspect
from pathlib import Path
import logging

logger = logging.getLogger("ZivaTools")


class ToolManager:
    """
    Gerenciador de ferramentas dinâmicas (Plugins).

    Carrega, valida e expõe funções Python como ferramentas utilizáveis
    pelo Agente Ziva. Suporta hot-reloading (teórico).
    """

    def __init__(self, extensions_path=None):
        """
        Inicializa o gerenciador.

        Args:
            extensions_path (str): Diretório onde estão os scripts .py das
                                   ferramentas. Defaults to ./extensions logic.
        """
        if extensions_path:
            self.extensions_path = Path(extensions_path)
        else:
            # Caminho relativo à raiz do projeto (assumindo agent/tools.py)
            self.extensions_path = Path(__file__).parent.parent / "extensions"
        
        logger.info(f"ToolManager Path: {self.extensions_path.resolve()}")
        self.loaded_tools = {}

    def load_tools(self):
        """
        Varre o diretório de extensões e o novo diretório de skills.
        """
        if not self.extensions_path.exists():
            logger.info(f"Path {self.extensions_path} does not exist, creating it.")
            self.extensions_path.mkdir(parents=True, exist_ok=True)
            
        # 1. Load Legacy Extensions
        logger.info(f"Scanning legacy extensions: {self.extensions_path}")
        for file_path in self.extensions_path.glob("*.py"):
            self._load_module(file_path)

        # 2. Load Modular Skills (Phase 1 Integration)
        skills_path = self.extensions_path.parent / "skills"
        if skills_path.exists():
            logger.info(f"Scanning modular skills: {skills_path}")
            for skill_dir in skills_path.iterdir():
                if skill_dir.is_dir():
                    main_py = skill_dir / "main.py"
                    if main_py.exists():
                        logger.info(f"Loading skill from {skill_dir.name}")
                        self._load_module(main_py)

    def _load_module(self, file_path):
        """
        Carrega um módulo específico e registra suas ferramentas.

        Args:
            file_path (Path): Caminho para o arquivo do módulo.
        """
        module_name = file_path.stem
        try:
            spec = importlib.util.spec_from_file_location(module_name,
                                                          file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Procura por funções com atributo 'is_tool' ou convenção similar
            for name, obj in inspect.getmembers(module):
                if inspect.isfunction(obj) and getattr(obj, "_is_ziva_tool",
                                                       False):
                    self.loaded_tools[name] = obj
                    logger.info(f"Ferramenta carregada: {name}")

        except Exception as e:
            logger.error(f"Erro ao carregar módulo {module_name}: {e}")

    def get_tool(self, name):
        """
        Recupera uma ferramenta carregada pelo nome.

        Args:
            name (str): Nome da função/ferramenta.

        Returns:
            callable: A função executável ou None se não encontrada.
        """
        return self.loaded_tools.get(name)

    def list_tools(self):
        """
        Lista os nomes de todas as ferramentas disponíveis.

        Returns:
            list[str]: Lista de identificadores de ferramentas.
        """
        return list(self.loaded_tools.keys())


# Decorator para facilitar criação
def ziva_tool(func):
    """
    Decorator para marcar funções como ferramentas do Ziva.

    Adiciona metadata necessário para discovery pelo ToolManager.
    """
    func._is_ziva_tool = True
    return func
