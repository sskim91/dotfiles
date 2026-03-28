# Web Search Protocol

**CRITICAL**: Use `tavily_search` for all web searches. WebSearch is fallback only.

| Task | Tool | Fallback |
|------|------|----------|
| Web search | `tavily_search` | WebSearch |
| URL content | WebFetch | `tavily_extract` |
| Site crawling | `tavily_crawl` | - |
| Site URL mapping | `tavily_map` | - |

## URL Extraction Flow

1. **GitHub URL** → `gh` CLI (`gh pr view`, `gh issue view`, `gh repo view`)
2. **Other URL** → WebFetch first
3. **WebFetch fails** (403, blocked, timeout) → `tavily_extract`
