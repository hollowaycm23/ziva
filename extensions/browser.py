import os
import logging
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from agent.tools import ziva_tool

logger = logging.getLogger("BrowserTools")

def _get_browser(playwright):
    """Retorna uma instância de browser (remoto ou local)."""
    remote_url = os.getenv("PLAYWRIGHT_WS_ENDPOINT")
    if remote_url:
        try:
            return playwright.chromium.connect_over_cdp(remote_url)
        except Exception as e:
            logger.warning(f"Falha ao conectar ao browser remoto: {e}. Usando local.")
    return playwright.chromium.launch(headless=True)


@ziva_tool
def browser_navigate(url: str, wait_seconds: int = 3) -> str:
    """
    Navega para uma URL e retorna o título da página.

    Args:
        url (str): URL completa para navegar (ex: 'https://example.com')
        wait_seconds (int): Segundos para aguardar carregamento (default 3)

    Returns:
        str: Título da página e status
    """
    try:
        with sync_playwright() as p:
            browser = _get_browser(p)
            page = browser.new_page()
            page.goto(url, timeout=30000)
            page.wait_for_timeout(wait_seconds * 1000)

            title = page.title()
            browser.close()

            return f"✅ Navegação bem-sucedida\nTítulo: {title}\nURL: {url}"
    except PlaywrightTimeout:
        return f"❌ Timeout ao acessar {url}"
    except Exception as e:
        logger.error(f"Erro no browser_navigate: {e}")
        return f"❌ Erro: {e}"


@ziva_tool
def browser_screenshot(
        url: str,
        filename: str = "screenshot.png",
        directory: str = "tmp") -> str:
    """
    Captura screenshot de uma página web.

    Args:
        url (str): URL para capturar
        filename (str): Nome do arquivo (default 'screenshot.png')
        directory (str): Diretório relativo a /home/holloway/ziva (default 'tmp')

    Returns:
        str: Caminho do arquivo salvo
    """
    try:
        if directory.startswith('/'):
            save_dir = Path(directory)
        else:
            save_dir = Path("/home/holloway/ziva") / directory

        save_dir.mkdir(parents=True, exist_ok=True)
        filepath = save_dir / filename

        with sync_playwright() as p:
            browser = _get_browser(p)
            page = browser.new_page()
            page.goto(url, timeout=30000)
            page.wait_for_load_state("networkidle")
            page.screenshot(path=str(filepath), full_page=True)
            browser.close()

        return f"✅ Screenshot salvo em: {filepath}"
    except Exception as e:
        logger.error(f"Erro no browser_screenshot: {e}")
        return f"❌ Erro: {e}"


@ziva_tool
def browser_extract(url: str, selector: str = "body",
                    wait_for_selector: str = None) -> str:
    """
    Extrai texto de páginas dinâmicas (JavaScript/SPA) usando seletor CSS.
    IDEAL para sites que carregam dados via JavaScript (React, Vue, etc).

    Args:
        url (str): URL para extrair dados
        selector (str): Seletor CSS do elemento (default 'body')
        wait_for_selector (str): Seletor para aguardar antes de extrair (opcional)

    Returns:
        str: Texto extraído (limitado a 2000 caracteres)
    """
    try:
        with sync_playwright() as p:
            browser = _get_browser(p)
            page = browser.new_page()
            page.goto(url, timeout=30000)

            # Aguardar carregamento completo do JavaScript
            page.wait_for_load_state("networkidle")

            # Se especificado, aguardar elemento específico aparecer
            if wait_for_selector:
                page.wait_for_selector(wait_for_selector, timeout=10000)

            element = page.locator(selector).first
            text = element.inner_text()
            browser.close()

            # Limitar tamanho da resposta
            if len(text) > 2000:
                text = text[:2000] + "... (truncado)"

            return f"✅ Texto extraído de {selector}:\n\n{text}"
    except Exception as e:
        logger.error(f"Erro no browser_extract: {e}")
        return f"❌ Erro: {e}"


@ziva_tool
def browser_execute_js(url: str, javascript_code: str) -> str:
    """
    Executa código JavaScript em uma página e retorna o resultado.
    Útil para extrair dados complexos ou interagir com APIs JavaScript.

    Args:
        url (str): URL da página
        javascript_code (str): Código JavaScript a executar (deve retornar valor)

    Returns:
        str: Resultado da execução do JavaScript
    """
    try:
        with sync_playwright() as p:
            browser = _get_browser(p)
            page = browser.new_page()
            page.goto(url, timeout=30000)
            page.wait_for_load_state("networkidle")

            result = page.evaluate(javascript_code)
            browser.close()

            return f"✅ JavaScript executado:\n{str(result)[:1000]}"
    except Exception as e:
        logger.error(f"Erro no browser_execute_js: {e}")
        return f"❌ Erro: {e}"
