"""
Unified Web Search with Automatic Fallback (SearXNG -> Brave -> DuckDuckGo -> MultiSource)
Prioritizes Local SearXNG (HTML Scraping) for reliability.
"""

import os
import logging
from typing import List, Dict, Optional, Any

logger = logging.getLogger("UnifiedSearch")

# Mark explicitly as Ziva Tool function
def unified_web_search(
    query: str,
    max_results: int = 5,
    prefer_brave: bool = False
) -> Dict[str, Any]:
    """
    Intelligent web search with automatic fallback.
    
    Strategy:
    1. SearXNG (Local HTML Scraping) - Primary (No API Key, No 403)
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
        # Import inside function to avoid startup circular deps
        from core.tools.searxng import SearXNGClient
        logger.info("🔭 Trying SearxNG Local (HTML Scraping)...")
        
        client = SearXNGClient() # Uses env defaults or localhost:8080
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
            # Don't return here, proceed to deep scraping if desired
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
                # Proceed to deep scraping
    except ImportError:
         logger.warning("⚠️ duckduckgo_search module not installed.")
    except Exception as e:
        logger.warning(f"⚠️ DuckDuckGo Search failed: {e}")

    # ==================== DEEP SCRAPING WITH PLAYWRIGHT = : = ====================
    if results["results"]:
        try:
            from core.tools.scraper import PlaywrightScraper
            scraper = PlaywrightScraper()
            logger.info(f"🕷️ Starting Deep Scraping for top {min(3, len(results['results']))} results...")
            
            deep_context = ""
            for i, res in enumerate(results["results"][:3]):
                url = res.get("url")
                if url and url != "#":
                    logger.info(f"   [{i+1}] Scraping: {url}")
                    scrape_res = scraper.scrape(url)
                    if scrape_res.get("status") == "success":
                        content = scrape_res.get("content", "")
                        # Store in result object for tool output
                        res["deep_content"] = content
                        deep_context += f"--- CONTEÚDO ÍNTEGRO ({res['title']}) ---\n{content[:5000]}\n\n"
                    else:
                        logger.warning(f"   ⚠️ Scrape failed for {url}: {scrape_res.get('error')}")
            
            if deep_context:
                # Add to results for synthesis
                results["deep_context"] = deep_context
                
                # AUTO-INDEXING with deep content
                try:
                    from core.config import config
                    from core.llm import LLMService
                    from core.rag_helper import get_rag_helper
                    
                    emb_config = config.get_llm_provider("agent.embedding_model")
                    model_name = emb_config["model_name"] if emb_config else "text-embedding-qwen2.5-0.5b-instruct"
                    
                    rag = get_rag_helper()
                    embedder = LLMService(model=model_name)
                    # Use deep context for better RAG
                    emb = embedder.embedding(deep_context[:10000]) # Cap for embedding
                    if emb:
                        rag.vector_store.add_text(deep_context[:15000], emb, {
                            "source": "unified_web_search_playwright",
                            "query": query,
                            "type": "deep_research"
                        })
                        logger.info("💾 Deep search results auto-indexed successfully.")
                except Exception as e:
                    logger.warning(f"⚠️ Deep indexing failed: {e}")
                    
        except ImportError:
            logger.warning("⚠️ PlaywrightScraper import failed. Skipping deep scraping.")
        except Exception as e:
            logger.error(f"⚠️ Deep scraping failed: {e}")

    return results

unified_web_search._is_ziva_tool = True
