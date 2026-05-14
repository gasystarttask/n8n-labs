"""Integration test script for web scraper MCP server

This script validates the server's core endpoints and tool execution.
Run this after starting the server with: python -m mcp_web_scraper.server --mode http
"""

import asyncio
import sys

try:
    import httpx
except ImportError:
    print("Error: httpx is required. Install with: pip install httpx")
    sys.exit(1)


class WebScraperMCPTester:
    """Test client for Web Scraper MCP Server"""

    def __init__(self, base_url: str = "http://localhost:8013"):
        self.base_url = base_url
        self.client = httpx.Client()
        self.results = []

    def log_test(self, name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "\u2713" if passed else "\u2717"
        print(f"{status} {name}")
        if details:
            print(f"  {details}")
        self.results.append((name, passed))

    async def test_health_endpoint(self):
        """Test /health endpoint"""
        try:
            response = self.client.get(f"{self.base_url}/health")
            passed = response.status_code == 200
            self.log_test("Health endpoint", passed, f"Status: {response.status_code}")
            return passed
        except Exception as e:
            self.log_test("Health endpoint", False, f"Error: {e}")
            return False

    async def test_tools_endpoint(self):
        """Test /mcp/tools endpoint"""
        try:
            response = self.client.get(f"{self.base_url}/mcp/tools")
            passed = response.status_code == 200
            if passed:
                data = response.json()
                has_tools = "tools" in data
                passed = has_tools and len(data.get("tools", {})) >= 2
                tools = list(data.get("tools", {}).keys())
                self.log_test(
                    "Tools endpoint",
                    passed,
                    f"Found tools: {', '.join(tools) if tools else 'none'}",
                )
            else:
                self.log_test("Tools endpoint", False, f"Status: {response.status_code}")
            return passed
        except Exception as e:
            self.log_test("Tools endpoint", False, f"Error: {e}")
            return False

    async def test_scrape_page_schema(self):
        """Verify scrape_page tool has correct schema"""
        try:
            response = self.client.get(f"{self.base_url}/mcp/tools")
            if response.status_code != 200:
                self.log_test("scrape_page schema", False, "Could not fetch tools")
                return False

            tools = response.json().get("tools", {})
            scrape_page = tools.get("scrape_page", {})
            params = scrape_page.get("parameters", {})
            props = params.get("properties", {})

            checks = [
                ("url" in props, "Has url parameter"),
                ("selectors" in props, "Has selectors parameter"),
                ("timeout" in props, "Has timeout parameter"),
                ("url" in params.get("required", []), "url is required"),
                ("selectors" in params.get("required", []), "selectors is required"),
            ]

            all_passed = all(check[0] for check in checks)
            details = "; ".join(
                [f"✓ {msg}" if passed else f"✗ {msg}" for passed, msg in checks]
            )
            self.log_test("scrape_page schema", all_passed, details)
            return all_passed
        except Exception as e:
            self.log_test("scrape_page schema", False, f"Error: {e}")
            return False

    async def test_crawl_site_schema(self):
            crawl_site = tools.get("crawl_site", {})
                ("max_pages" in props, "Has max_pages limit"),
            ]
        """Unit tests for web scraper MCP server"""

        import pytest

        server_module = pytest.importorskip("mcp_web_scraper.server")
        WebScraperMCPServer = server_module.WebScraperMCPServer
        SinglePageSpider = server_module.SinglePageSpider
        CrawlSpider = server_module.CrawlSpider


        class TestWebScraperMCPServer:
            """Tests for WebScraperMCPServer"""

            @pytest.fixture
            def server(self):
                """Create a server instance"""
                return WebScraperMCPServer()

            def test_server_initialization(self, server):
    tester = WebScraperMCPTester()

    # Run tests
    try:
        await tester.test_health_endpoint()
        await tester.test_tools_endpoint()
        await tester.test_scrape_page_schema()
        await tester.test_crawl_site_schema()
        await tester.test_execute_endpoint()

        success = tester.print_summary()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)
    finally:
        tester.client.close()
>>>>>>> origin/feature/issue-3-tests-docs


if __name__ == "__main__":
    asyncio.run(main())
