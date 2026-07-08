import requests
import re
from typing import List, Dict, Any, Optional


class KiwixClient:
    """
    Client for interacting with local Kiwix Server (port 8081).
    """

    def __init__(self, base_url: str = "http://localhost:8081"):
        self.base_url = base_url
        self.content_id = self._detect_content_id()

    def _detect_content_id(self) -> Optional[str]:
        """
        Detects the first available ZIM content ID from OPDS catalog.
        """
        try:
            resp = requests.get(
                f"{self.base_url}/catalog/v2/entries", timeout=2)
            if resp.status_code == 200:
                # Simple regex to find /content/SLUG
                match = re.search(r'href="/content/([^"]+)"', resp.text)
                if match:
                    slug = match.group(1)
                    print(f"  📚 Kiwix Content Detected: {slug}")
                    return slug
        except Exception as e:
            print(f"  ⚠️ Kiwix Detection Failed: {e}")
        return None

    def search(self, query: str, num_results: int = 3) -> List[Dict[str, Any]]:
        """
        Searches Kiwix and returns a list of results.
        """
        if not self.content_id:
            return []

        search_url = f"{self.base_url}/search"
        params = {"content": self.content_id, "pattern": query}

        results = []
        try:
            resp = requests.get(search_url, params=params, timeout=5)
            if resp.status_code != 200:
                return []

            items = resp.text.split('<li')

            for item in items[1:]:
                if len(results) >= num_results:
                    break
                try:
                    link_match = re.search(
                        r'href="([^"]+)"[^>]*>\s*([^<]+)\s*</a>', item)
                    if not link_match:
                        continue
                    sub_url = link_match.group(1)
                    title = link_match.group(2).strip()
                    cite_match = re.search(
                        r'<cite>(.*?)</cite>', item, re.DOTALL)
                    snippet = cite_match.group(
                        1).strip() if cite_match else ""
                    snippet = re.sub(r'<[^>]+>', '', snippet)
                    full_url = f"{self.base_url}{sub_url}"
                    results.append({
                        "title": title, "url": full_url, "content": snippet
                    })
                except Exception:
                    continue

        except Exception as e:
            print(f"  ❌ Kiwix Search Error: {e}")
        return results

    def get_page_content(self, url: str) -> str:
        """
        Fetches full text of a Kiwix page.
        """
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                text = re.sub(
                    r'<script.*?</script>', '', resp.text, flags=re.DOTALL)
                text = re.sub(r'<style.*?</style>', '', text, flags=re.DOTALL)
                text = re.sub(r'<[^>]+>', ' ', text)
                text = re.sub(r'\s+', ' ', text).strip()
                return text[:5000]
        except Exception:
            pass
        return ""
