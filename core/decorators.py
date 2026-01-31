"""
Decorators úteis para error handling e retry logic
"""

from functools import wraps
import time
import logging
from core.exceptions import RetriableError

logger = logging.getLogger(__name__)


def retry_on_retriable(max_attempts: int = 3,
                       delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator para retry automático em erros RetriableError.

    Args:
        max_attempts: Número máximo de tentativas (default: 3)
        delay: Delay inicial entre retries em segundos (default: 1.0)
        backoff: Multiplicador para exponential backoff (default: 2.0)

    Exemplo:
        @retry_on_retriable(max_attempts=3, delay=1.0)
        def search_qdrant(query):
            # Se falhar com RetriableError, tenta 3x
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)

                except RetriableError as e:
                    if attempt == max_attempts - 1:
                        # Última tentativa, re-raise
                        logger.error(
                            f"❌ {func.__name__} failed after "
                            f"{max_attempts} attempts: {e}")
                        raise

                    # Log e aguardar antes do retry
                    logger.warning(
                        f"⚠️ {
                            func.__name__} attempt {
                            attempt + 1}/{max_attempts} failed: {e}. "
                        f"Retrying in {current_delay:.1f}s..."
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff  # Exponential backoff

            return None  # Nunca deve chegar aqui

        return wrapper
    return decorator


def log_exceptions(logger_instance: logging.Logger = None):
    """
    Decorator para logar exceções com stacktrace completo.

    Útil para debugging - garante que nenhum erro passe silencioso.

    Exemplo:
        @log_exceptions()
        def critical_function():
            # Qualquer exception será logada com traceback
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log = logger_instance or logger
                log.exception(f"Exception in {func.__name__}: {e}")
                raise  # Re-raise após logar
        return wrapper
    return decorator
