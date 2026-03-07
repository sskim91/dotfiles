---
name: mcp-integration
description: Integrate Model Context Protocol (MCP) servers into Claude Code plugins for external tool and service access. Covers stdio, SSE, HTTP, and WebSocket server types with authentication patterns. Use when user asks to "add MCP server", "integrate MCP", "configure MCP", "use .mcp.json", "set up MCP", "MCP 서버 추가", or discusses MCP server types and plugin configuration. Do NOT use for Serena initialization (use init-serena skill), general plugin development, or non-MCP tool integrations.
---

# MCP Integration for Claude Code Plugins

## Overview

Model Context Protocol (MCP) enables Claude Code plugins to integrate with external services and APIs by providing structured tool access. Use MCP integration to expose external service capabilities as tools within Claude Code.

**Key capabilities:**
- Connect to external services (databases, APIs, file systems)
- Provide 10+ related tools from a single service
- Handle OAuth and complex authentication flows
- Bundle MCP servers with plugins for automatic setup

## MCP Server Configuration Methods

Plugins can bundle MCP servers in two ways:

### Method 1: Dedicated .mcp.json (Recommended)

Create `.mcp.json` at plugin root:

```json
{
  "database-tools": {
    "command": "${CLAUDE_PLUGIN_ROOT}/servers/db-server",
    "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"],
    "env": {
      "DB_URL": "${DB_URL}"
    }
  }
}
```

**Benefits:**
- Clear separation of concerns
- Easier to maintain
- Better for multiple servers

### Method 2: Inline in plugin.json

Add `mcpServers` field to plugin.json:

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "mcpServers": {
    "plugin-api": {
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/api-server",
      "args": ["--port", "8080"]
    }
  }
}
```

**Benefits:**
- Single configuration file
- Good for simple single-server plugins

## MCP Server Types

### stdio (Local Process)

Execute local MCP servers as child processes. Best for local tools and custom servers.

**Configuration:**
```json
{
  "filesystem": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "/allowed/path"],
    "env": {
      "LOG_LEVEL": "debug"
    }
  }
}
```

**Use cases:**
- File system access
- Local database connections
- Custom MCP servers
- NPM-packaged MCP servers

**Process management:**
- Claude Code spawns and manages the process
- Communicates via stdin/stdout
- Terminates when Claude Code exits

### SSE (Server-Sent Events)

Connect to hosted MCP servers with OAuth support. Best for cloud services.

**Configuration:**
```json
{
  "asana": {
    "type": "sse",
    "url": "https://mcp.asana.com/sse"
  }
}
```

**Use cases:**
- Official hosted MCP servers (Asana, GitHub, etc.)
- Cloud services with MCP endpoints
- OAuth-based authentication
- No local installation needed

**Authentication:**
- OAuth flows handled automatically
- User prompted on first use
- Tokens managed by Claude Code

### HTTP (REST API)

Connect to RESTful MCP servers with token authentication.

**Configuration:**
```json
{
  "api-service": {
    "type": "http",
    "url": "https://api.example.com/mcp",
    "headers": {
      "Authorization": "Bearer ${API_TOKEN}",
      "X-Custom-Header": "value"
    }
  }
}
```

**Use cases:**
- REST API-based MCP servers
- Token-based authentication
- Custom API backends
- Stateless interactions

### WebSocket (Real-time)

Connect to WebSocket MCP servers for real-time bidirectional communication.

**Configuration:**
```json
{
  "realtime-service": {
    "type": "ws",
    "url": "wss://mcp.example.com/ws",
    "headers": {
      "Authorization": "Bearer ${TOKEN}"
    }
  }
}
```

**Use cases:**
- Real-time data streaming
- Persistent connections
- Push notifications from server
- Low-latency requirements

## Environment Variable Expansion

All MCP configurations support environment variable substitution:

**${CLAUDE_PLUGIN_ROOT}** - Plugin directory (always use for portability):
```json
{
  "command": "${CLAUDE_PLUGIN_ROOT}/servers/my-server"
}
```

**User environment variables** - From user's shell:
```json
{
  "env": {
    "API_KEY": "${MY_API_KEY}",
    "DATABASE_URL": "${DB_URL}"
  }
}
```

**Best practice:** Document all required environment variables in plugin README.

## MCP Tool Naming

When MCP servers provide tools, they're automatically prefixed:

**Format:** `mcp__plugin_<plugin-name>_<server-name>__<tool-name>`

**Example:**
- Plugin: `asana`
- Server: `asana`
- Tool: `create_task`
- **Full name:** `mcp__plugin_asana_asana__asana_create_task`

### Using MCP Tools in Commands

Pre-allow specific MCP tools in command frontmatter:

```markdown
---
allowed-tools: [
  "mcp__plugin_asana_asana__asana_create_task",
  "mcp__plugin_asana_asana__asana_search_tasks"
]
---
```

**Wildcard (use sparingly):**
```markdown
---
allowed-tools: ["mcp__plugin_asana_asana__*"]
---
```

**Best practice:** Pre-allow specific tools, not wildcards, for security.

## Lifecycle Management

**Automatic startup:**
- MCP servers start when plugin enables
- Connection established before first tool use
- Restart required for configuration changes

**Lifecycle:**
1. Plugin loads
2. MCP configuration parsed
3. Server process started (stdio) or connection established (SSE/HTTP/WS)
4. Tools discovered and registered
5. Tools available as `mcp__plugin_...__...`

**Viewing servers:**
Use `/mcp` command to see all servers including plugin-provided ones.

## Authentication Patterns

### OAuth (SSE/HTTP)

OAuth handled automatically by Claude Code:

```json
{
  "type": "sse",
  "url": "https://mcp.example.com/sse"
}
```

User authenticates in browser on first use. No additional configuration needed.

### Token-Based (Headers)

Static or environment variable tokens:

```json
{
  "type": "http",
  "url": "https://api.example.com",
  "headers": {
    "Authorization": "Bearer ${API_TOKEN}"
  }
}
```

Document required environment variables in README.

### Environment Variables (stdio)

Pass configuration to MCP server:

```json
{
  "command": "python",
  "args": ["-m", "my_mcp_server"],
  "env": {
    "DATABASE_URL": "${DB_URL}",
    "API_KEY": "${API_KEY}",
    "LOG_LEVEL": "info"
  }
}
```

## Integration Patterns, Security, and Debugging

For integration patterns (tool wrapper, autonomous agent, multi-server), security best practices, error handling, performance tips, and debugging guide, see [references/integration-patterns.md](references/integration-patterns.md).

## Quick Reference

### MCP Server Types

| Type | Transport | Best For | Auth |
|------|-----------|----------|------|
| stdio | Process | Local tools, custom servers | Env vars |
| SSE | HTTP | Hosted services, cloud APIs | OAuth |
| HTTP | REST | API backends, token auth | Tokens |
| ws | WebSocket | Real-time, streaming | Tokens |

### Configuration Checklist

- [ ] Server type specified (stdio/SSE/HTTP/ws)
- [ ] Type-specific fields complete (command or url)
- [ ] Authentication configured
- [ ] Environment variables documented
- [ ] HTTPS/WSS used (not HTTP/WS)
- [ ] ${CLAUDE_PLUGIN_ROOT} used for paths

### Best Practices

**DO:**
- ✅ Use ${CLAUDE_PLUGIN_ROOT} for portable paths
- ✅ Document required environment variables
- ✅ Use secure connections (HTTPS/WSS)
- ✅ Pre-allow specific MCP tools in commands
- ✅ Test MCP integration before publishing
- ✅ Handle connection and tool errors gracefully

**DON'T:**
- ❌ Hardcode absolute paths
- ❌ Commit credentials to git
- ❌ Use HTTP instead of HTTPS
- ❌ Pre-allow all tools with wildcards
- ❌ Skip error handling
- ❌ Forget to document setup

## Additional Resources

### Reference Files

For detailed information, consult:

- **`references/server-types.md`** - Deep dive on each server type
- **`references/authentication.md`** - Authentication patterns and OAuth
- **`references/tool-usage.md`** - Using MCP tools in commands and agents

### Example Configurations

Working examples in `examples/`:

- **`stdio-server.json`** - Local stdio MCP server
- **`sse-server.json`** - Hosted SSE server with OAuth
- **`http-server.json`** - REST API with token auth

### External Resources

- **Official MCP Docs**: https://modelcontextprotocol.io/
- **Claude Code MCP Docs**: https://docs.claude.com/en/docs/claude-code/mcp
- **MCP SDK**: @modelcontextprotocol/sdk
- **Testing**: Use `claude --debug` and `/mcp` command

## Implementation Workflow

To add MCP integration to a plugin:

1. Choose MCP server type (stdio, SSE, HTTP, ws)
2. Create `.mcp.json` at plugin root with configuration
3. Use ${CLAUDE_PLUGIN_ROOT} for all file references
4. Document required environment variables in README
5. Test locally with `/mcp` command
6. Pre-allow MCP tools in relevant commands
7. Handle authentication (OAuth or tokens)
8. Test error cases (connection failures, auth errors)
9. Document MCP integration in plugin README

Focus on stdio for custom/local servers, SSE for hosted services with OAuth.
