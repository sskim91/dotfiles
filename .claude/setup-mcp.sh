#!/bin/bash
# Claude Code MCP server registration (user scope)
# Usage: ~/.claude/setup-mcp.sh

if ! command -v claude &> /dev/null; then
    echo "⚠️  claude not found, skipping MCP server setup..."
    exit 1
fi

echo "Setting up Claude Code MCP servers..."

CLAUDECODE= claude mcp add -s user desktop-commander -- npx -y @wonderwhy-er/desktop-commander 2>/dev/null \
    && echo "✓ desktop-commander added" || echo "✓ desktop-commander already exists"

CLAUDECODE= claude mcp add -s user tavily-remote -- sh -c "npx -y mcp-remote \"https://mcp.tavily.com/mcp/?tavilyApiKey=\$TAVILY_API_KEY\"" 2>/dev/null \
    && echo "✓ tavily-remote added" || echo "✓ tavily-remote already exists"

CLAUDECODE= claude mcp add -s user brave-search -- sh -c "BRAVE_API_KEY=\"\$BRAVE_API_KEY\" npx -y @brave/brave-search-mcp-server" 2>/dev/null \
    && echo "✓ brave-search added" || echo "✓ brave-search already exists"

if [ -f "$HOME/.dotfiles/.env.local" ]; then . "$HOME/.dotfiles/.env.local"; fi
if [ -n "$YOUTRACK_URL" ] && [ -n "$YOUTRACK_TOKEN" ]; then
    CLAUDECODE= claude mcp add -s user --transport http youtrack \
        "$YOUTRACK_URL/mcp" \
        --header "Authorization: Bearer $YOUTRACK_TOKEN" 2>/dev/null \
        && echo "✓ youtrack added" || echo "✓ youtrack already exists"
else
    echo "⚠️  youtrack skipped (YOUTRACK_URL or YOUTRACK_TOKEN not set in .env.local)"
fi

echo "✅ Claude Code MCP servers registered"
