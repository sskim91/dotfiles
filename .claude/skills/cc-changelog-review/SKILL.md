---
name: cc-changelog-review
description: Review Claude Code CLI changelog updates against the user's dotfiles configuration and recommend which new features are worth adopting. Make sure to use this skill whenever the user mentions "claude code 변경사항", "체인지로그 검토", "claude code 업데이트 검토", "release notes 검토", "버전 X 추가할거", "최근 릴리스 뭐있나", "claude code changelog review", references CHANGELOG.md or anchor URLs like #21128, gives a version range like 2.1.120..2.1.128, or asks "뭐 추가할거 있나" / "what's worth adopting" in the context of Claude Code releases — even if they don't explicitly ask for a "review". Do NOT use for non-Claude-Code changelogs (Gemini, Codex, OpenAI SDK, etc.) or for general release-note reading without a dotfiles cross-reference.
---

# Claude Code CLI Changelog Review

Compares recent Claude Code CLI releases against the user's dotfiles configuration and produces tiered, actionable recommendations.

**Output only — never auto-apply changes.** The user must explicitly choose what to adopt; that's the contract. Editing dotfiles silently would burn trust faster than any time saved.

## Why this exists

Claude Code ships rapid releases, often multiple per week. Each release contains 10-30 bullets, mostly bug fixes that don't need action — but a few introduce new hook fields, settings keys, or env vars that map directly to the user's existing dotfiles setup. Reading one release manually is feasible; doing the cross-reference across 5-10 releases without structure is where things slip through.

This skill is the cross-reference. It exists because the user already has a sophisticated dotfiles harness (custom hooks, MCP servers, plugins, ENABLE_* env toggles), and updates from upstream that *touch those exact surfaces* are high-leverage to adopt — but easy to miss if you scroll past them in a 30-bullet release.

## Inputs

The user's request might come as:

| Format | Example | Resolution |
|---|---|---|
| Range | `2.1.120..2.1.128`, `2.1.120 to 2.1.128` | Inclusive both ends |
| Last N | `last 5`, `최근 5개` | N most recent |
| Anchor URL | `#21128` | Strip `#`, restore dots → `2.1.128` |
| Single version | `2.1.128` | Just that one |
| Nothing | — | Default to last 5 |

If the request is genuinely ambiguous, ask once. The bundled fetch script handles all of these formats including anchor normalization.

## Workflow

The natural order is fetch → read user config → categorize → tier → render. **Adapt as needed** — if the conversation already contains the CHANGELOG, skip fetch; if `.mcp.json` doesn't exist, skip that read; if the user asks just about a single category (e.g., "hook 관련만 봐"), narrow accordingly.

### Fetch

Use the bundled script. It handles `gh` rate-limit fallback, version filtering, and anchor normalization in one place — three things that are individually easy to get wrong:

```bash
~/.dotfiles/.claude/skills/cc-changelog-review/scripts/fetch-changelog.sh        # last 5
~/.dotfiles/.claude/skills/cc-changelog-review/scripts/fetch-changelog.sh 10     # last N
~/.dotfiles/.claude/skills/cc-changelog-review/scripts/fetch-changelog.sh 2.1.128
~/.dotfiles/.claude/skills/cc-changelog-review/scripts/fetch-changelog.sh 2.1.120 2.1.128
~/.dotfiles/.claude/skills/cc-changelog-review/scripts/fetch-changelog.sh '#21128'
```

Why a script and not inline `gh api`: deterministic fallback (gh → curl), correct anchor handling, and avoidance of macOS-specific bash gotchas (BSD awk doesn't emit `\0`, awk `exit` triggers SIGPIPE under `set -e`). The script encodes those once.

### Read user config (parallel)

In a single message, read all of:

- `~/.dotfiles/.claude/settings.json` — hooks, env, permissions, plugins, statusLine, autoMode, defaultMode
- `~/.dotfiles/.mcp.json` (if present) — MCP server configuration
- `~/.dotfiles/zsh/path.zsh` — `ENABLE_*` env vars
- `~/.dotfiles/zsh/functions.zsh` — AI CLI wrappers (`ccv`, `cco`, `gem`, `cdx`) and their flags
- `~/.claude/projects/-Users-sskim--dotfiles/memory/MEMORY.md` (and linked memory files when relevant) — multi-machine context, security posture, prior decisions
- `ls ~/.dotfiles/.claude/hooks/` — hook script names
- `ls ~/.dotfiles/.claude/skills/` — skill names

Reading in parallel matters because the cross-reference is the whole point — having all files in context simultaneously means you don't re-read the same file three times when classifying different bullets.

The memory file matters specifically because some recommendations only make sense with cross-machine context (e.g., recommending `prUrlTemplate` requires knowing the user has a company Mac with a different git remote; recommending shell-config deny rules requires knowing they sync dotfiles across machines). Without that context, recommendations look generic and the user dismisses them as noise.

### Categorize each bullet

Apply the mapping in `references/category-mapping.md` — read it now if you haven't this session. The table covers 14 categories (hooks, MCP, env vars, permissions, skills, slash commands, themes, plugins, CLI, vim, statusline, auto/plan mode, plus per-category notes that capture this user's specific posture).

One bullet can touch multiple categories. Don't force a 1:1 mapping; record both/all.

### Assign Tier

- **Tier 1 — 즉시 효과**: Maps to existing user config; user can enable now with a small edit. This is where leverage lives — the whole reason to read the changelog.
- **Tier 2 — 워크플로우 추가**: New optional capability requiring fresh config (alias, hook, env var, skill placeholder).
- **Tier 3 — 마이너 정리**: Doc/spinnerTips updates, deprecation refreshes, awareness only.
- **Skip**: Pure bug fixes — note in the summary line, don't list.

If a candidate would actually require touching 5+ files, demote it from Tier 1 to Tier 2. The "small edit" criterion is what makes Tier 1 useful as a signal — once it stops being small, the user reads the tier label as a lie.

### Render

The output should convey, at minimum:

1. Version range covered, total bullets, bullets-after-bug-filter
2. Tier 1/2/3 sections, each with: changelog item, version, target `file_path:line_number`, recommended action
3. One concrete top recommendation with reasoning (why it's the highest leverage — token cost, maintenance load, fit with existing posture)

Tables work well for the tier sections because they compress the cross-reference. Korean output (matches the user's `language: korean` setting), but technical identifiers stay in original form.

End with: **"어느 항목을 적용할까요? 또는 '전체 검토만'으로 답하시면 종료합니다."** The closing question is the contract — review-only means waiting for explicit selection before any write.

#### Example output skeleton

```markdown
## 변경사항 요약 (2.1.120 ~ 2.1.128)
9개 릴리스, 142개 변경사항 (버그픽스 87건 제외 — 55건 분석)

### Tier 1 — 즉시 효과
| # | 변경사항 | 버전 | 사용자 설정 | 권장 액션 |
|---|---|---|---|---|
| 1 | PostToolUse `duration_ms` 입력 추가 | 2.1.119 | `.claude/settings.json:71` | 3-체인 훅에 perf log 추가 |

### Tier 2 — 워크플로우 추가
...

### Tier 3 — 마이너 정리
...

## 즉시 적용 권장 1건
[Tier 1 #1]을 권장. 근거: 사용자 PostToolUse 훅이 3개 체인이고 til-review가 300s timeout이라 어느 훅이 느린지 측정 가치가 큼. 토큰 비용 0(stderr 로그만), 유지보수 거의 없음.

어느 항목을 적용할까요? 또는 '전체 검토만'으로 답하시면 종료합니다.
```

This is a guideline, not a contract — adapt the headings and column count to fit what's actually in the range. If a Tier is empty, omit it entirely rather than printing "(없음)".

## Verify before recommending

Before recommending a setting, run `jq '.path.to.key' ~/.dotfiles/.claude/settings.json`. If it's already set, drop the recommendation — it's noise, and the user trusts you to filter that out. The cost of one wasted recommendation is high because each one trains them to skim the next.

## Cite paths

Every recommendation referencing existing config must include `file_path:line_number`. The user navigates with this — they shouldn't have to grep to verify your claim.

## Gotchas

These are mistakes that look reasonable but burn time. Worth re-reading on each invocation.

- **GitHub `gh` rate limit is shared** across all gh-using tools/agents in the session (5,000/hr). One CHANGELOG fetch is cheap, but if the session already used many gh calls earlier, fall back to `curl`/WebFetch immediately rather than retrying. The bundled script does this automatically.
- **Anchor format strips dots**: `#21128` = section `## 2.1.128`, not `## 2.11.28`. Restore dots as `X.Y.{rest}`. The fetch script handles this; if you parse manually, watch for it.
- **Canonical settings path is `~/.dotfiles/.claude/settings.json`**, not `~/.claude/settings.json` (the latter is a symlink). Recommend edits at the dotfiles location so changes are tracked in git.
- **One bullet can touch multiple categories** — don't force 1:1. "Added env var X with permission Y" hits both `env` and `permissions`.
- **`ENABLE_TOOL_SEARCH=1`** in settings means MCP-related changelog items are higher leverage — items announcing "always-loaded tools" matter more for users with deferred loading.
- **Pre-commit hooks may modify files on commit** (e.g., `end-of-file-fixer`). After recommending an edit, expect a possible re-staging cycle on the user's next commit — that's the same change, not a different one.
- **Some bullets are deprecation announcements**, not new features. e.g., "/cost merged into /usage" means update `spinnerTipsOverride.tips` references, not enable a new capability.
- **Scope creep**: a Tier 1 recommendation that spans 5+ files is actually a Tier 2 project. Re-tier when effort exceeds "small edit" — users read tiers as effort signals, so mis-tiering breaks the signal.
- **Don't promote `--dangerously-skip-permissions` items to Tier 1** unless `skipDangerousModePermissionPrompt: true` is already set. Otherwise the user accepted the safer mode and the change requires opting back into a riskier path; that's an explicit decision, not a small edit.
- **Protection-shrinking changes are *risk increases*, not *convenience wins*.** When a release announces "X path is no longer protected from skip-permissions" or "Y operation no longer prompts", the surface-level reading is "fewer interruptions" — but for a user who *already* has skip-mode active (the only kind of user it affects), the actual effect is "previously-guarded files can now be silently rewritten by any agent". Surface this as a Tier 1 *security review* item with a deny-rule recommendation, not as "auto-applied, no action needed". A worked example: 2.1.126's `--dangerously-skip-permissions` expansion to `.claude/`, `.git/`, `.vscode/`, and shell config means a user with `skipDangerousModePermissionPrompt: true` plus a `ccv -y` alias has lost guardrails on their own dotfiles and shell init — recommend explicit `permissions.deny` entries for those paths, not silence.
- **The skill cannot replace thinking.** When the workflow says "categorize → tier", that mechanizes the *bookkeeping*, not the *judgment*. Each Tier 1 candidate still needs the question "is this actually good for *this* user given *this* posture?" — sometimes the answer flips the direction of the recommendation entirely (see the protection-shrinking gotcha above).
- **Listing items verbatim is the failure mode** — if your output mirrors the CHANGELOG, you've added no value. Filter aggressively.

## Files

- `references/category-mapping.md` — full table of changelog-item categories and where each maps in the user's dotfiles, plus per-category notes that capture this user's specific posture (custom hooks, ENABLE_* pattern, etc.). Read it when categorizing bullets.
- `scripts/fetch-changelog.sh` — fetch + filter helper. Always prefer this over inline `gh api` calls; it handles fallback, anchor normalization, and macOS bash quirks.

## Example invocations

```
"claude code 2.1.120부터 128까지 변경사항 검토"
"changelog #21128 review"
"최근 5개 릴리스에서 추가할거 있나"
"버전 2.1.128 검토해줘"
"release notes 보고 dotfiles에 추가할거"
```
