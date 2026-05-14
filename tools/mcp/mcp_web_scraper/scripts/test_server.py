"""Scaffold helper for web scraper MCP server.

This script intentionally does not validate tool execution in scaffold phase.
Runtime verification is added in Issue #3.
"""

import asyncio
import sys


async def main():
    """Print scaffold testing guidance."""
    print("Web Scraper MCP Server Scaffold Script")
    print("Scaffold phase: runtime integration checks are deferred to Issue #3")
    print("To inspect tool contracts, set MCP_WEB_SCRAPER_ENABLE_STUB_TOOLS=true")


if __name__ == "__main__":
    asyncio.run(main())
