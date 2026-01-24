# Web Search Protocol

## Tool Priority

| Task | Priority | Fallback |
|------|----------|----------|
| Web search | `tavily_search` | WebSearch |
| URL extraction (user-provided) | WebFetch | `tavily_extract` |
| Site crawling | `tavily_crawl` | - |
| Site URL mapping | `tavily_map` | - |

### URL Extraction Flow

사용자가 URL을 제공한 경우:
1. **GitHub URL** → `gh` CLI 사용
2. **기타 URL** → WebFetch 먼저 시도
3. **WebFetch 실패 시** (403, blocked, timeout) → `tavily_extract` 사용

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

## GitHub Exception

For GitHub URLs, use `gh` CLI instead of Tavily:

```bash
# PR/Issue
gh pr view <number>
gh issue view <number>

# Repository info
gh repo view <owner/repo>

# API for other resources
gh api repos/<owner>/<repo>/pulls/<number>/comments
gh api repos/<owner>/<repo>/contents/<path>
```

GitHub URL 패턴:
- `github.com/<owner>/<repo>/pull/<number>` → `gh pr view`
- `github.com/<owner>/<repo>/issues/<number>` → `gh issue view`
- `github.com/<owner>/<repo>` → `gh repo view`

## Fallback

Use WebSearch when:
- Tavily API is unavailable

Use `gh` CLI when:
- GitHub URL (PR, Issue, Repo)
