---
name: init-serena
description: Initialize Serena MCP server for semantic code analysis. Loads instructions manual and activates the current project. Use when user says "init serena", "serena 초기화", "start serena", "세레나 시작", or wants to begin semantic code navigation and symbol analysis with Serena MCP. Do NOT use for general MCP server integration (use mcp-integration skill), code analysis without Serena, or project overview (use project-overview skill).
---

# Init Serena MCP

1. Execute `mcp__plugin_serena_serena__activate_project` with the current working directory path to activate the project in Serena's web dashboard.
