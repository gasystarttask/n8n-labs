"""Web scraper tools for MCP.

This module provides standalone functions that delegate to WebScraperMCPServer.
All core logic is implemented in server.py to avoid code duplication.
"""

from typing import Any, Dict, Optional, cast

from .server import WebScraperMCPServer


class _ServerHolder:
    """Holder class for singleton server instance to avoid global statement."""

    instance: Optional[WebScraperMCPServer] = None


def _get_server() -> WebScraperMCPServer:
    """Get or create the singleton server instance."""
    if _ServerHolder.instance is None:
        _ServerHolder.instance = WebScraperMCPServer()
    return _ServerHolder.instance


# Tool registry for backwards compatibility
TOOLS = {}


def register_tool(name: str):
    """Decorator to register a tool"""

    def decorator(func):
        TOOLS[name] = func
        return func

    return decorator


@register_tool("scrape_page")
async def scrape_page(
    url: str,
    selectors: Dict[str, str],
    timeout: int = 30,
) -> Dict[str, Any]:
    """Extract structured data from a single web page using CSS/XPath selectors.

    Args:
        url: URL to scrape
        selectors: CSS or XPath selectors to extract data (key -> selector mapping)
        timeout: Request timeout in seconds

    Returns:
        Dictionary with extracted data and metadata
    """
    server = _get_server()
    result = await server.scrape_page(url=url, selectors=selectors, timeout=timeout)
    return cast(Dict[str, Any], result)


@register_tool("crawl_site")
async def crawl_site(
    start_url: str,
    follow_links: str,
    selectors: Dict[str, str],
    allowed_domains: list = None,
    max_pages: int = 10,
    max_depth: int = 2,
    timeout_seconds: int = 120,
) -> Dict[str, Any]:
    """Crawl a website starting from a URL with bounded limits and selector extraction.

    Args:
        start_url: Starting URL for crawl
        follow_links: CSS selector for links to follow
        selectors: CSS or XPath selectors to extract data from each page
        allowed_domains: List of allowed domains (empty = same domain)
        max_pages: Maximum pages to crawl
        max_depth: Maximum crawl depth
        timeout_seconds: Total crawl timeout in seconds

    Returns:
        Dictionary with crawl results, items extracted, and stats
    """
    server = _get_server()
    result = await server.crawl_site(
        start_url=start_url,
        follow_links=follow_links,
        selectors=selectors,
        allowed_domains=allowed_domains,
        max_pages=max_pages,
        max_depth=max_depth,
        timeout_seconds=timeout_seconds,
    )
    return cast(Dict[str, Any], result)
