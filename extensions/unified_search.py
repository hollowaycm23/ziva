"""
Unified Web Search with Automatic Fallback (SearXNG -> Brave -> DuckDuckGo -> MultiSource)
Prioritizes Local SearXNG (HTML Scraping) for reliability.
"""

import os
import logging
from typing import Dict, Any

logger = logging.getLogger("UnifiedSearch")


def _ddg_search(query: str, max_results: int = 5) -> list:
    try:
        from ddgs import DDGS
    except ImportError:
        from duckduckgo_search import DDGS
    results = []
    with DDGS() as ddgs:
        ddg_gen = ddgs.text(query, max_results=max_results)
        if ddg_gen:
            for r in ddg_gen:
                results.append({
                    "title": r.get("title"),
                    "url": r.get("href") or r.get("link") or r.get("url"),
                    "source": "duckduckgo",
                    "description": r.get("body") or r.get("snippet") or r.get("description", "")
                })
    return results


# Mark explicitly as Ziva Tool function
def unified_web_search(
    query: str,
    max_results: int = 5,
    prefer_brave: bool = False,
    deep_scrape: bool = True
) -> Dict[str, Any]:
    """
    Intelligent web search with automatic fallback.

    Strategy:
    1. SearXNG (Local HTML Scraping) - Primary (No API Key, No 403)
    2. Brave Search (if API Key present)
    3. DuckDuckGo (if installed)
    4. Multi-Source (Wikipedia, etc)

    Args:
        deep_scrape: If True, performs Playwright deep scraping on top results (slow, ~20s per URL).
                     Set to False for quick lookups where snippets suffice.
    """

    results = {
        "query": query,
        "primary_engine": None,
        "sources_used": [],
        "results": [],
        "total": 0
    }

    # ==================== STRATEGY 1: SEARXNG (LOCAL & RELIABLE) ====================
    try:
        # Import inside function to avoid startup circular deps
        from core.tools.searxng import SearXNGClient
        logger.info("🔭 Trying SearxNG Local (HTML Scraping)...")

        client = SearXNGClient()  # Uses env defaults or localhost:8080
        # This client handles HTML parsing to bypass 403 errors
        searx_results = client.search(query, num_results=max_results)

        if searx_results:
            std_results = []
            context_text = f"--- BUSCA WEB: {query} ---\n"
            for r in searx_results:
                title = r.get("title", "No Title")
                snippet = r.get("snippet", "")
                url = r.get("url", "#")
                std_results.append({
                    "title": title,
                    "url": url,
                    "source": "searxng",
                    "description": snippet
                })
                context_text += f"Título: {title}\nURL: {url}\nResumo: {snippet}\n\n"

            try:
                from core.config import config
                from core.llm import LLMService
                from core.rag_helper import get_rag_helper

                emb_config = config.get_llm_provider("agent.embedding_model")
                model_name = emb_config["model_name"] if emb_config else "text-embedding-qwen2.5-0.5b-instruct"

                rag = get_rag_helper()
                embedder = LLMService(model=model_name)
                emb = embedder.embedding(context_text)
                if emb:
                    rag.vector_store.add_text(context_text, emb, {
                        "source": "unified_web_search",
                        "source_domain": next((r.get("url", "") for r in searx_results if r.get("url")), ""),
                        "query": query,
                        "type": "web_research",
                        "content_type": "web_search",
                        "author": "",
                        "date": "",
                    })
                    logger.info("💾 Search results auto-indexed successfully.")
            except Exception as e:
                logger.warning(f"⚠️ Auto-indexing failed: {e}")

            results["primary_engine"] = "searxng"
            results["sources_used"].append("searxng")
            results["results"].extend(std_results)
            results["total"] = len(std_results)
            logger.info(f"✅ SearxNG returned {len(std_results)} results")

            # Try DuckDuckGo in parallel for more coverage (non-blocking)
            try:
                from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
                with ThreadPoolExecutor(max_workers=1) as pool:
                    future = pool.submit(_ddg_search, query, max_results)
                    try:
                        ddg_extra = future.result(timeout=10)
                        if ddg_extra:
                            seen_urls = {r.get("url") for r in results["results"] if r.get("url")}
                            for r in ddg_extra:
                                if r.get("url") not in seen_urls:
                                    results["results"].append(r)
                                    seen_urls.add(r.get("url"))
                            results["total"] = len(results["results"])
                            results["sources_used"].append("duckduckgo")
                            logger.info(f"✅ DuckDuckGo added {len(ddg_extra)} extra results")
                    except FuturesTimeout:
                        logger.debug("DuckDuckGo parallel search timed out")
            except Exception as e:
                logger.debug(f"DuckDuckGo parallel search failed: {e}")

            # Deep scrape happens here BEFORE returning (parallel, ~20s for 3 URLs)
            if deep_scrape and results["results"]:
                _run_deep_scrape(results)

            return results
    except Exception as e:
        logger.warning(f"⚠️ SearxNG failed: {e}")

    # ==================== STRATEGY 2: BRAVE ====================
    brave_api_key = os.getenv("BRAVE_API_KEY")
    if brave_api_key and brave_api_key != "YOUR_KEY_HERE":
        try:
            from extensions.multi_search import search_brave
            logger.info("🔍 Trying Brave Search...")
            brave_results = search_brave(query, max_results)
            if brave_results:
                results["primary_engine"] = "brave"
                results["sources_used"].append("brave")
                results["results"].extend(brave_results)
                results["total"] = len(brave_results)
                # Proceed to deep scraping
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"⚠️ Brave Search failed: {e}")

    # ==================== STRATEGY 3: DUCKDUCKGO ====================
    try:
        from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
        logger.info("🦆 Trying DuckDuckGo Search...")
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_ddg_search, query, max_results)
            try:
                ddg_results = future.result(timeout=15)
                if ddg_results:
                    results["primary_engine"] = "duckduckgo"
                    results["sources_used"].append("duckduckgo")
                    results["results"].extend(ddg_results)
                    results["total"] = len(ddg_results)
            except FuturesTimeout:
                logger.warning("⚠️ DuckDuckGo search timed out")
    except ImportError:
        logger.warning("duckduckgo_search module not installed.")
    except Exception as e:
        logger.warning(f"⚠️ DuckDuckGo Search failed: {e}")

    # Also try deep scrape for fallback paths (Brave/DDG as primary)
    if deep_scrape and results["results"]:
        _run_deep_scrape(results)

    return results


def _run_deep_scrape(results: dict) -> None:
    """Run Playwright deep scraping on top 3 results in parallel (mutates results in-place)."""
    try:
        from core.tools.scraper import PlaywrightScraper
        from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

        scraper = PlaywrightScraper()
        logger.info(f"🕷️ Deep scraping top {min(3, len(results['results']))} results...")

        deep_context = ""
        urls_to_scrape = [(i, res) for i, res in enumerate(results["results"][:3])
                          if res.get("url") and res.get("url") != "#"]
        if urls_to_scrape:
            logger.info(f"   Scraping {len(urls_to_scrape)} URLs in parallel...")
            with ThreadPoolExecutor(max_workers=len(urls_to_scrape)) as exec:
                fut_map = {exec.submit(scraper.scrape, res["url"]): (i, res) for i, res in urls_to_scrape}
                for future in fut_map:
                    i, res = fut_map[future]
                    try:
                        scrape_res = future.result(timeout=20)
                        if scrape_res.get("status") == "success":
                            content = scrape_res.get("content", "")
                            res["deep_content"] = content
                            deep_context += f"--- CONTEÚDO ÍNTEGRO ({res['title']}) ---\n{content[:5000]}\n\n"
                        else:
                            logger.warning(f"   ⚠️ Scrape failed for {res.get('url')}: {scrape_res.get('error')}")
                    except FuturesTimeout:
                        logger.warning(f"   ⚠️ Scrape timed out for {res.get('url')}")

        if deep_context:
            results["deep_context"] = deep_context
            try:
                from core.config import config
                from core.llm import LLMService
                from core.rag_helper import get_rag_helper

                emb_config = config.get_llm_provider("agent.embedding_model")
                model_name = emb_config["model_name"] if emb_config else "text-embedding-qwen2.5-0.5b-instruct"
                rag = get_rag_helper()
                embedder = LLMService(model=model_name)
                emb = embedder.embedding(deep_context[:10000])
                if emb:
                    rag.vector_store.add_text(deep_context[:15000], emb, {
                        "source": "unified_web_search_playwright",
                        "source_domain": next((r.get("url", "") for r in results["results"][:3] if r.get("url")), ""),
                        "query": results.get("query", ""),
                        "type": "deep_research",
                        "content_type": "web_scrape",
                        "author": "",
                        "date": "",
                    })
                    logger.info("💾 Deep search results auto-indexed successfully.")
            except Exception as e:
                logger.warning(f"⚠️ Deep indexing failed: {e}")

    except ImportError:
        logger.warning("⚠️ PlaywrightScraper import failed. Skipping deep scraping.")
    except Exception as e:
        logger.error(f"⚠️ Deep scraping failed: {e}")
