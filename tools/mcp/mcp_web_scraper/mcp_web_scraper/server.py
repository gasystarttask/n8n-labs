"""Web Scraper MCP Server - Scrapy-based web scraping"""

import argparse
import asyncio
import time
from typing import Any, Dict, List
from urllib.parse import urljoin, urlparse

import scrapy
from scrapy.crawler import CrawlerRunner
from scrapy.utils.defer import deferred_to_future
from scrapy.utils.log import configure_logging
from twisted.internet import asyncioreactor

from mcp_core.base_server import BaseMCPServer
from mcp_core.utils import setup_logging

# Configure asyncioreactor before importing reactor
try:
    asyncioreactor.install()
except Exception:
    pass


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

                # Clean up HTML tags if present
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

        # Extract data
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

        # Stop if reached max pages
        if self.pages_crawled >= self.max_pages:
            return

        # Follow links if not at max depth
        if depth < self.max_depth:
            try:
                for link in response.css(self.follow_links).getall():
                    # Extract href from link
                    if isinstance(link, str) and "href=" in link:
                        import re
                        href_match = re.search(r'href=["\']([^"\']+ )["\']', link)
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
        self._single_page_runner = CrawlerRunner(
            {
                "CONCURRENT_REQUESTS": 1,
                "DOWNLOAD_DELAY": 0,
                "USER_AGENT": "mcp-web-scraper/1.0",
                "ROBOTSTXT_OBEY": True,
            }
        )
        self._crawl_runner = CrawlerRunner(
            {
                "CONCURRENT_REQUESTS": 4,
                "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
                "DOWNLOAD_DELAY": 0.5,
                "USER_AGENT": "mcp-web-scraper/1.0",
                "ROBOTSTXT_OBEY": True,
            }
        )
        self.logger.info("Web Scraper MCP Server initialized")

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

    # =========================================================================
    # Tool Implementations
    # =========================================================================

    async def scrape_page(
        self,
        url: str,
        selectors: Dict[str, str],
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """Extract structured data from a single web page.

        Args:
            url: URL to scrape
            selectors: CSS or XPath selectors mapping
            timeout: Request timeout in seconds

        Returns:
            Dictionary with extracted data
        """
        start_time = time.time()
        try:
            self.logger.info("scrape_page called for URL: %s", url)

            items: List[Dict[str, Any]] = []
            deferred = self._single_page_runner.crawl(
                SinglePageSpider,
                url=url,
                selectors=selectors,
                output_items=items,
            )

            try:
                await asyncio.wait_for(
                    deferred_to_future(deferred),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                self.logger.error("Scrape page timeout for URL: %s", url)
                return {
                    "success": False,
                    "url": url,
                    "error": f"Request timeout after {timeout} seconds",
                    "elapsed_time": time.time() - start_time,
                }

            return {
                "success": True,
                "url": url,
                "data": items[0] if items else {},
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
        """Crawl a website with bounded limits.

        Args:
            start_url: Starting URL for crawl
            follow_links: CSS selector for links to follow
            selectors: CSS or XPath selectors for data extraction
            allowed_domains: List of allowed domains
            max_pages: Maximum pages to crawl
            max_depth: Maximum crawl depth
            timeout_seconds: Total timeout in seconds

        Returns:
            Dictionary with crawl results
        """
        start_time = time.time()
        try:
            self.logger.info("crawl_site called for start_url: %s", start_url)

            if not allowed_domains:
                allowed_domains = [urlparse(start_url).netloc]

            items: List[Dict[str, Any]] = []
            spider = CrawlSpider(
                start_url=start_url,
                follow_links=follow_links,
                selectors=selectors,
                allowed_domains=allowed_domains,
                max_pages=max_pages,
                max_depth=max_depth,
                output_items=items,
            )
            deferred = self._crawl_runner.crawl(spider)
            try:
                await asyncio.wait_for(
                    deferred_to_future(deferred),
                    timeout=timeout_seconds,
                )
            except asyncio.TimeoutError:
                self.logger.warning("Crawl site timeout for URL: %s", start_url)

            elapsed = time.time() - start_time
            return {
                "success": True,
                "start_url": start_url,
                "pages_crawled": spider.pages_crawled,
                "items_extracted": len(items),
                "items": items,
                "stats": {
                    "elapsed_time": elapsed,
                    "items_per_page": (
                        len(items) / spider.pages_crawled
                        if spider.pages_crawled > 0
                        else 0
                    ),
                    "errors": spider.errors,
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
