#!/bin/bash

# SessionStart hook: sync per-skill symlinks in ~/.claude/skills/
#
# New skill directories added under dotfiles are auto-linked here so they
# appear without re-running install.sh. ~/.claude/skills/ stays a REAL
# directory (not a folder-level symlink) so external/plugin skills can live
# as siblings; therefore this hook is ADD-ONLY — it never deletes, only
# creates links that are missing. Idempotent.

cat >/dev/null 2>&1  # drain hook payload on stdin (unused)

SRC_DIR="$HOME/.dotfiles/.claude/skills"
DST_DIR="$HOME/.claude/skills"

linked=""
if [ -d "$SRC_DIR" ]; then
  mkdir -p "$DST_DIR"
  for src in "$SRC_DIR"/*/; do
    [ -d "$src" ] || continue
    name=$(basename "$src")
    # -e follows symlinks: skips valid links and real (external) dirs alike,
    # only acts when the entry is absent or a dangling link.
    if [ ! -e "$DST_DIR/$name" ]; then
      ln -nfs "$src" "$DST_DIR/$name" && linked="$linked $name"
    fi
  done
fi

if [ -n "$linked" ]; then
  jq -n --arg ctx "Newly linked Claude skills:$linked (effective next session)" '{
    "suppressOutput": true,
    "hookSpecificOutput": {
      "hookEventName": "SessionStart",
      "additionalContext": $ctx
    }
  }'
else
  jq -n '{ "suppressOutput": true }'
fi
