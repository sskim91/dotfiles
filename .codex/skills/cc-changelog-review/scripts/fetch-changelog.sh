#!/bin/bash
# Fetch and filter the Claude Code CLI CHANGELOG from anthropics/claude-code.
#
# Usage:
#   fetch-changelog.sh                    # last 5 versions (default)
#   fetch-changelog.sh 10                 # last N versions
#   fetch-changelog.sh 2.1.128            # single version
#   fetch-changelog.sh 2.1.120 2.1.128    # inclusive range (low → high)
#   fetch-changelog.sh '#21128'           # GitHub anchor format (auto-converted)
#
# Output: raw markdown of selected sections, descending order (newest first).
# Falls back from `gh api` to `curl` when gh fails or rate limit is hit.
#
# Implementation note: BSD awk on macOS does not emit literal NUL bytes via
# printf "%s\0", so we render all sections to stdout as-is and filter in bash
# using version-line markers. This keeps the script portable across macOS/Linux.

set -euo pipefail

REPO="anthropics/claude-code"

fetch_raw() {
	if command -v gh >/dev/null 2>&1; then
		if out=$(gh api "repos/$REPO/contents/CHANGELOG.md" --jq '.content' 2>/dev/null); then
			if decoded=$(printf '%s' "$out" | base64 -d 2>/dev/null); then
				printf '%s' "$decoded"
				return 0
			fi
		fi
	fi
	curl -fsSL "https://raw.githubusercontent.com/$REPO/main/CHANGELOG.md"
}

# Convert GitHub anchor (e.g. "21128" or "#21128") back to dotted version "2.1.128".
# Anchors strip dots, so first digit = major, second = minor, rest = patch.
normalize_anchor() {
	local s="${1#\#}"
	if [[ "$s" =~ ^[0-9]+$ ]] && [[ ${#s} -ge 3 ]]; then
		echo "${s:0:1}.${s:1:1}.${s:2}"
	else
		echo "$s"
	fi
}

# semver-ish compare: returns 0 if $1 >= $2.
ver_ge() {
	[[ "$(printf '%s\n%s\n' "$1" "$2" | sort -V | tail -n 1)" == "$1" ]]
}

# Print just the version numbers found in the changelog, in document order.
list_versions() {
	awk '/^## [0-9]+\.[0-9]+\.[0-9]+/ {print $2}'
}

# Extract a single version's section (from "## X.Y.Z" up to the line before
# the next "## " heading or EOF). Does not use awk `exit` because that closes
# stdin and triggers SIGPIPE in the upstream `printf`, which under `set -e`
# would terminate the calling script.
extract_section() {
	local target="$1"
	awk -v target="$target" '
		/^## [0-9]+\.[0-9]+\.[0-9]+/ {
			if (in_target && $2 != target) {
				in_target = 0
			} else if ($2 == target) {
				in_target = 1
			}
		}
		in_target { print }
	'
}

main() {
	local mode="last" n=5 lo="" hi=""
	case $# in
		0) ;;
		1)
			local arg="$1"
			if [[ "$arg" =~ ^[0-9]+$ ]] && [[ ${#arg} -le 2 ]]; then
				n="$arg"
			else
				mode="single"
				lo="$(normalize_anchor "$arg")"
			fi
			;;
		2)
			mode="range"
			lo="$(normalize_anchor "$1")"
			hi="$(normalize_anchor "$2")"
			if ! ver_ge "$hi" "$lo"; then
				local tmp="$lo"; lo="$hi"; hi="$tmp"
			fi
			;;
		*)
			echo "Usage: $0 [N | VERSION | LO HI]" >&2
			exit 1
			;;
	esac

	local raw
	raw="$(fetch_raw)"

	# Build the list of versions we want, then extract each from raw.
	local -a wanted=()
	local versions
	versions="$(printf '%s' "$raw" | list_versions)"

	case "$mode" in
		last)
			while IFS= read -r v; do
				[[ -z "$v" ]] && continue
				wanted+=("$v")
				(( ${#wanted[@]} >= n )) && break
			done <<< "$versions"
			;;
		single)
			while IFS= read -r v; do
				if [[ "$v" == "$lo" ]]; then
					wanted+=("$v")
					break
				fi
			done <<< "$versions"
			;;
		range)
			while IFS= read -r v; do
				[[ -z "$v" ]] && continue
				if ver_ge "$v" "$lo" && ver_ge "$hi" "$v"; then
					wanted+=("$v")
				fi
			done <<< "$versions"
			;;
	esac

	if (( ${#wanted[@]} == 0 )); then
		echo "No matching versions found." >&2
		exit 1
	fi

	for v in "${wanted[@]}"; do
		printf '%s' "$raw" | extract_section "$v"
		echo
	done
}

main "$@"
