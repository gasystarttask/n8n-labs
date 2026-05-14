# Web Scraper MCP Architecture & Operations

## Overview

This document describes scaffold architecture for the Web Scraper MCP package.
In this phase, contracts and packaging are present while runtime scraping logic is deferred to Issue #5.

## Architecture

### Core Components

1. **WebScraperMCPServer** (`server.py`)
   - Extends `BaseMCPServer` from `mcp_core`
   - Implements tool schemas for `scrape_page` and `crawl_site`
  - Returns scaffold responses for tool execution until runtime is implemented
  - Can expose contracts in scaffold mode via `MCP_WEB_SCRAPER_ENABLE_STUB_TOOLS=true`

2. **Tool Wrappers** (`tools.py`)
   - Provides async function wrappers for each tool
   - Singleton `WebScraperMCPServer` instance management
   - Clean delegation to server implementation

3. **Scrapy Integration**
  - Planned for Issue #5
  - Contracts here are forward-looking and document target runtime behavior

### Planned Safety & Limits

The runtime server (Issue #5) will enforce strict bounds on crawl operations:

- **`max_pages`**: Maximum pages to crawl before stopping (default: 10)
- **`max_depth`**: Maximum link following depth from start URL (default: 2)
- **`timeout_seconds`**: Global timeout for entire crawl operation (default: 120s)
- **`allowed_domains`**: Whitelist of domains to crawl (default: same as start_url domain)
- **`CONCURRENT_REQUESTS`**: Concurrent request limit (default: 4)
- **`CONCURRENT_REQUESTS_PER_DOMAIN`**: Per-domain concurrency limit (default: 2)
- **`DOWNLOAD_DELAY`**: Delay between requests in seconds (default: 0.5s)
- **robots.txt Respect**: Enabled by default (configurable)

### Selector Support

Both CSS and XPath selectors are supported:

- **CSS Selectors**: Standard CSS3 selectors (e.g., `div.article > h2`)
- **XPath Selectors**: XPath 1.0 syntax (e.g., `//h2[@class="title"]`)
- **Attribute Extraction**: Special syntax for attributes (e.g., `a::attr(href)`)

## Tool Contracts

In scaffold mode, `GET /mcp/tools` returns an empty set unless
`MCP_WEB_SCRAPER_ENABLE_STUB_TOOLS=true` is set.
When enabled, contracts below are visible for integration planning.

## Planned Tools

### scrape_page

Extracts structured data from a **single page** without crawling.

**Input:**
```json
{
  "url": "https://example.com/article",
  "selectors": {
    "title": "h1",
    "author": ".author-name",
    "date": "span.publish-date",
    "paragraphs": "article p"
  },
  "timeout": 30
}
```

**Output:**
```json
{
  "success": true,
  "url": "https://example.com/article",
  "data": {
    "title": "Article Title",
    "author": "John Doe",
    "date": "2024-05-14",
    "paragraphs": ["Paragraph 1...", "Paragraph 2..."]
  },
  "elapsed_time": 2.34
}
```

### crawl_site

Crawls multiple pages starting from a URL, following links and extracting data.

**Input:**
```json
{
  "start_url": "https://example.com/blog",
  "follow_links": "a[href*='/article/']",
  "selectors": {
    "title": "h2.article-title",
    "excerpt": ".article-excerpt",
    "url": "a::attr(href)"
  },
  "allowed_domains": ["example.com"],
  "max_pages": 20,
  "max_depth": 3,
  "timeout_seconds": 120
}
```

**Output:**
```json
{
  "success": true,
  "start_url": "https://example.com/blog",
  "pages_crawled": 15,
  "items_extracted": 15,
  "items": [
    {
      "url": "https://example.com/article/1",
      "title": "First Article",
      "excerpt": "..."
    },
    ...
  ],
  "stats": {
    "elapsed_time": 45.2,
    "items_per_page": 1.0,
    "errors": 0
  }
}
```

## Configuration

### Environment Variables

- `MCP_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR) - default: INFO
- `MCP_SCRAPY_AUTOTHROTTLE`: Enable AutoThrottle (true/false) - default: false

### Scrapy Settings

Configurable via environment or code:

```python
SCRAPY_SETTINGS = {
    'CONCURRENT_REQUESTS': 4,
    'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
    'DOWNLOAD_DELAY': 0.5,
    'ROBOTSTXT_OBEY': True,
    'USER_AGENT': 'mcp-web-scraper/1.0',
}
```

## Operational Notes

### Resource Management (Planned Runtime)

- Spiders are created per-request and garbage collected after completion
- No long-lived spider pools to avoid resource exhaustion
- Memory usage scales with page count and item size

### Error Handling (Planned Runtime)

Common error scenarios:

1. **Network Errors**: HTTP timeouts, connection refused
   - Returns with `success: false` and error message
2. **Invalid Selectors**: Malformed CSS/XPath
   - Returns empty arrays for that selector
3. **Timeout Exceeded**: Total operation time > timeout_seconds
   - Stops crawl early and returns partial results
4. **Robots.txt Blocked**: Link violates robots.txt rules
   - Skips link (logs if DEBUG enabled)

### Performance Considerations (Planned Runtime)

- Use specific CSS/XPath selectors to minimize DOM traversal
- Increase `DOWNLOAD_DELAY` if receiving 429 (rate limit) responses
- Set `max_depth: 1` for single-level crawls to save resources
- Adjust `max_pages` and `timeout_seconds` based on expected data volume

## Integration

### MCP Endpoints

- `GET /health`: Server health check (returns 200 OK)
- `GET /mcp/tools`: Empty in scaffold mode by default
- `POST /mcp/execute`: Returns explicit not-implemented scaffold responses

### Example Integration (HTTP)

```python
import requests

# List available tools
response = requests.get("http://localhost:8013/mcp/tools")
tools = response.json()["tools"]

# Execute scrape_page
result = requests.post(
    "http://localhost:8013/mcp/execute",
    json={
        "tool": "scrape_page",
        "parameters": {
            "url": "https://example.com",
            "selectors": {"title": "h1"}
        }
    }
)
```

## Troubleshooting

### Server won't start

1. Check port 8013 is not already in use
2. Verify mcp_core package is installed
3. Check logs for dependency issues

### Selector returns empty results

1. Use browser DevTools to inspect actual element selectors
2. Try XPath alternative: `//h2[@class="title"]`
3. Enable DEBUG logging to see page HTML

### Crawl times out frequently

1. Increase `timeout_seconds` parameter
2. Decrease `max_pages` or `max_depth`
3. Increase `DOWNLOAD_DELAY` if receiving 429 responses

## Testing

Run tests with:
```bash
pytest tests/
```

Run integration tests:
```bash
python scripts/test_server.py
```

See [test_web_scraper.py](../tests/test_web_scraper.py) for unit test coverage.
