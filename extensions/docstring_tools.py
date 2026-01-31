import logging
import ast
import re
from pathlib import Path
from typing import List, Dict
from agent.tools import ziva_tool
from core.llm import LLMService

logger = logging.getLogger("DocstringTools")


@ziva_tool
def standardize_docstrings(file_path: str, auto_fix: bool = True) -> str:
    """
    Padroniza docstrings de um arquivo Python para Google Style.

    Analisa funções e classes, detecta docstrings ausentes ou mal formatadas,
    e usa o LLM para gerar documentação padronizada automaticamente.

    Args:
        file_path (str): Caminho do arquivo Python a padronizar
        auto_fix (bool, optional): Se True, atualiza o arquivo automaticamente. Defaults to True.

    Returns:
        str: Relatório de padronização com estatísticas

    Examples:
        >>> standardize_docstrings("/home/holloway/ziva/core/llm.py")
        "✅ Padronizadas: 5 funções, 2 classes"
    """
    try:
        llm = LLMService()
        path = Path(file_path)

        if not path.exists():
            return f"❌ Arquivo não encontrado: {file_path}"

        # Ler código
        code = path.read_text(encoding='utf-8')
        tree = ast.parse(code)

        functions_fixed = 0
        classes_fixed = 0
        issues = []

        # Analisar funções e classes
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                docstring = ast.get_docstring(node)

                # Verificar se precisa padronizar
                if not docstring or not is_google_style(docstring):
                    # Gerar docstring padronizada
                    new_docstring = generate_google_docstring(node, code, llm)

                    if new_docstring and auto_fix:
                        # Atualizar código
                        code = update_docstring_in_code(
                            code, node, new_docstring)

                        if isinstance(node, ast.FunctionDef):
                            functions_fixed += 1
                        else:
                            classes_fixed += 1
                    else:
                        issues.append(f"{node.name}: {type(node).__name__}")

        # Salvar arquivo atualizado
        if auto_fix and (functions_fixed > 0 or classes_fixed > 0):
            path.write_text(code, encoding='utf-8')
            logger.info(f"✅ Arquivo atualizado: {file_path}")

        return f"""✅ Padronização Completa:
- Funções corrigidas: {functions_fixed}
- Classes corrigidas: {classes_fixed}
- Pendentes: {len(issues)}
- Arquivo: {path.name}"""

    except Exception as e:
        logger.error(f"Erro ao padronizar {file_path}: {e}")
        return f"❌ Erro: {e}"


def is_google_style(docstring: str) -> bool:
    """
    Verifica se docstring segue o padrão Google Style.

    Args:
        docstring (str): Docstring a verificar

    Returns:
        bool: True se está no padrão, False caso contrário
    """
    if not docstring:
        return False

    # Verificar seções obrigatórias
    has_args = "Args:" in docstring or "Parameters:" in docstring
    has_returns = "Returns:" in docstring

    # Docstrings simples (sem parâmetros) são válidas
    if not has_args and not has_returns:
        return len(docstring.strip()) > 10  # Pelo menos uma descrição

    return True


def generate_google_docstring(node, code: str, llm: LLMService) -> str:
    """
    Gera docstring Google Style usando LLM.

    Args:
        node: Nó AST (FunctionDef ou ClassDef)
        code (str): Código fonte completo
        llm (LLMService): Serviço LLM para geração

    Returns:
        str: Docstring gerada no formato Google Style
    """
    # Extrair assinatura e corpo
    func_name = node.name

    # Extrair parâmetros
    params = []
    if isinstance(node, ast.FunctionDef):
        for arg in node.args.args:
            params.append(arg.arg)

    # Prompt para LLM
    prompt = f"""Gere uma docstring Google Style para esta função/classe Python:

Nome: {func_name}
Parâmetros: {
        ', '.join(params) if params else 'nenhum'}

Formato obrigatório:
\"\"\"
Breve descrição em uma linha.

Descrição detalhada (opcional).

Args:
    param1 (tipo): Descrição
    param2 (tipo): Descrição

Returns:
    tipo: Descrição do retorno

\"\"\"

Gere APENAS a docstring, sem código adicional:"""

    response = llm.completion(prompt, temperature=0.3, max_tokens=300)

    # Limpar resposta
    if response:
        # Remover marcadores de código se existirem
        response = response.replace('```python', '').replace('```', '').strip()
        return response

    return None


def update_docstring_in_code(code: str, node, new_docstring: str) -> str:
    """
    Atualiza docstring no código fonte.

    Args:
        code (str): Código fonte original
        node: Nó AST da função/classe
        new_docstring (str): Nova docstring a inserir

    Returns:
        str: Código atualizado
    """
    lines = code.split('\n')

    # Encontrar linha da definição
    def_line = node.lineno - 1

    # Inserir docstring após a definição
    indent = '    '  # 4 espaços
    docstring_lines = [
        f'{indent}"""',
        *[f'{indent}{line}' for line in new_docstring.strip().split('\n')],
        f'{indent}"""'
    ]

    # Inserir após a linha de definição
    lines[def_line + 1:def_line + 1] = docstring_lines

    return '\n'.join(lines)
