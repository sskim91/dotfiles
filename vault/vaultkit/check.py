"""vault 점검(읽기 전용).

``vk check``가 부르는 :func:`run_check`는 vault·스킬 사본을 훑어 정책
위반을 :class:`Finding` 목록으로 보고한다. 아무 파일도 쓰지 않는다.
scope ``other``(``Wiki/_MOC``, ``Attachments``, ``Excalidraw`` 등)의
노트는 점검 대상에서 빠진다 — MOC 파일 자체는 ``moc-duplicate``/
``count`` 점검이 따로 다룬다.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path

from . import frontmatter
from .links import link_key, link_targets, wikilinks
from .policy import Policy, scope_of
from .register import register_note, update_counts
from .tags import tag_violations

KINDS = (
    "tag",
    "frontmatter",
    "unparseable",
    "moc-missing",
    "moc-duplicate",
    "hub-missing",
    "count",
    "link",
    "til-body-edited",  # 예약: 판정 로직은 TIL 동기화(Task 6)가 제공
    "name-conflict",  # 예약: Task 6 이후 연결
    "wiki-only-til-tag",
    "skill-drift",
    "tag-empty",
)

# tags가 비었거나 없으면 안 되는 scope(분류·MOC 등록이 태그에 의존).
TAG_REQUIRED_SCOPES = ("wiki-til", "wiki-only", "projects")

# 규칙 문서를 가리켜야 하는 노트 관련 스킬(Claude판·Codex판 공통).
NOTE_SKILLS = (
    "obsidian-note",
    "youtube-summarizer",
    "translate-article",
    "tech-blog-writer",
    "genos-knowledge-capture",
    "write-genos-patch-notes",
    "til",
    "til-tagger",
    "vault-linter",
)
RULE_DOC_REF = "vault/references/note-rules.md"

# TIL 저장소에서 노트 폴더가 아닌 최상위 폴더.
TIL_NON_NOTE_DIRS = frozenset({"scripts"})

# scope -> policy.frontmatter 키. inbox/templates는 스키마가 없다.
FRONTMATTER_KEY = {
    "wiki-til": "Wiki",
    "wiki-only": "Wiki",
    "projects": "Projects",
    "sources": "Sources",
    "archive": "Archive",
}


@dataclass
class Finding:
    kind: str
    path: str
    detail: str


@dataclass
class Report:
    findings: list[Finding]
    warnings: list[str] = field(default_factory=list)

    @property
    def exit_code(self) -> int:
        return 1 if self.findings else 0

    def counts(self) -> dict[str, int]:
        return dict(sorted(Counter(f.kind for f in self.findings).items()))


@dataclass
class Note:
    path: Path  # 파일시스템 경로(원래 정규화 형태 유지 — 쓰기에 사용)
    rel: str  # vault 상대 경로, NFC(보고·비교용)
    scope: str


def nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def read_text(path: Path) -> str:
    """줄 끝(CRLF 등)을 바꾸지 않고 읽는다 — 본문 바이트 보존을 위해."""
    with open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def til_stems(policy: Policy) -> set[str] | None:
    """``til_root/*/*.md``의 stem(NFC) 집합. ``til_root``가 없으면 ``None``.

    숨김 폴더(``.github``, ``.githooks`` 등)와 ``scripts``는 노트 폴더가
    아니므로 제외한다 — 그 안의 README 등이 같은 이름의 Wiki 노트를
    wiki-til로 오판하게 만들지 않도록.
    """
    if not policy.til_root.is_dir():
        return None
    return {
        nfc(p.stem)
        for p in policy.til_root.glob("*/*.md")
        if not p.parent.name.startswith(".") and p.parent.name not in TIL_NON_NOTE_DIRS
    }


def iter_notes(policy: Policy, stems: set[str] | None) -> Iterator[Note]:
    """vault의 ``*.md``를 scope와 함께 돌려준다(점(.) 경로·scope ``other`` 제외)."""
    root = policy.vault_root
    for path in sorted(root.rglob("*.md")):
        rel_path = path.relative_to(root)
        if any(part.startswith(".") for part in rel_path.parts) or not path.is_file():
            continue
        rel = nfc(rel_path.as_posix())
        is_til = stems is not None and nfc(path.stem) in stems
        scope = scope_of(rel, is_til)
        if scope == "other":
            continue
        yield Note(path=path, rel=rel, scope=scope)


def parse_note(path: Path) -> frontmatter.Doc | None:
    try:
        return frontmatter.parse(read_text(path))
    except (UnicodeDecodeError, OSError):
        return None


def expected_order(doc: frontmatter.Doc, order: list[str]) -> list[str]:
    """``frontmatter.reorder``를 적용했을 때의 키 순서."""
    present = set(doc.order)
    front = [k for k in order if k in present]
    return front + [k for k in doc.order if k not in set(front)]


def run_check(policy: Policy) -> Report:
    report = Report(findings=[])
    add = lambda kind, path, detail: report.findings.append(Finding(kind, path, detail))

    stems = til_stems(policy)
    if stems is None:
        report.warnings.append(
            f"til_root 없음({policy.til_root}): 모든 Wiki 노트를 wiki-only로 점검한다"
        )

    targets = link_targets(policy.vault_root)
    topic_names = set(policy.topics.values())

    for note in iter_notes(policy, stems):
        try:
            text = read_text(note.path)
        except (UnicodeDecodeError, OSError) as exc:
            add("unparseable", note.rel, f"읽기 실패: {exc}")
            continue
        doc = frontmatter.parse(text)

        if note.scope != "archive":
            for target in wikilinks(text):
                if link_key(target) not in targets:
                    add("link", note.rel, f"[[{target}]]")

        if doc is None:
            if note.scope != "templates":
                add("unparseable", note.rel, "frontmatter 파싱 불가(수정하지 않음)")
            continue

        tags = frontmatter.get_list(doc, "tags")
        if note.scope in TAG_REQUIRED_SCOPES and not any(t.strip() for t in tags):
            add("tag-empty", note.rel, "tags 없음" if "tags" not in doc.fields else "tags 비어 있음")
        for reason in tag_violations(tags, policy, note.scope):
            add("tag", note.rel, reason)
        if note.scope == "wiki-only" and "til" in (t.strip() for t in tags):
            add("wiki-only-til-tag", note.rel, "Wiki 전용 노트에 'til' 태그")

        _check_frontmatter(doc, note, policy, topic_names, add)

        if note.scope in ("wiki-til", "wiki-only", "projects"):
            result = register_note(note.path, policy, dry_run=True)
            if result.status in ("added", "unclassified"):
                kind = "hub-missing" if note.scope == "projects" else "moc-missing"
                where = f"{result.target} / {result.section}" if result.target else "대응 없음"
                add(kind, note.rel, f"{result.status}: {where}")

    _check_duplicates(policy, add)

    for path in update_counts(policy, dry_run=True):
        add("count", nfc(path.relative_to(policy.vault_root).as_posix()), "노트 개수 표기 불일치")

    _check_skill_drift(policy, add)
    return report


def _check_frontmatter(doc, note: Note, policy: Policy, topic_names: set[str], add) -> None:
    schema = policy.frontmatter.get(FRONTMATTER_KEY.get(note.scope, ""))
    if not schema:
        return
    required = schema.get("required", [])
    if not doc.has_fm:
        if required:
            add("frontmatter", note.rel, "frontmatter 없음")
        return
    missing = [k for k in required if k not in doc.fields]
    if missing:
        add("frontmatter", note.rel, f"필수 필드 누락: {', '.join(missing)}")
    order = schema.get("order", [])
    if doc.order != expected_order(doc, order):
        add("frontmatter", note.rel, f"필드 순서: {', '.join(doc.order)}")
    if note.scope == "wiki-only":
        bad = [t for t in frontmatter.get_list(doc, "topics") if t not in topic_names]
        if bad:
            add("frontmatter", note.rel, f"topics 값이 policy.topics 밖: {', '.join(bad)}")


_REG_LINE_RE = re.compile(r"^- \[\[([^\]|#\\]+)")


def _registered_stems(path: Path) -> list[str]:
    return [
        nfc(m.group(1).strip())
        for line in read_text(path).splitlines()
        if (m := _REG_LINE_RE.match(line))
    ]


def _check_duplicates(policy: Policy, add) -> None:
    """MOC 전체에서 두 번 이상 등록된 노트, 허브 파일 안에서 중복 등록된 노트."""
    moc_dir = policy.vault_root / "Wiki" / "_MOC"
    seen: dict[str, list[str]] = {}
    for moc_path in sorted(moc_dir.glob("MOC-*.md")):
        for stem in _registered_stems(moc_path):
            seen.setdefault(stem, []).append(nfc(moc_path.stem))
    for stem, mocs in seen.items():
        if len(mocs) > 1:
            add("moc-duplicate", stem, f"MOC 중복 등록: {', '.join(mocs)}")

    for prefix, cfg in policy.hubs.items():
        hub_path = policy.vault_root / prefix / f"{cfg.get('hub')}.md"
        if not hub_path.is_file():
            continue
        for stem, n in Counter(_registered_stems(hub_path)).items():
            if n > 1:
                add("moc-duplicate", stem, f"허브 중복 등록: {cfg.get('hub')} x{n}")


def _check_skill_drift(policy: Policy, add) -> None:
    if len(policy.skill_roots) < 2:
        return
    for name in NOTE_SKILLS:
        skill_files = [root / name / "SKILL.md" for root in policy.skill_roots]
        if not all(p.is_file() for p in skill_files):
            continue
        missing = [str(p) for p in skill_files if RULE_DOC_REF not in read_text(p)]
        if missing:
            add("skill-drift", name, f"{RULE_DOC_REF} 미참조: {', '.join(missing)}")
