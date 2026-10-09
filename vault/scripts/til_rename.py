#!/usr/bin/env python3
"""TIL 노트 이름 변경 이관 도구 (spec: 2026-10-09-til-title-prefix-design.md).

TIL 노트의 파일명·H1을 매핑표대로 바꾸고, 그 노트를 가리키는 참조를 함께 옮긴다.
TIL 링크, tag-mapping.json 키, Wiki 파일명, .til-sync-state.json 키, vault 위키링크가 대상이다.
동기화(sync-to-obsidian.py)는 추가만 하고 이름 변경을 모르므로, 이 도구 없이 이름만 바꾸면
Wiki에 옛 이름과 새 이름 노트가 함께 남는다.

입력 매핑 JSON: [{"folder": str, "old": str, "h1": str}, ...]
  새 파일명은 h1에서 til 스킬 Step 7 규칙으로 계산한다(to_stem). 다른 키는 무시한다.

단계:
  --plan    --mapping M --out DIR            읽기 전용. DIR에 plan.json·summary.md를 쓴다.
  --apply   --mapping M --out DIR [--real]   plan대로 쓴다. 쓰기 전에 DIR/backup에 백업하고
                                             DIR/journal.json에 작업을 기록한다.
  --verify  --mapping M --out DIR [--strict] 읽기 전용. spec 7절 검사.
  --restore --out DIR [--real]               journal·backup으로 되돌린다(삭제 없음).

경로(환경변수로 덮어씀):
  TIL_PATH(~/dev/TIL), OBSIDIAN_PATH(vault/Wiki), SYNC_STATE_PATH(OBSIDIAN_PATH/.til-sync-state.json)
  vault 루트는 OBSIDIAN_PATH의 상위 폴더다.

안전장치:
  --apply·--restore는 TIL_PATH·OBSIDIAN_PATH를 명시해야 하고, 그 값이 실제 기본 경로면
  --real 없이는 거부한다(테스트가 실제 데이터를 쓰지 않도록).
  --plan은 --out이 TIL·vault 안이면 거부한다.
  파일은 지우지 않는다. 쓰기는 같은 폴더 임시 파일 + os.replace로 한다.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import unicodedata
from dataclasses import dataclass
from pathlib import Path

VAULT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(VAULT_DIR))

from vaultkit import frontmatter as fm
from vaultkit import tilsync

REAL_TIL = Path.home() / "dev/TIL"
REAL_WIKI = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/Note/Wiki"

# TIL sync script(sync-to-obsidian.py)와 같은 제외 규칙
EXCLUDE_FILES = {"README.md", "CLAUDE.md", "GEMINI.md", "AGENTS.md"}
EXCLUDE_DIRS = {".git", ".github", ".githooks", ".claude", "scripts", ".reviews"}
VAULT_EXCLUDE_DIRS = {".obsidian", ".trash"}

_DROP = re.compile(r"['\"`]")
_TO_SPACE = re.compile(r"[/?:*()\[\],@=—]")
_H1 = re.compile(r"^# (.+)$", re.MULTILINE)
# [[대상 ...: 대상 바로 뒤가 ], |, \|, # 중 하나일 때만(접두어가 겹치는 다른 노트 제외)
_WIKI_TARGET = re.compile(r"\[\[([^\[\]|#\\\n]+)(?=\]|\||\\\||#)")


class UsageError(Exception):
    """exit 2로 끝낼 사용 오류(쓰기 전 거부)."""


@dataclass(frozen=True)
class Rename:
    folder: str
    old: str
    new: str
    old_h1: str
    new_h1: str


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def _read(path: Path) -> str:
    with open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def _split_frontmatter(text: str) -> tuple[str, str]:
    """(frontmatter 구간 ``---\\n...\\n---\\n``, 나머지). frontmatter가 없으면 ("", text)."""
    if text.startswith("---\n"):
        end = re.search(r"\n---\n", text[3:])
        if end:
            cut = 3 + end.end()
            return text[:cut], text[cut:]
    return "", text


def to_stem(h1: str) -> str:
    """H1 -> 파일명 stem (til 스킬 Step 7)."""
    text = _TO_SPACE.sub(" ", _DROP.sub("", h1))
    stem = re.sub(r"\s+", "-", text.strip())
    return _nfc(re.sub(r"-{2,}", "-", stem).strip("-"))


def _find_note(til: Path, folder: str, stem: str) -> Path | None:
    folder_dir = til / folder
    if not folder_dir.is_dir():
        return None
    for path in folder_dir.glob("*.md"):
        if _nfc(path.stem) == stem:
            return path
    return None


def _h1_of(text: str) -> str | None:
    match = _H1.search(_split_frontmatter(text)[1])
    return match.group(1).strip() if match else None


def load_renames(mapping_path: Path, til: Path) -> list[Rename]:
    try:
        rows = json.loads(_read(mapping_path))
    except (OSError, json.JSONDecodeError) as exc:
        raise UsageError(f"매핑 파일을 읽을 수 없음: {mapping_path} ({exc})") from exc
    renames: list[Rename] = []
    seen: dict[str, str] = {}
    for row in rows:
        folder, old, new_h1 = _nfc(row["folder"]), _nfc(row["old"]), _nfc(row["h1"])
        path = _find_note(til, folder, old)
        if path is None:
            raise UsageError(f"TIL 노트 없음: {folder}/{old}.md")
        old_h1 = _h1_of(_read(path))
        if old_h1 is None:
            raise UsageError(f"H1 없음: {folder}/{old}.md")
        new = to_stem(new_h1)
        if not tilsync._STEM_RE.fullmatch(new):
            raise UsageError(f"새 파일명이 동기화 링크 규칙(_STEM)에 맞지 않음: {new}")
        key = new.casefold()
        if key in seen:
            raise UsageError(f"새 파일명 중복: {new} ({seen[key]}, {old})")
        seen[key] = old
        renames.append(Rename(folder, old, new, _nfc(old_h1), new_h1))
    return renames


def replace_h1(text: str, new_h1: str) -> str:
    """frontmatter 다음 첫 ``# `` 줄만 ``# new_h1``으로 바꾼다."""
    head, body = _split_frontmatter(text)
    new_body, n = _H1.subn(lambda _m: f"# {new_h1}", body, count=1)
    if n == 0:
        raise UsageError("H1 없음")
    return head + new_body


def rewrite_til_links(text: str, renames: list[Rename]) -> tuple[str, int, list[str]]:
    """코드 밖 ``[label](./old.md#a)`` 링크의 대상을 새 stem으로 바꾼다.

    label이 옛 H1이면 새 H1, 옛 stem이면 새 stem으로 바꾸고, 그 밖의 label은 두고 보고한다.
    """
    by_old = {r.old: r for r in renames}
    count = 0
    unmatched: list[str] = []

    def repl(m: re.Match, _text: str) -> str:
        nonlocal count
        r = by_old.get(_nfc(m.group(2)))
        if r is None:
            return m.group(0)
        count += 1
        label = _nfc(m.group(1))
        if label == r.old_h1:
            label = r.new_h1
        elif label == r.old:
            label = r.new
        else:
            label = m.group(1)
            unmatched.append(f"{r.old}: {label}")
        whole, base = m.group(0), m.start()
        between = whole[m.end(1) - base : m.start(2) - base]  # "](" + 경로 접두
        return f"[{label}{between}{r.new}{whole[m.end(2) - base :]}"

    new = tilsync._sub_outside_code(text, tilsync.INTERNAL_LINK_PATTERN, repl)
    return new, count, unmatched


def rewrite_wikilinks(text: str, renames: list[Rename]) -> tuple[str, int]:
    """``[[old]]``·``![[old]]``·``[[old|x]]``·``[[old\\|x]]``·``[[old#h]]``의 대상을 바꾼다(코드 포함)."""
    by_old = {r.old: r.new for r in renames}
    count = 0

    def repl(m: re.Match) -> str:
        nonlocal count
        new = by_old.get(_nfc(m.group(1)))
        if new is None:
            return m.group(0)
        count += 1
        return f"[[{new}"

    return _WIKI_TARGET.sub(repl, text), count


def rewrite_frontmatter_links(text: str, renames: list[Rename]) -> tuple[str, int]:
    head, body = _split_frontmatter(text)
    if not head:
        return text, 0
    new_head, count = rewrite_wikilinks(head, renames)
    return new_head + body, count


def vault_scope(path: Path, wiki: Path, state: dict) -> str:
    """TIL에서 온 Wiki 노트이고 본문이 마지막 동기화 그대로면 "frontmatter", 아니면 "full"."""
    if path.parent != wiki:
        return "full"
    entry = state.get("notes", {}).get(_nfc(path.stem))
    if not entry or entry.get("status") != "synced":
        return "full"
    doc = fm.parse(_read(path))
    if doc is None or tilsync.body_sha(doc.body) != entry.get("body_sha"):
        return "full"
    return "frontmatter"


def move_keys(d: dict, renames: list[Rename]) -> dict:
    """NFC 기준으로 옛 stem 키만 새 stem으로 바꾼 새 dict(순서·값 유지)."""
    by_old = {r.old: r.new for r in renames}
    return {by_old.get(_nfc(k), k): v for k, v in d.items()}


# ------------------------------------------------------------------
# 경로
# ------------------------------------------------------------------


def _same_path(a: Path, b: Path) -> bool:
    return _nfc(str(a.expanduser().resolve())) == _nfc(str(b.expanduser().resolve()))


def _inside(child: Path, parent: Path) -> bool:
    c = _nfc(str(child.expanduser().resolve()))
    p = _nfc(str(parent.expanduser().resolve()))
    return c == p or c.startswith(p.rstrip("/") + "/")


def resolve_paths(action: str, real: bool) -> dict:
    """환경변수 -> 경로. vault 루트는 Wiki의 상위 폴더.

    쓰기 단계(apply·restore)는 TIL_PATH·OBSIDIAN_PATH를 명시해야 하고 실제 경로는 --real로만.
    """
    env = os.environ
    writes = action in ("apply", "restore")
    if writes and not real:
        missing = [v for v in ("TIL_PATH", "OBSIDIAN_PATH") if not env.get(v)]
        if missing:
            raise UsageError(
                f"--{action}에는 {', '.join(missing)} 환경변수가 필요함"
                " (실제 TIL·vault에 쓰려면 사용자 승인 뒤 --real)"
            )
    til = Path(env.get("TIL_PATH") or REAL_TIL)
    wiki = Path(env.get("OBSIDIAN_PATH") or REAL_WIKI)
    state = Path(env.get("SYNC_STATE_PATH") or wiki / ".til-sync-state.json")
    if writes and not real:
        for name, path, default in (("TIL_PATH", til, REAL_TIL), ("OBSIDIAN_PATH", wiki, REAL_WIKI)):
            if _same_path(path, default):
                raise UsageError(f"{name}가 실제 경로({path}) → --real 없이는 쓰지 않음")
        if _inside(state, REAL_WIKI.parent) or _inside(state, REAL_TIL):
            raise UsageError(f"SYNC_STATE_PATH가 실제 경로({state}) → --real 없이는 쓰지 않음")
    return {"til": til, "wiki": wiki, "state": state, "vault": wiki.parent}


def _check_out(out: Path, paths: dict) -> None:
    for root in (paths["til"], paths["vault"]):
        if _inside(out, root):
            raise UsageError(f"--out이 TIL·vault 안({out}) → 거부")


def _til_notes(til: Path) -> list[Path]:
    return [
        p
        for p in til.glob("*/*.md")
        if p.parent.name not in EXCLUDE_DIRS and p.name not in EXCLUDE_FILES
    ]


def _vault_notes(vault_root: Path) -> list[Path]:
    return [
        p
        for p in vault_root.rglob("*.md")
        if not VAULT_EXCLUDE_DIRS.intersection(p.relative_to(vault_root).parts)
    ]


def check_collisions(renames: list[Rename], til: Path, vault_root: Path) -> list[str]:
    olds = {r.old.casefold() for r in renames}
    existing: dict[str, str] = {}
    for root, paths in (("TIL", _til_notes(til)), ("vault", _vault_notes(vault_root))):
        for p in paths:
            key = _nfc(p.stem).casefold()
            if key not in olds:
                existing.setdefault(key, f"{root}: {p.relative_to(til if root == 'TIL' else vault_root)}")
    return [
        f"{r.folder}/{r.old} -> {r.new}: 이미 있는 노트와 겹침 ({existing[r.new.casefold()]})"
        for r in renames
        if r.new.casefold() in existing
    ]


# ------------------------------------------------------------------
# plan
# ------------------------------------------------------------------


def _load_json(path: Path, default):
    try:
        return json.loads(_read(path))
    except FileNotFoundError:
        return default


def _wiki_index(wiki: Path) -> dict[str, Path]:
    return {_nfc(p.stem): p for p in wiki.glob("*.md")}


def build_plan(paths: dict, renames: list[Rename]) -> dict:
    """읽기 전용 판정: 무엇을 몇 곳 바꾸는가(이름 변경 전 경로 기준)."""
    til, wiki, vault = paths["til"], paths["wiki"], paths["vault"]
    state = tilsync.load_state(paths["state"])
    tag_keys = {_nfc(k) for k in _load_json(til / "tag-mapping.json", {})}
    wiki_index = _wiki_index(wiki)

    til_files: dict[str, int] = {}
    unmatched: list[str] = []
    for p in sorted(_til_notes(til)):
        text, n1, missed = rewrite_til_links(_read(p), renames)
        _, n2 = rewrite_wikilinks(text, renames)
        rel = _nfc(str(p.relative_to(til)))
        if n1 + n2:
            til_files[rel] = n1 + n2
        unmatched += [f"{rel}: {m}" for m in missed]

    vault_files: dict[str, dict] = {}
    body_left = 0
    for p in sorted(_vault_notes(vault)):
        text = _read(p)
        _, total = rewrite_wikilinks(text, renames)
        if not total:
            continue
        scope = vault_scope(p, wiki, state)
        count = rewrite_frontmatter_links(text, renames)[1] if scope == "frontmatter" else total
        body_left += total - count
        if count:
            vault_files[_nfc(str(p.relative_to(vault)))] = {"scope": scope, "count": count}

    rows = [
        {
            "folder": r.folder,
            "old": r.old,
            "new": r.new,
            "old_h1": r.old_h1,
            "new_h1": r.new_h1,
            "wiki_exists": r.old in wiki_index,
            "state_status": (state["notes"].get(r.old) or {}).get("status"),
        }
        for r in renames
    ]
    return {
        "renames": rows,
        "til_files": til_files,
        "til_unmatched": unmatched,
        "vault_files": vault_files,
        "vault_body_left": body_left,
        "tag_keys": sum(r.old in tag_keys for r in renames),
        "counts": {
            "renames": len(renames),
            "til_links": sum(til_files.values()),
            "til_link_files": len(til_files),
            "vault_links": sum(v["count"] for v in vault_files.values()),
            "vault_body_left": body_left,
            "tag_keys": sum(r.old in tag_keys for r in renames),
            "wiki_renames": sum(row["wiki_exists"] for row in rows),
        },
    }


def _render_summary(plan: dict) -> str:
    lines = ["# TIL 이름 변경 plan", "", "## 건수", ""]
    lines += [f"- {k}: {v}" for k, v in plan["counts"].items()]
    lines += ["", "## 이름 변경", "", "| 폴더 | 옛 이름 | 새 이름 | Wiki | state |", "|---|---|---|---|---|"]
    for r in plan["renames"]:
        lines.append(
            f"| {r['folder']} | {r['old']} | {r['new']} | {'있음' if r['wiki_exists'] else '없음'} | {r['state_status'] or '-'} |"
        )
    lines += ["", "## 그대로 두는 링크 텍스트 (옛 H1·옛 파일명과 다름)", ""]
    lines += [f"- {u}" for u in plan["til_unmatched"]] or ["- 없음"]
    lines += ["", "## 이름 충돌", ""]
    lines += [f"- {c}" for c in plan["collisions"]] or ["- 없음"]
    return "\n".join(lines) + "\n"


def _mapping_sha(mapping: Path) -> str:
    return hashlib.sha256(mapping.read_bytes()).hexdigest()


def _refuse_used_out(out: Path) -> None:
    """한 번 apply한 out은 다시 쓰지 않는다(백업·작업 기록이 유일한 vault 복구 수단)."""
    if (out / "journal.json").exists() or (out / "backup").exists():
        raise UsageError(
            f"이미 apply한 --out({out}) → 되돌리려면 --restore --out {out}, 다시 하려면 새 --out으로 --plan"
        )


def cmd_plan(mapping: Path, out: Path) -> int:
    paths = resolve_paths("plan", real=False)
    _check_out(out, paths)
    _refuse_used_out(out)
    renames = load_renames(mapping, paths["til"])
    plan = build_plan(paths, renames)
    plan["mapping_sha"] = _mapping_sha(mapping)
    plan["collisions"] = check_collisions(renames, paths["til"], paths["vault"])
    out.mkdir(parents=True, exist_ok=True)
    (out / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "summary.md").write_text(_render_summary(plan), encoding="utf-8")
    for key, value in plan["counts"].items():
        print(f"  {key}: {value}")
    print(f"  collisions: {len(plan['collisions'])}")
    print(f"plan: {out}")
    return 0


# ------------------------------------------------------------------
# apply
# ------------------------------------------------------------------


class StalePlan(Exception):
    """exit 1로 끝낼 plan 불일치(쓰기 전 거부)."""


def _write_atomic(path: Path, text: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)  # 이 함수가 만든 임시 파일만 정리
        raise


def _backup_rel(path: Path, paths: dict) -> str:
    for name in ("til", "vault"):
        if _inside(path, paths[name]):
            return f"{name}/{_nfc(str(path.resolve().relative_to(paths[name].resolve())))}"
    return f"other/{_nfc(path.name)}"


def _save_journal(out: Path, journal: dict) -> None:
    _write_atomic(out / "journal.json", json.dumps(journal, ensure_ascii=False, indent=2) + "\n")


def _load_fresh_plan(mapping: Path, out: Path, paths: dict) -> tuple[list[Rename], dict]:
    """plan.json과 지금 다시 계산한 plan이 같을 때만 (renames, plan)."""
    try:
        saved = json.loads(_read(out / "plan.json"))
    except FileNotFoundError as exc:
        raise StalePlan(f"plan 없음: {out / 'plan.json'} (먼저 --plan)") from exc
    if saved.get("mapping_sha") != _mapping_sha(mapping):
        raise StalePlan("매핑 파일이 plan 이후 바뀜 → 새 --out으로 --plan 다시 실행")
    renames = load_renames(mapping, paths["til"])
    fresh = build_plan(paths, renames)
    if fresh["counts"] != saved.get("counts"):
        raise StalePlan(f"plan 이후 상태가 바뀜: {saved.get('counts')} → {fresh['counts']} (새 --out으로 --plan)")
    collisions = check_collisions(renames, paths["til"], paths["vault"])
    if collisions:
        raise UsageError("이름 충돌: " + "; ".join(collisions))
    return renames, fresh


def cmd_apply(mapping: Path, out: Path, real: bool) -> int:
    paths = resolve_paths("apply", real)
    til, wiki, vault = paths["til"], paths["wiki"], paths["vault"]
    _refuse_used_out(out)
    renames, plan = _load_fresh_plan(mapping, out, paths)
    by_old = {r.old: r for r in renames}
    wiki_index = _wiki_index(wiki)

    # 바꿀 파일(이름 변경 전 경로)
    til_renamed = {r.old: _find_note(til, r.folder, r.old) for r in renames}
    til_edit = {p.resolve(): p for p in til_renamed.values() if p is not None}
    for rel in plan["til_files"]:
        folder, name = rel.split("/", 1)
        p = _find_note(til, folder, Path(name).stem) or til / rel
        til_edit[p.resolve()] = p
    vault_edit = {}
    for rel, info in plan["vault_files"].items():
        p = next((q for q in (vault / rel).parent.glob("*.md") if _nfc(q.name) == Path(rel).name), vault / rel)
        vault_edit[p.resolve()] = (p, info["scope"])
    wiki_renamed = {r.old: wiki_index[r.old] for r in renames if r.old in wiki_index}
    tag_path = til / "tag-mapping.json"

    targets = list(til_edit.values()) + [p for p, _ in vault_edit.values()] + list(wiki_renamed.values())
    targets += [p for p in (tag_path, paths["state"]) if p.exists()]

    # 1. 백업 2. 작업 기록
    journal: dict = {"renames": [], "backups": []}
    seen: set[Path] = set()
    for p in targets:
        if p.resolve() in seen:
            continue
        seen.add(p.resolve())
        rel = _backup_rel(p, paths)
        copy = out / "backup" / rel
        copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, copy)
        journal["backups"].append({"orig": str(p), "copy": f"backup/{rel}"})
    _save_journal(out, journal)
    print(f"  backup: {len(journal['backups'])}")

    # TIL 커밋 때 스테이징할 경로(옛 경로·새 경로·수정 파일). add -u만 하면 46편이 삭제로 커밋된다.
    git_paths = {_nfc(str(p.relative_to(til))) for p in til_edit.values()}
    git_paths |= {_nfc(str(p.with_name(f"{by_old[o].new}.md").relative_to(til))) for o, p in til_renamed.items() if p}
    if tag_path.exists():
        git_paths.add("tag-mapping.json")
    (out / "git-paths.txt").write_text("\n".join(sorted(git_paths)) + "\n", encoding="utf-8")

    try:
        _apply_writes(paths, renames, out, journal, til_edit, til_renamed, vault_edit, wiki_renamed, tag_path)
    except BaseException as exc:
        restore = f"--restore --out {out}" + (" --real" if real else "")
        print(f"❌ 부분 적용됨({exc!r}) → 원인을 해결한 뒤 {restore}로 되돌린다", file=sys.stderr)
        raise
    print(f"  git 스테이징: git -C {til} add --pathspec-from-file={out / 'git-paths.txt'}")
    print(f"apply: {out}")
    return 0


def _apply_writes(paths, renames, out, journal, til_edit, til_renamed, vault_edit, wiki_renamed, tag_path) -> None:
    """apply 3~6단계. 실패하면 호출부가 --restore를 안내한다."""
    wiki = paths["wiki"]
    by_old = {r.old: r for r in renames}

    # 3. TIL 내용(원래 경로)
    renamed_paths = {p.resolve(): by_old[old] for old, p in til_renamed.items() if p is not None}
    for key, p in til_edit.items():
        text = _read(p)
        new = replace_h1(text, renamed_paths[key].new_h1) if key in renamed_paths else text
        new = rewrite_til_links(new, renames)[0]
        new = rewrite_wikilinks(new, renames)[0]
        if new != text:
            _write_atomic(p, new)
    print(f"  til edited: {len(til_edit)}")

    # 4. vault 내용(원래 경로, state는 아직 옛 키)
    for p, scope in vault_edit.values():
        text = _read(p)
        new = (rewrite_frontmatter_links if scope == "frontmatter" else rewrite_wikilinks)(text, renames)[0]
        if new != text:
            _write_atomic(p, new)
    print(f"  vault edited: {len(vault_edit)}")

    # 5. 이름 변경
    moves = [(p, p.with_name(f"{by_old[old].new}.md")) for old, p in til_renamed.items() if p is not None]
    moves += [(p, wiki / f"{by_old[old].new}.md") for old, p in wiki_renamed.items()]
    journal["renames"] = [{"from": str(a), "to": str(b)} for a, b in moves]
    _save_journal(out, journal)
    for src, dst in moves:
        os.replace(src, dst)
    print(f"  renamed: {len(moves)}")

    # 6. 키 이동
    if tag_path.exists():
        tags = json.loads(_read(tag_path))
        _write_atomic(tag_path, json.dumps(move_keys(tags, renames), ensure_ascii=False, indent=2) + "\n")
    state = tilsync.load_state(paths["state"])
    state["notes"] = move_keys(state["notes"], renames)
    tilsync.save_state(paths["state"], state)
    print("  keys moved: tag-mapping, state")


# ------------------------------------------------------------------
# verify / restore
# ------------------------------------------------------------------


def _plan_renames(plan: dict) -> list[Rename]:
    return [Rename(r["folder"], r["old"], r["new"], r["old_h1"], r["new_h1"]) for r in plan["renames"]]


def _til_link_count(text: str, olds: set[str], renames: list[Rename]) -> int:
    md = sum(
        1
        for m in tilsync._matches_outside_code(text, tilsync.INTERNAL_LINK_PATTERN)
        if _nfc(m.group(2)) in olds
    )
    return md + rewrite_wikilinks(text, renames)[1]


def cmd_verify(mapping: Path | None, out: Path, strict: bool) -> int:
    paths = resolve_paths("verify", real=False)
    til, wiki, vault = paths["til"], paths["wiki"], paths["vault"]
    try:
        plan = json.loads(_read(out / "plan.json"))
    except FileNotFoundError as exc:
        raise UsageError(f"plan 없음: {out / 'plan.json'}") from exc
    if mapping is not None and plan.get("mapping_sha") != _mapping_sha(mapping):
        raise UsageError("매핑 파일이 plan과 다름")
    renames = _plan_renames(plan)
    olds = {r.old for r in renames}
    results: list[tuple[int, list[str], list[str]]] = []

    # 1. TIL 파일명·H1
    errs: list[str] = []
    for r in renames:
        if _find_note(til, r.folder, r.old) is not None:
            errs.append(f"옛 파일 남음: {r.folder}/{r.old}.md")
        new = _find_note(til, r.folder, r.new)
        if new is None:
            errs.append(f"새 파일 없음: {r.folder}/{r.new}.md")
            continue
        h1 = _h1_of(_read(new))
        if h1 != r.new_h1 or to_stem(h1 or "") != r.new:
            errs.append(f"H1 불일치: {r.folder}/{r.new}.md ({h1})")
    results.append((1, errs, []))

    # 2. TIL 링크
    errs = [
        f"옛 링크 {n}곳: {_nfc(str(p.relative_to(til)))}"
        for p in sorted(_til_notes(til))
        if (n := _til_link_count(_read(p), olds, renames))
    ]
    results.append((2, errs, []))

    # 3. tag-mapping
    errs = []
    try:
        keys = {_nfc(k) for k in json.loads(_read(til / "tag-mapping.json"))}
        errs += [f"옛 키 남음: {o}" for o in sorted(olds & keys)]
        new_keys = sum(r.new in keys for r in renames)
        if new_keys != plan["tag_keys"]:
            errs.append(f"새 키 {new_keys}개 (plan {plan['tag_keys']}개)")
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        errs.append(f"tag-mapping 읽기 실패: {exc}")
    results.append((3, errs, []))

    # 4. Wiki 파일·state
    errs = []
    wiki_index = _wiki_index(wiki)
    errs += [f"Wiki 옛 파일 남음: {o}.md" for o in sorted(olds & set(wiki_index))]
    new_files = sum(r.new in wiki_index for r in renames)
    if new_files != plan["counts"]["wiki_renames"]:
        errs.append(f"Wiki 새 파일 {new_files}개 (plan {plan['counts']['wiki_renames']}개)")
    state = tilsync.load_state(paths["state"])
    notes = {_nfc(k): v for k, v in state["notes"].items()}
    errs += [f"state 옛 키 남음: {o}" for o in sorted(olds & set(notes))]
    for row in plan["renames"]:
        status = (notes.get(row["new"]) or {}).get("status")
        if status != row["state_status"]:
            errs.append(f"state 상태 불일치: {row['new']} ({status}, plan {row['state_status']})")
    results.append((4, errs, []))

    # 5. vault 링크(범위별)
    errs, infos = [], []
    body_left = 0
    for p in sorted(_vault_notes(vault)):
        text = _read(p)
        total = rewrite_wikilinks(text, renames)[1]
        if not total:
            continue
        rel = _nfc(str(p.relative_to(vault)))
        if vault_scope(p, wiki, state) == "frontmatter":
            in_head = rewrite_frontmatter_links(text, renames)[1]
            if in_head:
                errs.append(f"frontmatter 옛 링크 {in_head}곳: {rel}")
            body_left += total - in_head
        else:
            errs.append(f"옛 링크 {total}곳: {rel}")
    infos.append(f"동기화가 고칠 본문 옛 링크: {body_left}곳")
    if strict and body_left:
        errs.append(f"--strict: 본문 옛 링크 {body_left}곳 남음")
    results.append((5, errs, infos))

    for num, errs, infos in results:
        print(f"PASS {num}" if not errs else f"FAIL {num}")
        for line in errs[:20]:
            print(f"    {line}")
        if len(errs) > 20:
            print(f"    ... 외 {len(errs) - 20}건")
        for line in infos:
            print(f"    ({line})")
    return 0 if all(not errs for _, errs, _ in results) else 1


def cmd_restore(out: Path, real: bool) -> int:
    resolve_paths("restore", real)
    try:
        journal = json.loads(_read(out / "journal.json"))
    except FileNotFoundError as exc:
        raise UsageError(f"작업 기록 없음: {out / 'journal.json'}") from exc
    moved = 0
    for item in reversed(journal["renames"]):
        src, dst = Path(item["to"]), Path(item["from"])
        if src.exists():
            os.replace(src, dst)
            moved += 1
    for item in journal["backups"]:
        orig = Path(item["orig"])
        fd, tmp = tempfile.mkstemp(dir=orig.parent, prefix=f".{orig.name}.", suffix=".tmp")
        os.close(fd)
        shutil.copy2(out / item["copy"], tmp)
        os.replace(tmp, orig)
    print(f"  renamed back: {moved}")
    print(f"  restored: {len(journal['backups'])}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="TIL 노트 이름 변경 이관")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--plan", action="store_true", help="읽기 전용: 바뀔 내용 미리보기")
    group.add_argument("--apply", action="store_true", help="plan대로 쓰기(백업·작업 기록)")
    group.add_argument("--verify", action="store_true", help="읽기 전용: 이관 결과 검사")
    group.add_argument("--restore", action="store_true", help="백업·작업 기록으로 되돌리기")
    parser.add_argument("--mapping", type=Path, help="매핑 JSON")
    parser.add_argument("--out", type=Path, required=True, help="plan·백업·작업 기록 폴더")
    parser.add_argument("--real", action="store_true", help="실제 TIL·vault에 쓰기 허용")
    parser.add_argument("--strict", action="store_true", help="verify: 본문 남은 링크도 0이어야 함")
    args = parser.parse_args(argv)
    try:
        if args.plan:
            if args.mapping is None:
                raise UsageError("--plan에는 --mapping이 필요함")
            return cmd_plan(args.mapping, args.out)
        if args.apply:
            if args.mapping is None:
                raise UsageError("--apply에는 --mapping이 필요함")
            return cmd_apply(args.mapping, args.out, args.real)
        if args.verify:
            return cmd_verify(args.mapping, args.out, args.strict)
        return cmd_restore(args.out, args.real)
    except UsageError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2
    except StalePlan as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
