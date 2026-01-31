"""
Multi-Source Web Search Tool
Aggregates results from multiple free sources without CAPTCHA issues.

Sources:
1. Brave Search API (Free tier: 2000 requests/month)
2. Wikipedia API (Unlimited, free)
3. GitHub API (60 requests/hour no auth, 5000 with auth)
4. StackOverflow API (300 requests/day)
5. Semantic Scholar API (Academic papers, free)
"""

import requests
import json
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger("MultiSearch")


# ==================== BRAVE SEARCH ====================
def search_brave(query: str, count: int = 5) -> List[Dict]:
    """
    Search using Brave Search API (free tier).

    Note: Requires API key from https://brave.com/search/api/
    Free tier: 2000 requests/month, 1 req/second
    """
    # Check if API key is configured
    import os
    api_key = os.getenv("BRAVE_API_KEY")

    if not api_key or api_key == "YOUR_KEY_HERE":
        logger.warning("Brave API key not configured, skipping Brave Search")
        return []

    try:
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": api_key
        }
        params = {
            "q": query,
            "count": count
        }

        response = requests.get(url, headers=headers, params=params, timeout=5)
        response.raise_for_status()

        data = response.json()
        results = []

        for item in data.get("web", {}).get("results", [])[:count]:
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "description": item.get("description", ""),
                "source": "Brave Search"
            })

        return results

    except Exception as e:
        logger.error(f"Brave Search error: {e}")
        return []


# ==================== WIKIPEDIA ====================
def search_wikipedia(query: str, count: int = 3,
                     lang: str = "pt") -> List[Dict]:
    """
    Search Wikipedia (completely free, no limits).

    Args:
        query: Search query
        count: Number of results
        lang: Language code (pt, en, es, etc.)
    """
    try:
        # Wikipedia API endpoint
        url = f"https://{lang}.wikipedia.org/w/api.php"

        # Wikipedia requires User-Agent
        headers = {
            "User-Agent": "ZivaBot/1.0 (https://github.com/ziva; ziva@example.com)"}

        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "limit": count,
            "format": "json"
        }

        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()

        data = response.json()
        results = []

        search_results = data.get("query", {}).get("search", [])
        for item in search_results:
            results.append({
                "title": item.get("title", ""),
                "url": f"https://{lang}.wikipedia.org/wiki/{item.get('title', '').replace(' ', '_')}",
                "description": item.get("snippet", "").replace('<span class="searchmatch">', '').replace('</span>', ''),
                "source": f"Wikipedia ({lang.upper()})"
            })

        return results

    except Exception as e:
        logger.error(f"Wikipedia search error: {e}")
        return []


# ==================== GITHUB ====================
def search_github(query: str, count: int = 5,
                  search_type: str = "repositories") -> List[Dict]:
    """
    Search GitHub repositories, code, or users.

    Free tier: 60 requests/hour (no auth), 5000/hour (with token)

    Args:
        query: Search query
        count: Number of results
        search_type: "repositories", "code", "users", or "issues"
    """
    try:
        url = f"https://api.github.com/search/{search_type}"

        headers = {"Accept": "application/vnd.github.v3+json"}

        # Add token if available
        import os
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            headers["Authorization"] = f"token {github_token}"

        params = {
            "q": query,
            "per_page": count,
            "sort": "stars" if search_type == "repositories" else "score"
        }

        response = requests.get(url, headers=headers, params=params, timeout=5)
        response.raise_for_status()

        data = response.json()
        results = []

        for item in data.get("items", [])[:count]:
            if search_type == "repositories":
                results.append({
                    "title": item.get("full_name", ""),
                    "url": item.get("html_url", ""),
                    "description": item.get("description", ""),
                    "stars": item.get("stargazers_count", 0),
                    "language": item.get("language", ""),
                    "source": "GitHub"
                })
            elif search_type == "code":
                results.append({
                    "title": item.get("name", ""),
                    "url": item.get("html_url", ""),
                    "description": f"Repository: {item.get('repository', {}).get('full_name', '')}",
                    "source": "GitHub Code"
                })

        return results

    except Exception as e:
        logger.error(f"GitHub search error: {e}")
        return []


# ==================== STACK OVERFLOW ====================
def search_stackoverflow(query: str, count: int = 5) -> List[Dict]:
    """
    Search Stack Overflow questions.

    Free tier: 300 requests/day (no auth), 10000/day (with key)
    """
    try:
        url = "https://api.stackexchange.com/2.3/search/advanced"

        params = {
            "order": "desc",
            "sort": "relevance",
            "q": query,
            "site": "stackoverflow",
            "pagesize": count
        }

        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()

        data = response.json()
        results = []

        for item in data.get("items", [])[:count]:
            results.append(
                {
                    "title": item.get(
                        "title", ""), "url": item.get(
                        "link", ""), "description": f"Answers: {
                        item.get(
                            'answer_count', 0)} | Score: {
                            item.get(
                                'score', 0)}", "tags": item.get(
                                    "tags", []), "answered": item.get(
                                        "is_answered", False), "source": "Stack Overflow"})

        return results

    except Exception as e:
        logger.error(f"Stack Overflow search error: {e}")
        return []


# ==================== SEMANTIC SCHOLAR ====================
def search_scholar(query: str, count: int = 5) -> List[Dict]:
    """
    Search academic papers via Semantic Scholar.

    Completely free, no rate limits (with reasonable use)
    """
    try:
        url = "https://api.semanticscholar.org/graph/v1/paper/search"

        headers = {
            "User-Agent": "ZivaBot/1.0 (Research Assistant; ziva@example.com)"
        }

        params = {
            "query": query,
            "limit": count,
            "fields": "title,authors,year,abstract,url,citationCount"
        }

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=10)
        response.raise_for_status()

        data = response.json()
        results = []

        for item in data.get("data", [])[:count]:
            authors = ", ".join([a.get("name", "")
                                for a in item.get("authors", [])[:3]])

            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "description": item.get("abstract", "")[:200] + "..." if item.get("abstract") else "",
                "authors": authors,
                "year": item.get("year"),
                "citations": item.get("citationCount", 0),
                "source": "Semantic Scholar"
            })

        return results

    except Exception as e:
        logger.error(f"Semantic Scholar search error: {e}")
        return []


# ==================== UNIFIED SEARCH ====================
def multi_source_search(
    query: str,
    sources: List[str] = None,
    max_results_per_source: int = 3
) -> Dict:
    """
    Search across multiple sources and aggregate results.

    Args:
        query: Search query
        sources: List of sources to use. Options:
                 ["brave", "wikipedia", "github", "stackoverflow", "scholar"]
                 If None, uses all available sources
        max_results_per_source: Maximum results from each source

    Returns:
        Dictionary with results from each source
    """

    if sources is None:
        sources = ["wikipedia", "github", "stackoverflow", "scholar", "brave"]

    all_results = {
        "query": query,
        "timestamp": datetime.now().isoformat(),
        "sources": {}
    }

    source_functions = {
        "brave": lambda: search_brave(query, max_results_per_source),
        "wikipedia": lambda: search_wikipedia(query, max_results_per_source),
        "github": lambda: search_github(query, max_results_per_source),
        "stackoverflow": lambda: search_stackoverflow(query, max_results_per_source),
        "scholar": lambda: search_scholar(query, max_results_per_source)
    }

    for source in sources:
        if source in source_functions:
            try:
                logger.info(f"Searching {source}...")
                results = source_functions[source]()
                all_results["sources"][source] = {
                    "count": len(results),
                    "results": results
                }
            except Exception as e:
                logger.error(f"Error searching {source}: {e}")
                all_results["sources"][source] = {
                    "count": 0,
                    "results": [],
                    "error": str(e)
                }

    # Calculate total results
    total = sum(s.get("count", 0) for s in all_results["sources"].values())
    all_results["total_results"] = total

    return all_results


# Mark as Ziva tool
multi_source_search._is_ziva_tool = True


if __name__ == "__main__":
    # Test the multi-source search
    print("🧪 Testing Multi-Source Search\n")

    test_query = "python tutorial"

    results = multi_source_search(test_query, max_results_per_source=2)

    print(f"Query: {test_query}")
    print(f"Total results: {results['total_results']}\n")

    for source_name, source_data in results["sources"].items():
        print(f"\n📍 {source_name.upper()} ({source_data['count']} results):")
        for i, item in enumerate(source_data.get("results", []), 1):
            print(f"  {i}. {item['title'][:60]}...")
            print(f"     {item['url']}")
