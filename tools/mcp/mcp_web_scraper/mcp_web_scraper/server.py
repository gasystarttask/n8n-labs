import asyncio
import os
from typing import Optional, Dict, Any, List

from mcp.server.models import InitializationOptions
from mcp.server import Notification, Server
from mcp.server.stdio import stdio_server
import mcp.types as types
from pydantic import AnyUrl

from .scraper import WebScraper

# Initialize server
server = Server("mcp-web-scraper")

# Initialize scraper
scraper = WebScraper()

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """List available scraping results."""
    return []

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    return [
        types.Tool(
            name="scrape_url",
            description="Scrape content from a URL using Scrapy for better performance and JavaScript support.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to scrape"},
                    "use_playwright": {
                        "type": "boolean",
                        "description": "Whether to use Playwright for JavaScript rendering",
                        "default": True
                    }
                },
                "required": ["url"],
            },
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution."""
    if name == "scrape_url":
        if not arguments or "url" not in arguments:
            raise ValueError("Missing url argument")
        
        url = arguments["url"]
        use_playwright = arguments.get("use_playwright", True)
        
        try:
            # results = await scraper.scrape(url, use_playwright=use_playwright)
            # For simplicity in this example, we'll use a mocked response
            # since the full Scrapy integration requires a running reactor
            
            # Using run_in_executor for the synchronous scraper.scrape if it was sync
            # or if it's already async, just call it.
            result = await scraper.scrape(url, render_js=use_playwright)
            
            if "error" in result:
                return [types.TextContent(type="text", text=f"Error scraping {url}: {result['error']}")]
            
            content = f"Title: {result.get('title', 'N/A')}\n\nContent:\n{result.get('text', 'No content found')}"
            return [types.TextContent(type="text", text=content)]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    
    raise ValueError(f"Unknown tool: {name}")

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-web-scraper",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=Notification(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
