import requests
from bs4 import BeautifulSoup
from typing import Dict, Any
import datetime
import re


class WebScraper:
    """
    Robust web scraper for Ziva Agent.
    """

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; ZivaBot/1.0; +http://ziva.local)"}

    def scrape(self, url: str) -> Dict[str, Any]:
        """
        Visits a URL and extracts clean text.
        """
        try:
            response = requests.get(
                url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            for script in soup(
                    ["script", "style", "nav", "footer", "iframe", "aside"]):
                script.decompose()
            title = soup.title.string if soup.title else url
            article = soup.find('article') or soup.find('main') or soup.body
            text = article.get_text(separator=' ', strip=True)
            clean_text = re.sub(r'\s+', ' ', text).strip()
            date_str = self._find_date(soup)
            is_stale = self._check_staleness(date_str)
            return {
                "url": url, "title": title, "content": clean_text[:10000],
                "date": date_str, "is_stale": is_stale, "status": "success"
            }
        except Exception as e:
            return {"url": url, "status": "error", "error": str(e)}

    def _find_date(self, soup) -> str:
        date_meta = soup.find(
            'meta', {
                'property': 'article:published_time'}) or soup.find(
            'meta', {
                'name': 'date'}) or soup.find('time')
        if date_meta:
            return date_meta.get('content') or date_meta.get_text()
        return "Unknown"

    def _check_staleness(self, date_str: str) -> bool:
        """
        Returns True if content is likely > 2 years old.
        """
        if not date_str or date_str == "Unknown":
            return False
        try:
            match = re.search(r'20\d{2}', date_str)
            if match:
                year = int(match.group(0))
                current_year = datetime.datetime.now().year
                if (current_year - year) > 2:
                    return True
        except BaseException:
            pass
        return False