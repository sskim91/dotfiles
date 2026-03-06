# MCP Integration - Patterns and Security

## Integration Patterns

### Pattern 1: Simple Tool Wrapper

Commands use MCP tools with user interaction:

```markdown
# Command: create-item.md
---
allowed-tools: ["mcp__plugin_name_server__create_item"]
---

Steps:
1. Gather item details from user
2. Use mcp__plugin_name_server__create_item
3. Confirm creation
```

**Use for:** Adding validation or preprocessing before MCP calls.

### Pattern 2: Autonomous Agent

Agents use MCP tools autonomously:

```markdown
# Agent: data-analyzer.md

Analysis Process:
1. Query data via mcp__plugin_db_server__query
2. Process and analyze results
3. Generate insights report
```

**Use for:** Multi-step MCP workflows without user interaction.

### Pattern 3: Multi-Server Plugin

Integrate multiple MCP servers:

```json
{
  "github": {
    "type": "sse",
    "url": "https://mcp.github.com/sse"
  },
  "jira": {
    "type": "sse",
    "url": "https://mcp.jira.com/sse"
  }
}
```

**Use for:** Workflows spanning multiple services.

## Security Best Practices

### Use HTTPS/WSS

Always use secure connections:

```json
"url": "https://mcp.example.com/sse"
```

### Token Management

**DO:**
- Use environment variables for tokens
- Document required env vars in README
- Let OAuth flow handle authentication

**DON'T:**
- Hardcode tokens in configuration
- Commit tokens to git
- Share tokens in documentation

### Permission Scoping

Pre-allow only necessary MCP tools:

```markdown
allowed-tools: [
  "mcp__plugin_api_server__read_data",
  "mcp__plugin_api_server__create_item"
]
```

Avoid wildcards: `mcp__plugin_api_server__*`

## Error Handling

### Connection Failures
- Provide fallback behavior in commands
- Inform user of connection issues
- Check server URL and configuration

### Tool Call Errors
- Validate inputs before calling MCP tools
- Provide clear error messages
- Check rate limiting and quotas

### Configuration Errors
- Test server connectivity during development
- Validate JSON syntax
- Check required environment variables

## Performance

### Lazy Loading
- MCP servers connect on-demand
- First tool use triggers connection
- Connection pooling managed automatically

### Batching
Batch similar requests when possible:

```
# Good: Single query with filters
tasks = search_tasks(project="X", assignee="me", limit=50)

# Avoid: Many individual queries
for id in task_ids:
    task = get_task(id)
```

## Debugging

### Enable Debug Logging

```bash
claude --debug
```

Look for:
- MCP server connection attempts
- Tool discovery logs
- Authentication flows
- Tool call errors

### Common Issues

**Server not connecting:**
- Check URL is correct
- Verify server is running (stdio)
- Check network connectivity
- Review authentication configuration

**Tools not available:**
- Verify server connected successfully
- Check tool names match exactly
- Run `/mcp` to see available tools
- Restart Claude Code after config changes

**Authentication failing:**
- Clear cached auth tokens
- Re-authenticate
- Check token scopes and permissions
- Verify environment variables set
