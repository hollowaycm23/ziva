import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta  # New import
import inspect
import importlib.util  # For dynamic loading

logger = logging.getLogger("ToolRegistry")

REGISTRY_FILE = Path("/home/holloway/ziva/data/tool_registry.json")


class ToolRegistry:
    """
    Gerencia o registro, versionamento e metadados de ferramentas dinâmicas.
    """

    def __init__(
        self,
        max_total_tools: int = 100,
        max_versions_per_tool: int = 5,
        min_time_between_creations_seconds: int = 60  # 1 minute
    ):
        self.max_total_tools = max_total_tools
        self.max_versions_per_tool = max_versions_per_tool
        # Reduced from 60 for better responsiveness
        self.min_time_between_creations_seconds = 1
        self.tools = self._load_registry()
        self.last_registered_tool_timestamp = datetime.min  # Allow immediate creation
        self.load_extensions()  # Auto-load extensions

    def load_extensions(
            self, extensions_path="/home/holloway/ziva/extensions"):
        """Scans and registers tools from the extensions directory."""
        path = Path(extensions_path)
        if not path.exists():
            return

        logger.info(f"Scanning extensions in {path}...")
        for file_path in path.glob("*.py"):
            try:
                module_name = file_path.stem
                spec = importlib.util.spec_from_file_location(
                    module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                for name, obj in inspect.getmembers(module):
                    if inspect.isfunction(obj) and getattr(
                            obj, "_is_ziva_tool", False):
                        # Infer schema if missing (simplified)
                        # Ideally ziva_tool decorator should store schema in metadata
                        # For now, we register with basic checks

                        # Extract source code
                        try:
                            source = inspect.getsource(obj)
                            # Remove decorators to avoid NameError in isolated
                            # runtime
                            source_lines = source.split('\n')
                            filtered_lines = [
                                line for line in source_lines
                                if not line.strip().startswith('@ziva_tool') and
                                not line.strip().startswith('@tool')
                            ]
                            source = '\n'.join(filtered_lines)
                        except BaseException:
                            source = "# Source not available"

                        # Extract schema from signature
                        try:
                            sig = inspect.signature(obj)
                            input_schema = {
                                "type": "object",
                                "properties": {},
                                "required": []
                            }
                            for param_name, param in sig.parameters.items():
                                param_info = {
                                    "type": "string"}  # Default to string
                                if param.default != inspect.Parameter.empty:
                                    param_info["default"] = param.default
                                else:
                                    input_schema["required"].append(param_name)
                                input_schema["properties"][param_name] = param_info
                        except Exception as e:
                            logger.warning(
                                f"Failed to infer schema for {name}: {e}")
                            input_schema = {}

                        # Register tool (forced update for extensions)
                        # We use version 1.0.0 for static extensions
                        self.register_tool(
                            name=name,
                            code=source,
                            description=obj.__doc__ or "No description",
                            input_schema=input_schema,
                            output_schema={},
                            version="1.0.0",
                            author="Extension",
                            overwrite=True  # Always update extension code
                        )
            except Exception as e:
                logger.error(f"Failed to load extension {file_path}: {e}")

    def _load_registry(self) -> Dict[str, Any]:  # Modified signature
        """Carrega o registro de ferramentas do arquivo."""
        if REGISTRY_FILE.exists():
            try:
                with open(REGISTRY_FILE, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                logger.error(
                    f"Erro ao decodificar JSON do registro de ferramentas: {e}")
                return {}
            except Exception as e:
                logger.error(f"Erro ao carregar registro de ferramentas: {e}")
                return {}
        return {}

    def _save_registry(self):
        """Salva o registro de ferramentas no arquivo."""
        try:
            REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(REGISTRY_FILE, 'w') as f:
                json.dump(self.tools, f, indent=4)
        except Exception as e:
            logger.error(f"Erro ao salvar registro de ferramentas: {e}")

    def register_tool(
        self,
        name: str,
        code: str,
        description: str,
        input_schema: Dict[str, Any],
        output_schema: Dict[str, Any],
        version: str = "1.0.0",
        author: str = "LLM",
        overwrite: bool = False
    ) -> bool:
        """
        Registra ou atualiza uma ferramenta.

        Args:
            name: Nome único da ferramenta.
            code: Código Python da ferramenta.
            description: Descrição da ferramenta.
            input_schema: Esquema JSON para os inputs da ferramenta.
            output_schema: Esquema JSON para os outputs da ferramenta.
            version: Versão da ferramenta.
            author: Autor da ferramenta.

        Returns:
            True se a ferramenta foi registrada/atualizada com sucesso, False caso contrário.
        """
        # Enforce total tool limit
        if len(self.tools) >= self.max_total_tools and name not in self.tools:
            logger.warning(f"Limite máximo de {self.max_total_tools} ferramentas atingido. Ferramenta '{name}' não registrada.")
            return False

        # Enforce time limit between creations (only for new tool names)
        if name not in self.tools:
            time_since_last_creation = datetime.now() - self.last_registered_tool_timestamp
            if time_since_last_creation < timedelta(
                    seconds=self.min_time_between_creations_seconds):
                logger.warning(f"Tentativa de criar nova ferramenta '{name}' muito rápido. Mínimo de {self.min_time_between_creations_seconds}s entre criações.")
                return False

        if name not in self.tools:
            self.tools[name] = []

        # Check for max versions per tool
        if len(self.tools[name]) >= self.max_versions_per_tool:
            # If version exists in the limited list, we still want to return
            # True
            pass

        # Check if version already exists
        for i, tool_entry in enumerate(self.tools[name]):
            if tool_entry["version"] == version:
                if overwrite:
                    logger.info(
                        f"Atualizando versão {version} da ferramenta '{name}' (overwrite=True).")
                    self.tools[name][i] = {
                        "version": version,
                        "timestamp": datetime.now().isoformat(),
                        "author": author,
                        "code": code,
                        "description": description,
                        "input_schema": input_schema,
                        "output_schema": output_schema,
                        "usage_history": tool_entry.get("usage_history", [])
                    }
                    self._save_registry()
                    return True
                else:
                    logger.info(
                        f"Versão {version} da ferramenta '{name}' já existe. Retornando sucesso (idempotente).")
                    return True

        # Adiciona a nova versão
        tool_entry = {
            "version": version,
            "timestamp": datetime.now().isoformat(),  # Use actual datetime
            "author": author,
            "code": code,
            "description": description,
            "input_schema": input_schema,
            "output_schema": output_schema,
            "usage_history": []
        }
        self.tools[name].append(tool_entry)
        self._save_registry()

        # Update unconditionally on successful registration
        self.last_registered_tool_timestamp = datetime.now()

        logger.info(
            f"Ferramenta '{name}' (v{version}) registrada com sucesso.")
        return True

    def get_tool(self, name: str,
                 version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Recupera a ferramenta mais recente ou uma versão específica.

        Args:
            name: Nome da ferramenta.
            version: Versão específica da ferramenta. Se None, retorna a mais recente.

        Returns:
            Dicionário com os detalhes da ferramenta, ou None se não encontrada.
        """
        if name not in self.tools:
            return None

        versions = self.tools[name]
        if version:
            for tool_entry in versions:
                if tool_entry["version"] == version:
                    return tool_entry
            return None  # Versão específica não encontrada
        else:
            # Retorna a mais recente (última adicionada)
            return versions[-1] if versions else None

    def record_usage(self, name: str, version: str, timestamp: str,
                     inputs: Dict[str, Any], outputs: Dict[str, Any]):
        """
        Registra o uso de uma ferramenta.
        """
        tool_entry = self.get_tool(name, version)
        if tool_entry:
            tool_entry["usage_history"].append({
                "timestamp": timestamp,
                "inputs": inputs,
                "outputs": outputs
            })
            self._save_registry()
            logger.debug(
                f"Uso da ferramenta '{name}' (v{version}) registrado.")
        else:
            logger.warning(
                f"Tentativa de registrar uso de ferramenta desconhecida: '{name}' (v{version})")

    def list_tools(self) -> Dict[str, Any]:
        """Lista todas as ferramentas e suas versões."""
        return self.tools


if __name__ == "__main__":
    # Limpa o registro para um teste limpo
    if REGISTRY_FILE.exists():
        REGISTRY_FILE.unlink()

    registry = ToolRegistry(
        max_total_tools=100,
        max_versions_per_tool=5,
        min_time_between_creations_seconds=0)  # Reset limits for development

    # Registrar ferramentas
    print("Registrando ferramentas...")
    registry.register_tool(
        name="get_current_date",
        code="""
def get_current_date():
    from datetime import datetime
    return {"date": datetime.now().isoformat()}
""",
        description="Obtém a data e hora atuais.",
        input_schema={},
        output_schema={"date": "string"}
    )

    registry.register_tool(
        name="add_numbers",
        code="""
def add_numbers(a: int, b: int):
    return {"sum": a + b}
""",
        description="Soma dois números.",
        input_schema={"a": "integer", "b": "integer"},
        output_schema={"sum": "integer"},
        version="1.0.0"
    )

    # Registrar nova versão
    registry.register_tool(
        name="add_numbers",
        code="""
def add_numbers(a: int, b: int):
    return {"result": a + b, "type": "integer"}
""",
        description="Soma dois números (nova versão).",
        input_schema={"a": "integer", "b": "integer"},
        output_schema={"result": "integer", "type": "string"},
        version="1.0.1"
    )

    # Listar ferramentas
    print("\nFerramentas registradas:")
    for name, versions in registry.list_tools().items():
        print(f"- {name}: {len(versions)} versões")
        for v in versions:
            print(f"  - v{v['version']} ({v['timestamp']})")

    # Obter ferramenta mais recente
    date_tool = registry.get_tool("get_current_date")
    if date_tool:
        print(f"\nFerramenta 'get_current_date' (mais recente): v{date_tool['version']}")

    # Obter versão específica
    add_tool_v1_0_0 = registry.get_tool("add_numbers", version="1.0.0")
    if add_tool_v1_0_0:
        print(f"Ferramenta 'add_numbers' (v1.0.0): {add_tool_v1_0_0['description']}")

    # Registrar uso (exemplo)
    if date_tool:
        registry.record_usage(
            name="get_current_date",
            version=date_tool["version"],
            timestamp="2026-01-01T10:00:00",
            inputs={},
            outputs={"date": "2026-01-01T10:00:00"}
        )
        print("\nUso de 'get_current_date' registrado.")

    updated_date_tool = registry.get_tool("get_current_date")
    print(f"Histórico de uso de 'get_current_date': {updated_date_tool['usage_history']}")

    print("\nTeste do ToolRegistry concluído.")
