#!/bin/bash
# Fetch and filter Codex CLI release notes from openai/codex GitHub releases.
#
# Usage:
#   fetch-codex-changelog.sh                         # last 5 stable releases
#   fetch-codex-changelog.sh 10                      # last N stable releases
#   fetch-codex-changelog.sh 0.137.0                 # single release
#   fetch-codex-changelog.sh rust-v0.137.0           # single release
#   fetch-codex-changelog.sh 0.136.0 0.137.0         # inclusive range
#   fetch-codex-changelog.sh --include-prerelease 5  # include alpha/pre-releases
#
# Output: markdown release sections, newest first.

set -euo pipefail

REPO="openai/codex"

fetch_releases() {
	if command -v gh >/dev/null 2>&1; then
		if gh api "repos/$REPO/releases?per_page=100" 2>/dev/null; then
			return 0
		fi
	fi
	curl -fsSL "https://api.github.com/repos/$REPO/releases?per_page=100"
}

tmp="$(mktemp -t codex-releases.XXXXXX.json)"
trap 'rm -f "$tmp"' EXIT
fetch_releases >"$tmp"

python3 - "$tmp" "$@" <<'PY'
import json
import re
import sys

path = sys.argv[1]
args = sys.argv[2:]

include_prerelease = False
if args and args[0] == "--include-prerelease":
    include_prerelease = True
    args = args[1:]

if len(args) > 2:
    print("Usage: fetch-codex-changelog.sh [--include-prerelease] [N | VERSION | LO HI]", file=sys.stderr)
    sys.exit(1)

with open(path, "r", encoding="utf-8") as f:
    releases = json.load(f)

def normalize_version(value: str) -> str:
    value = value.strip()
    value = value.removeprefix("rust-v")
    value = value.removeprefix("v")
    return value

def version_key(value: str):
    value = normalize_version(value)
    main, _, suffix = value.partition("-")
    nums = [int(part) for part in main.split(".") if part.isdigit()]
    while len(nums) < 3:
        nums.append(0)
    # Stable sorts after prerelease for the same numeric version.
    stable_rank = 1 if not suffix else 0
    return (*nums[:3], stable_rank, suffix)

def rel_version(rel):
    return normalize_version(rel.get("name") or rel.get("tag_name") or "")

filtered = []
for rel in releases:
    version = rel_version(rel)
    if not re.match(r"^\d+\.\d+\.\d+", version):
        continue
    if not include_prerelease and (rel.get("prerelease") or "-" in version):
        continue
    filtered.append(rel)

filtered.sort(key=lambda rel: version_key(rel_version(rel)), reverse=True)

mode = "last"
n = 5
lo = hi = None

if len(args) == 1:
    if re.match(r"^\d+$", args[0]):
        n = int(args[0])
    else:
        mode = "single"
        lo = normalize_version(args[0])
elif len(args) == 2:
    mode = "range"
    lo = normalize_version(args[0])
    hi = normalize_version(args[1])
    if version_key(lo) > version_key(hi):
        lo, hi = hi, lo

if mode == "last":
    selected = filtered[:n]
elif mode == "single":
    selected = [rel for rel in filtered if rel_version(rel) == lo]
else:
    selected = [
        rel
        for rel in filtered
        if version_key(lo) <= version_key(rel_version(rel)) <= version_key(hi)
    ]

if not selected:
    print("No matching Codex CLI releases found.", file=sys.stderr)
    sys.exit(1)

print("Source: https://developers.openai.com/codex/changelog")
print("GitHub: https://github.com/openai/codex/releases")
print()

for rel in selected:
    version = rel_version(rel)
    tag = rel.get("tag_name", "")
    published = (rel.get("published_at") or "").split("T")[0]
    url = rel.get("html_url", "")
    body = (rel.get("body") or "").strip()

    print(f"## Codex CLI {version}")
    if published:
        print(f"Published: {published}")
    if tag:
        print(f"Tag: {tag}")
    if url:
        print(f"Release: {url}")
    print(f"Install: `npm install -g @openai/codex@{version}`")
    print()
    print(body)
    print()
PY
