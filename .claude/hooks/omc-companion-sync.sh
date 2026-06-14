#!/bin/bash

# SessionStart hook: keep ~/.claude/CLAUDE-omc.md in sync with the installed OMC plugin.
#
# The base CLAUDE.md imports `@~/.claude/CLAUDE-omc.md` (always-on OMC orchestration
# layer). That companion file is a COPY of the plugin's docs/CLAUDE.md OMC block,
# frozen at setup time. With plugin auto-update enabled, the plugin can advance to a
# newer version while the copy silently lags. This hook re-syncs the
# OMC:START..OMC:END block from the active plugin on every session start.
#
# ADD-ONLY / idempotent: only the marked block is replaced; any content outside the
# markers is preserved. Silent when already in sync. A re-synced block takes effect
# the NEXT session (base CLAUDE.md is already loaded for the current one).
#
# Toggle: ENABLE_OMC_COMPANION_SYNC (default on; safe because idempotent + silent).

cat >/dev/null 2>&1  # drain hook payload on stdin (unused)

quiet() { jq -n '{ "suppressOutput": true }'; exit 0; }
report() {
  jq -n --arg ctx "$1" '{
    "suppressOutput": true,
    "hookSpecificOutput": {
      "hookEventName": "SessionStart",
      "additionalContext": $ctx
    }
  }'
  exit 0
}

# Gate
[ "${ENABLE_OMC_COMPANION_SYNC:-1}" = "1" ] || quiet

CONFIG_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
COMPANION="$CONFIG_DIR/CLAUDE-omc.md"
CACHE_BASE="$CONFIG_DIR/plugins/cache/omc/oh-my-claudecode"

[ -d "$CACHE_BASE" ] || quiet

# Resolve the latest installed version dir that actually ships docs/CLAUDE.md.
# Portable numeric sort on X.Y.Z (avoids relying on `sort -V`).
latest=""
for v in $(ls -1 "$CACHE_BASE" 2>/dev/null \
            | grep -E '^[0-9]+\.[0-9]+\.[0-9]+' \
            | sort -t. -k1,1nr -k2,2nr -k3,3nr); do
  if [ -f "$CACHE_BASE/$v/docs/CLAUDE.md" ]; then latest="$v"; break; fi
done
[ -n "$latest" ] || quiet

CANON="$CACHE_BASE/$latest/docs/CLAUDE.md"

# Extract the OMC:START..OMC:END block (inclusive of markers) from the canonical doc.
extract_block() {
  awk '/<!-- OMC:START -->/{p=1} p; /<!-- OMC:END -->/{p=0}' "$1"
}
block=$(extract_block "$CANON")
[ -n "$block" ] || quiet
newver=$(printf '%s\n' "$block" | grep -oE 'OMC:VERSION:[0-9][0-9.]*' | head -1)

# Self-heal: companion missing or lacks markers -> (re)write it with just the block.
if [ ! -f "$COMPANION" ] || ! grep -q '<!-- OMC:START -->' "$COMPANION"; then
  printf '%s\n' "$block" > "$COMPANION"
  report "OMC companion (re)created from plugin $latest ($newver) (effective next session)"
fi

# Already in sync?
[ "$(extract_block "$COMPANION")" = "$block" ] && quiet

# Replace only the block; preserve anything before OMC:START and after OMC:END.
pre=$(awk '/<!-- OMC:START -->/{exit} {print}' "$COMPANION")
post=$(awk 'f{print} /<!-- OMC:END -->/{f=1}' "$COMPANION")
oldver=$(extract_block "$COMPANION" | grep -oE 'OMC:VERSION:[0-9][0-9.]*' | head -1)

tmp="$COMPANION.sync.$$"
{
  [ -n "$pre" ] && printf '%s\n' "$pre"
  printf '%s\n' "$block"
  [ -n "$post" ] && printf '%s\n' "$post"
} > "$tmp" && mv "$tmp" "$COMPANION"

report "OMC companion synced: ${oldver:-unknown} -> ${newver} (plugin $latest, effective next session)"
