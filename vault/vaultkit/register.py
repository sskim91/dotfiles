"""MOC·허브·패치노트 표 등록.

새 노트가 Wiki(→ MOC)나 Projects(→ 허브/패치노트 표) 어디에 만들어져도,
그 노트가 속할 목차 파일과 섹션을 정책(``vault-policy.json``의 ``moc``/
``hubs``)에서 찾아 한 줄을 덧붙인다. 이미 등록돼 있으면 아무것도 하지
않는다(멱등).

이 모듈이 편집하는 대상은 항상 목차/허브 파일(MOC, ``00 … 시작하기``,
``GenOS 버전별 변경 요약``)이지 노트 자신이 아니다 — 노트는 태그와 요약
문장을 읽는 데만 쓰인다.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from . import frontmatter
from .policy import Policy
from .tags import normalize_tags

RegisterStatus = Literal["added", "exists", "unclassified", "skipped"]


@dataclass
class RegisterResult:
    status: RegisterStatus
    target: str | None
    section: str | None
    line: str | None


# ---------------------------------------------------------------------------
# 공통 유틸
# ---------------------------------------------------------------------------


def _nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def _read(path: Path) -> str:
    """줄 끝(CRLF 등)을 바꾸지 않고 읽는다 — 목차 파일의 줄바꿈 방식 보존."""
    with open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def _write(path: Path, text: str) -> None:
    """``text``의 줄 끝을 그대로 쓴다(플랫폼 변환 없음)."""
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def _newline_of(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


_HEADING_RE = re.compile(r"^#{1,6}\s")
_LIST_ITEM_RE = re.compile(r"^- ")
_SENTENCE_END_RE = re.compile(r"[.?!](?=\s|$)")
_WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")


def _resolve_wikilinks(text: str) -> str:
    """``[[a|b]]`` -> ``b``, ``[[a]]`` -> ``a``로 위키링크를 평문으로 푼다.

    등록 줄의 요약에 다른 노트 링크가 그대로 남으면, 그 노트가 이미
    등록된 것으로 ``exists`` 판정을 오염시킬 수 있어 여기서 미리 없앤다.
    """
    return _WIKILINK_RE.sub(
        lambda m: m.group(2) if m.group(2) is not None else m.group(1), text
    )


def summary_line(path: Path) -> str:
    """노트 본문 첫 문단의 첫 문장을 반환한다.

    callout(``>``로 시작하는 줄), heading, 코드블록(```` ``` ````로 감싼
    구간)은 건너뛴다. 위키링크는 평문으로 푼다. 60자(코드포인트 기준)
    초과 시 60자에서 잘라 ``…``을 붙인다.
    """
    text = path.read_text(encoding="utf-8")
    doc = frontmatter.parse(text)
    body = doc.body if doc is not None else text

    in_code = False
    paragraph_lines: list[str] = []
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if line == "":
            if paragraph_lines:
                break
            continue
        if _HEADING_RE.match(line):
            if paragraph_lines:
                break
            continue
        if line.startswith(">"):
            if paragraph_lines:
                break
            continue
        paragraph_lines.append(line)

    paragraph = _resolve_wikilinks(_nfc(" ".join(paragraph_lines)))
    match = _SENTENCE_END_RE.search(paragraph)
    sentence = paragraph[: match.end()] if match else paragraph

    if len(sentence) > 60:
        sentence = sentence[:60] + "…"
    return sentence


def _exists_in(text: str, stem: str) -> bool:
    """``text`` 안에 ``[[stem`` 이 이미 있는지(NFC 비교, 경계 포함) 확인한다."""
    text_nfc = _nfc(text)
    stem_nfc = _nfc(stem)
    pattern = re.compile(r"\[\[" + re.escape(stem_nfc) + r"(?=[|\]#\\])")
    return pattern.search(text_nfc) is not None


def _majority(counter: dict[str, int]) -> str:
    """빈도 최다 키를 반환한다. 동률이면 알파벳순 첫 키."""
    best_key = None
    best_count = -1
    for key in sorted(counter):
        count = counter[key]
        if count > best_count:
            best_count = count
            best_key = key
    return best_key


# ---------------------------------------------------------------------------
# register_note
# ---------------------------------------------------------------------------


def register_note(path: Path, policy: Policy, *, dry_run: bool = False) -> RegisterResult:
    vault_root = policy.vault_root.resolve()
    note_path = path.resolve()
    try:
        rel = note_path.relative_to(vault_root)
    except ValueError:
        return RegisterResult("skipped", None, None, None)

    rel_nfc = _nfc(str(rel))
    parts = Path(rel_nfc).parts
    if not parts:
        return RegisterResult("skipped", None, None, None)

    top = parts[0]

    if top == "Wiki":
        if len(parts) != 2:
            return RegisterResult("skipped", None, None, None)
        return _register_wiki(note_path, parts[1], policy, dry_run=dry_run)

    if top == "Projects":
        return _register_project(note_path, rel_nfc, policy, dry_run=dry_run)

    return RegisterResult("skipped", None, None, None)


def _read_note_tags(note_path: Path) -> list[str] | None:
    """노트의 raw 태그(정규화 전)를 읽는다. 파싱 불가면 ``None``."""
    text = note_path.read_text(encoding="utf-8")
    doc = frontmatter.parse(text)
    if doc is None or not doc.has_fm:
        return None
    return frontmatter.get_list(doc, "tags")


def _read_normalized_tags(
    note_path: Path, policy: Policy, scope: str
) -> list[str] | None:
    """노트 태그를 읽어 정책 정규화(rename/drop/conditional)를 적용해 반환한다.

    ``moc``/``hubs.section_by_tag``는 정규화된(canonical) 태그 형태로
    쓰여 있으므로, 아직 정규화 적용(Task 8) 전인 노트라도 여기서 맞춰
    비교해야 매칭이 어긋나지 않는다.
    """
    tags = _read_note_tags(note_path)
    if tags is None:
        return None
    return normalize_tags(tags, policy, scope=scope)


def _moc_lookup(tags: list[str], moc: dict[str, list[str]]) -> list[str] | None:
    """태그를 순서대로 보며, 각 태그에 대해 정확 일치 -> 도메인 와일드카드 순으로 찾는다."""
    for tag in tags:
        if tag in moc:
            return moc[tag]
        domain = tag.split("/", 1)[0]
        wildcard = f"{domain}/*"
        if wildcard in moc:
            return moc[wildcard]
    return None


def _find_existing_wiki_registration(
    vault_root: Path, stem: str
) -> tuple[str, str | None] | None:
    """``Wiki/_MOC/MOC-*.md`` 전체에서 ``stem``이 이미 등록돼 있는지 찾는다.

    태그로 고른 대상 파일 하나만 보면, 사람이 실제로는 다른 MOC에 등록해
    둔 노트를 "아직 없음"으로 오판해 두 번째 MOC에 중복 등록하게 된다
    (컨트롤러 fix 1). 찾으면 ``(실제 MOC stem, 그 안의 절 이름)``을
    반환한다 — 절 이름은 알아낼 수 없으면 ``None``.
    """
    moc_dir = vault_root / "Wiki" / "_MOC"
    stem_nfc = _nfc(stem)
    pattern = re.compile(r"\[\[" + re.escape(stem_nfc) + r"(?=[|\]#\\])")

    for moc_path in sorted(moc_dir.glob("MOC-*.md")):
        text = _read(moc_path)
        if not _exists_in(text, stem):
            continue
        section = None
        current_section = None
        for raw_line in _nfc(text).splitlines():
            heading = re.match(r"^## (.+)$", raw_line)
            if heading:
                current_section = heading.group(1).strip()
                continue
            if pattern.search(raw_line):
                section = current_section
                break
        return moc_path.stem, section

    return None


def _register_wiki(
    note_path: Path, filename: str, policy: Policy, *, dry_run: bool
) -> RegisterResult:
    stem = Path(filename).stem

    existing = _find_existing_wiki_registration(policy.vault_root, stem)
    if existing is not None:
        moc_stem, section = existing
        return RegisterResult("exists", moc_stem, section, None)

    tags = _read_normalized_tags(note_path, policy, "wiki-only")
    if not tags:
        return RegisterResult("unclassified", None, None, None)

    match = _moc_lookup(tags, policy.moc)
    if match is None:
        return RegisterResult("unclassified", None, None, None)

    moc_stem, section = match
    target_path = policy.vault_root / "Wiki" / "_MOC" / f"{moc_stem}.md"
    if not target_path.exists():
        return RegisterResult("unclassified", None, None, None)

    target_text = _read(target_path)

    summary = summary_line(note_path)
    new_line = f"- [[{stem}]] — {summary}"

    new_text = _insert_into_section(target_text, section, new_line)
    if new_text is None:
        return RegisterResult("unclassified", None, None, None)

    if not dry_run:
        _write(target_path, new_text)

    return RegisterResult("added", moc_stem, section, new_line)


def _ensure_trailing_newline(text: str) -> str:
    """``text``가 개행 없이 끝나면 개행 하나를 붙여 돌려준다.

    Obsidian은 끝 개행을 강제하지 않는다. 개행 없이 끝난 파일에 줄 단위로
    삽입하면 새 줄이 기존 마지막 줄에 그대로 붙어 항목이 깨진다
    (컨트롤러 fix 2). 파일에서 이미 쓰인 개행 방식(``\\r\\n``)을 따른다.
    """
    if text == "" or text.endswith(("\n", "\r\n")):
        return text
    nl = "\r\n" if "\r\n" in text else "\n"
    return text + nl


def _insert_into_section(text: str, section: str, new_line: str) -> str | None:
    """``## {section}`` 절의 마지막 ``- `` 항목 뒤에 ``new_line``을 삽입한다.

    절을 찾지 못하면 ``None``을 반환한다.
    """
    text = _ensure_trailing_newline(text)
    lines = text.splitlines(keepends=True)
    section_nfc = _nfc(section)

    heading_idx = None
    for i, raw in enumerate(lines):
        stripped = raw.rstrip("\r\n")
        if stripped.startswith("## ") and _nfc(stripped[3:].strip()) == section_nfc:
            heading_idx = i
            break
    if heading_idx is None:
        return None

    end_idx = len(lines)
    for i in range(heading_idx + 1, len(lines)):
        if lines[i].rstrip("\r\n").startswith("## "):
            end_idx = i
            break

    insert_at = heading_idx + 1
    for i in range(heading_idx + 1, end_idx):
        if _LIST_ITEM_RE.match(lines[i].rstrip("\r\n")):
            insert_at = i + 1

    nl = _newline_of(text)
    new_lines = lines[:insert_at] + [new_line + nl] + lines[insert_at:]
    return "".join(new_lines)


# ---------------------------------------------------------------------------
# Projects -> 허브 / 패치노트 표
# ---------------------------------------------------------------------------


def _match_hub(rel_nfc: str, hubs: dict[str, dict]) -> tuple[str, dict, str] | None:
    """가장 긴 접두 키를 찾는다. 반환: (prefix, cfg, remainder)."""
    candidates = []
    for prefix, cfg in hubs.items():
        prefix_nfc = _nfc(prefix)
        if rel_nfc == prefix_nfc:
            candidates.append((prefix_nfc, cfg, ""))
        elif rel_nfc.startswith(prefix_nfc + "/"):
            remainder = rel_nfc[len(prefix_nfc) + 1 :]
            candidates.append((prefix_nfc, cfg, remainder))
    if not candidates:
        return None
    candidates.sort(key=lambda c: len(c[0]), reverse=True)
    return candidates[0]


def _register_project(
    note_path: Path, rel_nfc: str, policy: Policy, *, dry_run: bool
) -> RegisterResult:
    matched = _match_hub(rel_nfc, policy.hubs)
    if matched is None:
        # spec D3: 대응(허브)이 없으면 미분류로 보고한다(컨트롤러 fix 3).
        return RegisterResult("unclassified", None, None, None)

    prefix, cfg, remainder = matched
    if remainder == "":
        return RegisterResult("skipped", None, None, None)

    hub_name = cfg.get("hub")
    stem = Path(remainder).stem

    if _nfc(stem) == _nfc(hub_name or ""):
        return RegisterResult("skipped", None, None, None)

    target_path = policy.vault_root / Path(prefix) / f"{hub_name}.md"
    if not target_path.exists():
        return RegisterResult("skipped", None, None, None)

    if cfg.get("mode") == "patchnote-table":
        return _register_patchnote(note_path, stem, target_path, hub_name, dry_run=dry_run)

    target_text = _read(target_path)
    if _exists_in(target_text, stem):
        return RegisterResult("exists", hub_name, None, None)

    if cfg.get("section_by_subfolder"):
        remainder_parts = Path(remainder).parts
        if len(remainder_parts) < 2:
            return RegisterResult("unclassified", None, None, None)
        section = remainder_parts[0]
    else:
        tags = _read_normalized_tags(note_path, policy, "projects")
        section_by_tag = cfg.get("section_by_tag", {})
        section = None
        if tags:
            for tag in tags:
                if tag in section_by_tag:
                    section = section_by_tag[tag]
                    break
        if section is None:
            return RegisterResult("unclassified", None, None, None)

    summary = summary_line(note_path)
    new_line = f"- [[{stem}]] — {summary}"
    new_text = _insert_into_section(target_text, section, new_line)
    if new_text is None:
        return RegisterResult("unclassified", None, None, None)

    if not dry_run:
        _write(target_path, new_text)

    return RegisterResult("added", hub_name, section, new_line)


_VERSION_RE = re.compile(r"v(\d+(?:\.\d+)*)")


def _version_tuple(text: str) -> tuple[int, ...] | None:
    match = _VERSION_RE.search(text)
    if not match:
        return None
    return tuple(int(p) for p in match.group(1).split("."))


def _register_patchnote(
    note_path: Path,
    stem: str,
    target_path: Path,
    hub_name: str,
    *,
    dry_run: bool,
) -> RegisterResult:
    target_text = _ensure_trailing_newline(_read(target_path))
    if _exists_in(target_text, stem):
        return RegisterResult("exists", hub_name, None, None)

    version_tuple = _version_tuple(stem)
    if version_tuple is None:
        return RegisterResult("unclassified", None, None, None)
    version_str = ".".join(str(p) for p in version_tuple)

    lines = target_text.splitlines(keepends=True)

    header_idx = None
    for i, raw in enumerate(lines):
        s = raw.rstrip("\r\n")
        if s.startswith("|") and header_idx is None and i + 1 < len(lines):
            sep = lines[i + 1].rstrip("\r\n")
            if re.match(r"^\|[\s:|-]+\|$", sep):
                header_idx = i
                break
    if header_idx is None:
        return RegisterResult("unclassified", None, None, None)

    header_cells = [c.strip() for c in lines[header_idx].rstrip("\r\n").strip("|").split("|")]
    n_cols = len(header_cells)

    row_start = header_idx + 2
    row_end = row_start
    for i in range(row_start, len(lines)):
        if lines[i].rstrip("\r\n").startswith("|"):
            row_end = i + 1
        else:
            break

    insert_at = row_end
    for i in range(row_start, row_end):
        row_text = lines[i].rstrip("\r\n")
        existing_version = _version_tuple(row_text)
        if existing_version is not None and existing_version > version_tuple:
            insert_at = i
            break

    content_col = None
    for idx, header in enumerate(header_cells):
        if idx == 0:
            continue
        if "핵심" in header or "변경" in header:
            content_col = idx
            break

    summary = summary_line(note_path).replace("|", "\\|")
    cells = ["-"] * n_cols
    cells[0] = f"[[{stem}\\|v{version_str}]]"
    if content_col is not None:
        cells[content_col] = summary
    elif n_cols > 1:
        cells[-1] = summary

    new_line = "| " + " | ".join(cells) + " |"

    nl = _newline_of(target_text)
    new_lines = lines[:insert_at] + [new_line + nl] + lines[insert_at:]
    new_text = "".join(new_lines)

    if not dry_run:
        _write(target_path, new_text)

    return RegisterResult("added", hub_name, None, new_line)


# ---------------------------------------------------------------------------
# update_counts
# ---------------------------------------------------------------------------

_INTRO_COUNT_RE = re.compile(r"노트 (\d+)개를")
_SUMMARY_LINE_RE = re.compile(r"^(- \[\[([^\]]+)\]\] — )(\d+)개(.*)$")


def update_counts(policy: Policy, *, dry_run: bool = False) -> list[Path]:
    """MOC 도입문·00-Wiki-MOC의 노트 개수 표기를 실제 개수로 맞춘다.

    변경이 필요했던(또는 dry_run이면 필요할) 파일 목록을 반환한다.
    """
    moc_dir = policy.vault_root / "Wiki" / "_MOC"
    changed: list[Path] = []

    counts: dict[str, int] = {}

    for moc_path in sorted(moc_dir.glob("MOC-*.md")):
        text = _read(moc_path)
        actual = len(re.findall(r"^- \[\[", text, flags=re.MULTILINE))
        counts[_nfc(moc_path.stem)] = actual

        new_text, n_subs = _INTRO_COUNT_RE.subn(f"노트 {actual}개를", text, count=1)
        if n_subs and new_text != text:
            changed.append(moc_path)
            if not dry_run:
                _write(moc_path, new_text)

    index_path = moc_dir / "00-Wiki-MOC.md"
    if index_path.exists():
        text = _read(index_path)
        original = text

        total = sum(counts.values())
        text, _ = _INTRO_COUNT_RE.subn(f"노트 {total}개를", text, count=1)

        def _replace_line(match: re.Match) -> str:
            moc_stem = _nfc(match.group(2))
            if moc_stem in counts:
                return f"{match.group(1)}{counts[moc_stem]}개{match.group(4)}"
            return match.group(0)

        lines = text.split("\n")
        lines = [
            _SUMMARY_LINE_RE.sub(_replace_line, line) if line.startswith("- [[") else line
            for line in lines
        ]
        text = "\n".join(lines)

        if text != original:
            changed.append(index_path)
            if not dry_run:
                _write(index_path, text)

    return changed


# ---------------------------------------------------------------------------
# derive_maps
# ---------------------------------------------------------------------------

_NOISE_PREFIXES = ("work/", "customer/")


def _is_noise_tag(tag: str) -> bool:
    return any(tag.startswith(p) for p in _NOISE_PREFIXES)


def _build_name_index(root: Path) -> dict[str, Path]:
    index: dict[str, Path] = {}
    if not root.exists():
        return index
    for p in root.rglob("*.md"):
        if p.is_file():
            index[_nfc(p.name)] = p
    return index


def derive_maps(policy: Policy) -> dict:
    """현재 vault(읽기 전용)에서 moc/hubs.section_by_tag/genos_subfolders 추천값을 만든다."""
    result = {
        "moc": _derive_moc(policy),
        "hubs": _derive_hub_section_by_tag(policy),
        "genos_subfolders": _derive_genos_subfolders(policy),
    }
    return result


def _derive_moc(policy: Policy) -> dict[str, list[str]]:
    moc_dir = policy.vault_root / "Wiki" / "_MOC"
    wiki_dir = policy.vault_root / "Wiki"
    wiki_index = {
        _nfc(p.name): p for p in wiki_dir.glob("*.md") if p.is_file()
    }

    tag_votes: dict[str, dict[tuple[str, str], int]] = {}
    domain_votes: dict[str, dict[tuple[str, str], int]] = {}

    for moc_path in sorted(moc_dir.glob("MOC-*.md")):
        moc_stem = _nfc(moc_path.stem)
        text = moc_path.read_text(encoding="utf-8")
        current_section = None
        for raw_line in text.splitlines():
            heading = re.match(r"^## (.+)$", raw_line)
            if heading:
                current_section = heading.group(1).strip()
                continue
            item = re.match(r"^- \[\[([^\]|#]+)", raw_line)
            if not item or current_section is None:
                continue
            stem = _nfc(item.group(1).strip())
            note_path = wiki_index.get(f"{stem}.md")
            if note_path is None:
                continue
            tags = _read_normalized_tags(note_path, policy, "wiki-only")
            if tags is None:
                continue
            for tag in tags:
                if _is_noise_tag(tag):
                    continue
                segments = tag.split("/")
                if segments[0] not in policy.domains:
                    continue
                key = (moc_stem, current_section)
                bucket = tag_votes.setdefault(tag, {})
                bucket[key] = bucket.get(key, 0) + 1
                if len(segments) > 1:
                    domain = segments[0]
                    dbucket = domain_votes.setdefault(domain, {})
                    dbucket[key] = dbucket.get(key, 0) + 1

    moc_map: dict[str, list[str]] = {}
    for tag, bucket in tag_votes.items():
        moc_stem, section = _majority(bucket)
        moc_map[tag] = [moc_stem, section]
    for domain, bucket in domain_votes.items():
        moc_stem, section = _majority(bucket)
        moc_map[f"{domain}/*"] = [moc_stem, section]

    return dict(sorted(moc_map.items()))


def _derive_hub_section_by_tag(policy: Policy) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for prefix, cfg in policy.hubs.items():
        if cfg.get("section_by_subfolder") or cfg.get("mode") == "patchnote-table":
            continue
        hub_dir = policy.vault_root / Path(prefix)
        hub_path = hub_dir / f"{cfg['hub']}.md"
        if not hub_path.exists():
            continue
        name_index = _build_name_index(hub_dir)
        text = hub_path.read_text(encoding="utf-8")

        tag_votes: dict[str, dict[str, int]] = {}
        current_section = None
        for raw_line in text.splitlines():
            heading = re.match(r"^## (.+)$", raw_line)
            if heading:
                current_section = heading.group(1).strip()
                continue
            item = re.match(r"^- \[\[([^\]|#]+)", raw_line)
            if not item or current_section is None:
                continue
            stem = _nfc(item.group(1).strip())
            note_path = name_index.get(f"{stem}.md")
            if note_path is None:
                continue
            tags = _read_normalized_tags(note_path, policy, "projects")
            if tags is None:
                continue
            for tag in tags:
                if _is_noise_tag(tag):
                    continue
                bucket = tag_votes.setdefault(tag, {})
                bucket[current_section] = bucket.get(current_section, 0) + 1

        section_by_tag = {tag: _majority(bucket) for tag, bucket in tag_votes.items()}
        if section_by_tag:
            result[prefix] = {"section_by_tag": dict(sorted(section_by_tag.items()))}

    return result


def _derive_genos_subfolders(policy: Policy) -> dict[str, list[str]]:
    genos_prefix = None
    for prefix, cfg in policy.hubs.items():
        if cfg.get("section_by_subfolder"):
            genos_prefix = prefix
            break
    if genos_prefix is None:
        return {}

    genos_dir = policy.vault_root / Path(genos_prefix)
    if not genos_dir.exists():
        return {}

    other_hub_prefixes = {
        _nfc(prefix) for prefix in policy.hubs if prefix != genos_prefix
    }

    result: dict[str, list[str]] = {}
    for sub in sorted(p for p in genos_dir.iterdir() if p.is_dir()):
        sub_prefix = _nfc(f"{genos_prefix}/{sub.name}")
        if sub_prefix in other_hub_prefixes:
            continue
        counts: dict[str, int] = {}
        for note_path in sorted(sub.glob("*.md")):
            tags = _read_normalized_tags(note_path, policy, "projects")
            if not tags:
                continue
            for tag in tags:
                if _is_noise_tag(tag):
                    continue
                counts[tag] = counts.get(tag, 0) + 1
        if not counts:
            continue
        top5 = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
        result[_nfc(sub.name)] = [tag for tag, _ in top5]

    return result
