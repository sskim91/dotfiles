#!/usr/bin/env bash
# SessionStart(resume|fork) hook: re-inject the superpowers `using-superpowers` skill.
#
# The superpowers plugin's own SessionStart hook only matches `startup|clear|compact`
# (plugins/cache/.../superpowers/<ver>/hooks/hooks.json), so a resumed or forked
# session starts without the "you have superpowers" bootstrap and skill checks get
# skipped. This wrapper emits the same additionalContext for the missing sources.
# It reads the SKILL.md of the plugin version Claude Code actually has installed
# (installed_plugins.json, any `superpowers@<marketplace>` key), falling back to the
# newest `plugins/cache/*/superpowers/<ver>` directory.
#
# Toggle: ENABLE_SUPERPOWERS_CONTEXT (default 1)

set -euo pipefail

[ "${ENABLE_SUPERPOWERS_CONTEXT:-1}" = "1" ] || exit 0
command -v jq >/dev/null 2>&1 || exit 0

CONFIG_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
REGISTRY="$CONFIG_DIR/plugins/installed_plugins.json"
CACHE_ROOT="$CONFIG_DIR/plugins/cache"

plugin_dir=""
if [ -f "$REGISTRY" ]; then
  plugin_dir=$(jq -r '.plugins | to_entries[] | select(.key | startswith("superpowers@")) | .value[].installPath // empty' \
    "$REGISTRY" 2>/dev/null | while IFS= read -r p; do [ -d "$p" ] && printf '%s\n' "$p"; done | head -1)
fi
if [ -z "$plugin_dir" ] && [ -d "$CACHE_ROOT" ]; then
  plugin_dir=$(find "$CACHE_ROOT" -mindepth 3 -maxdepth 3 -type d -path '*/superpowers/*' | sort -V | tail -1)
fi
[ -n "$plugin_dir" ] || exit 0

skill="$plugin_dir/skills/using-superpowers/SKILL.md"
[ -f "$skill" ] || exit 0

jq -n --rawfile skill "$skill" '{
  hookSpecificOutput: {
    hookEventName: "SessionStart",
    additionalContext: ("<EXTREMELY_IMPORTANT>\nYou have superpowers.\n\n**Below is the full content of your '\''superpowers:using-superpowers'\'' skill - your introduction to using skills. For all other skills, use the '\''Skill'\'' tool:**\n\n" + $skill + "\n</EXTREMELY_IMPORTANT>")
  }
}'
