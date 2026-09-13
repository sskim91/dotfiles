# Codex hook defaults. Independent of Claude's ENABLE_* shell variables.
# Explicit CODEX_ENABLE_* environment overrides take precedence.
CODEX_ENABLE_RUFF=${CODEX_ENABLE_RUFF:-1}
CODEX_ENABLE_ENV_FILE_CHECK=${CODEX_ENABLE_ENV_FILE_CHECK:-0}
CODEX_ENABLE_SECRET_SCAN=${CODEX_ENABLE_SECRET_SCAN:-0}
