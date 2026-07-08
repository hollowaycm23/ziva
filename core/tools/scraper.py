from playwright.sync_api import sync_playwright
from datetime import datetime
import re
from typing import Dict, Any


import os
VERBOSE = os.getenv("ZIVA_VERBOSE", "false").lower() == "true"


class PlaywrightScraper:
    """
    Stealth web scraper using Playwright (Headless Chromium).
    """

    def scrape(self, url: str) -> Dict[str, Any]:
        """
        Visits a URL and extracts clean text.
        """
        remote_url = os.getenv("PLAYWRIGHT_WS_ENDPOINT")
        
        try:
            with sync_playwright() as p:
                if remote_url:
                    if VERBOSE:
                        print(f"    🌐 Connecting to remote browser: {remote_url}")
                    try:
                        browser = p.chromium.connect_over_cdp(remote_url)
                    except Exception as e:
                        if VERBOSE:
                            print(f"    ⚠️ Failed to connect to remote browser: {e}. Falling back to local.")
                        browser = p.chromium.launch(headless=True)
                else:
                    browser = p.chromium.launch(headless=True)

                context = browser.new_context(
                    user_agent=("Mozilla/5.0 (X11; Linux x86_64) "
                                "AppleWebKit/537.36 (KHTML, like Gecko) "
                                "Chrome/120.0.0.0 Safari/537.36"),
                    viewport={"width": 1280, "height": 720},
                    locale="pt-BR")
                page = context.new_page()
                if VERBOSE:
                    print(f"    🕷️ Navigating to: {url}")
                try:
                    page.goto(
                        url, timeout=20000, wait_until="domcontentloaded")
                    page.wait_for_load_state("load", timeout=5000)
                except Exception as e:
                    if VERBOSE:
                        print(f"    ⚠️ Navigation warning: {e}")
                title = "No Title"
                content = ""
                
                # Use Readability.js for better article extraction
                try:
                    # Inject Readability library and extract article
                    readability_result = page.evaluate("""() => {
                        // Simplified Readability extraction (inline version)
                        function getArticleContent() {
                            // Try common article selectors first
                            const selectors = [
                                'article',
                                'main',
                                '[role="main"]',
                                '.article-content',
                                '.post-content',
                                '.entry-content',
                                '#content'
                            ];
                            
                            for (const selector of selectors) {
                                const element = document.querySelector(selector);
                                if (element) {
                                    // Remove junk
                                    const junk = element.querySelectorAll('script, style, nav, footer, iframe, aside, .ad, .advertisement, .social-share, .comments');
                                    junk.forEach(el => el.remove());
                                    
                                    const text = element.innerText;
                                    if (text && text.length > 200) {
                                        return {
                                            title: document.title,
                                            content: text,
                                            success: true
                                        };
                                    }
                                }
                            }
                            
                            // Fallback: use body but filter more aggressively
                            const body = document.body.cloneNode(true);
                            const junk = body.querySelectorAll('script, style, nav, header, footer, iframe, aside, .ad, .advertisement, .menu, .sidebar, .social, .comments, .related');
                            junk.forEach(el => el.remove());
                            
                            return {
                                title: document.title,
                                content: body.innerText,
                                success: true
                            };
                        }
                        
                        return getArticleContent();
                    }""")
                    
                    if readability_result.get("success"):
                        title = readability_result.get("title", "No Title")
                        content = readability_result.get("content", "")
                        if VERBOSE:
                            print(f"    ✅ Readability extracted {len(content)} chars")
                    else:
                        raise Exception("Readability extraction failed")
                        
                except Exception as e:
                    if VERBOSE:
                        print(f"    ⚠️ Readability failed ({e}), using fallback")
                    # Fallback to original method
                    for attempt in range(3):
                        try:
                            if attempt > 0:
                                page.wait_for_timeout(1000)
                            title = page.title()
                            content = page.evaluate("""() => {
                                const article = document.querySelector('article') || document.querySelector('main') || document.body;
                                const junk = article.querySelectorAll('script, style, nav, footer, iframe, aside, .ad, .advertisement');
                                junk.forEach(el => el.remove());
                                return article.innerText;
                            }""")
                            break
                        except Exception as e:
                            if VERBOSE:
                                print(f"    ⚠️ Attempt {attempt + 1} failed ({e}), retrying.")
                            continue
                
                date_str = "Unknown"
                meta_tags = [
                    'meta[property="article:published_time"]',
                    'meta[name="date"]',
                    'meta[name="pubdate"]',
                    'meta[name="publish-date"]',
                    'meta[name="citation_date"]',
                    'meta[property="og:published_time"]'
                ]
                
                for tag in meta_tags:
                    try:
                        val = page.locator(tag).get_attribute('content')
                        if val:
                            # Normalize YYYY-MM-DD
                            match = re.search(r'(\d{4}-\d{2}-\d{2})', val)
                            if match:
                                date_str = match.group(1)
                                break
                    except Exception:
                        continue
                
                # Heuristic: Try to find date in URL (e.g. /2024/01/14/)
                if date_str == "Unknown":
                    try:
                        match = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', url)
                        if match:
                            date_str = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
                    except Exception:
                        pass

                browser.close()
                clean_text = re.sub(r'\s+', ' ', content).strip()
                is_stale = self._check_staleness(date_str)
                return {
                    "url": url, "title": title, "content": clean_text[:15000],
                    "date": date_str, "is_stale": is_stale, "status": "success"
                }
        except Exception as e:
            return {"url": url, "status": "error", "error": str(e)}

    def _check_staleness(self, date_str: str) -> bool:
        """
        Returns True if content is likely > 2 years old.
        """
        if not date_str or date_str == "Unknown":
            return False
        try:
            match = re.search(r'20\d{2}', str(date_str))
            if match:
                year = int(match.group(0))
                current_year = datetime.now().year
                if (current_year - year) > 2:
                    return True
        except BaseException:
            pass
        return False
