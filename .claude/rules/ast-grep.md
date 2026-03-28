# ast-grep for Structural Code Search

When a code search involves **structure** (negation, nesting, containment) rather than text, use `ast-grep` and invoke the `ast-grep` skill.

Signals: "without error handling", "missing try-catch", "inside class methods", "functions with N+ params", "deprecated pattern usages", structural refactoring.

Not for shell scripts (Bash/Zsh support is limited).
