#!/usr/bin/env python3
"""
Enhanced Web Scraping Script using Playwright.
Extracts content from web pages, including dynamic sites with JavaScript/SPA.

Features:
- Async support for concurrent scraping
- Proper error handling and retry logic
- Configurable timeouts and browser settings
- Input validation and sanitization
- Comprehensive logging
- Browser context reuse for performance
- Type hints and dataclasses for better maintainability
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Union
from urllib.parse import urlparse

from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from playwright.sync_api import sync_playwright


# Configuration Constants
@dataclass
class ScraperConfig:
    """Configuration settings for the web scraper."""
    browser_timeout: int = 30000
    element_timeout: int = 10000
    max_retries: int = 3
    retry_delay: float = 1.0
    max_text_length: int = 50000  # Increased from 2000
    screenshot_dir: str = "screenshots"
    headless: bool = True
    user_agent: str = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    viewport: Dict[str, int] = None

    def __post_init__(self):
        if self.viewport is None:
            self.viewport = {"width": 1280, "height": 720}


# Custom Exceptions
class ScraperError(Exception):
    """Base exception for scraper errors."""
    pass


class NetworkError(ScraperError):
    """Network-related scraping errors."""
    pass


class ElementNotFoundError(ScraperError):
    """Element selector not found errors."""
    pass


class ValidationError(ScraperError):
    """Input validation errors."""
    pass


@dataclass
class ScrapeResult:
    """Structured result from scraping operation."""
    url: str
    title: str
    selector: str
    text: str
    html_length: int
    screenshot_path: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    response_time: float = 0.0
    timestamp: float = 0.0

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def save_to_file(self, filepath: Union[str, Path]) -> None:
        """Save result to JSON file."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)


class WebScraper:
    """Enhanced web scraper with proper error handling and performance optimizations."""

    def __init__(self, config: Optional[ScraperConfig] = None):
        self.config = config or ScraperConfig()
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self.logger = logging.getLogger(__name__)

    def _setup_logging(self):
        """Configure logging if not already configured."""
        if not logging.getLogger().handlers:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

    def _validate_url(self, url: str) -> str:
        """Validate and normalize URL."""
        if not url or not isinstance(url, str):
            raise ValidationError("URL must be a non-empty string")

        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            url = f'https://{url}'

        try:
            parsed = urlparse(url)
            if not parsed.netloc:
                raise ValidationError(f"Invalid URL format: {url}")
        except Exception as e:
            raise ValidationError(f"URL parsing failed: {e}")

        return url

    def _validate_selector(self, selector: str) -> str:
        """Validate CSS selector."""
        if not selector or not isinstance(selector, str):
            raise ValidationError("Selector must be a non-empty string")

        selector = selector.strip()
        if not selector:
            raise ValidationError("Selector cannot be empty after stripping")

        return selector

    def _create_browser_context(self) -> BrowserContext:
        """Create and configure browser context."""
        if self._browser is None:
            playwright = sync_playwright().start()
            self._browser = playwright.chromium.launch(
                headless=self.config.headless,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )

        if self._context is None:
            self._context = self._browser.new_context(
                user_agent=self.config.user_agent,
                viewport=self.config.viewport
            )

        return self._context

    def _take_screenshot(self, page: Page, url: str) -> Optional[str]:
        """Take screenshot of the page."""
        try:
            screenshot_dir = Path(self.config.screenshot_dir)
            screenshot_dir.mkdir(exist_ok=True)

            # Create safe filename from URL
            domain = urlparse(url).netloc.replace('.', '_')
            timestamp = int(time.time())
            filename = f"{domain}_{timestamp}.png"
            screenshot_path = screenshot_dir / filename

            page.screenshot(path=str(screenshot_path), full_page=True)
            self.logger.info(f"Screenshot saved: {screenshot_path}")
            return str(screenshot_path)

        except Exception as e:
            self.logger.warning(f"Failed to take screenshot: {e}")
            return None

    def _extract_content(self, page: Page, selector: str) -> tuple[str, str]:
        """Extract text and HTML content from selector."""
        try:
            element = page.locator(selector).first
            text_content = element.inner_text()
            html_content = element.inner_html()
            return text_content, html_content
        except Exception as e:
            raise ElementNotFoundError(f"Selector '{selector}' not found or failed to extract content: {e}")

    def scrape_page(
        self,
        url: str,
        selector: str = "body",
        wait_for: Optional[str] = None,
        take_screenshot: bool = True
    ) -> ScrapeResult:
        """
        Scrape a single web page with retry logic and error handling.

        Args:
            url: URL to scrape
            selector: CSS selector for content extraction
            wait_for: Optional CSS selector to wait for before extraction
            take_screenshot: Whether to take a screenshot

        Returns:
            ScrapeResult object with extracted data

        Raises:
            ScraperError: For various scraping failures
        """
        self._setup_logging()

        # Input validation
        url = self._validate_url(url)
        selector = self._validate_selector(selector)

        start_time = time.time()
        last_exception = None

        for attempt in range(self.config.max_retries):
            try:
                self.logger.info(f"Scraping {url} (attempt {attempt + 1}/{self.config.max_retries})")

                context = self._create_browser_context()
                page = context.new_page()

                # Navigate with timeout
                page.goto(url, timeout=self.config.browser_timeout)
                page.wait_for_load_state("networkidle")

                # Wait for specific element if requested
                if wait_for:
                    self.logger.debug(f"Waiting for selector: {wait_for}")
                    page.wait_for_selector(wait_for, timeout=self.config.element_timeout)

                # Extract content
                title = page.title()
                text_content, html_content = self._extract_content(page, selector)

                # Limit text length
                if len(text_content) > self.config.max_text_length:
                    text_content = text_content[:self.config.max_text_length]
                    self.logger.warning(f"Text content truncated to {self.config.max_text_length} characters")

                # Take screenshot if requested
                screenshot_path = None
                if take_screenshot:
                    screenshot_path = self._take_screenshot(page, url)

                page.close()

                response_time = time.time() - start_time

                return ScrapeResult(
                    url=url,
                    title=title,
                    selector=selector,
                    text=text_content,
                    html_length=len(html_content),
                    screenshot_path=screenshot_path,
                    success=True,
                    response_time=response_time,
                    timestamp=start_time
                )

            except Exception as e:
                last_exception = e
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")

                if attempt < self.config.max_retries - 1:
                    delay = self.config.retry_delay * (2 ** attempt)  # Exponential backoff
                    self.logger.info(f"Retrying in {delay:.1f} seconds...")
                    time.sleep(delay)

                if 'page' in locals():
                    try:
                        page.close()
                    except:
                        pass

        # All retries failed
        error_msg = f"Failed after {self.config.max_retries} attempts: {last_exception}"
        self.logger.error(error_msg)

        return ScrapeResult(
            url=url,
            title="",
            selector=selector,
            text="",
            html_length=0,
            success=False,
            error_message=error_msg,
            response_time=time.time() - start_time,
            timestamp=start_time
        )

    def scrape_multiple_pages(
        self,
        urls: List[str],
        selector: str = "body",
        wait_for: Optional[str] = None,
        take_screenshots: bool = True,
        max_concurrent: int = 3
    ) -> List[ScrapeResult]:
        """
        Scrape multiple pages concurrently.

        Args:
            urls: List of URLs to scrape
            selector: CSS selector for content extraction
            wait_for: Optional CSS selector to wait for
            take_screenshots: Whether to take screenshots
            max_concurrent: Maximum concurrent scraping operations

        Returns:
            List of ScrapeResult objects
        """
        async def scrape_async():
            semaphore = asyncio.Semaphore(max_concurrent)

            async def scrape_with_semaphore(url):
                async with semaphore:
                    # Run sync scraping in thread pool to avoid blocking
                    loop = asyncio.get_event_loop()
                    return await loop.run_in_executor(
                        None,
                        lambda: self.scrape_page(url, selector, wait_for, take_screenshots)
                    )

            tasks = [scrape_with_semaphore(url) for url in urls]
            return await asyncio.gather(*tasks, return_exceptions=True)

        # Run async scraping
        results = asyncio.run(scrape_async())

        # Handle exceptions in results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Async scraping failed for {urls[i]}: {result}")
                processed_results.append(ScrapeResult(
                    url=urls[i],
                    title="",
                    selector=selector,
                    text="",
                    html_length=0,
                    success=False,
                    error_message=str(result),
                    timestamp=time.time()
                ))
            else:
                processed_results.append(result)

        return processed_results

    def close(self):
        """Clean up browser resources."""
        if self._context:
            try:
                self._context.close()
            except:
                pass
            self._context = None

        if self._browser:
            try:
                self._browser.close()
            except:
                pass
            self._browser = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Legacy functions for backward compatibility
def scrape_page(url: str, selector: str = "body",
                wait_for: str = None, output_file: str = None) -> Dict:
    """
    Legacy function for backward compatibility.
    Use WebScraper class for new code.
    """
    config = ScraperConfig()
    with WebScraper(config) as scraper:
        result = scraper.scrape_page(url, selector, wait_for, take_screenshot=True)

        # Save to file if requested
        if output_file:
            result.save_to_file(output_file)

        return result.to_dict()


def scrape_multiple_pages(urls: List[str], selector: str = "body") -> List[Dict]:
    """
    Legacy function for backward compatibility.
    Use WebScraper class for new code.
    """
    config = ScraperConfig()
    with WebScraper(config) as scraper:
        results = scraper.scrape_multiple_pages(urls, selector)
        return [result.to_dict() for result in results]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Enhanced Web Scraping with Playwright",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python web_scraper.py https://example.com
  python web_scraper.py https://example.com --selector "article" --output result.json
  python web_scraper.py https://example.com --wait-for ".content-loaded"
        """
    )

    parser.add_argument("url", help="URL to scrape")
    parser.add_argument(
        "--selector",
        default="body",
        help="CSS selector for content extraction (default: body)"
    )
    parser.add_argument(
        "--wait-for",
        help="CSS selector to wait for before extraction"
    )
    parser.add_argument(
        "--output",
        help="Output JSON file path"
    )
    parser.add_argument(
        "--no-screenshot",
        action="store_true",
        help="Disable screenshot capture"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    try:
        # Use new WebScraper class
        config = ScraperConfig()
        with WebScraper(config) as scraper:
            result = scraper.scrape_page(
                url=args.url,
                selector=args.selector,
                wait_for=args.wait_for,
                take_screenshot=not args.no_screenshot
            )

            # Display results
            print(f"\n{'='*50}")
            print(f"URL: {result.url}")
            print(f"Title: {result.title}")
            print(f"Success: {result.success}")
            if result.error_message:
                print(f"Error: {result.error_message}")
            print(f"Response Time: {result.response_time:.2f}s")
            print(f"Text Length: {len(result.text)} characters")
            print(f"HTML Length: {result.html_length}")
            if result.screenshot_path:
                print(f"Screenshot: {result.screenshot_path}")
            print(f"{'='*50}")

            # Save to file if requested
            if args.output:
                result.save_to_file(args.output)
                print(f"Results saved to: {args.output}")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
