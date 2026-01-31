import os
import logging
from typing import List, Dict, Optional, Any
from agent.tools import ziva_tool

logger = logging.getLogger("SkillWebSearch")

@ziva_tool
def unified_web_search(
    query: str,
    max_results: int = 5,
    prefer_brave: bool = False
) -> Dict[str, Any]:
    """
    Intelligent web search with automatic fallback.
    
    Strategy:
    1. SearXNG (Local HTML Scraping) - Primary
    2. Brave Search (if API Key present)
    3. DuckDuckGo (if installed)
    4. Multi-Source (Wikipedia, etc)
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
        from core.tools.searxng import SearXNGClient
        logger.info("🔭 Trying SearxNG Local (HTML Scraping) via Skill...")
        
        client = SearXNGClient() 
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
            
            # AUTO-INDEXING
            try:
                from core.rag_helper import get_rag_helper
                from core.llm import LLMService
                rag = get_rag_helper()
                embedder = LLMService(model="nomic-embed-text")
                emb = embedder.embedding(context_text)
                if emb:
                    rag.vector_store.add_text(context_text, emb, {
                        "source": "unified_web_search",
                        "query": query,
                        "type": "web_research"
                    })
                    logger.info("💾 Search results auto-indexed successfully.")
            except Exception as e:
                logger.warning(f"⚠️ Auto-indexing failed: {e}")

            results["primary_engine"] = "searxng"
            results["sources_used"].append("searxng")
            results["results"].extend(std_results)
            results["total"] = len(std_results)
            logger.info(f"✅ SearxNG returned {len(std_results)} results")
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
                return results
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"⚠️ Brave Search failed: {e}")

    # ==================== STRATEGY 3: DUCKDUCKGO ====================
    try:
        from duckduckgo_search import DDGS
        logger.info("🦆 Trying DuckDuckGo Search...")
        with DDGS() as ddgs:
            ddg_gen = ddgs.text(query, max_results=max_results)
            ddg_results = []
            if ddg_gen:
                for r in ddg_gen:
                    ddg_results.append({
                        "title": r.get("title"),
                        "url": r.get("href"),
                        "source": "duckduckgo",
                        "description": r.get("body")
                    })
            if ddg_results:
                results["primary_engine"] = "duckduckgo"
                results["sources_used"].append("duckduckgo")
                results["results"].extend(ddg_results)
                results["total"] = len(ddg_results)
                return results
    except ImportError:
         logger.warning("⚠️ duckduckgo_search module not installed.")
    except Exception as e:
        logger.warning(f"⚠️ DuckDuckGo Search failed: {e}")

    return results
