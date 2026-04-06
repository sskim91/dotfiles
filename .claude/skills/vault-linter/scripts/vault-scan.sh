#!/bin/bash
# vault-scan.sh — Vault Linter의 결정적 검증 스크립트
# 자연어 해석 없이 정확한 결과를 보장하는 wikilink/orphan 검사

set -euo pipefail

VAULT="${VAULT:-$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/Note}"

# 노트 인덱스 캐시 (세션 내 1회만 빌드)
_NOTE_INDEX=""

# macOS 파일시스템은 NFD, 노트 본문은 NFC → 비교 전 통일 필요
nfc() {
    python3 -c "import sys,unicodedata; [print(unicodedata.normalize('NFC',l),end='') for l in sys.stdin]"
}

usage() {
    cat <<'EOF'
Usage: vault-scan.sh <command> [args]

Commands:
  list-notes              List all vault notes (basename without .md)
  extract-links <file>    Extract [[wikilinks]] from a file (one per line)
  check-links <file>      Check which links in a file are broken (outputs broken ones)
  find-orphans            Find notes not referenced by any other note
  tag-list                List all tags with counts

Environment:
  VAULT    Vault path (default: ~/Library/Mobile Documents/.../Note)
EOF
    exit 1
}

# 제외 대상 필터 (Template, .obsidian)
# iCloud 경로에 공백("Mobile Documents")이 포함되므로 -print0 버전도 제공
find_notes() {
    find "$VAULT" -name "*.md" \
        -not -path "*/Templates/*" \
        -not -path "*/.obsidian/*" \
        -not -name "Vault-Lint-Report*" \
        2>/dev/null
}

find_notes0() {
    find "$VAULT" -name "*.md" \
        -not -path "*/Templates/*" \
        -not -path "*/.obsidian/*" \
        -not -name "Vault-Lint-Report*" \
        -print0 \
        2>/dev/null
}

# 노트 이름 인덱스 빌드 (find + mdfind 병합, 중복 제거)
# iCloud evicted 파일은 find가 못 찾을 수 있으므로 mdfind로 보완
build_note_index() {
    if [[ -n "$_NOTE_INDEX" ]]; then
        echo "$_NOTE_INDEX"
        return
    fi
    local from_find from_mdfind
    from_find=$(find_notes | while read -r f; do basename "$f" .md; done | nfc)
    from_mdfind=$(mdfind -onlyin "$VAULT" 'kMDItemFSName == "*.md"' 2>/dev/null \
        | grep -v '/.obsidian/' | grep -v '/Templates/' \
        | grep -v 'Vault-Lint-Report' \
        | while read -r f; do basename "$f" .md; done | nfc)
    # LC_ALL=C: macOS default locale sort -u merges distinct Korean names via ICU collation
    _NOTE_INDEX=$(printf '%s\n%s' "$from_find" "$from_mdfind" | LC_ALL=C sort -u)
    echo "$_NOTE_INDEX"
}

cmd_list_notes() {
    build_note_index
}

cmd_extract_links() {
    local file="$1"
    # 코드블록(```)을 제거한 후 [[링크]] 추출 (false positive 방지)
    # [[링크|별칭]] 에서 링크 부분만 추출
    # strip trailing \ (markdown table pipe escape: [[link\|alias]])
    sed '/^```/,/^```/d' "$file" 2>/dev/null \
        | grep -oE '\[\[[^]|]+' \
        | sed 's/\[\[//; s/\\$//' | nfc | LC_ALL=C sort -u
}

cmd_check_links() {
    local file="$1"
    local broken=0
    local index
    index=$(build_note_index)

    while IFS= read -r link; do
        # 인덱스에서 인메모리 매칭 (find 호출 제거)
        if ! echo "$index" | LC_ALL=C grep -qxF "$link"; then
            echo "$link"
            broken=$((broken + 1))
        fi
    done < <(cmd_extract_links "$file")

    return $broken
}

cmd_find_orphans() {
    # 전체 vault의 wikilink를 한 번에 수집 (공백 경로 안전)
    local all_links
    # orphan 탐지에서는 코드블록 제거 불필요 (false positive가 참조를 늘려 정밀도 향상)
    all_links=$(find_notes0 | xargs -0 grep -ohE '\[\[[^]|]+' 2>/dev/null | sed 's/\[\[//; s/\\$//' | nfc | LC_ALL=C sort -u)

    local index
    index=$(build_note_index)

    echo "$index" | while IFS= read -r name; do
        [[ -z "$name" ]] && continue
        if ! echo "$all_links" | grep -qxF "$name"; then
            echo "$name"
        fi
    done
}

cmd_tag_list() {
    # tags: 블록 내의 항목만 추출 (source 등 다른 필드의 URL 제외)
    find_notes0 | xargs -0 awk '
        FNR==1 { fm=0; tags=0 }
        /^---$/ && !fm { fm=1; next }
        /^---$/ && fm { fm=0; tags=0; next }
        fm && /^tags:/ { tags=1; next }
        fm && tags && /^[^ ]/ { tags=0 }
        fm && tags && /^  - / { print }
    ' 2>/dev/null \
        | grep -E '^\s+-\s+\S+/\S+' \
        | sed 's/^[[:space:]]*-[[:space:]]*//' \
        | sort | uniq -c | sort -rn
}

# --- Main ---
[[ $# -lt 1 ]] && usage

case "$1" in
    list-notes)     cmd_list_notes ;;
    extract-links)  [[ $# -lt 2 ]] && usage; cmd_extract_links "$2" ;;
    check-links)    [[ $# -lt 2 ]] && usage; cmd_check_links "$2" ;;
    find-orphans)   cmd_find_orphans ;;
    tag-list)       cmd_tag_list ;;
    *)              usage ;;
esac
