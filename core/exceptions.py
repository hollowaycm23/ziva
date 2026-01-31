"""
Custom Exception Hierarchy para Ziva

Substitui `except Exception:` genérico por exceções tipadas,
permitindo:
- Error handling específico por tipo
- Retry automático para erros transientes
- Debugging eficiente com stacktraces preservados
"""


class ZivaError(Exception):
    """Base class para todas exceções do Ziva"""
    pass


class RetriableError(ZivaError):
    """
    Erros transientes que podem ser resolvidos com retry.

    Exemplos:
    - Timeout de rede
    - Qdrant temporariamente indisponível
    - Rate limit da API
    """
    pass


class VectorStoreError(ZivaError):
    """Erros relacionados ao Qdrant/vector database"""
    pass


class EmbeddingError(ZivaError):
    """
    Erros na geração de embeddings.

    Exemplos:
    - Texto inválido/vazio
    - Modelo não carregado
    - CUDA out of memory
    """
    pass


class DatabaseError(ZivaError):
    """Erros do SQLite/database layer"""
    pass


class GraphExecutionError(ZivaError):
    """Erros durante execução do LangGraph"""
    pass


class LLMError(ZivaError):
    """Erros de comunicação com Ollama/LLM"""
    pass


class ValidationError(ZivaError):
    """Erros de validação de dados/entrada"""
    pass
