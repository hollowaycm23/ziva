"""
Search Connector - Interface para busca externa
Conecta com SearxNG (Web) e Kiwix (Offline Knowledge)
"""

import logging
import requests
import json
import threading
import time
from typing import List, Dict, Optional
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SearchConnector")


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str  # 'web', 'wikipedia', etc.


class SearchConnector:
    """
    Conector unificado para ferramentas de busca externa
    """

    def __init__(self, searxng_url: str = "http://localhost:8082",
                 kiwix_url: str = "http://localhost:8081"):
        self.searxng_url = searxng_url
        self.kiwix_url = kiwix_url
        self._searxng_ok = None
        self._kiwix_ok = None
        self._last_check = 0.0
        self._check_ttl = 30.0

    def _check_availability(self, force=False):
        """Verifica quais serviços estão online (lazy com TTL)"""
        now = time.time()
        if not force and (now - self._last_check) < self._check_ttl:
            return
        self._last_check = now

        try:
            requests.get(self.searxng_url, timeout=2)
            self._searxng_ok = True
        except Exception:
            if self._searxng_ok is not False:
                logger.warning(f"SearxNG offline em {self.searxng_url}")
            self._searxng_ok = False

        try:
            requests.get(self.kiwix_url, timeout=2)
            self._kiwix_ok = True
        except Exception:
            if self._kiwix_ok is not False:
                logger.warning(f"Kiwix offline em {self.kiwix_url}")
            self._kiwix_ok = False

    @property
    def searxng_ok(self):
        self._check_availability()
        return self._searxng_ok or False

    @property
    def kiwix_ok(self):
        self._check_availability()
        return self._kiwix_ok or False

    def search_web(self, query: str, limit: int = 5) -> List[SearchResult]:
        """
        Busca na web via SearxNG (HTML Scraping para evitar 403)
        """
        results = []
        if not self.searxng_ok:
            logger.warning("SearxNG indisponível. Falha na busca web.")
            return []

        try:
            from core.tools.searxng import SearXNGClient
            client = SearXNGClient(base_url=self.searxng_url)
            searx_results = client.search(query, num_results=limit)
            
            for item in searx_results:
                results.append(SearchResult(
                    title=item.get('title', ''),
                    url=item.get('url', ''),
                    snippet=item.get('snippet', ''),
                    source='searxng'
                ))

        except Exception as e:
            logger.error(f"Erro na busca web (Scraping): {e}")

        return results

    def search_knowledge(self, query: str,
                         limit: int = 3) -> List[SearchResult]:
        """
        Busca conhecimento offline (Kiwix) ou Wikipedia via SearxNG
        """
        results = []

        # Tenta Kiwix primeiro (Offline priority)
        if self.kiwix_ok:
            # Implementação básica do Kiwix via SearXNGClient se suportado ou direto
            pass

        # Fallback para SearxNG com !wiki (Usando Scraping)
        if self.searxng_ok:
            try:
                from core.tools.searxng import SearXNGClient
                client = SearXNGClient(base_url=self.searxng_url)
                # Adicionar operador !wiki na query
                searx_results = client.search(f"!wiki {query}", num_results=limit)
                
                for item in searx_results:
                    results.append(SearchResult(
                        title=item.get('title', ''),
                        url=item.get('url', ''),
                        snippet=item.get('snippet', ''),
                        source='wikipedia'
                    ))
            except Exception as e:
                logger.error(f"Erro na busca wiki (Scraping): {e}")

        return results

    def close(self):
        pass

    def robust_search(self, query: str) -> Dict[str, List[SearchResult]]:
        """
        Realiza busca combinada (Web + Knowledge)
        """
        return {
            'web': self.search_web(query),
            'knowledge': self.search_knowledge(query)
        }


# Singleton
_connector = None
_connector_lock = threading.Lock()


def get_search_connector() -> SearchConnector:
    global _connector
    if _connector is None:
        with _connector_lock:
            if _connector is None:
                _connector = SearchConnector()
    return _connector


if __name__ == "__main__":
    print("🔍 Testando Search Connector...")
    connector = SearchConnector()

    if connector.searxng_ok:
        print("✅ SearxNG Online")
        res = connector.search_web("Python async patterns")
        print(f"   Resultados Web: {len(res)}")
        for r in res[:2]:
            print(f"   - {r.title}: {r.snippet[:100]}...")
    else:
        print("❌ SearxNG Offline")

    print("\n")
