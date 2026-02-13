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

echo "✅ Claude Code MCP servers registered"
