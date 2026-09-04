#!/bin/bash

# Sync ~/.claude/CLAUDE-omc.md with the OMC plugin version Claude Code actually loads.
#
# The base CLAUDE.md imports `@~/.claude/CLAUDE-omc.md` (always-on OMC orchestration
# layer). That companion file is a COPY of the plugin's docs/CLAUDE.md OMC block, so it
# can drift from the plugin.
#
# HOW IT RUNS: from the SessionStart(startup) hook wrapper
# .claude/hooks/omc-companion-sync.sh (toggle ENABLE_OMC_COMPANION_SYNC) and once from
# install.sh to seed a fresh machine.
#
# History: 2026-08-29 this was moved out of the hook into a `ccpu` update function on
# the belief that marketplace autoUpdate only refreshes the catalog, so the installed
# version could only change when a person ran `claude plugin update`. That was wrong:
# autoUpdate updates installed plugins in the background a few minutes after startup
# (official docs; measured 2026-09-05, 5.0.2 -> 5.2.0 landed 7 minutes into a
# session). Drift therefore happens with no user command, and the next startup is the
# only place to catch it. Restored as a hook 2026-09-05; `ccpu` was deleted.
# Note the OMC block body has been byte-identical across both bumps so far
# (5.0.0 -> 5.0.2 -> 5.2.0); only the version marker moved.
#
# ADD-ONLY / idempotent: only the OMC:START..OMC:END block is replaced; content outside
# the markers is preserved. A re-synced block takes effect in the NEXT session.
#
# Usage: omc-companion-sync.sh [-q]    (-q: only report changes and failures)

quiet_mode=0
[ "$1" = "-q" ] && quiet_mode=1

say()  { [ "$quiet_mode" -eq 1 ] || printf '%s\n' "$1"; }
note() { printf '%s\n' "$1"; }            # always shown (change or failure)
skip() { say "$1"; exit 0; }

CONFIG_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
COMPANION="$CONFIG_DIR/CLAUDE-omc.md"
CACHE_BASE="$CONFIG_DIR/plugins/cache/omc/oh-my-claudecode"
INSTALLED_JSON="$CONFIG_DIR/plugins/installed_plugins.json"

# Resolve the plugin dir Claude Code ACTUALLY LOADS, from the install record.
#
# Do NOT just take the highest version in the cache. The cache keeps old and
# prefetched builds side by side, so the newest directory is frequently not the one in
# use, and the companion then documents a build that is not running. Measured
# 2026-08-29: cache held 5.0.2 while installed_plugins.json pinned 5.0.0, so
# CLAUDE-omc.md announced `ultrawork` as retired while the running 5.0.0 keyword
# detector still matched a bare `ulw` and routed it to the skill 5.0.0 had deleted.
# A doc that runs AHEAD of the plugin misleads as much as one that lags -- and looks
# correct while doing it.
plugin_dir=""
if [ -f "$INSTALLED_JSON" ] && command -v jq >/dev/null 2>&1; then
  # Entries live under .plugins["<name>@<marketplace>"], not at the top level.
  installed_paths=$(jq -r '.plugins["oh-my-claudecode@omc"] // [] | .[].installPath // empty' \
                      "$INSTALLED_JSON" 2>/dev/null)
  while IFS= read -r p; do
    [ -n "$p" ] || continue
    if [ -f "$p/docs/CLAUDE.md" ]; then plugin_dir="$p"; break; fi
  done <<< "$installed_paths"
fi

# Fallback only when the install record is missing or unreadable: newest cache dir that
# ships the doc. Better than nothing, but it can pick a build that is merely
# downloaded, so it stays the second choice.
if [ -z "$plugin_dir" ] && [ -d "$CACHE_BASE" ]; then
  for v in $(ls -1 "$CACHE_BASE" 2>/dev/null \
              | grep -E '^[0-9]+\.[0-9]+\.[0-9]+' \
              | sort -t. -k1,1nr -k2,2nr -k3,3nr); do
    if [ -f "$CACHE_BASE/$v/docs/CLAUDE.md" ]; then plugin_dir="$CACHE_BASE/$v"; break; fi
  done
fi
[ -n "$plugin_dir" ] || skip "OMC plugin not found; nothing to sync"

latest=$(basename "$plugin_dir")
CANON="$plugin_dir/docs/CLAUDE.md"

# Extract the OMC:START..OMC:END block (inclusive of markers) from the canonical doc.
extract_block() {
  awk '/<!-- OMC:START -->/{p=1} p; /<!-- OMC:END -->/{p=0}' "$1"
}
block=$(extract_block "$CANON")
[ -n "$block" ] || skip "OMC block not found in $CANON; nothing to sync"
newver=$(printf '%s\n' "$block" | grep -oE 'OMC:VERSION:[0-9][0-9.]*' | head -1)

# Self-heal: companion missing or lacks markers -> (re)write it with just the block.
if [ ! -f "$COMPANION" ] || ! grep -q '<!-- OMC:START -->' "$COMPANION"; then
  printf '%s\n' "$block" > "$COMPANION"
  note "OMC companion (re)created from plugin $latest ($newver); effective next session"
  exit 0
fi

# Already in sync?
[ "$(extract_block "$COMPANION")" = "$block" ] && skip "OMC companion already in sync ($newver)"

# Replace only the block; preserve anything before OMC:START and after OMC:END.
pre=$(awk '/<!-- OMC:START -->/{exit} {print}' "$COMPANION")
post=$(awk 'f{print} /<!-- OMC:END -->/{f=1}' "$COMPANION")
oldver=$(extract_block "$COMPANION" | grep -oE 'OMC:VERSION:[0-9][0-9.]*' | head -1)

tmp="$COMPANION.sync.$$"

# Use `if` for the optional pre/post parts, not `[ -n "$x" ] && printf`.
# A brace group exits with the status of its LAST command: when the companion holds
# only the OMC block, `post` is empty, the trailing test returns 1, the group "fails",
# and `&& mv` is silently skipped -- leaving a .sync.<pid> orphan behind and the
# companion stale, while the report below still claimed success.
if {
  if [ -n "$pre" ]; then printf '%s\n' "$pre"; fi
  printf '%s\n' "$block"
  if [ -n "$post" ]; then printf '%s\n' "$post"; fi
} > "$tmp" && mv "$tmp" "$COMPANION"; then
  note "OMC companion synced: ${oldver:-unknown} -> ${newver} (plugin $latest); effective next session"
  exit 0
fi

# Write or rename failed: drop the temp file so orphans cannot accumulate, and say what
# actually happened instead of reporting a sync that did not occur.
command rm -f "$tmp"
note "OMC companion sync FAILED to write $COMPANION; still at ${oldver:-unknown}"
exit 1
