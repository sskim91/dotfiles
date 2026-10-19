#!/usr/bin/env python3
"""vault-index.py — Generate vault index markdown file.

Writes $VAULT/_Inbox/Vault-Index.md only when catalog content changes.
"""
import os
import sys
import unicodedata
import datetime
from pathlib import Path
from collections import defaultdict
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "vault"))
from vaultkit import frontmatter as fm

VAULT = Path(os.environ.get(
    'VAULT',
    os.path.expanduser('~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Note')
))
INDEX_FILE = VAULT / '_Inbox' / 'Vault-Index.md'
DATE = datetime.datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()

EXCLUDE_DIRS = {'Templates', 'Attachments', '.obsidian'}
EXCLUDE_PREFIXES = ('Vault-Lint-Report', 'Vault-Semantic-Report')
EXCLUDE_NAMES = {'Vault-Index.md', 'Vault-Log.md', '_INDEX.md'}


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


def render_frontmatter(date: str, updated: str | None = None) -> str:
    """Index frontmatter. Keys follow the Wiki order in vault-policy.json and
    the tag is already policy-normalized, so `vk apply` leaves it unchanged."""
    return (
        f"---\n"
        f'title: "Vault Index"\n'
        f"tags:\n"
        f"  - productivity/vault-maintenance\n"
        f"created: {date}\n"
        f"updated: {updated or date}\n"
        f"---\n"
    )


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

    # Dates are not part of catalog identity. Keep legacy files untouched on a no-op.
    sections = []
    for folder in sorted(entries):
        items = entries[folder]
        sections.append(f"## {folder} ({len(items)})\n\n")
        for name, summary in items:
            sections.append(f"- [[{name}]]" + (f" — {summary}" if summary else "") + "\n")
        sections.append("\n")
    catalog = "".join(sections)
    existing = INDEX_FILE.read_text(encoding="utf-8") if INDEX_FILE.exists() else None
    doc = fm.parse(existing) if existing is not None else None
    if doc is not None and not doc.has_fm:
        raise ValueError("기존 인덱스 frontmatter 없음 — 날짜를 추정하지 않고 중단")
    old_catalog = ""
    if doc is not None:
        offset = doc.body.find("## ")
        old_catalog = doc.body[offset:] if offset >= 0 else ""
    if existing is not None and old_catalog == catalog:
        print(f"Unchanged: {INDEX_FILE}")
    else:
        if doc is None:
            doc = fm.parse(render_frontmatter(DATE))
        # Preserve original creation date and unknown metadata on existing indexes.
        fm.set_scalar(doc, "updated", DATE)
        doc.body = (
            "\n# Vault Index\n\n"
            "> 자동 생성 (vault-linter --index). 수동 편집 금지.\n"
            f"> 총 {total}개 노트\n\n" + catalog
        )
        INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
        INDEX_FILE.write_text(fm.render(doc), encoding="utf-8")
        print(f"Wrote: {INDEX_FILE}")
    print(f"Total: {total} notes across {len(entries)} folders")

    return 0


if __name__ == '__main__':
    sys.exit(main())
