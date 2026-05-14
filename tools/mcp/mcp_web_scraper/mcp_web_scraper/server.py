"""Web Scraper MCP Server - Scrapy-based web scraping"""

import argparse
import os
from typing import Any, Dict

from mcp_core.base_server import BaseMCPServer
from mcp_core.utils import setup_logging


class WebScraperMCPServer(BaseMCPServer):
    """MCP Server for web scraping with Scrapy"""

    def __init__(self):
        super().__init__(
            name="Web Scraper MCP Server",
            version="1.0.0",
            port=8013,
        )
        self.enable_stub_tools = os.getenv("MCP_WEB_SCRAPER_ENABLE_STUB_TOOLS", "false").lower() == "true"
        self.logger = setup_logging("WebScraperMCP")
        self.logger.info("Web Scraper MCP Server initialized")

    def get_tools(self) -> Dict[str, Dict[str, Any]]:
        """Return available tools.

        During scaffold phase, tool contracts are hidden by default to avoid
        exposing non-functional runtime behavior. Set
        MCP_WEB_SCRAPER_ENABLE_STUB_TOOLS=true to surface contracts explicitly.
        """
        if not self.enable_stub_tools:
            return {}
        return self._tool_contracts()

    def _tool_contracts(self) -> Dict[str, Dict[str, Any]]:
        """Return scaffolded tool schemas."""
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
    # Tool Implementations (stub methods for now)
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
        self.logger.info("scrape_page called for URL: %s", url)
        # Scaffold-only implementation; runtime is added in Issue #5.
        return {
            "success": False,
            "error": "Not yet implemented - awaiting Issue #5 (Scrapy runtime implementation)",
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
        self.logger.info("crawl_site called for start_url: %s", start_url)
        # Scaffold-only implementation; runtime is added in Issue #5.
        return {
            "success": False,
            "error": "Not yet implemented - awaiting Issue #5 (Scrapy runtime implementation)",
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
