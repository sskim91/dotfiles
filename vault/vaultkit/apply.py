"""기계적 수정 적용.

``vk apply``가 부르는 :func:`run_apply`는 정책으로 결정되는 수정만 한다:
태그 정규화, 폴더별 frontmatter 순서, wiki-only topics 표기, 대응표로
결정되는 MOC/허브 등록(``added``만), MOC 개수 표기. Wiki의 TIL 노트
(scope ``wiki-til``)는 노트 파일을 절대 쓰지 않는다 — 원본은 TIL이며,
같은 규칙은 ``til_mapping=True``로 ``tag-mapping.json``에 적용한다
(scope ``til-source``).

모든 쓰기는 내용이 달라질 때만 하며, 쓰기 직전 원본을
``<백업 루트>/<YYYYmmdd-HHMMSS>/<상대경로>``에 복사한다. 백업 루트는
``backup_root`` 인자(``--backup-dir``) > ``VAULTKIT_BACKUP_DIR`` >
``~/.local/state/vaultkit/backups`` 순으로 정한다(``$TMPDIR``은 macOS가
주기적으로 지우므로 쓰지 않는다).

안전 가드:
- 비어 있지 않던 ``tags``가 정규화로 비게 되는 노트는 쓰지 않고
  ``empty_after_normalize``로 보고한다(다른 수정도 하지 않는다).
- ``til_root``가 없으면 TIL 파생 노트를 구분할 수 없으므로 쓰기 모드는
  :class:`ApplyRefused`로 거부하고, dry-run은 경고와 함께 진행한다.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

from . import frontmatter
from .check import FRONTMATTER_KEY, iter_notes, nfc, parse_note, read_text, til_stems
from .policy import Policy
from .register import register_note, update_counts
from .tags import normalize_tags

APPLY_SCOPES = frozenset({"projects", "archive", "sources", "templates", "inbox", "wiki-only"})
REGISTER_SCOPES = frozenset({"wiki-til", "wiki-only", "projects"})


class ApplyRefused(Exception):
    """쓰기 전에 apply를 거부한다(아무것도 쓰지 않음)."""


@dataclass
class ApplyResult:
    changed: list[str]
    backup_dir: Path | None
    skipped_unparseable: list[str]
    empty_after_normalize: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def backup_root(explicit: Path | None = None) -> Path:
    """백업 루트: ``explicit`` > ``VAULTKIT_BACKUP_DIR`` > ``~/.local/state/vaultkit/backups``."""
    if explicit is not None:
        return Path(explicit).expanduser()
    env = os.environ.get("VAULTKIT_BACKUP_DIR")
    if env:
        return Path(env).expanduser()
    return Path.home() / ".local/state/vaultkit/backups"


def new_backup_dir(root: Path, prefix: str = "") -> Path:
    """``root/<prefix><YYYYmmdd-HHMMSS>[-n]``을 새로 만들어 돌려준다."""
    stamp = prefix + datetime.now().strftime("%Y%m%d-%H%M%S")
    candidate = root / stamp
    n = 1
    while candidate.exists():
        candidate = root / f"{stamp}-{n}"
        n += 1
    candidate.mkdir(parents=True)
    return candidate


class _Writer:
    """변경 기록·백업·쓰기를 한곳에서 처리한다(dry-run이면 기록만)."""

    def __init__(
        self,
        dry_run: bool,
        backup_root: Path | None = None,
        on_backup_dir: Callable[[Path], None] | None = None,
    ) -> None:
        self.dry_run = dry_run
        self.changed: list[str] = []
        self.backup_dir: Path | None = None
        self._backup_root = backup_root
        self._on_backup_dir = on_backup_dir
        self._backed_up: set[str] = set()

    def mark(self, label: str) -> None:
        if label not in self.changed:
            self.changed.append(label)

    def backup(self, path: Path, backup_rel: str) -> None:
        """원본을 백업한다(파일당 한 번 — 첫 쓰기 전 상태를 남긴다)."""
        if self.dry_run or backup_rel in self._backed_up or not path.is_file():
            return
        if self.backup_dir is None:
            # 첫 쓰기 전에 위치를 알린다 — 이후 예외가 나도 호출자가 경로를 안다
            self.backup_dir = new_backup_dir(backup_root(self._backup_root))
            if self._on_backup_dir is not None:
                self._on_backup_dir(self.backup_dir)
        dest = self.backup_dir / backup_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(path.read_bytes())
        self._backed_up.add(backup_rel)

    def write(self, path: Path, backup_rel: str, label: str, old: str, new: str) -> None:
        if old == new:
            return
        self.mark(label)
        if self.dry_run:
            return
        self.backup(path, backup_rel)
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(new)


def run_apply(
    policy: Policy,
    *,
    dry_run: bool,
    til_mapping: bool = False,
    backup_root: Path | None = None,
    on_backup_dir: Callable[[Path], None] | None = None,
) -> ApplyResult:
    """정책 수정을 적용한다. ``on_backup_dir``는 백업 디렉터리를 만든 직후(첫 쓰기 전) 불린다."""
    stems = til_stems(policy)
    warnings: list[str] = []
    if stems is None:
        message = f"til_root 없음({policy.til_root}): TIL 파생 노트를 구분할 수 없음"
        if not dry_run:
            raise ApplyRefused(message + " → 쓰기 거부")
        warnings.append(message + " → 모든 Wiki 노트를 wiki-only로 판정한 결과(쓰기 모드는 거부됨)")

    writer = _Writer(dry_run, backup_root, on_backup_dir)
    skipped: list[str] = []
    emptied: list[str] = []
    root = policy.vault_root
    to_register = []

    for note in iter_notes(policy, stems):
        if note.scope not in APPLY_SCOPES and note.scope not in REGISTER_SCOPES:
            continue
        doc = parse_note(note.path)
        if doc is None:
            if note.scope in APPLY_SCOPES:
                skipped.append(note.rel)
            continue
        if note.scope in APPLY_SCOPES:
            old = read_text(note.path)
            new = _fix_note(doc, note.scope, policy)
            if new is None:
                emptied.append(note.rel)
            else:
                writer.write(note.path, _rel(note.path, root), note.rel, old, new)
        if note.scope in REGISTER_SCOPES:
            to_register.append(note)

    _register(policy, to_register, writer)
    _counts(policy, writer)

    if til_mapping:
        _apply_til_mapping(policy, writer)

    return ApplyResult(
        changed=writer.changed,
        backup_dir=writer.backup_dir,
        skipped_unparseable=skipped,
        empty_after_normalize=emptied,
        warnings=warnings,
    )


def _rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _fix_note(doc: frontmatter.Doc, scope: str, policy: Policy) -> str | None:
    """태그 정규화·topics 표기·필드 순서를 적용한 텍스트. frontmatter 없으면 그대로.

    비어 있지 않던 ``tags``가 정규화로 비게 되면 ``None``(그 파일은 쓰지 않는다).
    """
    if not doc.has_fm:
        return frontmatter.render(doc)

    if "tags" in doc.fields:
        tags = frontmatter.get_list(doc, "tags")
        normalized = normalize_tags(tags, policy, scope)
        if not normalized and any(t.strip() for t in tags):
            return None
        if normalized != tags:
            frontmatter.set_list(doc, "tags", normalized)

    if scope == "wiki-only" and "topics" in doc.fields:
        topics = frontmatter.get_list(doc, "topics")
        display = [policy.topics.get(t.lower(), t) for t in topics]
        if display != topics:
            frontmatter.set_list(doc, "topics", display)

    schema = policy.frontmatter.get(FRONTMATTER_KEY.get(scope, ""))
    if schema:
        frontmatter.reorder(doc, schema.get("order", []))
    return frontmatter.render(doc)


def _registry_files(policy: Policy) -> dict[str, Path]:
    """등록이 편집할 수 있는 목차 파일: 등록 결과 target(stem) -> 경로."""
    files: dict[str, Path] = {}
    moc_dir = policy.vault_root / "Wiki" / "_MOC"
    for path in sorted(moc_dir.glob("*.md")):
        files[nfc(path.stem)] = path
    for prefix, cfg in policy.hubs.items():
        hub = cfg.get("hub")
        if hub:
            files.setdefault(nfc(hub), policy.vault_root / prefix / f"{hub}.md")
    return files


def _register(policy: Policy, notes, writer: _Writer) -> None:
    root = policy.vault_root
    files = _registry_files(policy)
    for note in notes:
        probe = register_note(note.path, policy, dry_run=True)
        if probe.status != "added":
            continue
        target = files.get(nfc(probe.target or ""))
        if target is None:
            continue
        writer.mark(nfc(_rel(target, root)))
        if writer.dry_run:
            continue
        writer.backup(target, _rel(target, root))
        register_note(note.path, policy, dry_run=False)


def _counts(policy: Policy, writer: _Writer) -> None:
    root = policy.vault_root
    pending = update_counts(policy, dry_run=True)
    for path in pending:
        writer.mark(nfc(_rel(path, root)))
        writer.backup(path, _rel(path, root))
    if pending and not writer.dry_run:
        update_counts(policy, dry_run=False)


def _apply_til_mapping(policy: Policy, writer: _Writer) -> None:
    """``tag-mapping.json`` 값에 TIL 원본용 태그 규칙(scope ``til-source``)을 적용한다.

    ``til-source``는 facet 접두사(``work/``·``customer/``)를 지우지 않는다 —
    이 파일이 Wiki 태그의 원본이라, 여기서 지우면 다음 동기화에서 Wiki에서도
    사라진다. 키 순서는 보존한다. 값이 문자열이면 1원소 리스트로 보고
    정규화하며, 결과가 그대로면 문자열 형태를 유지한다.
    """
    path = policy.til_root / "tag-mapping.json"
    if not path.is_file():
        return
    old = read_text(path)
    data = json.loads(old)
    normalized = {}
    for key, tags in data.items():
        as_list = [tags] if isinstance(tags, str) else list(tags)
        result = normalize_tags(as_list, policy, "til-source")
        normalized[key] = tags if isinstance(tags, str) and result == as_list else result
    if normalized == data:
        return
    new = json.dumps(normalized, indent=2, ensure_ascii=False) + "\n"
    writer.write(path, "TIL/tag-mapping.json", str(path), old, new)
