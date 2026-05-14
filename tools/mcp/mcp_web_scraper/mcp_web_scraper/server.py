"""Web Scraper MCP Server - Scrapy-based web scraping"""

import argparse
import asyncio
import time
from collections import deque
from typing import Any, Dict, List, Set, Tuple
from urllib.parse import urldefrag, urljoin, urlparse
from urllib.request import Request, urlopen

from twisted.internet import asyncioreactor

# Configure asyncioreactor before importing Scrapy/Twisted reactor users
try:
    asyncioreactor.install()
except Exception:
    pass

import scrapy
from scrapy.utils.log import configure_logging
from parsel import Selector

from mcp_core.base_server import BaseMCPServer
from mcp_core.utils import setup_logging


def is_xpath_selector(selector: str) -> bool:
    """Return True when selector appears to be XPath, False for CSS."""
    value = selector.strip()
    return (
        value.startswith("/")
        or value.startswith("./")
        or value.startswith("../")
        or value.startswith("(")
        or "::" in value
    )


class SinglePageSpider(scrapy.Spider):
    """Spider for extracting data from a single page"""

    name = "single_page_spider"
    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": 1,
        "DOWNLOAD_DELAY": 0,
        "USER_AGENT": "mcp-web-scraper/1.0",
    }

    def __init__(
        self,
        url: str,
        selectors: Dict[str, str],
        output_items: List[Dict[str, Any]] = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.url = url
        self.selectors = selectors
        self.items = output_items if output_items is not None else []

    def start_requests(self):
        yield scrapy.Request(self.url, callback=self.parse, errback=self.errback)

    def parse(self, response):
        """Extract data from response"""
        item = {}
        for key, selector in self.selectors.items():
            try:
                if is_xpath_selector(selector):
                    values = response.xpath(selector).getall()
                else:
                    values = response.css(selector).getall()

                if values:
                    item[key] = values if len(values) > 1 else values[0]
                else:
                    item[key] = None
            except Exception as e:
                self.logger.warning(f"Error extracting {key}: {e}")
                item[key] = None

        self.items.append(item)

    def errback(self, failure):
        """Handle errors"""
        self.logger.error(f"Error fetching {self.url}: {failure.value}")


class CrawlSpider(scrapy.Spider):
    """Spider for crawling multiple pages with bounded limits"""

    name = "crawl_spider"
    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": 4,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "DOWNLOAD_DELAY": 0.5,
        "USER_AGENT": "mcp-web-scraper/1.0",
        "AUTOTHROTTLE_ENABLED": False,
    }

    def __init__(
        self,
        start_url: str,
        follow_links: str,
        selectors: Dict[str, str],
        allowed_domains: List[str] = None,
        max_pages: int = 10,
        max_depth: int = 2,
        output_items: List[Dict[str, Any]] = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.start_url = start_url
        self.follow_links = follow_links
        self.selectors = selectors
        self.allowed_domains = allowed_domains or [urlparse(start_url).netloc]
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.items = output_items if output_items is not None else []
        self.pages_crawled = 0
        self.errors = 0

    def start_requests(self):
        yield scrapy.Request(self.start_url, callback=self.parse, meta={"depth": 0}, errback=self.errback)

    def parse(self, response):
        """Extract data and follow links"""
        depth = response.meta.get("depth", 0)

        item = {}
        for key, selector in self.selectors.items():
            try:
                if is_xpath_selector(selector):
                    values = response.xpath(selector).getall()
                else:
                    values = response.css(selector).getall()

                if values:
                    item[key] = values if len(values) > 1 else values[0]
                else:
                    item[key] = None
            except Exception as e:
                self.logger.warning(f"Error extracting {key}: {e}")
                item[key] = None

        self.items.append(item)
        self.pages_crawled += 1

        if self.pages_crawled >= self.max_pages:
            return

        if depth < self.max_depth:
            try:
                for link in response.css(self.follow_links).getall():
                    if isinstance(link, str) and "href=" in link:
                        import re

                        href_match = re.search(r'href=["\']([^"\']+)["\']', link)
                        if href_match:
                            url = href_match.group(1)
                            url = urljoin(response.url, url)
                            domain = urlparse(url).netloc
                            if domain in self.allowed_domains:
                                yield scrapy.Request(
                                    url,
                                    callback=self.parse,
                                    meta={"depth": depth + 1},
                                    errback=self.errback,
                                    dont_obey_robotstxt=False,
                                )
            except Exception as e:
                self.logger.warning(f"Error following links: {e}")

    def errback(self, failure):
        """Handle errors"""
        self.logger.error(f"Error in crawl: {failure.value}")
        self.errors += 1


class WebScraperMCPServer(BaseMCPServer):
    """MCP Server for web scraping with Scrapy"""

    def __init__(self):
        super().__init__(
            name="Web Scraper MCP Server",
            version="1.0.0",
            port=8013,
        )
        self.logger = setup_logging("WebScraperMCP")
        configure_logging({"LOG_LEVEL": "ERROR"})
        self.logger.info("Web Scraper MCP Server initialized")

    @staticmethod
    def _extract_values(selector_obj: Selector, selectors: Dict[str, str]) -> Dict[str, Any]:
        item: Dict[str, Any] = {}
        for key, selector in selectors.items():
            try:
                if is_xpath_selector(selector):
                    values = selector_obj.xpath(selector).getall()
                else:
                    values = selector_obj.css(selector).getall()
                item[key] = values if len(values) > 1 else (values[0] if values else None)
            except Exception:
                item[key] = None
        return item

    @staticmethod
    def _extract_follow_links(selector_obj: Selector, follow_links: str) -> List[str]:
        if is_xpath_selector(follow_links):
            if "@href" in follow_links:
                hrefs = selector_obj.xpath(follow_links).getall()
            else:
                hrefs = selector_obj.xpath(f"{follow_links}/@href").getall()
        else:
            if "::attr(" in follow_links:
                hrefs = selector_obj.css(follow_links).getall()
            else:
                hrefs = selector_obj.css(f"{follow_links}::attr(href)").getall()
        return [href.strip() for href in hrefs if isinstance(href, str) and href.strip()]

    @staticmethod
    def _blocking_fetch(url: str, timeout: int) -> Tuple[str, int, str]:
        req = Request(url, headers={"User-Agent": "mcp-web-scraper/1.0"})
        with urlopen(req, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            return response.geturl(), int(response.status), body

    async def _fetch_url(self, url: str, timeout: int) -> Tuple[str, int, str]:
        return await asyncio.to_thread(self._blocking_fetch, url, timeout)

    def get_tools(self) -> Dict[str, Dict[str, Any]]:
        """Return available web scraper tools"""
        return {
            "scrape_page": {
                "description": "Extract structured data from a single web page using CSS/XPath selectors",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL to scrape",
                        },
                        "selectors": {
                            "type": "object",
                            "description": "CSS or XPath selectors to extract data (key -> selector mapping)",
                            "additionalProperties": {"type": "string"},
                        },
                        "timeout": {
                            "type": "integer",
                            "default": 30,
                            "description": "Request timeout in seconds",
                        },
                    },
                    "required": ["url", "selectors"],
                },
            },
            "crawl_site": {
                "description": "Crawl a website starting from a URL with bounded limits and selector extraction",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_url": {
                            "type": "string",
                            "description": "Starting URL for crawl",
                        },
                        "follow_links": {
                            "type": "string",
                            "description": "CSS selector for links to follow",
                        },
                        "selectors": {
                            "type": "object",
                            "description": "CSS or XPath selectors to extract data from each page",
                            "additionalProperties": {"type": "string"},
                        },
                        "allowed_domains": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of allowed domains (empty = same domain)",
                        },
                        "max_pages": {
                            "type": "integer",
                            "default": 10,
                            "description": "Maximum pages to crawl",
                        },
                        "max_depth": {
                            "type": "integer",
                            "default": 2,
                            "description": "Maximum crawl depth",
                        },
                        "timeout_seconds": {
                            "type": "integer",
                            "default": 120,
                            "description": "Total crawl timeout in seconds",
                        },
                    },
                    "required": ["start_url", "follow_links", "selectors"],
                },
            },
        }

    async def scrape_page(
        self,
        url: str,
        selectors: Dict[str, str],
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """Extract structured data from a single web page."""
        start_time = time.time()
        try:
            self.logger.info("scrape_page called for URL: %s", url)
            try:
                final_url, status, html = await self._fetch_url(url, timeout)
            except asyncio.TimeoutError:
                self.logger.error("Scrape page timeout for URL: %s", url)
                return {
                    "success": False,
                    "url": url,
                    "error": f"Request timeout after {timeout} seconds",
                    "elapsed_time": time.time() - start_time,
                }
            except Exception as e:
                return {
                    "success": False,
                    "url": url,
                    "error": str(e),
                    "elapsed_time": time.time() - start_time,
                }

            data = self._extract_values(Selector(text=html), selectors)

            return {
                "success": True,
                "url": final_url,
                "status_code": status,
                "data": data,
                "elapsed_time": time.time() - start_time,
            }

        except Exception as e:
            self.logger.error("Error scraping page: %s", str(e))
            return {
                "success": False,
                "url": url,
                "error": str(e),
                "elapsed_time": time.time() - start_time,
            }

    async def crawl_site(
        self,
        start_url: str,
        follow_links: str,
        selectors: Dict[str, str],
        allowed_domains: list = None,
        max_pages: int = 10,
        max_depth: int = 2,
        timeout_seconds: int = 120,
    ) -> Dict[str, Any]:
        """Crawl a website with bounded limits."""
        start_time = time.time()
        try:
            self.logger.info("crawl_site called for start_url: %s", start_url)

            domain_allowlist: Set[str] = set(allowed_domains or [urlparse(start_url).netloc])
            queue: deque[Tuple[str, int]] = deque([(start_url, 0)])
            visited: Set[str] = set()
            items: List[Dict[str, Any]] = []
            errors = 0

            while queue and len(items) < max_pages:
                elapsed = time.time() - start_time
                if elapsed >= timeout_seconds:
                    break

                current_url, depth = queue.popleft()
                normalized_url, _ = urldefrag(current_url)
                if normalized_url in visited:
                    continue

                if urlparse(normalized_url).netloc not in domain_allowlist:
                    continue

                visited.add(normalized_url)
                remaining = max(1, int(timeout_seconds - elapsed))

                try:
                    final_url, _status, html = await self._fetch_url(normalized_url, remaining)
                except Exception:
                    errors += 1
                    continue

                selector_obj = Selector(text=html)
                extracted = self._extract_values(selector_obj, selectors)
                extracted["_url"] = final_url
                items.append(extracted)

                if depth >= max_depth:
                    continue

                for href in self._extract_follow_links(selector_obj, follow_links):
                    next_url, _ = urldefrag(urljoin(final_url, href))
                    if next_url and next_url not in visited:
                        if urlparse(next_url).netloc in domain_allowlist:
                            queue.append((next_url, depth + 1))

            elapsed = time.time() - start_time
            pages_crawled = len(items)
            return {
                "success": True,
                "start_url": start_url,
                "pages_crawled": pages_crawled,
                "items_extracted": len(items),
                "items": items,
                "stats": {
                    "elapsed_time": elapsed,
                    "items_per_page": (
                        len(items) / pages_crawled
                        if pages_crawled > 0
                        else 0
                    ),
                    "errors": errors,
                },
            }

        except Exception as e:
            self.logger.error("Error crawling site: %s", str(e))
            return {
                "success": False,
                "start_url": start_url,
                "error": str(e),
                "elapsed_time": time.time() - start_time,
            }


def main():
    """Run the Web Scraper MCP Server"""
    parser = argparse.ArgumentParser(description="Web Scraper MCP Server")
    parser.add_argument(
        "--mode",
        choices=["http", "stdio"],
        default="http",
        help="Server mode (http or stdio)",
    )
    args = parser.parse_args()

    server = WebScraperMCPServer()
    server.run(mode=args.mode)


if __name__ == "__main__":
    main()
