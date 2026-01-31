from typing import Dict, Any


class TechNewsClient:
    """
    Client to fetch and summarize tech news from Brazilian sources.
    """

    def __init__(self):
        self.sources = {
            "adrenaline": "https://adrenaline.com.br/",
            "tecnoblog": "https://tecnoblog.net/",
            "ign_brasil": "https://br.ign.com/"
        }

    def fetch_headlines(self, max_sources: int = 2) -> Dict[str, Any]:
        """
        Fetches latest headlines from tech news sources.
        """
        from core.tools.scraper import PlaywrightScraper

        scraper = PlaywrightScraper()
        results = {}

        for source_name, url in list(self.sources.items())[:max_sources]:
            print(f"  📰 Fetching headlines from {source_name}...")

            try:
                data = scraper.scrape(url)

                if data["status"] == "success":
                    content = data["content"][:800]
                    results[source_name] = {
                        "url": url,
                        "title": data["title"],
                        "content": content,
                        "date": data["date"]
                    }
                else:
                    results[source_name] = {
                        "error": data.get("error", "Unknown error")}

            except Exception as e:
                results[source_name] = {"error": str(e)}

        return results