import requests
from typing import List, Dict, Any


class SearXNGClient:
    """
    Client for interacting with a local SearXNG instance.
    """

    def __init__(self, base_url: str = None):
        if base_url is None:
            import os
            # Default to docker hostname, fallback to localhost if env var not set
            base_url = os.getenv("SEARXNG_URL", "http://localhost:8082")
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64; rv:109.0) "
                           "Gecko/20100101 Firefox/115.0"),
            "X-Forwarded-For": "127.0.0.1",
            "X-Real-IP": "127.0.0.1"
        }

    def search(self, query: str, num_results: int = 5, **kwargs) -> List[Dict[str, Any]]:
        """
        Queries SearXNG and returns a list of results (HTML scraping).
        """
        import re
        
        # Use JSON format for reliable parsing
        params = {
            "q": query, "categories": "general",
            "language": "pt-BR", "format": "json",
            "safe_search": 0
        }
        params.update(kwargs)
        
        try:
            response = requests.get(
                f"{self.base_url}/search", params=params,
                headers=self.headers, timeout=10)
            
            # Debug: Check if we got JSON
            content_type = response.headers.get("Content-Type", "")
            if "application/json" not in content_type:
                 print(f"⚠️ SearXNG Warning: Expected JSON but got {content_type}. Status: {response.status_code}")
                 # If 403 or HTML, might be config issue, but we try to parse anyway if status is OK
            
            response.raise_for_status()
            data = response.json()
            
            # SearXNG JSON structure: {'results': [{'title':..., 'url':..., 'content':...}, ...]}
            raw_results = data.get("results", [])
            
            results = []
            for r in raw_results[:num_results]:
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("content", "") or r.get("snippet", "")
                })
                
            return results

        except Exception as e:
            print(f"⚠️ SearXNG API Error: {e}")
            return []
