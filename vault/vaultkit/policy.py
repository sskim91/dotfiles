"""vault-policy.json 로드와 검증.

vaultkit이 다루는 모든 규칙(태그 rename/drop/conditional, frontmatter
스키마, topics, TIL 폴더 매핑, MOC/허브 등록표, 경로)의 유일한 원본은
``vault-policy.json``이다. 이 모듈은 그 파일을 읽어 :class:`Policy`로
만들고, 로드 시점에 rename/conditional 표의 정합성을 검증한다.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class PolicyError(Exception):
    """vault-policy.json 로드 또는 검증 실패."""


# vaultkit 패키지(이 파일의 부모 디렉터리) 옆, 즉 vault/vault-policy.json.
_DEFAULT_POLICY_PATH = Path(__file__).resolve().parent.parent / "vault-policy.json"


@dataclass(frozen=True)
class Policy:
    domains: frozenset[str]
    facets: frozenset[str]
    single_allowed: frozenset[str]
    rename: dict[str, str]
    drop: frozenset[str]
    conditional: list[dict[str, Any]]
    drop_outside_projects: frozenset[str]
    frontmatter: dict[str, dict[str, Any]]
    topics: dict[str, str]
    til_folder_domain: dict[str, str]
    moc: dict[str, list[str]]
    hubs: dict[str, dict[str, Any]]
    genos_subfolders: dict[str, list[str]]
    vault_root: Path
    til_root: Path
    skill_roots: list[Path]


def load_policy(path: Path | None = None) -> Policy:
    """``vault-policy.json``을 읽어 검증된 :class:`Policy`를 반환한다.

    path가 없으면 vaultkit 패키지 옆 ``vault-policy.json``을 기본으로 쓴다.
    파싱 실패나 규칙 위반(rename 연쇄, 허용 밖 대상 등)은 모두
    :class:`PolicyError`로 올라온다.
    """
    policy_path = path if path is not None else _DEFAULT_POLICY_PATH

    try:
        raw_text = policy_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PolicyError(f"vault-policy.json을 읽을 수 없음: {policy_path} ({exc})") from exc

    try:
        raw: dict[str, Any] = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise PolicyError(f"vault-policy.json 파싱 실패: {policy_path} ({exc})") from exc

    tags = raw.get("tags", {})
    domains = frozenset(tags.get("domains", []))
    facets = frozenset(tags.get("project_facets", []))
    single_allowed = frozenset(tags.get("single_segment_allowed", []))
    drop_outside_projects = frozenset(tags.get("drop_outside_projects", []))
    rename: dict[str, str] = dict(tags.get("rename", {}))
    drop = frozenset(tags.get("drop", []))
    conditional: list[dict[str, Any]] = list(tags.get("conditional", []))

    _validate_rename_and_conditional(
        rename=rename,
        conditional=conditional,
        domains=domains,
        facets=facets,
        single_allowed=single_allowed,
    )

    paths = raw.get("paths", {})
    try:
        vault_root = Path(paths["vault_root"]).expanduser()
        til_root = Path(paths["til_root"]).expanduser()
    except KeyError as exc:
        raise PolicyError(f"paths에 필수 키가 없음: {exc}") from exc
    skill_roots = [Path(p).expanduser() for p in paths.get("skill_roots", [])]

    return Policy(
        domains=domains,
        facets=facets,
        single_allowed=single_allowed,
        rename=rename,
        drop=drop,
        conditional=conditional,
        drop_outside_projects=drop_outside_projects,
        frontmatter=dict(raw.get("frontmatter", {})),
        topics=dict(raw.get("topics", {})),
        til_folder_domain=dict(raw.get("til_folder_domain", {})),
        moc=dict(raw.get("moc", {})),
        hubs=dict(raw.get("hubs", {})),
        genos_subfolders=dict(raw.get("genos_subfolders", {})),
        vault_root=vault_root,
        til_root=til_root,
        skill_roots=skill_roots,
    )


def _validate_rename_and_conditional(
    *,
    rename: dict[str, str],
    conditional: list[dict[str, Any]],
    domains: frozenset[str],
    facets: frozenset[str],
    single_allowed: frozenset[str],
) -> None:
    allowed_first_segments = domains | facets

    def _validate_target(value: str, problem_key: str) -> None:
        if value in single_allowed:
            return
        segments = value.split("/")
        if len(segments) > 2:
            raise PolicyError(
                f"세그먼트 수 초과(2개 이하만 허용): '{problem_key}' -> '{value}'"
            )
        first_segment = segments[0]
        if first_segment not in allowed_first_segments:
            raise PolicyError(
                f"허용되지 않은 대상: '{problem_key}' -> '{value}' "
                f"(첫 세그먼트 '{first_segment}'가 domains/project_facets/"
                "single_segment_allowed 밖)"
            )

    # rename 값이 다시 rename 키가 되는 연쇄를 금지한다.
    for key, value in rename.items():
        if value in rename:
            raise PolicyError(
                f"rename 연쇄 금지: '{key}' -> '{value}'가 다시 rename 표의 키임"
            )
        _validate_target(value, key)

    # conditional의 then/else 값 중 "drop"이 아닌 것은 rename과 같은 규칙으로 검증한다.
    for item in conditional:
        tag = item.get("tag", "<unknown>")
        for field_name in ("then", "else"):
            value = item.get(field_name)
            if value is None or value == "drop":
                continue
            _validate_target(value, f"conditional[{tag}].{field_name}")


_SCOPE_TOP_FOLDERS = {
    "Archive": "archive",
    "Sources": "sources",
    "Templates": "templates",
    "Projects": "projects",
    "_Inbox": "inbox",
}


def scope_of(rel_path: str, is_til_note: bool) -> str:
    """vault 상대 경로를 정책 scope로 분류한다.

    반환값: ``"wiki-til" | "wiki-only" | "projects" | "archive" |
    "sources" | "templates" | "inbox" | "other"``.

    ``Wiki`` 바로 아래(한 단계)의 노트만 ``wiki-til``/``wiki-only``이고,
    ``Wiki/_MOC/...`` 같은 하위 폴더나 그 밖의 최상위 폴더
    (``Attachments``, ``Excalidraw`` 등)는 ``"other"``다.
    """
    parts = Path(rel_path).parts
    if not parts:
        return "other"

    top = parts[0]

    if top == "Wiki":
        if len(parts) != 2:
            return "other"
        return "wiki-til" if is_til_note else "wiki-only"

    return _SCOPE_TOP_FOLDERS.get(top, "other")
