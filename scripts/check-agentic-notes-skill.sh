#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
agentic="$root/.claude/skills/agentic-notes/SKILL.md"
obsidian="$root/.claude/skills/obsidian-note/SKILL.md"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

contains() {
  local file="$1"
  local needle="$2"
  grep -Fq -- "$needle" "$file" || fail "$file missing: $needle"
}

test -f "$agentic" || fail "missing .claude/skills/agentic-notes/SKILL.md"
contains "$agentic" "name: agentic-notes"
contains "$agentic" "source-hunter"
contains "$agentic" "vault-researcher"
contains "$agentic" "skeptic"
contains "$agentic" "synthesizer"
contains "$agentic" "note-writer"
contains "$agentic" "TASK:"
contains "$agentic" "DELIVERABLE:"
contains "$agentic" "SCOPE:"
contains "$agentic" "VERIFY:"
printf 'PASS: agentic-notes-skill-present\n'

contains "$obsidian" "leaf writer"
contains "$obsidian" "agentic-notes"
contains "$obsidian" "Claude Code"
contains "$obsidian" "Codex"
printf 'PASS: obsidian-note-boundary\n'

strict="$root/.claude/skills/agentic-notes/references/strict-verification.md"
test -f "$strict" || fail "missing strict verification reference"
contains "$strict" "--verify strict"
contains "$strict" "--deep"
contains "$strict" "claim ledger"
printf 'PASS: strict-reference-tracked\n'

for reference in writing-style.md complete-example.md post-write-linking.md obsidian-syntax.md; do
  test -f "$root/.claude/skills/obsidian-note/references/$reference" || fail "missing obsidian reference: $reference"
done
contains "$obsidian" "Post-write linking"
printf 'PASS: obsidian-note-existing-references\n'
