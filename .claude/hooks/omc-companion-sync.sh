#!/bin/bash

# SessionStart(startup) hook: keep ~/.claude/CLAUDE-omc.md aligned with the OMC plugin
# version Claude Code actually loads.
#
# Why a hook (restored 2026-09-05): marketplace autoUpdate updates the INSTALLED plugin
# in the background a few minutes after a session starts. Nobody types a command for
# that, so the only place to catch the resulting drift is the next startup. The heavy
# lifting (version resolution, block replace, self-heal) lives in
# scripts/omc-companion-sync.sh; this wrapper only adds the ENABLE_* toggle.
#
# Output: silent when already in sync; one line when the block changed or the write
# failed. A re-synced block takes effect in the NEXT session.

cat >/dev/null 2>&1  # drain hook payload on stdin (unused)

[ "${ENABLE_OMC_COMPANION_SYNC:-1}" = "1" ] || exit 0

SYNC="$HOME/.dotfiles/scripts/omc-companion-sync.sh"
[ -x "$SYNC" ] || exit 0

exec "$SYNC" -q
