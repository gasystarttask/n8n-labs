# MCP Web Scraper

A Model Context Protocol (MCP) server for efficient web scraping using Scrapy with bounded crawl controls and safety limits.

## Features

- **Single Page Scraping** (`scrape_page`): Extract structured data from a single URL using CSS or XPath selectors
- **Site Crawling** (`crawl_site`): Crawl multiple pages with configurable limits
- **Bounded Limits**: Control crawl behavior with max pages, depth, and timeout settings
- **Safe Defaults**: robots.txt respect, domain restrictions, request throttling
- **Efficient Extraction**: Support for both CSS and XPath selectors for data extraction

## Installation

```bash
pip install mcp-web-scraper
```

## Running the Server

HTTP mode (default):
```bash
python -m mcp_web_scraper.server --mode http
```

Stdio mode:
```bash
python -m mcp_web_scraper.server --mode stdio
```

## Tool Usage

### scrape_page

Extract structured data from a single web page.

**Parameters:**
- `url` (string, required): URL to scrape
- `selectors` (object, required): CSS or XPath selectors for data extraction (key -> selector mapping)
- `timeout` (integer, optional): Request timeout in seconds (default: 30)

**Example:**
```json
{
  "url": "https://example.com",
  "selectors": {
    "title": "h1",
    "description": ".description",
    "links": "a::attr(href)"
  },
  "timeout": 30
}
```

### crawl_site

Crawl a website starting from a URL with bounded limits.

**Parameters:**
- `start_url` (string, required): Starting URL for crawl
- `follow_links` (string, required): CSS selector for links to follow
- `selectors` (object, required): CSS or XPath selectors for data extraction from each page
- `allowed_domains` (array, optional): List of allowed domains (empty = same domain)
- `max_pages` (integer, optional): Maximum pages to crawl (default: 10)
- `max_depth` (integer, optional): Maximum crawl depth (default: 2)
- `timeout_seconds` (integer, optional): Total crawl timeout in seconds (default: 120)

**Example:**
```json
{
  "start_url": "https://example.com",
  "follow_links": "a[href*='/articles/']",
  "selectors": {
    "title": "h2",
    "date": ".publish-date",
    "content": "article"
  },
  "max_pages": 20,
  "max_depth": 3
}
```

## Configuration

Environment variables:
- `MCP_LOG_LEVEL`: Log level (default: INFO)

## API Endpoints

- `GET /health`: Health check
- `GET /mcp/tools`: List available tools and their schemas
- `POST /mcp/execute`: Execute a tool

## Safety Features

- **Domain Whitelisting**: Restrict crawling to specific domains
- **Crawl Limits**: Enforce max pages and depth limits
- **Timeouts**: Global timeout for crawl operations
- **robots.txt Respect**: Honor robots.txt rules (configurable)
- **Request Throttling**: Configurable delays between requests
- **AutoThrottle**: Optional dynamic throttling based on server response

## Architecture

This server follows the standard MCP architecture:
- Extends `BaseMCPServer` from `mcp_core`
- HTTP mode for integration with agents and services
- Clean separation between server logic (server.py) and tool wrappers (tools.py)

See [docs/README.md](docs/README.md) for detailed architecture and operational notes.
