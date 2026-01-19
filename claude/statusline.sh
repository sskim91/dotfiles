#!/bin/bash
# Claude Code statusline - Enhanced version
# Features: directory, git, model, context (from stdin), config counts, tool activity, agent status, todo progress

input=$(cat)

# ---- color helpers ----
use_color=1
[ -n "$NO_COLOR" ] && use_color=0

C() { [ "$use_color" -eq 1 ] && printf '\033[%sm' "$1"; }
RST() { [ "$use_color" -eq 1 ] && printf '\033[0m'; }

# ---- colors ----
dir_color() { C '38;5;117'; }      # sky blue
git_color() { C '38;5;150'; }      # soft green
model_color() { C '38;5;147'; }    # light purple
version_color() { C '38;5;180'; }  # soft yellow
cc_version_color() { C '38;5;249'; } # light gray
config_color() { C '38;5;245'; }   # gray
agent_color() { C '38;5;213'; }    # pink
todo_color() { C '38;5;156'; }     # light green
rst() { RST; }

# ---- context colors based on remaining % ----
context_color_by_pct() {
  local remaining=$1
  if [ "$remaining" -le 20 ]; then
    C '38;5;203'  # coral red (danger)
  elif [ "$remaining" -le 40 ]; then
    C '38;5;215'  # peach (warning)
  else
    C '38;5;158'  # mint green (good)
  fi
}

# ---- context bar (hackathon winner style) ----
# Uses █ (full), ▄ (half), ░ (empty) blocks
context_bar() {
  local used_pct="${1:-0}" width="${2:-10}"
  [[ "$used_pct" =~ ^[0-9]+$ ]] || used_pct=0
  ((used_pct<0)) && used_pct=0; ((used_pct>100)) && used_pct=100

  local bar=""
  local progress_per_block=$((100 / width))  # 10% per block for width=10

  for ((i=0; i<width; i++)); do
    local block_threshold=$(( (i + 1) * progress_per_block ))
    local half_threshold=$(( block_threshold - progress_per_block / 2 ))

    if [[ $used_pct -ge $block_threshold ]]; then
      bar+="█"  # full block
    elif [[ $used_pct -ge $half_threshold ]]; then
      bar+="▄"  # half block
    else
      bar+="░"  # empty block
    fi
  done

  printf '%s' "$bar"
}

# ---- parse stdin JSON ----
if command -v jq >/dev/null 2>&1; then
  cwd=$(echo "$input" | jq -r '.cwd // "unknown"' 2>/dev/null)
  current_dir=$(echo "$cwd" | sed "s|^$HOME|~|g")
  model_name=$(echo "$input" | jq -r '.model.display_name // "Claude"' 2>/dev/null)
  model_version=$(echo "$input" | jq -r '.model.version // ""' 2>/dev/null)
  cc_version=$(echo "$input" | jq -r '.version // ""' 2>/dev/null)
  transcript_path=$(echo "$input" | jq -r '.transcript_path // ""' 2>/dev/null)

  # Context window from stdin (native data from Claude Code)
  ctx_input=$(echo "$input" | jq -r '.context_window.current_usage.input_tokens // 0' 2>/dev/null)
  ctx_cache_create=$(echo "$input" | jq -r '.context_window.current_usage.cache_creation_input_tokens // 0' 2>/dev/null)
  ctx_cache_read=$(echo "$input" | jq -r '.context_window.current_usage.cache_read_input_tokens // 0' 2>/dev/null)
  ctx_size=$(echo "$input" | jq -r '.context_window.context_window_size // 0' 2>/dev/null)
else
  current_dir="unknown"
  model_name="Claude"
  model_version=""
  cc_version=""
  transcript_path=""
  ctx_input=0; ctx_cache_create=0; ctx_cache_read=0; ctx_size=0
fi

# ---- git branch ----
git_branch=""
if [ -n "$cwd" ] && [ -d "$cwd" ]; then
  git_branch=$(git -C "$cwd" branch --show-current 2>/dev/null || git -C "$cwd" rev-parse --short HEAD 2>/dev/null)
fi

# ---- context calculation moved to render section ----

# ---- config counts ----
claude_md_count=0
rules_count=0
mcp_count=0
hooks_count=0

if [ -n "$cwd" ] && [ -d "$cwd" ]; then
  # Count CLAUDE.md files (project + global)
  [ -f "$cwd/CLAUDE.md" ] && claude_md_count=$((claude_md_count + 1))
  [ -f "$HOME/.claude/CLAUDE.md" ] && claude_md_count=$((claude_md_count + 1))

  # Count rules (*.md in .claude/rules or global rules)
  if [ -d "$cwd/.claude/rules" ]; then
    rules_count=$(ls -1 "$cwd/.claude/rules"/*.md 2>/dev/null | wc -l | tr -d ' ')
  fi
  if [ -d "$HOME/.claude/rules" ]; then
    global_rules=$(ls -1 "$HOME/.claude/rules"/*.md 2>/dev/null | wc -l | tr -d ' ')
    rules_count=$((rules_count + global_rules))
  fi

  # Count MCP servers from .mcp.json
  if [ -f "$cwd/.mcp.json" ]; then
    mcp_count=$(jq '.mcpServers | length' "$cwd/.mcp.json" 2>/dev/null || echo 0)
  fi
  if [ -f "$HOME/.claude/.mcp.json" ]; then
    global_mcp=$(jq '.mcpServers | length' "$HOME/.claude/.mcp.json" 2>/dev/null || echo 0)
    mcp_count=$((mcp_count + global_mcp))
  fi

  # Count hooks from settings.json
  if [ -f "$cwd/.claude/settings.json" ]; then
    hooks_count=$(jq '[.hooks // {} | to_entries[] | .value | length] | add // 0' "$cwd/.claude/settings.json" 2>/dev/null || echo 0)
  fi
  if [ -f "$HOME/.claude/settings.json" ]; then
    global_hooks=$(jq '[.hooks // {} | to_entries[] | .value | length] | add // 0' "$HOME/.claude/settings.json" 2>/dev/null || echo 0)
    hooks_count=$((hooks_count + global_hooks))
  fi
fi

# ---- transcript parsing for agents, todos ----
agent_status=""
todo_status=""

if [ -n "$transcript_path" ] && [ -f "$transcript_path" ]; then
  # Parse last 100 lines for recent activity
  transcript_tail=$(tail -n 100 "$transcript_path" 2>/dev/null)

  if [ -n "$transcript_tail" ]; then
    # Agent status: find running Task agents
    running_agents=$(echo "$transcript_tail" | jq -r '
      select(.type == "assistant") |
      .message.content[]? |
      select(.type == "tool_use" and .name == "Task") |
      .input.description // .input.prompt[:30]
    ' 2>/dev/null | tail -3)

    if [ -n "$running_agents" ]; then
      agent_status=$(echo "$running_agents" | while read desc; do
        [ -n "$desc" ] && printf "⚡%s " "$desc"
      done | sed 's/ $//')
    fi

    # TODO progress: find latest TodoWrite
    todo_data=$(echo "$transcript_tail" | jq -s '
      [.[] | select(.type == "assistant") |
       .message.content[]? |
       select(.type == "tool_use" and .name == "TodoWrite") |
       .input.todos] | last // []
    ' 2>/dev/null)

    if [ -n "$todo_data" ] && [ "$todo_data" != "[]" ] && [ "$todo_data" != "null" ]; then
      total=$(echo "$todo_data" | jq 'length' 2>/dev/null)
      completed=$(echo "$todo_data" | jq '[.[] | select(.status == "completed")] | length' 2>/dev/null)
      in_progress=$(echo "$todo_data" | jq -r '.[] | select(.status == "in_progress") | .content' 2>/dev/null | head -1)

      if [ "$total" -gt 0 ]; then
        if [ "$completed" -eq "$total" ]; then
          todo_status="✓ All done ($completed/$total)"
        elif [ -n "$in_progress" ]; then
          todo_status="▶ ${in_progress:0:25}... ($completed/$total)"
        else
          todo_status="📋 $completed/$total"
        fi
      fi
    fi
  fi
fi

# ---- session duration from transcript ----
session_duration=""
if [ -n "$transcript_path" ] && [ -f "$transcript_path" ]; then
  first_ts=$(head -1 "$transcript_path" 2>/dev/null | jq -r '.timestamp // empty' 2>/dev/null)
  if [ -n "$first_ts" ]; then
    # Parse ISO timestamp
    if command -v gdate >/dev/null 2>&1; then
      start_sec=$(gdate -d "$first_ts" +%s 2>/dev/null)
    else
      start_sec=$(date -j -f "%Y-%m-%dT%H:%M:%S" "${first_ts%%.*}" +%s 2>/dev/null)
    fi
    if [ -n "$start_sec" ]; then
      now_sec=$(date +%s)
      elapsed=$((now_sec - start_sec))
      mins=$((elapsed / 60))
      if [ "$mins" -lt 1 ]; then
        session_duration="<1m"
      elif [ "$mins" -lt 60 ]; then
        session_duration="${mins}m"
      else
        hours=$((mins / 60))
        rem_mins=$((mins % 60))
        session_duration="${hours}h ${rem_mins}m"
      fi
    fi
  fi
fi

# ==== RENDER ====

# Line 1: Project, git, model, version
printf '📁 %s%s%s' "$(dir_color)" "$current_dir" "$(rst)"

if [ -n "$git_branch" ]; then
  printf '  🌿 %s%s%s' "$(git_color)" "$git_branch" "$(rst)"
fi

printf '  🤖 %s%s%s' "$(model_color)" "$model_name" "$(rst)"

if [ -n "$cc_version" ] && [ "$cc_version" != "null" ]; then
  printf '  📟 %sv%s%s' "$(cc_version_color)" "$cc_version" "$(rst)"
fi

if [ -n "$session_duration" ]; then
  printf '  ⏱️ %s' "$session_duration"
fi

# Line 2: Context + Config counts
printf '\n'

# Context (hackathon winner style)
if [ "$ctx_size" -gt 0 ]; then
  total_tokens=$((ctx_input + ctx_cache_create + ctx_cache_read))
  context_used_pct=$((total_tokens * 100 / ctx_size))
  context_remaining_pct=$((100 - context_used_pct))
  max_k=$((ctx_size / 1000))

  ctx_bar=$(context_bar "$context_used_pct" 10)
  printf '🧠 %s%s ~%d%% of %dk tokens%s' "$(context_color_by_pct "$context_remaining_pct")" "$ctx_bar" "$context_used_pct" "$max_k" "$(rst)"
else
  printf '🧠 %s░░░░░░░░░░ ~0%% of ?k tokens%s' "$(config_color)" "$(rst)"
fi

# Config counts
printf '  %s│%s' "$(config_color)" "$(rst)"
printf '  📄 %s%d CLAUDE.md%s' "$(config_color)" "$claude_md_count" "$(rst)"
printf '  📜 %s%d rules%s' "$(config_color)" "$rules_count" "$(rst)"
printf '  🔌 %s%d MCPs%s' "$(config_color)" "$mcp_count" "$(rst)"
printf '  🪝 %s%d hooks%s' "$(config_color)" "$hooks_count" "$(rst)"

# Line 3: Agent status (if any)
if [ -n "$agent_status" ]; then
  printf '\n🤖 %s%s%s' "$(agent_color)" "$agent_status" "$(rst)"
fi

# Line 5: TODO progress (if any)
if [ -n "$todo_status" ]; then
  printf '\n📝 %s%s%s' "$(todo_color)" "$todo_status" "$(rst)"
fi

printf '\n'
