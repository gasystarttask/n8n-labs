"""Scaffold tests for web scraper MCP server."""

import pytest

from mcp_web_scraper.server import WebScraperMCPServer


def test_server_initialization():
    """Server should initialize with expected metadata."""
    server = WebScraperMCPServer()
    assert server.name == "Web Scraper MCP Server"
    assert server.version == "1.0.0"
    assert server.port == 8013


def test_tools_hidden_by_default(monkeypatch):
    """Scaffold branch should not expose non-functional tools by default."""
    monkeypatch.delenv("MCP_WEB_SCRAPER_ENABLE_STUB_TOOLS", raising=False)
    server = WebScraperMCPServer()
    assert server.get_tools() == {}


def test_tool_contracts_exposed_with_flag(monkeypatch):
    """Tool contracts should be visible only when explicitly enabled."""
    monkeypatch.setenv("MCP_WEB_SCRAPER_ENABLE_STUB_TOOLS", "true")
    server = WebScraperMCPServer()
    tools = server.get_tools()

    assert "scrape_page" in tools
    assert "crawl_site" in tools

    scrape_required = tools["scrape_page"]["parameters"]["required"]
    crawl_required = tools["crawl_site"]["parameters"]["required"]
    assert scrape_required == ["url", "selectors"]
    assert crawl_required == ["start_url", "follow_links", "selectors"]


@pytest.mark.asyncio
async def test_scrape_page_scaffold_response():
    """Scaffold execution should return a stable not-implemented payload."""
    server = WebScraperMCPServer()
    result = await server.scrape_page("https://example.com", {"title": "h1"})

    assert result["success"] is False
    assert "Not yet implemented" in result["error"]


@pytest.mark.asyncio
async def test_crawl_site_scaffold_response():
    """Scaffold execution should return a stable not-implemented payload."""
    server = WebScraperMCPServer()
    result = await server.crawl_site(
        start_url="https://example.com",
        follow_links="a",
        selectors={"title": "h1"},
    )

    assert result["success"] is False
    assert "Not yet implemented" in result["error"]
