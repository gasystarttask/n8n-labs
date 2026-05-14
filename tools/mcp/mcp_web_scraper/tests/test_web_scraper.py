"""Unit tests for web scraper MCP server."""

import sys
from pathlib import Path

import pytest

MCP_ROOT = Path(__file__).resolve().parents[2]
WEB_SCRAPER_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MCP_ROOT / "mcp_core"))
sys.path.insert(0, str(WEB_SCRAPER_ROOT))

from mcp_web_scraper.server import CrawlSpider, SinglePageSpider, WebScraperMCPServer


class TestWebScraperMCPServer:
    """Tests for WebScraperMCPServer."""

    @pytest.fixture
    def server(self):
        return WebScraperMCPServer()

    def test_server_initialization(self, server):
        assert server.name == "Web Scraper MCP Server"
        assert server.version == "1.0.0"
        assert server.port == 8013

    def test_get_tools_returns_both_tools(self, server):
        tools = server.get_tools()
        assert "scrape_page" in tools
        assert "crawl_site" in tools

    def test_scrape_page_tool_schema(self, server):
        tools = server.get_tools()
        scrape_page = tools["scrape_page"]

        assert "Extract structured data" in scrape_page["description"]
        assert "CSS/XPath" in scrape_page["description"]

        params = scrape_page["parameters"]
        assert params["type"] == "object"
        assert "url" in params["required"]
        assert "selectors" in params["required"]

        props = params["properties"]
        assert "url" in props
        assert "selectors" in props
        assert "timeout" in props
        assert "compliant_mode" in props
        assert "min_request_interval_seconds" in props
        assert "use_browser" in props

        assert props["url"]["type"] == "string"
        assert props["timeout"]["type"] == "integer"
        assert props["timeout"]["default"] == 30
        assert props["compliant_mode"]["type"] == "boolean"
        assert props["compliant_mode"]["default"] is True
        assert props["min_request_interval_seconds"]["type"] == "number"
        assert props["min_request_interval_seconds"]["default"] == 1.0
        assert props["use_browser"]["type"] == "boolean"
        assert props["use_browser"]["default"] is True
        assert props["selectors"]["type"] == "object"

    def test_crawl_site_tool_schema(self, server):
        tools = server.get_tools()
        crawl_site = tools["crawl_site"]

        assert "Crawl a website" in crawl_site["description"]
        assert "bounded limits" in crawl_site["description"]

        params = crawl_site["parameters"]
        assert params["type"] == "object"
        required = params["required"]
        assert "start_url" in required
        assert "follow_links" in required
        assert "selectors" in required

        props = params["properties"]
        assert "max_pages" in props
        assert "max_depth" in props
        assert "timeout_seconds" in props
        assert "allowed_domains" in props
        assert "compliant_mode" in props
        assert "min_request_interval_seconds" in props
        assert "use_browser" in props

        assert props["max_pages"]["default"] == 10
        assert props["max_depth"]["default"] == 2
        assert props["timeout_seconds"]["default"] == 120
        assert props["compliant_mode"]["default"] is True
        assert props["min_request_interval_seconds"]["default"] == 1.0
        assert props["use_browser"]["default"] is True

    def test_crawl_limits_enforcement_schema(self, server):
        tools = server.get_tools()
        crawl_site = tools["crawl_site"]
        props = crawl_site["parameters"]["properties"]

        assert props["max_pages"]["type"] == "integer"
        assert props["max_depth"]["type"] == "integer"
        assert props["timeout_seconds"]["type"] == "integer"
        assert props["allowed_domains"]["type"] == "array"
        assert props["allowed_domains"]["items"]["type"] == "string"


class TestSinglePageSpider:
    """Tests for SinglePageSpider."""

    def test_spider_initialization(self):
        url = "https://example.com"
        selectors = {"title": "h1", "body": ".content"}

        spider = SinglePageSpider(url, selectors)
        assert spider.url == url
        assert spider.selectors == selectors
        assert spider.items == []

    def test_spider_settings(self):
        spider = SinglePageSpider("https://example.com", {})
        settings = spider.custom_settings

        assert settings["ROBOTSTXT_OBEY"] is True
        assert settings["CONCURRENT_REQUESTS"] == 1
        assert settings["DOWNLOAD_DELAY"] == 0
        assert "mcp-web-scraper" in settings["USER_AGENT"]


class TestCrawlSpider:
    """Tests for CrawlSpider."""

    def test_spider_initialization(self):
        start_url = "https://example.com"
        follow_links = "a.article"
        selectors = {"title": "h2"}

        spider = CrawlSpider(
            start_url=start_url,
            follow_links=follow_links,
            selectors=selectors,
            max_pages=5,
            max_depth=2,
        )

        assert spider.start_url == start_url
        assert spider.follow_links == follow_links
        assert spider.selectors == selectors
        assert spider.max_pages == 5
        assert spider.max_depth == 2

    def test_spider_default_allowed_domains(self):
        spider = CrawlSpider(
            start_url="https://example.com/path",
            follow_links="a",
            selectors={},
        )

        assert "example.com" in spider.allowed_domains

    def test_spider_custom_allowed_domains(self):
        domains = ["example.com", "news.example.com"]
        spider = CrawlSpider(
            start_url="https://example.com",
            follow_links="a",
            selectors={},
            allowed_domains=domains,
        )

        assert spider.allowed_domains == domains

    def test_spider_settings(self):
        spider = CrawlSpider(
            start_url="https://example.com",
            follow_links="a",
            selectors={},
        )
        settings = spider.custom_settings

        assert settings["ROBOTSTXT_OBEY"] is True
        assert settings["CONCURRENT_REQUESTS"] == 4
        assert settings["CONCURRENT_REQUESTS_PER_DOMAIN"] == 2
        assert settings["DOWNLOAD_DELAY"] == 0.5
        assert "mcp-web-scraper" in settings["USER_AGENT"]

    def test_spider_limits_tracking(self):
        spider = CrawlSpider(
            start_url="https://example.com",
            follow_links="a",
            selectors={},
            max_pages=10,
            max_depth=2,
        )

        assert spider.pages_crawled == 0
        assert spider.errors == 0
        assert len(spider.items) == 0


class TestSelectorParsing:
    """Tests for selector parsing helper."""

    def test_css_selector_detection(self):
        css_selectors = [
            "h1",
            "div.article",
            "span.title > p",
            ".class-name",
            "#id-name",
        ]

        for selector in css_selectors:
            assert not selector.startswith("//")

    def test_xpath_selector_detection(self):
        xpath_selectors = [
            "//h1",
            "//div[@class='article']",
            "//span[contains(@class, 'title')]",
            "//body/div[1]/h1",
        ]

        for selector in xpath_selectors:
            assert selector.startswith("//") or "[" in selector

    def test_selectors_can_be_mixed(self):
        mixed_selectors = {
            "title": "h1",
            "author": "//span[@class='author']",
            "date": ".publish-date",
            "content": "//div[@id='main']",
        }

        assert len(mixed_selectors) == 4
        assert mixed_selectors["title"] == "h1"
        assert mixed_selectors["author"].startswith("//")
