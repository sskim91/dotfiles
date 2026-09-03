#!/bin/bash

# SessionStart + PostModelSwitch hook: inject model-specific prompting guidance.
#
# Why a hook and not CLAUDE.md: CLAUDE.md is loaded regardless of model, and the
# harness already injects Fable 5.1's prompting snippets (progress updates,
# autonomy block, batch nudge) itself. Opus 5 needs a different set — shorter
# replies, no over-verification, capped delegation — per
# https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5
#
# Model detection: PostModelSwitch always carries `to_model`; SessionStart carries
# `model` only sometimes (docs: "Claude Code doesn't always include it"). Both are
# read so a fresh session and a mid-session /model switch are both covered. When
# neither field is present, print nothing — no guess.
#
# Toggle: ENABLE_MODEL_CONTEXT (zsh/path.zsh). Plain stdout becomes context.

[[ "${ENABLE_MODEL_CONTEXT:-1}" == "1" ]] || exit 0

INPUT=$(cat)
# Set MODEL_CONTEXT_DEBUG=<file> to capture the raw hook payload (field audit).
[[ -n "${MODEL_CONTEXT_DEBUG:-}" ]] && printf '%s\n' "$INPUT" >> "$MODEL_CONTEXT_DEBUG"
MODEL=$(printf '%s\n' "$INPUT" | jq -r '.to_model // .model // empty' 2>/dev/null)

# Measured 2026-09-03 (2.1.259): SessionStart:startup payload has no `model`
# field at all, and PostModelSwitch does not fire for the initial model. So a
# fresh session would never get this context. Fall back to the saved default:
# `/model` persists its choice as the `model` key in settings, and ANTHROPIC_MODEL
# outranks it. A one-off `--model` CLI flag is not visible here and is missed.
if [[ -z "$MODEL" ]]; then
  MODEL="${ANTHROPIC_MODEL:-}"
  for f in ~/.claude/settings.local.json ~/.claude/settings.json; do
    [[ -n "$MODEL" ]] && break
    [[ -f "$f" ]] && MODEL=$(jq -r '.model // empty' "$f" 2>/dev/null)
  done
fi

[[ -z "$MODEL" ]] && exit 0

case "$MODEL" in
  *opus-5*|*opus5*)
    cat <<'EOF'
## Opus 5 session guidance
Keep responses focused, brief, and concise. Keep disclaimers and caveats short, and spend most of the response on the main answer. When asked to explain something, give a high-level summary unless an in-depth explanation is specifically requested.

Match the length of written documents to what the task needs: cover the substance, but do not pad with filler sections, redundant summaries, or boilerplate.

Only correct an earlier statement when the error would change the user's code, conclusions, or decisions. State corrections plainly and briefly, then continue the task. For slips that change nothing for the user, make the fix and move on without noting it.
EOF
    # Delegation guidance is intentionally absent: the harness adds its own on
    # Opus 5, the global CLAUDE.md override covers it, and the env caps
    # (CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH / MAX_CONCURRENT_SUBAGENTS) are the
    # deterministic lever. A fourth copy would compound.
    ;;
  *)
    # Fable 5.x: the harness already injects the model-specific snippets.
    ;;
esac

exit 0
