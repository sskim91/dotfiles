"""위키링크 추출과 링크 대상 색인.

깨진 링크 점검(``check``의 ``link`` kind)이 쓴다. 과거에 표 안의
``[[a\\|b]]``와 코드블록 속 ``[[...]]``를 깨진 링크로 오판한 사고가 있어,
코드(펜스·인라인)는 먼저 지우고, ``\\|``는 별칭 구분자로 다루며, 같은
노트 안의 ``[[#heading]]``은 대상에서 뺀다.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

_FENCE_RE = re.compile(r"^[ \t]*(```|~~~)")
_INLINE_CODE_RE = re.compile(r"(`+)(?:(?!\1).)+?\1")
_WIKILINK_RE = re.compile(r"\[\[([^\[\]\n]*)\]\]")


def _strip_code(text: str) -> str:
    """펜스 코드블록(```/~~~)과 인라인 코드 구간을 지운 텍스트를 돌려준다."""
    kept: list[str] = []
    fence: str | None = None
    for line in text.splitlines():
        match = _FENCE_RE.match(line)
        if fence is None:
            if match:
                fence = match.group(1)
                continue
            kept.append(_INLINE_CODE_RE.sub("", line))
        elif match and match.group(1) == fence:
            fence = None
    return "\n".join(kept)


def wikilinks(text: str) -> list[str]:
    """텍스트(frontmatter 포함)의 위키링크 대상 basename을 등장 순서대로 반환한다.

    ``[[a|b]]``/``[[a\\|b]]`` -> ``a``, ``[[a#h]]`` -> ``a``,
    ``[[dir/a]]`` -> ``a``, ``![[img.png]]`` -> ``img.png``. 대상이 빈
    링크(``[[#h]]`` 등)와 코드 안의 링크는 제외한다. 확장자(``.md`` 등)는
    그대로 두며 정규화는 호출자 몫이다.
    """
    targets: list[str] = []
    for match in _WIKILINK_RE.finditer(_strip_code(text)):
        inner = match.group(1).replace("\\|", "|")
        target = inner.split("|", 1)[0].split("#", 1)[0].strip()
        if not target:
            continue
        targets.append(target.rsplit("/", 1)[-1])
    return targets


def _nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def link_key(target: str) -> str:
    """링크 대상 비교 키: NFC, 끝 ``.md`` 제거, 대소문자 무시(Obsidian 해석과 동일)."""
    key = _nfc(target)
    if key.lower().endswith(".md"):
        key = key[:-3]
    return key.casefold()


def link_targets(root: Path) -> set[str]:
    """vault 전체에서 링크로 가리킬 수 있는 이름의 :func:`link_key` 집합.

    ``.md``는 확장자를 뺀 stem, 그 밖의 파일은 확장자 포함 파일명.
    ``.obsidian`` 같은 점(.)으로 시작하는 경로는 건너뛴다.
    """
    keys: set[str] = set()
    for path in root.rglob("*"):
        rel_parts = path.relative_to(root).parts
        if any(part.startswith(".") for part in rel_parts) or not path.is_file():
            continue
        keys.add(link_key(path.name))
    return keys
