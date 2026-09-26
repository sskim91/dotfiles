"""frontmatter 라인 파서·편집기.

vault 노트의 frontmatter를 줄 단위로 파싱·재작성한다. 표준 라이브러리만
쓰고(PyYAML 금지, spec 3.1 참고), 변경하지 않은 키는 원본 raw 라인을
그대로 다시 써서 본문·기타 키의 바이트를 보존한다.

지원 형태: ``key: value``, ``key: "quoted"``, ``key: []``,
``key:`` 다음 줄들의 ``  - item``, 단순 스칼라 항목만으로 된 인라인 흐름
시퀀스 ``key: [a, b, c]``(따옴표·공백 변형 포함). 그 외(중첩 dict, 블록
스칼라, 인라인 매핑, 중첩된 인라인 시퀀스, 항목 따옴표 안 쉼표, 중복 키
등)는 ``parse()``가 ``None``을 반환한다 — 절대 수정하지 않고 보고만 하는
정책(Global Constraint) 때문이다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_LINE_RE = re.compile(r"[^\n]*\n|[^\n]+$")
_KEY_RE = re.compile(r"^([A-Za-z_][\w-]*):\s?(.*)$")
_LIST_ITEM_RE = re.compile(r"^\s+-\s(.*)$")
_BLOCK_SCALARS = {"|", ">", "|-", ">-", "|+", ">+"}

# ": " 는 별도 체크. 그 외 특수문자는 위치와 무관하게 등장하면 따옴표 처리.
_ANYWHERE_SPECIAL = set("*&!|>'\"%@`#")
_LEADING_SPECIAL = set("[{")


@dataclass
class Doc:
    has_fm: bool
    fields: dict[str, str | list[str] | None]
    order: list[str]
    body: str
    _raw: dict[str, list[str]] = field(default_factory=dict)
    # 아래 셋은 브리프의 인터페이스 밖 내부 필드(라운드트립·CRLF 보존용).
    _open_raw: str = "---\n"
    _close_raw: str = "---\n"
    _nl: str = "\n"


def _parse_inline_flow_list(inner: str) -> list[str] | None:
    """``key: [a, b, c]`` 값의 대괄호 안(``inner``)을 파싱한다.

    단순 스칼라 항목(따옴표 유무·앞뒤 공백 무관)만 지원한다. 항목 안에
    ``[``/``]``/``{``/``}``가 있으면(중첩 컬렉션) 또는 따옴표로 감싼 항목
    안에 쉼표가 있으면(구분자와 구분 불가) ``None``을 반환해 상위에서
    전체 문서 파싱을 포기하게 한다.
    """
    items: list[str] = []
    buf: list[str] = []
    quote: str | None = None
    quoted_comma = False

    for ch in inner:
        if quote is not None:
            buf.append(ch)
            if ch == ",":
                quoted_comma = True
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
            buf.append(ch)
            continue
        if ch in "[]{}":
            return None
        if ch == ",":
            items.append("".join(buf))
            buf = []
            continue
        buf.append(ch)

    if quote is not None:
        return None  # 닫히지 않은 따옴표
    items.append("".join(buf))

    if quoted_comma:
        return None

    return [item.strip() for item in items]


def _split_line(raw: str) -> tuple:
    """줄 종결자를 분리한다. (내용, 종결자) — 종결자 없으면 ``""``."""
    if raw.endswith("\r\n"):
        return raw[:-2], "\r\n"
    if raw.endswith("\n"):
        return raw[:-1], "\n"
    return raw, ""


def parse(text: str) -> Doc | None:
    """frontmatter를 파싱한다.

    첫 줄이 정확히 ``---``가 아니면 frontmatter 없음(``has_fm=False``)으로
    본다. 첫 줄이 ``---``인데 닫는 ``---``를 찾지 못하거나, 지원 밖 형태
    (중첩 dict, 블록 스칼라, 인라인 컬렉션, 중복 키, 빈 줄/주석)를 만나면
    ``None``을 반환한다.
    """
    matches = list(_LINE_RE.finditer(text))
    if not matches:
        return Doc(has_fm=False, fields={}, order=[], body=text, _raw={})

    first_content, first_nl = _split_line(matches[0].group())
    if first_content != "---":
        return Doc(has_fm=False, fields={}, order=[], body=text, _raw={})

    close_idx = None
    for i in range(1, len(matches)):
        content, _ = _split_line(matches[i].group())
        if content == "---":
            close_idx = i
            break
    if close_idx is None:
        return None

    fields: dict = {}
    order: list = []
    raw: dict = {}
    current_key = None
    current_is_open = False

    for i in range(1, close_idx):
        raw_line = matches[i].group()
        content, _ = _split_line(raw_line)

        if content == "":
            return None  # 빈 줄: 지원 밖

        item_match = _LIST_ITEM_RE.match(content)
        if item_match:
            if current_key is None or not current_is_open:
                return None
            item_raw = item_match.group(1)
            existing = fields[current_key]
            if existing is None:
                existing = []
                fields[current_key] = existing
            existing.append(item_raw)
            raw[current_key].append(raw_line)
            continue

        if content[0].isspace():
            return None  # 들여쓴 비-리스트 라인: 중첩 dict 등 지원 밖

        if content.lstrip().startswith("#"):
            return None  # 주석: 지원 밖

        key_match = _KEY_RE.match(content)
        if not key_match:
            return None

        key, rest = key_match.group(1), key_match.group(2)
        if key in raw:
            return None  # 중복 키

        current_key = key
        order.append(key)
        raw[key] = [raw_line]

        if rest == "":
            current_is_open = True
            fields[key] = None
        elif rest == "[]":
            current_is_open = False
            fields[key] = []
        elif rest in _BLOCK_SCALARS:
            return None
        elif rest.startswith("["):
            if not rest.endswith("]"):
                return None  # 닫는 ] 없음: 지원 밖
            parsed_items = _parse_inline_flow_list(rest[1:-1])
            if parsed_items is None:
                return None  # 중첩 컬렉션·따옴표 안 쉼표 등: 지원 밖
            current_is_open = False
            fields[key] = parsed_items
        elif rest.startswith("{"):
            return None  # 인라인 매핑: 지원 밖
        else:
            current_is_open = False
            fields[key] = rest

    close_raw = matches[close_idx].group()
    body = text[matches[close_idx].end() :]

    return Doc(
        has_fm=True,
        fields=fields,
        order=order,
        body=body,
        _raw=raw,
        _open_raw=matches[0].group(),
        _close_raw=close_raw,
        _nl=first_nl or "\n",
    )


def _unquote(raw: str) -> str:
    """값의 바깥 따옴표(단일 쌍)를 벗겨 반환한다."""
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in ("'", '"'):
        inner = raw[1:-1]
        if raw[0] == '"':
            inner = inner.replace('\\"', '"').replace("\\\\", "\\")
        return inner
    return raw


def _needs_quote(value: str) -> bool:
    if not value:
        return False
    if value[0] in _LEADING_SPECIAL:
        return True
    if ": " in value:
        return True
    return any(ch in value for ch in _ANYWHERE_SPECIAL)


def _quote(value: str) -> str:
    """set_list/set_scalar가 새로 쓰는 값에 대한 따옴표 규칙(컨트롤러 ruling)."""
    if value.startswith("[["):
        needs = True
    else:
        needs = _needs_quote(value)
    if not needs:
        return value
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def get_list(doc: Doc, key: str) -> list:
    """값을 리스트로 반환한다(문자열 스칼라도 1원소 리스트로, 바깥 따옴표는 벗김)."""
    value = doc.fields.get(key)
    if value is None:
        return []
    if isinstance(value, list):
        return [_unquote(item) for item in value]
    return [_unquote(value)]


def set_list(doc: Doc, key: str, values: list) -> None:
    """리스트 값을 설정한다.

    이미 블록 리스트 형태(``key:\\n  - item``)로 쓰여 있고 값이 실질적으로
    같으면 원본 raw를 그대로 둔다. 문자열 스칼라(``key: value``), 인라인
    흐름 시퀀스(``key: [a, b]``), ``None``이던 값은 내용이 같아도 표준 블록
    리스트 출력 형식으로 정규화한다 — 이 형태들을 그대로 두면 브리프가 정한
    리스트 출력 형식을 벗어나기 때문이다. (빈 리스트 ``key: []``는 어느
    형태로 재작성하든 출력이 동일해 예외 없이 그대로 둔다.)
    """
    current = doc.fields.get(key)
    raw_lines = doc._raw.get(key)
    is_block_list_form = isinstance(current, list) and (
        not current or (raw_lines is not None and len(raw_lines) > 1)
    )
    if key in doc._raw and is_block_list_form and get_list(doc, key) == list(values):
        return
    doc.fields[key] = [_quote(v) for v in values]
    doc._raw.pop(key, None)
    if key not in doc.order:
        doc.order.append(key)
    doc.has_fm = True


def set_scalar(doc: Doc, key: str, value: str) -> None:
    """스칼라 값을 설정한다. 값이 실질적으로 같으면 원본 raw를 그대로 둔다."""
    current = doc.fields.get(key)
    if key in doc._raw and isinstance(current, str) and _unquote(current) == value:
        return
    doc.fields[key] = _quote(value)
    doc._raw.pop(key, None)
    if key not in doc.order:
        doc.order.append(key)
    doc.has_fm = True


def reorder(doc: Doc, order: list) -> None:
    """``order``에 있는 키를 그 순서로 앞에, 나머지는 원래 상대 순서로 뒤에 둔다."""
    existing_set = set(doc.order)
    front = [k for k in order if k in existing_set]
    front_set = set(front)
    rest = [k for k in doc.order if k not in front_set]
    doc.order = front + rest


def _render_field(key: str, value, nl: str) -> str:
    if value is None:
        return f"{key}:{nl}"
    if isinstance(value, list):
        if not value:
            return f"{key}: []{nl}"
        lines = [f"{key}:{nl}"]
        lines.extend(f"  - {item}{nl}" for item in value)
        return "".join(lines)
    return f"{key}: {value}{nl}"


def render(doc: Doc) -> str:
    """Doc을 다시 텍스트로 만든다. 변경 없는 키는 원본 raw 라인 그대로."""
    if not doc.has_fm:
        return doc.body

    parts = [doc._open_raw]
    for key in doc.order:
        if key in doc._raw:
            parts.append("".join(doc._raw[key]))
        else:
            parts.append(_render_field(key, doc.fields.get(key), doc._nl))
    parts.append(doc._close_raw)
    parts.append(doc.body)
    return "".join(parts)
