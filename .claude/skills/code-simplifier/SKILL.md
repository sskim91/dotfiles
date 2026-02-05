---
name: code-simplifier
description: Code review and improvement suggestions. Select scope from recent commit, current session work, or staged files.
user_invocable: true
---

# Code Simplifier

A refactoring skill that improves code clarity, consistency, and maintainability.

## Usage

```
/code-simplifier              # Interactive scope selection
/code-simplifier <file_path>  # Review specific file directly
```

## Instructions

### Step 1: Scope Selection

If a file path is provided as argument, skip to Step 2.

Otherwise, use **AskUserQuestion** to determine review scope:

```
header: "Scope"
question: "Which code should I review?"
options:
  - label: "Recent commit"
    description: "Analyze changes from the most recent commit"
  - label: "Current session work"
    description: "Files modified during this conversation"
  - label: "Staged files"
    description: "Files staged in git status"
```

**If user selects Other**, accept custom file/directory path input.

### Step 2: Code Collection

Collect code based on selected scope:

| Scope | Collection Method |
|-------|-------------------|
| Recent commit | `git show --stat HEAD` + `git diff HEAD~1` |
| Current session work | Files edited/written during conversation |
| Staged files | `git diff --cached` |
| Custom path | Read files at specified path |

### Step 3: Agent Invocation

Invoke the `code-simplifier:code-simplifier` agent using Task tool.

```
Task(
  subagent_type: "code-simplifier:code-simplifier",
  description: "Code review",
  prompt: "Review the following code. Apply language and framework-specific best practices. Organize findings by severity.

[collected code/diff content]"
)
```

## Review Categories

Agent auto-detects language/framework and reviews using these categories:

1. **Critical Issues** - Security vulnerabilities, resource leaks, concurrency bugs
2. **Potential Bugs** - Missing exception handling, type error risks
3. **Performance** - N+1 queries, inefficient loops
4. **Code Hygiene** - Dead code, magic numbers, naming issues
5. **Design** - SOLID violations, over-engineering

## Output Format

```markdown
## Review Results

### Critical (Fix Immediately)
- [file:line] Issue description + fix suggestion

### High Priority
- ...

### Medium Priority
- ...

### Suggestions
- ...
```

## Guidelines

- Preserve existing behavior during refactoring
- Verify tests pass if available
- Prefer incremental improvements
