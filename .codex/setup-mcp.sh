#!/bin/bash
# Codex CLI MCP server registration
# Usage: ~/.codex/setup-mcp.sh
#
# Registers MCP servers into ~/.codex/config.toml via `codex mcp add`.
# Safe to re-run: existing servers are skipped.

if ! command -v codex &> /dev/null; then
    echo "codex not found, skipping MCP server setup..."
    exit 1
fi

echo "Setting up Codex MCP servers..."

existing=$(codex mcp list 2>/dev/null)

add_if_missing() {
    local name="$1"; shift
    if echo "$existing" | grep -q "$name"; then
        echo "  . $name (already exists)"
    else
        codex mcp add "$@" 2>/dev/null \
            && echo "  + $name added" \
            || echo "  ! $name failed"
    fi
}

# stdio servers
add_if_missing context7          context7 -- npx -y @upstash/context7-mcp
add_if_missing playwright        playwright -- npx @playwright/mcp@latest
add_if_missing desktop-commander desktop-commander -- npx -y @wonderwhy-er/desktop-commander
add_if_missing tavily-remote     tavily-remote -- sh -c "npx -y mcp-remote \"https://mcp.tavily.com/mcp/?tavilyApiKey=\$TAVILY_API_KEY\""
add_if_missing brave-search      brave-search -- sh -c 'if [ -f "$HOME/.dotfiles/.env.local" ]; then . "$HOME/.dotfiles/.env.local"; fi; exec npx -y @brave/brave-search-mcp-server --transport stdio'

# remote MCP servers via stdio proxy
add_if_missing mermaid-mcp       mermaid-mcp -- npx -y mcp-remote https://mcp.mermaid.ai/mcp

echo "Codex MCP servers setup complete"
