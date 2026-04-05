#!/usr/bin/env python3
"""vault-index.py — Generate vault index markdown file.

Writes $VAULT/00.Inbox/Vault-Index.md (full overwrite each run).
Initializes $VAULT/00.Inbox/Vault-Log.md if missing (Claude appends entries).
"""
import os
import sys
import unicodedata
import datetime
from pathlib import Path
from collections import defaultdict

VAULT = Path(os.environ.get(
    'VAULT',
    os.path.expanduser('~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Note')
))
INDEX_FILE = VAULT / '00.Inbox' / 'Vault-Index.md'
LOG_FILE = VAULT / '00.Inbox' / 'Vault-Log.md'
DATE = datetime.date.today().isoformat()

EXCLUDE_DIRS = {'99.Template', '98.image', '.obsidian'}
EXCLUDE_PREFIXES = ('Vault-Lint-Report', 'Vault-Semantic-Report')
EXCLUDE_NAMES = {'Vault-Index.md', 'Vault-Log.md'}


def extract_summary(path: Path) -> str:
    """First meaningful body line: skips frontmatter, headings, table rows."""
    try:
        with open(path, encoding='utf-8') as f:
            in_fm = False
            for i, raw in enumerate(f):
                s = raw.rstrip('\n').strip()
                if i == 0 and s == '---':
                    in_fm = True
                    continue
                if in_fm:
                    if s == '---':
                        in_fm = False
                    continue
                if not s or s.startswith('#') or s.startswith('|'):
                    continue
                # Strip blockquote / callout markers
                if s.startswith('>'):
                    s = s.lstrip('>').strip()
                    if not s:
                        continue
                return unicodedata.normalize('NFC', s.replace('\t', ' '))[:100]
    except Exception:
        pass
    return ''


def main() -> int:
    entries: dict[str, list[tuple[str, str]]] = defaultdict(list)

    for md in VAULT.rglob('*.md'):
        parts = md.relative_to(VAULT).parts
        if any(p in EXCLUDE_DIRS for p in parts):
            continue
        if md.name in EXCLUDE_NAMES:
            continue
        if any(md.name.startswith(p) for p in EXCLUDE_PREFIXES):
            continue

        folder = parts[0]
        name = unicodedata.normalize('NFC', md.stem)
        summary = extract_summary(md)
        entries[folder].append((name, summary))

    for folder in entries:
        entries[folder].sort(key=lambda x: x[0])

    total = sum(len(v) for v in entries.values())

    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        f.write(
            f"---\n"
            f"tags:\n"
            f"  - vault/maintenance\n"
            f"created: {DATE}\n"
            f"---\n\n"
            f"# Vault Index\n\n"
            f"> 자동 생성 (vault-linter --index). 수동 편집 금지.\n"
            f"> 생성일: {DATE} | 총 {total}개 노트\n\n"
        )
        for folder in sorted(entries.keys()):
            items = entries[folder]
            f.write(f"## {folder} ({len(items)})\n\n")
            for name, summary in items:
                if summary:
                    f.write(f"- [[{name}]] — {summary}\n")
                else:
                    f.write(f"- [[{name}]]\n")
            f.write("\n")

    print(f"Wrote: {INDEX_FILE}")
    print(f"Total: {total} notes across {len(entries)} folders")

    if not LOG_FILE.exists():
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            f.write(
                f"---\n"
                f"tags:\n"
                f"  - vault/maintenance\n"
                f"created: {DATE}\n"
                f"---\n\n"
                f"# Vault Maintenance Log\n\n"
                f"> Append-only. 각 entry는 vault-linter --index 실행 시 Claude가 추가.\n"
                f"> 포맷: `## [YYYY-MM-DD] phase summary`\n\n"
            )
        print(f"Initialized: {LOG_FILE}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
