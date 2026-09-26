"""TIL -> Wiki 동기화의 순수 로직(spec 5).

파일 탐색·git diff·실제 쓰기는 호출자(TIL git hook, 1회 이관 스크립트)의
몫이다. 이 모듈은 TIL 노트 하나를 Wiki용 값으로 만들고(:func:`build_note`),
기존 Wiki 문서·상태 엔트리와 비교해 무엇을 할지 판정한다(:func:`merge`).
유일한 파일 쓰기는 :func:`save_state`(임시 파일 + ``os.replace``)다.

판정표(spec 5.2)와 :class:`Decision` 필드:

======================  ==================  ===========  ==============================
Wiki 문서 / state        action              text         entry
======================  ==================  ===========  ==============================
없음 / 없음               create              새 문서       synced(gen 본문 해시)
없음 / synced             retire              None         retired
있음·없음 / retired        skip-retired        None         retired (그대로)
있음·없음 / 형식 오류       conflict            None         기존 엔트리 그대로
있음 / 없음               conflict            None         None (state에 기록하지 않음)
있음(파싱 불가) / synced   conflict            None         기존 엔트리 그대로
있음 / 본문 해시 일치      update              병합 문서     synced(gen 본문 해시)
있음 / 불일치·내용 동등**  update              병합 문서     synced(gen 본문 해시)
있음 / 불일치·내용 다름    frontmatter-only    병합 문서*    기존 엔트리 그대로
결과 == 기존 (update)      unchanged           None         synced(gen 본문 해시)
======================  ==================  ===========  ==============================

``*`` frontmatter-only는 병합 결과가 기존 문서와 같아도 action을 유지하고
``text=None``으로 돌려준다 — "TIL로 이관 필요" 보고가 사라지면 안 되고,
body_sha를 Wiki 본문 해시로 전진시키면 다음 TIL 변경이 Wiki 수정을 덮기
때문이다. 호출자는 ``text``가 None이 아닐 때만 쓴다.

``**`` 내용 동등: Wiki 본문과 TIL 생성 본문의 body_sha가 같거나, 링크
표기만 정규화(역변환 -> 정방향)한 뒤 같을 때. 사용자가 Wiki 수정을 TIL로
옮기면 다음 동기화에서 frontmatter-only를 벗어난다(컨트롤러 판정, 리뷰 1차).

링크 변환(정방향/역방향)은 서로의 역이 되도록 맞춘다.

- 정방향: ``[x](./s.md)``, ``[x](s.md)``, ``[x](../dir/s.md)`` (+ ``#h``)
  -> ``[[s#h|x]]``, 텍스트가 ``s#h``와 같으면 ``[[s#h]]``. 표 행(``|``로
  시작하는 줄) 안에서는 ``\\|``로 쓴다.
- 역방향: ``[[s#h|x]]`` -> 같은 폴더면 ``[x](./s.md#h)``, 다른 폴더면
  ``[x](../dir/s.md#h)``.
- 양쪽 모두 fenced code block과 인라인 코드 안은 건드리지 않는다.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import tempfile
import unicodedata
from collections.abc import Iterator
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

from . import frontmatter as fm
from .policy import Policy, load_policy
from .tags import normalize_tags

# 정방향 링크: [텍스트](./stem.md#h) | (stem.md) | (../dir/stem.md)
# stem은 ``.``을 포함할 수 있다(Jackson-3.0, llms.txt-AI). 첫 글자는 ``.``이 아니고,
# 끝의 ``.md`` 뒤에는 ``#`` 또는 ``)``만 온다(.mdx·.md.bak 제외).
_STEM = r"[\w\-][\w\-.]*"
INTERNAL_LINK_PATTERN = re.compile(
    rf"\[([^\]]+)\]\((?:\./|\.\./[\w\-]+/)?({_STEM})\.md(#[^)\n]*)?\)"
)
_STEM_RE = re.compile(_STEM)
# 역방향: ![[...]] 포함, 별칭 구분자는 | 또는 표 안의 \|
_WIKI_LINK_PATTERN = re.compile(r"(!?)\[\[([^\]\|]*?)(?:(\\?\|)([^\]]*))?\]\]")
_INLINE_CODE = re.compile(r"(`+)[^\n]*?(?<!`)\1(?!`)")
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_SOURCE_SECTION = re.compile(r"## 출처\s*\n([\s\S]*?)(?=\n## |\Z)")
_SOURCE_URL = re.compile(r"\[.*?\]\((https?://[^\)]+)\)|<(https?://[^>\s]+)>")

Action = Literal[
    "create", "update", "frontmatter-only", "unchanged", "conflict", "retire", "skip-retired"
]


@dataclass
class Generated:
    stem: str  # NFC
    title: str
    sources: list[str]
    topics: list[str]
    tags: list[str]
    til_links: list[str]  # "[[stem]]" 형식, 첫 등장 순서
    body: str  # Wiki frontmatter 뒤에 올 본문


@dataclass
class Decision:
    action: Action
    text: str | None
    entry: dict | None
    message: str


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


# ------------------------------------------------------------------
# 코드 영역 분리
# ------------------------------------------------------------------


def _matches_outside_code(text: str, pattern: re.Pattern) -> Iterator[re.Match]:
    """fenced code block 밖에서, 인라인 코드 안에서 시작하지 않는 매치를 순서대로 낸다.

    인라인 코드로 구간을 자르지 않고 매치 시작 위치로만 거른다 — 그래야
    ``[`code`](./a.md)``처럼 레이블 안에 백틱이 든 링크도 인식된다.
    """
    pos = 0
    plain_start = 0
    fence: str | None = None
    regions: list[tuple[int, int]] = []
    for line in text.splitlines(keepends=True):
        m = _FENCE.match(line)
        if fence is None and m:
            regions.append((plain_start, pos))
            fence = m.group(1)
        elif fence is not None and m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence):
            fence = None
            plain_start = pos + len(line)
        pos += len(line)
    if fence is None:
        regions.append((plain_start, len(text)))

    for start, end in regions:
        code = [c.span() for c in _INLINE_CODE.finditer(text, start, end)]
        for m in pattern.finditer(text, start, end):
            if not any(a <= m.start() < b for a, b in code):
                yield m


def _sub_outside_code(text: str, pattern: re.Pattern, repl) -> str:
    """코드 밖에서만 ``pattern``을 치환한다. ``repl(match, text)``."""
    out: list[str] = []
    last = 0
    for m in _matches_outside_code(text, pattern):
        out.append(text[last : m.start()])
        out.append(repl(m, text))
        last = m.end()
    out.append(text[last:])
    return "".join(out)


def _in_table_row(text: str, index: int) -> bool:
    line_start = text.rfind("\n", 0, index) + 1
    return text[line_start:index].lstrip().startswith("|")


# ------------------------------------------------------------------
# 정방향: TIL -> Wiki
# ------------------------------------------------------------------


def extract_title(content: str) -> str:
    """첫 번째 ``# `` 제목."""
    match = re.search(r"^# (.+)$", content, re.MULTILINE)
    return match.group(1).strip() if match else "Untitled"


def extract_sources(content: str) -> list[str]:
    """``## 출처`` 섹션의 ``[..](url)``·``<url>`` 출처를 등장 순서대로."""
    match = _SOURCE_SECTION.search(content)
    if not match:
        return []
    return [a or b for a, b in _SOURCE_URL.findall(match.group(1))]


def extract_related_notes(content: str) -> list[str]:
    """코드 밖 내부 링크 대상을 ``[[stem]]``으로, 중복 없이 순서 유지."""
    seen: set[str] = set()
    notes: list[str] = []
    for m in _matches_outside_code(content, INTERNAL_LINK_PATTERN):
        stem = m.group(2)
        if _nfc(stem) not in seen:
            seen.add(_nfc(stem))
            notes.append(f"[[{stem}]]")
    return notes


def convert_internal_links(content: str) -> str:
    """``[제목](./stem.md#h)`` -> ``[[stem#h|제목]]`` (코드 밖, 표 안은 ``\\|``)."""

    def replace(m: re.Match, text: str) -> str:
        label, stem, anchor = m.group(1), m.group(2), m.group(3) or ""
        target = stem + anchor
        if _nfc(label) == _nfc(target):
            return f"[[{target}]]"
        sep = "\\|" if _in_table_row(text, m.start()) else "|"
        return f"[[{target}{sep}{label}]]"

    return _sub_outside_code(content, INTERNAL_LINK_PATTERN, replace)


def _tags_for(stem: str, folder: str, policy: Policy, mapping: dict[str, list[str]]) -> list[str]:
    raw = mapping.get(stem)
    if not raw:
        raw = [f"{policy.til_folder_domain.get(folder, folder)}/untagged"]
    tags = normalize_tags(list(raw), policy, "til-source")
    if "til" not in tags:
        tags.append("til")
    return tags


def build_note(
    src: Path, folder: str, policy: Policy, mapping: dict[str, list[str]]
) -> Generated:
    """TIL 노트 파일 하나를 Wiki용 값으로 만든다(쓰기 없음)."""
    content = src.read_text(encoding="utf-8")

    if content.startswith("---"):
        end_match = re.search(r"\n---\n", content[3:])
        if end_match:
            content = content[3 + end_match.end() :]

    title = extract_title(content)
    sources = extract_sources(content)
    related = extract_related_notes(content)

    content = re.sub(r"^# .+\n+", "", content, count=1, flags=re.MULTILINE)
    body = convert_internal_links(content)

    stem = _nfc(src.stem)
    return Generated(
        stem=stem,
        title=title,
        sources=sources,
        topics=[policy.topics.get(folder, folder)],
        tags=_tags_for(stem, folder, policy, mapping),
        til_links=related,
        body=body,
    )


# ------------------------------------------------------------------
# 병합 판정
# ------------------------------------------------------------------


def body_sha(body: str) -> str:
    """NFC + 줄 끝 공백 제거 + 끝 빈 줄 제거 후 sha256 hex."""
    lines = [line.rstrip() for line in _nfc(body).split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


@lru_cache(maxsize=1)
def _default_policy() -> Policy:
    """``merge``에 policy를 넘기지 않았을 때 쓰는 기본 정책(로드 실패는 그대로 올림)."""
    return load_policy()


def _apply_fields(doc: fm.Doc, gen: Generated, today: str, order: list[str]) -> None:
    fm.set_scalar(doc, "title", gen.title)
    if gen.sources:
        fm.set_list(doc, "source", gen.sources)
    elif "source" in doc.order:
        doc.order.remove("source")
        doc.fields.pop("source", None)
        doc._raw.pop("source", None)
    fm.set_list(doc, "topics", gen.topics)

    existing_related = fm.get_list(doc, "related_notes")
    seen = {_nfc(x) for x in existing_related}
    related = list(existing_related)
    for link in gen.til_links:
        if _nfc(link) not in seen:
            seen.add(_nfc(link))
            related.append(link)
    if related:
        fm.set_list(doc, "related_notes", related)

    fm.set_list(doc, "tags", gen.tags)
    if not fm.get_list(doc, "created"):
        fm.set_scalar(doc, "created", today)
    fm.reorder(doc, order)


def merge(
    gen: Generated,
    existing: str | None,
    entry: dict | None,
    today: str,
    policy: Policy | None = None,
) -> Decision:
    """spec 5.2 판정표. 모듈 docstring의 표 참고.

    frontmatter 키 순서는 ``policy.frontmatter["Wiki"]["order"]``
    (policy가 None이면 기본 ``load_policy()``).
    """
    order = list((policy or _default_policy()).frontmatter["Wiki"]["order"])
    status = (entry or {}).get("status")
    new_entry = {"body_sha": body_sha(gen.body), "status": "synced"}

    if status == "retired":
        return Decision("skip-retired", None, entry, "retired 노트 → 다시 만들지 않음")

    if entry is not None and status != "synced":
        return Decision("conflict", None, entry, "상태 엔트리 형식 오류 → 쓰지 않음")

    if existing is None:
        if status == "synced":
            return Decision(
                "retire", None, {"status": "retired"}, "Wiki에서 삭제됨 → retired로 기록, 만들지 않음"
            )
        doc = fm.parse("---\n---\n")
        doc.body = gen.body
        _apply_fields(doc, gen, today, order)
        return Decision("create", fm.render(doc), new_entry, "Wiki에 새로 생성")

    if entry is None:
        return Decision(
            "conflict", None, None, "Wiki 전용 노트와 이름 충돌 → 쓰지 않음(수동 확인 필요)"
        )

    doc = fm.parse(existing)
    if doc is None:
        return Decision("conflict", None, entry, "Wiki 문서 frontmatter 파싱 불가 → 쓰지 않음")

    body_matches_state = body_sha(doc.body) == entry.get("body_sha")
    if body_matches_state or _same_content(doc.body, gen.body):
        doc.body = gen.body
        _apply_fields(doc, gen, today, order)
        text = fm.render(doc)
        if text == existing:
            return Decision("unchanged", None, new_entry, "변경 없음")
        if body_matches_state:
            return Decision("update", text, new_entry, "TIL 변경 반영(본문 교체 + frontmatter 병합)")
        return Decision(
            "update", text, new_entry, "Wiki 본문이 TIL과 내용 동등 → 동기화 재개(body_sha 갱신)"
        )

    _apply_fields(doc, gen, today, order)
    text = fm.render(doc)
    return Decision(
        "frontmatter-only",
        None if text == existing else text,
        entry,
        "Wiki에서 본문 수정됨 → TIL로 이관 필요",
    )


# ------------------------------------------------------------------
# 상태 파일
# ------------------------------------------------------------------


def _empty_state() -> dict:
    return {"version": 2, "notes": {}}


def load_state(path: Path) -> dict:
    """상태 파일을 읽는다. 부재·v1(평면 dict)은 빈 v2. 손상되면 ValueError."""
    try:
        raw_text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return _empty_state()
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"상태 파일 파싱 실패: {path} ({exc})") from exc
    if not isinstance(data, dict):
        raise ValueError(f"상태 파일 형식 오류: {path}")
    if "version" not in data:
        return _empty_state()  # v1: {stem: hash}
    if data.get("version") != 2 or not isinstance(data.get("notes"), dict):
        raise ValueError(f"지원하지 않는 상태 파일 형식: {path}")
    return data


def save_state(path: Path, state: dict) -> None:
    """같은 디렉터리 임시 파일에 쓴 뒤 ``os.replace``로 교체한다."""
    text = json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        try:
            fh = os.fdopen(fd, "w", encoding="utf-8")
        except BaseException:
            os.close(fd)
            raise
        with fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)  # 이 함수가 만든 임시 파일만 정리(원래 예외를 가리지 않음)
        raise
    # rename 내구성: 디렉터리 fsync(지원하지 않는 파일시스템이면 건너뜀)
    with contextlib.suppress(OSError):
        dir_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)


# ------------------------------------------------------------------
# 역방향: Wiki -> TIL (1회 이관)
# ------------------------------------------------------------------


def reverse_port(
    wiki_text: str, title: str, til_index: dict[str, str], folder: str
) -> tuple[str, list[str]]:
    """Wiki 문서를 TIL 본문으로 되돌린다. (TIL 텍스트, 변환 못한 링크 목록).

    ``til_index``: TIL stem -> 폴더. 대상이 TIL에 없거나, 정방향 규칙이
    다시 인식할 수 없는 stem이거나, 임베드(``![[..]]``)·같은 노트 링크면
    원문 그대로 두고 목록에 넣는다.
    """
    doc = fm.parse(wiki_text)
    if doc is None:
        raise ValueError("Wiki 문서 frontmatter 파싱 불가")
    index = {_nfc(k): v for k, v in til_index.items()}
    unresolved: list[str] = []
    body = _reverse_links(doc.body, index.get, folder, unresolved)
    return f"# {title}\n\n{body}", unresolved


def _reverse_links(body: str, folder_of, folder: str, unresolved: list[str]) -> str:
    """코드 밖 ``[[..]]``를 TIL 상대 링크로 바꾼다. ``folder_of(nfc_stem)``이
    None이면(또는 정방향이 다시 인식할 수 없으면) 원문 그대로 두고
    ``unresolved``에 넣는다."""

    def replace(m: re.Match, _text: str) -> str:
        bang, target, alias = m.group(1), m.group(2), m.group(4)
        stem, _, heading = target.partition("#")
        anchor = f"#{heading}" if "#" in target else ""
        target_folder = folder_of(_nfc(stem))
        if (
            bang
            or target_folder is None
            or not _STEM_RE.fullmatch(stem)
            or ")" in anchor
            or (alias is not None and alias == "")
        ):
            unresolved.append(m.group(0))
            return m.group(0)
        prefix = "./" if target_folder == folder else f"../{target_folder}/"
        label = target if alias is None else alias
        return f"[{label}]({prefix}{stem}.md{anchor})"

    return _sub_outside_code(body, _WIKI_LINK_PATTERN, replace)


def _canonical_link_form(body: str) -> str:
    """링크 표기만 정규화한 본문(역변환 -> 정방향 변환).

    대상 폴더는 정방향 결과에 남지 않으므로 모든 대상을 같은 폴더로 보고
    역변환한다. 두 본문의 이 값이 같으면 링크 표기(``[x](s.md)`` vs
    ``[[s|x]]``, 표 안 ``\\|``, ``[[a|a]]`` vs ``[[a]]``)만 다르다.
    """
    return convert_internal_links(_reverse_links(body, lambda _stem: "", "", []))


def _same_content(wiki_body: str, gen_body: str) -> bool:
    if body_sha(wiki_body) == body_sha(gen_body):
        return True
    return body_sha(_canonical_link_form(wiki_body)) == body_sha(_canonical_link_form(gen_body))
