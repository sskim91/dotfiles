# Web Search Protocol

When performing web searches or fetching web content, prefer Tavily MCP over built-in tools.

## Tool Priority

| Task | Use | Instead of |
|------|-----|------------|
| Web search | `tavily_search` | WebSearch |
| URL content extraction | `tavily_extract` | WebFetch |
| Site crawling | `tavily_crawl` | - |
| Site URL mapping | `tavily_map` | - |

## Why Tavily

- AI-agent optimized structured results
- Confidence scores and source tracking
- Advanced search depth options
- Free tier: 1,000 credits/month

## Usage

```bash
# Search
mcp-cli call tavily-remote-mcp/tavily_search '{"query": "...", "search_depth": "basic"}'

# Extract content from URL
mcp-cli call tavily-remote-mcp/tavily_extract '{"urls": ["..."]}'

# Crawl website
mcp-cli call tavily-remote-mcp/tavily_crawl '{"url": "...", "max_depth": 2}'

# Map site URLs
mcp-cli call tavily-remote-mcp/tavily_map '{"url": "..."}'
```

## Fallback

Use WebSearch/WebFetch when:
- Tavily API is unavailable
- Simple single-page fetch is sufficient
