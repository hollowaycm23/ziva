"""
Ad Domain Filter
Programmatic filtering of advertisement and spam domains.
Supplements Pi-hole DNS blocking with additional code-level checks.
"""
from typing import List, Set
from urllib.parse import urlparse
import logging

logger = logging.getLogger("AdFilter")


class AdDomainFilter:
    """
    Filters advertisement and spam domains from web search results.

    Works as a supplement to Pi-hole DNS blocking.
    """

    # Common ad networks and tracking domains
    BLOCKED_DOMAINS: Set[str] = {
        # Google Ads
        'ads.google.com',
        'adservice.google.com',
        'pagead2.googlesyndication.com',
        'googleads.g.doubleclick.net',
        'doubleclick.net',
        'ad.doubleclick.net',

        # Facebook/Meta Ads
        'ads.facebook.com',
        'an.facebook.com',

        # Generic ad networks
        'adnxs.com',
        'adsrvr.org',
        'advertising.com',
        'adtech.de',
        'criteo.com',
        'outbrain.com',
        'taboola.com',

        # Spam domains (common patterns)
        'clickfunnels.com',
        'bit.ly',  # Often used in spam
        'tinyurl.com',  # URL shorteners can hide spam

        # Low-quality content farms
        'ehow.com',
        'answers.com',
    }

    # Suspicious TLDs often used for spam
    SUSPICIOUS_TLDS: Set[str] = {
        '.tk', '.ml', '.ga', '.cf', '.gq',  # Free TLDs
        '.xyz', '.top', '.work', '.click',   # Cheap spam TLDs
    }

    # Spam keywords in URLs
    SPAM_KEYWORDS: List[str] = [
        'casino', 'poker', 'viagra', 'cialis',
        'weight-loss', 'make-money-fast',
        'bitcoin-doubler', 'free-iphone',
    ]

    def __init__(self):
        self.blocked_count = 0
        self.allowed_count = 0

    def is_blocked_domain(self, url: str) -> bool:
        """
        Check if URL belongs to a blocked domain.

        Args:
            url: URL to check

        Returns:
            True if domain should be blocked, False otherwise
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remove port if present
            if ':' in domain:
                domain = domain.split(':')[0]

            # Check exact domain match
            if domain in self.BLOCKED_DOMAINS:
                logger.debug(f"Blocked exact match: {domain}")
                return True

            # Check if domain ends with blocked domain (subdomain check)
            for blocked in self.BLOCKED_DOMAINS:
                if domain.endswith('.' + blocked) or domain == blocked:
                    logger.debug(
                        f"Blocked subdomain: {domain} (matches {blocked})")
                    return True

            # Check suspicious TLDs
            for tld in self.SUSPICIOUS_TLDS:
                if domain.endswith(tld):
                    logger.debug(f"Blocked suspicious TLD: {domain}")
                    return True

            # Check spam keywords in full URL
            url_lower = url.lower()
            for keyword in self.SPAM_KEYWORDS:
                if keyword in url_lower:
                    logger.debug(f"Blocked spam keyword: {keyword} in {url}")
                    return True

            return False

        except Exception as e:
            logger.error(f"Error parsing URL {url}: {e}")
            return False  # Don't block on error

    def filter_results(self, results: List[dict]) -> List[dict]:
        """
        Filter search results, removing blocked domains.

        Args:
            results: List of search result dicts with 'url' key

        Returns:
            Filtered list of results
        """
        filtered = []

        for result in results:
            url = result.get('url', '')

            if not url:
                continue

            if self.is_blocked_domain(url):
                self.blocked_count += 1
                logger.info(f"Filtered out: {url}")
            else:
                self.allowed_count += 1
                filtered.append(result)

        return filtered

    def get_stats(self) -> dict:
        """Get filtering statistics."""
        total = self.blocked_count + self.allowed_count
        block_rate = (self.blocked_count / total * 100) if total > 0 else 0

        return {
            'blocked': self.blocked_count,
            'allowed': self.allowed_count,
            'total': total,
            'block_rate': f"{block_rate:.1f}%"
        }


# Global instance
_filter = None


def get_ad_filter() -> AdDomainFilter:
    """Get or create global ad filter instance."""
    global _filter
    if _filter is None:
        _filter = AdDomainFilter()
    return _filter
