import os
import sys
from unittest.mock import MagicMock, patch

# Adicionar raiz do projeto ao path
sys.path.append(os.getcwd())

def test_scraper_fallback():
    print("🧪 Testando fallback do Scraper...")
    from core.tools.scraper import PlaywrightScraper
    
    scraper = PlaywrightScraper()
    
    # Mock do playwright para não tentar abrir nada real durante o teste unitário básico
    with patch('core.tools.scraper.sync_playwright') as mock_playwright:
        mock_p = mock_playwright.return_value.__enter__.return_value
        
        # Simular que não há endpoint remoto
        os.environ.pop("PLAYWRIGHT_WS_ENDPOINT", None)
        scraper.scrape("https://example.com")
        
        # Deve ter chamado launch (local)
        mock_p.chromium.launch.assert_called()
        print("✅ Fallback local detectado corretamente na ausência de endpoint.")

def test_scraper_remote_connection():
    print("🧪 Testando tentativa de conexão remota...")
    from core.tools.scraper import PlaywrightScraper
    
    scraper = PlaywrightScraper()
    
    with patch('core.tools.scraper.sync_playwright') as mock_playwright:
        mock_p = mock_playwright.return_value.__enter__.return_value
        
        # Simular endpoint remoto
        os.environ["PLAYWRIGHT_WS_ENDPOINT"] = "ws://mock-browser:3000"
        scraper.scrape("https://example.com")
        
        # Deve ter chamado connect_over_cdp
        mock_p.chromium.connect_over_cdp.assert_called_with("ws://mock-browser:3000")
        print("✅ Tentativa de conexão remota detectada com endpoint configurado.")

if __name__ == "__main__":
    try:
        test_scraper_fallback()
        test_scraper_remote_connection()
        print("\n✨ Todos os testes de lógica de conexão passaram!")
    except Exception as e:
        print(f"\n❌ Falha nos testes: {e}")
        sys.exit(1)
