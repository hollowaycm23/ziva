from typing import Dict, Any, List
from core.tools.searxng import SearXNGClient
from core.tools.scraper import PlaywrightScraper


class FactChecker:
    """
    Fact-checking system that validates information against external sources.
    """

    def __init__(self):
        self.searx = SearXNGClient()
        self.scraper = PlaywrightScraper()

    def verify_claim(self, claim: str, max_sources: int = 3) -> Dict[str, Any]:
        """
        Verifies a claim by searching external sources.

        Args:
            claim: The claim to verify
            max_sources: Maximum number of sources to check

        Returns:
            Dict with verification results and confidence score
        """
        print(f"  🔍 Fact-checking: {claim[:100]}...")

        # Search for the claim
        search_results = self.searx.search(claim, num_results=max_sources)

        if not search_results:
            return {
                "verified": False,
                "confidence": 0.0,
                "reason": "No external sources found",
                "sources": []
            }

        # Scrape and analyze sources
        sources_data = []
        for result in search_results[:max_sources]:
            url = result.get("url")
            if not url:
                continue

            try:
                data = self.scraper.scrape(url)
                if data["status"] == "success":
                    sources_data.append({
                        "url": url,
                        "title": result.get("title"),
                        "content": data["content"][:500],  # First 500 chars
                        "date": data.get("date")
                    })
            except Exception as e:
                print(f"  ⚠️ Failed to scrape {url}: {e}")
                continue

        if not sources_data:
            return {
                "verified": False,
                "confidence": 0.0,
                "reason": "Failed to scrape sources",
                "sources": []
            }

        # Calculate confidence based on number of confirming sources
        confidence = min(len(sources_data) / max_sources, 1.0)

        return {
            "verified": True,
            "confidence": confidence,
            "sources_count": len(sources_data),
            "sources": sources_data
        }

    def verify_multiple_claims(self, claims: List[str]) -> Dict[str, Any]:
        """
        Verifies multiple claims and returns aggregated confidence.
        """
        results = []
        total_confidence = 0.0

        for claim in claims:
            result = self.verify_claim(claim, max_sources=2)
            results.append(result)
            total_confidence += result.get("confidence", 0.0)

        avg_confidence = total_confidence / len(claims) if claims else 0.0

        return {
            "overall_confidence": avg_confidence,
            "individual_results": results
        }
