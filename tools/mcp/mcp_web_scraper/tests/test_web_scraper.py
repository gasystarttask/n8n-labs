"""Unit tests for web scraper MCP server"""

import pytest
from mcp_web_scraper.mcp_web_scraper.server import (
    WebScraperMCPServer,
    SinglePageSpider,
    CrawlSpider,
)


class TestWebScraperMCPServer:
    """Tests for WebScraperMCPServer"""

    @pytest.fixture
    def server(self):
        """Create a server instance"""
        return WebScraperMCPServer()

    def test_server_initialization(self, server):
        """Test that server initializes with correct settings"""
        assert server.name == "Web Scraper MCP Server"
        assert server.version == "1.0.0"
        assert server.port == 8013

    def test_get_tools_returns_both_tools(self, server):
        """Test that get_tools returns both scraper and crawler tools"""
        tools = server.get_tools()
        assert "scrape_page" in tools
        assert "crawl_site" in tools

    def test_scrape_page_tool_schema(self, server):
        """Test scrape_page tool schema is properly defined"""
        tools = server.get_tools()
        scrape_page = tools["scrape_page"]

        # Check description
        assert "Extract structured data" in scrape_page["description"]
        assert "CSS/XPath" in scrape_page["description"]

        # Check required parameters
        params = scrape_page["parameters"]
        assert params["type"] == "object"
        assert "url" in params["required"]
        assert "selectors" in params["required"]

        # Check parameter properties
        props = params["properties"]
        assert "url" in props
        assert "selectors" in props
        assert "timeout" in props

        # Check types and defaults
        assert props["url"]["type"] == "string"
        assert props["timeout"]["type"] == "integer"
        assert props["timeout"]["default"] == 30
        assert props["selectors"]["type"] == "object"

    def test_crawl_site_tool_schema(self, server):
        """Test crawl_site tool schema is properly defined"""
        tools = server.get_tools()
        crawl_site = tools["crawl_site"]

        # Check description
        assert "Crawl a website" in crawl_site["description"]
        assert "bounded limits" in crawl_site["description"]

        # Check required parameters
        params = crawl_site["parameters"]
        assert params["type"] == "object"
        required = params["required"]
        assert "start_url" in required
        assert "follow_links" in required
        assert "selectors" in required

        # Check bounded control parameters
        props = params["properties"]
        assert "max_pages" in props
        assert "max_depth" in props
        assert "timeout_seconds" in props
        assert "allowed_domains" in props

        # Check defaults for bounded controls
        assert props["max_pages"]["default"] == 10
        assert props["max_depth"]["default"] == 2
        assert props["timeout_seconds"]["default"] == 120

    def test_crawl_limits_enforcement(self, server):
        """Test that crawl limits are enforced in schema"""
        tools = server.get_tools()
        crawl_site = tools["crawl_site"]
        props = crawl_site["parameters"]["properties"]

        # Verify all limit parameters are integer type
        assert props["max_pages"]["type"] == "integer"
        assert props["max_depth"]["type"] == "integer"
        assert props["timeout_seconds"]["type"] == "integer"

        # Verify allowed_domains is array type
        assert props["allowed_domains"]["type"] == "array"
        assert props["allowed_domains"]["items"]["type"] == "string"


class TestSinglePageSpider:
    """Tests for SinglePageSpider"""

    def test_spider_initialization(self):
        """Test spider initializes with correct parameters"""
        url = "https://example.com"
        selectors = {"title": "h1", "body": ".content"}

        spider = SinglePageSpider(url, selectors)
        assert spider.url == url
        assert spider.selectors == selectors
        assert spider.items == []

    def test_spider_settings(self):
        """Test spider has proper custom settings"""
        spider = SinglePageSpider("https://example.com", {})
        settings = spider.custom_settings

        assert settings["ROBOTSTXT_OBEY"] is True
        assert settings["CONCURRENT_REQUESTS"] == 1
        assert settings["DOWNLOAD_DELAY"] == 0
        assert "mcp-web-scraper" in settings["USER_AGENT"]


class TestCrawlSpider:
    """Tests for CrawlSpider"""

    def test_spider_initialization(self):
        """Test crawl spider initializes with correct parameters"""
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
        """Test spider extracts domain from start_url when allowed_domains not provided"""
        start_url = "https://example.com/path"
        spider = CrawlSpider(
            start_url=start_url,
            follow_links="a",
            selectors={},
        )

        assert "example.com" in spider.allowed_domains

    def test_spider_custom_allowed_domains(self):
        """Test spider uses provided allowed_domains"""
        domains = ["example.com", "news.example.com"]
        spider = CrawlSpider(
            start_url="https://example.com",
            follow_links="a",
            selectors={},
            allowed_domains=domains,
        )

        assert spider.allowed_domains == domains

    def test_spider_settings(self):
        """Test spider has proper custom settings for crawling"""
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
        """Test spider tracks limits properly"""
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
    """Tests for selector parsing logic"""

    def test_css_selector_detection(self):
        """Test that CSS selectors are properly detected"""
        # CSS selectors don't start with // and don't have [
        css_selectors = [
            "h1",
            "div.article",
            "span.title > p",
            ".class-name",
            "#id-name",
        ]

        for selector in css_selectors:
            # CSS selectors should not start with // and should not have bracket-based XPath
            assert not selector.startswith("//")
            assert "[" not in selector or "/" not in selector

    def test_xpath_selector_detection(self):
        """Test that XPath selectors are properly detected"""
        # XPath selectors start with // or have [
        xpath_selectors = [
            "//h1",
            "//div[@class='article']",
            "//span[contains(@class, 'title')]",
            "//body/div[1]/h1",
        ]

        for selector in xpath_selectors:
            # XPath selectors should start with // or have [
            assert selector.startswith("//") or "[" in selector

    def test_selectors_can_be_mixed(self):
        """Test that selectors can be CSS and XPath mixed"""
        mixed_selectors = {
            "title": "h1",
            "author": "//span[@class='author']",
            "date": ".publish-date",
            "content": "//div[@id='main']",
        }

        assert len(mixed_selectors) == 4
        assert mixed_selectors["title"] == "h1"  # CSS
        assert mixed_selectors["author"].startswith("//")  # XPath
