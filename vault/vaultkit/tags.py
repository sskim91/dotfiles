"""태그 정규화와 위반 판정.

``apply``·``register``·TIL 동기화가 노트를 고치기 전에 모두 이 모듈을
거쳐 태그를 정리한다. 그래서 ``normalize_tags``는 반드시 멱등이어야
한다(``normalize_tags(normalize_tags(x)) == normalize_tags(x)``) — 이미
정규화된 노트를 다시 돌려도 태그가 흔들리면 안 된다.

scope는 :func:`vaultkit.policy.scope_of`가 반환하는 값에 더해,
TIL 원본(``tag-mapping.json`` 값)을 정규화할 때 쓰는 ``"til-source"``를
추가로 지원한다.
"""

from __future__ import annotations

from typing import Any

from .policy import Policy

# scope_of()가 반환하는 7종 + TIL 원본 정규화 전용 "til-source".
_KNOWN_SCOPES = frozenset(
    {
        "wiki-til",
        "wiki-only",
        "projects",
        "archive",
        "sources",
        "templates",
        "inbox",
        "til-source",
    }
)


def _require_known_scope(scope: str) -> None:
    if scope not in _KNOWN_SCOPES:
        raise ValueError(f"알 수 없는 scope: {scope!r}")


def _apply_rename(tags: list[str], rename: dict[str, str]) -> list[str]:
    return [rename.get(tag, tag) for tag in tags]


def _apply_drop(tags: list[str], drop: frozenset[str]) -> list[str]:
    return [tag for tag in tags if tag not in drop]


def _apply_conditional(tags: list[str], conditional: list[dict[str, Any]]) -> list[str]:
    result = list(tags)
    for rule in conditional:
        target_tag = rule["tag"]
        prefix = rule["if_other_prefix"]
        then_action = rule.get("then")
        else_action = rule.get("else")

        if target_tag not in result:
            continue

        has_other_with_prefix = any(
            tag != target_tag and tag.startswith(prefix) for tag in result
        )
        action = then_action if has_other_with_prefix else else_action

        next_result: list[str] = []
        for tag in result:
            if tag != target_tag:
                next_result.append(tag)
                continue
            if action == "drop":
                continue
            next_result.append(action)
        result = next_result
    return result


def _drop_prefixed(tags: list[str], prefixes: frozenset[str]) -> list[str]:
    return [tag for tag in tags if not any(tag.startswith(p) for p in prefixes)]


def _dedup_preserve_order(tags: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for tag in tags:
        if tag not in seen:
            seen.add(tag)
            result.append(tag)
    return result


def normalize_tags(tags: list[str], policy: Policy, scope: str) -> list[str]:
    """태그 목록을 정책에 따라 정규화한다.

    적용 순서: rename -> drop -> conditional ->
    (scope가 projects/til-source가 아니면 facet 접두사 삭제) ->
    (scope가 wiki-only면 ``til`` 삭제). 그 뒤 순서를 유지한 채 첫 등장
    기준으로 중복을 제거한다.

    scope가 ``"wiki-til"``이면 아무것도 하지 않고 입력을 그대로
    돌려준다 — 원본은 TIL이고, 같은 규칙을 TIL 원본(tag-mapping.json)에
    적용하는 것은 ``--til-mapping``(scope="til-source")의 몫이다.
    """
    if scope == "wiki-til":
        return list(tags)
    _require_known_scope(scope)

    result = _apply_rename(list(tags), policy.rename)
    result = _apply_drop(result, policy.drop)
    result = _apply_conditional(result, policy.conditional)

    if scope not in ("projects", "til-source"):
        result = _drop_prefixed(result, policy.drop_outside_projects)

    if scope == "wiki-only":
        result = [tag for tag in result if tag != "til"]

    return _dedup_preserve_order(result)


def tag_violations(tags: list[str], policy: Policy, scope: str) -> list[str]:
    """정규화되지 않은/규칙을 벗어난 태그를 사람이 읽는 사유 목록으로 보고한다.

    검사 항목: 첫 세그먼트가 허용 밖(scope가 projects면 domains ∪
    facets, 그 외는 domains), 세그먼트 1개인데 single_segment_allowed
    밖, 세그먼트 3개 이상, ``*/untagged`` 패턴, rename/drop 대상이
    정규화되지 않고 남아 있음. 비교 전 태그 양끝 공백은 제거하며
    대소문자는 그대로 비교한다(정책이 소문자이므로 대문자 태그는
    domains 밖 위반으로 보고된다).
    """
    _require_known_scope(scope)

    allowed_first_segments = (
        policy.domains | policy.facets if scope == "projects" else policy.domains
    )

    reasons: list[str] = []
    for raw_tag in tags:
        tag = raw_tag.strip()
        segments = tag.split("/")

        if len(segments) == 1:
            if tag not in policy.single_allowed:
                reasons.append(
                    f"'{tag}': 단일 세그먼트지만 single_segment_allowed 밖"
                )
        else:
            first_segment = segments[0]
            if first_segment not in allowed_first_segments:
                scope_desc = "domains/facets" if scope == "projects" else "domains"
                reasons.append(
                    f"'{tag}': 첫 세그먼트 '{first_segment}'가 {scope_desc} 밖"
                )
            if len(segments) >= 3:
                reasons.append(f"'{tag}': 세그먼트 3개 이상")
            if segments[-1] == "untagged":
                reasons.append(f"'{tag}': '*/untagged' 패턴")

        if tag in policy.rename:
            reasons.append(f"'{tag}': rename 대상이 정규화되지 않고 남음")
        if tag in policy.drop:
            reasons.append(f"'{tag}': drop 대상이 정규화되지 않고 남음")

    return reasons
