#!/usr/bin/env python3
"""TIL <- Wiki 최초 1회 이관 도구 (spec 5.3, Task 8).

Wiki에서 고친 TIL 파생 노트의 본문을 TIL 원문으로 되돌리고, 이관 뒤
TIL -> Wiki 동기화 상태 파일(v2)을 만든다. 1회용이다.

단계:
  --plan --out DIR         읽기 전용. DIR에 편별 diff·새 원문·plan.json·summary.md를 쓴다.
  --apply --out DIR        plan 결과대로 TIL 파일을 쓴다(사용자 승인 후).
      [--only a,b] [--unresolved text|github]
  --build-state --out DIR  SYNC_STATE_PATH에 state v2를 만든다(apply 뒤).

경로(환경변수로 덮어씀):
  TIL_PATH(~/dev/TIL), OBSIDIAN_PATH(vault/Wiki), VAULTKIT_POLICY(vault-policy.json),
  SYNC_STATE_PATH(OBSIDIAN_PATH/.til-sync-state.json)

안전장치:
  --apply·--build-state는 TIL_PATH·OBSIDIAN_PATH(·SYNC_STATE_PATH)를 명시해야 하고,
  그 값이 실제 기본 경로면 --real 없이는 거부한다(테스트가 실제 데이터를 쓰지 않도록).
  --plan은 --out이 TIL·Wiki 안이면 거부하고 --out 밖에는 쓰지 않는다.

동등 판정: tilsync의 내용 동등(body_sha 또는 링크 표기 정규화 후 동일)에
frontmatter 뒤 빈 줄 차이를 무시한 것. 이 기준으로 같으면 이관하지 않는다.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import subprocess
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from urllib.parse import quote

VAULT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(VAULT_DIR))

from vaultkit import frontmatter as fm
from vaultkit import tilsync
from vaultkit.policy import load_policy

REAL_TIL = Path.home() / "dev/TIL"
REAL_WIKI = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/Note/Wiki"

# TIL sync script(sync-to-obsidian.py)와 같은 제외 규칙
EXCLUDE_FILES = {"README.md", "CLAUDE.md", "GEMINI.md", "AGENTS.md"}
EXCLUDE_DIRS = {".git", ".github", ".githooks", ".claude", "scripts", ".reviews"}

_GITHUB_REMOTE = re.compile(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?/?$")


class UsageError(Exception):
    """exit 2로 끝낼 사용 오류(쓰기 전 거부)."""


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read(path: Path) -> str:
    with open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


# ------------------------------------------------------------------
# 경로와 가드
# ------------------------------------------------------------------


def _same_path(a: Path, b: Path) -> bool:
    return _nfc(str(a.expanduser().resolve())) == _nfc(str(b.expanduser().resolve()))


def _inside(child: Path, parent: Path) -> bool:
    c = _nfc(str(child.expanduser().resolve()))
    p = _nfc(str(parent.expanduser().resolve()))
    return c == p or c.startswith(p.rstrip("/") + "/")


def resolve_paths(action: str, real: bool) -> dict:
    """환경변수 -> 경로. 쓰기 단계는 명시한 env만 받고 실제 경로는 --real로만."""
    env = os.environ
    required = {"apply": ["TIL_PATH", "OBSIDIAN_PATH"], "build-state": ["TIL_PATH", "OBSIDIAN_PATH", "SYNC_STATE_PATH"]}
    if not real:
        missing = [v for v in required.get(action, []) if not env.get(v)]
        if missing:
            raise UsageError(
                f"--{action}에는 {', '.join(missing)} 환경변수가 필요함"
                " (실제 TIL·Wiki에 쓰려면 사용자 승인 뒤 --real)"
            )
    til = Path(env.get("TIL_PATH") or REAL_TIL)
    wiki = Path(env.get("OBSIDIAN_PATH") or REAL_WIKI)
    state = Path(env.get("SYNC_STATE_PATH") or wiki / ".til-sync-state.json")
    policy = Path(env["VAULTKIT_POLICY"]) if env.get("VAULTKIT_POLICY") else None
    if action != "plan" and not real:
        for name, path, default in (("TIL_PATH", til, REAL_TIL), ("OBSIDIAN_PATH", wiki, REAL_WIKI)):
            if _same_path(path, default):
                raise UsageError(f"{name}가 실제 경로({path}) → --real 없이는 쓰지 않음")
        if _inside(state, REAL_WIKI) or _inside(state, REAL_TIL):
            raise UsageError(f"SYNC_STATE_PATH가 실제 경로({state}) → --real 없이는 쓰지 않음")
    return {"til": til, "wiki": wiki, "state": state, "policy": policy}


def _check_out(out: Path, paths: dict) -> None:
    for root in (paths["til"], paths["wiki"]):
        if _inside(out, root):
            raise UsageError(f"--out이 TIL·Wiki 안({out}) → 거부")


# ------------------------------------------------------------------
# 탐색
# ------------------------------------------------------------------


def scan_til(til: Path) -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = {}
    for folder in sorted(til.iterdir()):
        if not folder.is_dir() or folder.name in EXCLUDE_DIRS:
            continue
        for md in sorted(folder.glob("*.md")):
            if md.name not in EXCLUDE_FILES:
                index.setdefault(_nfc(md.stem), []).append(md)
    return index


def scan_wiki(wiki: Path) -> dict[str, Path]:
    return {_nfc(p.stem): p for p in wiki.glob("*.md")}


def load_mapping(til: Path) -> dict[str, list[str]]:
    path = til / "tag-mapping.json"
    if not path.exists():
        return {}
    return {_nfc(k): v for k, v in json.loads(path.read_text(encoding="utf-8")).items()}


def til_history(til: Path, rel: str) -> list[tuple[str, str, str]]:
    """TIL 파일의 커밋 이력 [(commit, 날짜, 텍스트)], 최신 먼저(이력 없으면 빈 목록)."""
    git = ["git", "-C", str(til)]
    proc = subprocess.run([*git, "log", "--format=%H %cs", "--", rel], capture_output=True, text=True)
    if proc.returncode != 0:
        return []
    versions = []
    for line in proc.stdout.split("\n"):
        if not line.strip():
            continue
        commit, date = line.split(" ", 1)
        show = subprocess.run([*git, "show", f"{commit}:{rel}"], capture_output=True)
        if show.returncode == 0:  # 해당 커밋에서 삭제된 경우 등은 건너뜀
            versions.append((commit, date, show.stdout.decode("utf-8", errors="replace")))
    return versions


def github_base(til: Path) -> str | None:
    """``https://github.com/<owner>/<repo>/blob/main`` (origin이 GitHub가 아니면 None)."""
    proc = subprocess.run(
        ["git", "-C", str(til), "remote", "get-url", "origin"], capture_output=True, text=True
    )
    m = _GITHUB_REMOTE.search(proc.stdout.strip()) if proc.returncode == 0 else None
    return f"https://github.com/{m.group(1)}/{m.group(2)}/blob/main" if m else None


# ------------------------------------------------------------------
# 판정 보조
# ------------------------------------------------------------------


def equivalent(wiki_body: str, gen_body: str) -> bool:
    return tilsync._same_content(wiki_body.lstrip("\n"), gen_body.lstrip("\n"))


def append_sources(text: str, urls: list[str]) -> str:
    """본문 끝에 ``## 출처`` 절을 붙인다(extract_sources가 다시 읽는 ``<url>`` 형식)."""
    items = "".join(f"- <{u}>\n" for u in urls)
    return text.rstrip("\n") + "\n\n## 출처\n\n" + items


def _til_frontmatter_prefix(text: str) -> str:
    """build_note가 벗기는 TIL frontmatter 블록(없으면 빈 문자열)."""
    if text.startswith("---"):
        m = re.search(r"\n---\n", text[3:])
        if m:
            return text[: 3 + m.end()]
    return ""


def _link_parts(link: str) -> tuple[str, str, str | None]:
    """``[[stem#h|alias]]`` -> (stem, "#h" 또는 "", alias)."""
    m = tilsync._WIKI_LINK_PATTERN.fullmatch(link)
    target, alias = m.group(2), m.group(4)
    stem, _, heading = target.partition("#")
    return stem, (f"#{heading}" if "#" in target else ""), alias


def _link_text(link: str) -> str:
    stem, anchor, alias = _link_parts(link)
    if alias:
        return alias
    return stem or anchor.lstrip("#")


def _github_url(link: str, til_index: dict[str, list[Path]], base: str | None) -> str | None:
    if link.startswith("!") or base is None:
        return None
    stem, anchor, _alias = _link_parts(link)
    paths = til_index.get(_nfc(stem), [])
    if len(paths) != 1:
        return None
    folder = paths[0].parent.name
    return f"{base}/{quote(folder)}/{quote(_nfc(stem))}.md{quote(anchor, safe='#')}"


def resolve_unresolved(text: str, mode: str, table: dict[str, dict]) -> str:
    """코드 밖 남은 ``[[..]]``를 일반 텍스트 또는 GitHub 절대 링크로 바꾼다."""

    def repl(m: re.Match, _text: str) -> str:
        info = table.get(m.group(0))
        if info is None:
            return m.group(0)
        if mode == "github" and info["github"]:
            return f"[{info['text']}]({info['github']})"
        return info["text"]

    return tilsync._sub_outside_code(text, tilsync._WIKI_LINK_PATTERN, repl)


# ------------------------------------------------------------------
# plan
# ------------------------------------------------------------------


def _load_all(paths: dict):
    policy = load_policy(paths["policy"])
    mapping = load_mapping(paths["til"])
    return policy, mapping, scan_til(paths["til"]), scan_wiki(paths["wiki"])


def cmd_plan(out: Path, paths: dict) -> int:
    _check_out(out, paths)
    if out.exists() and any(out.iterdir()):
        raise UsageError(f"--out이 비어 있지 않음({out}) → 새 디렉터리를 지정")
    policy, mapping, til_index, wiki_index = _load_all(paths)
    base = github_base(paths["til"])
    folder_of = {stem: ps[0].parent.name for stem, ps in til_index.items() if len(ps) == 1}

    notes: dict[str, dict] = {}
    skipped: list[tuple[str, str]] = []
    equal_count = 0
    for stem in sorted(set(til_index) & set(wiki_index)):
        srcs = til_index[stem]
        if len(srcs) > 1:
            skipped.append((stem, "TIL 여러 폴더에 같은 이름"))
            continue
        src = srcs[0]
        folder = src.parent.name
        wiki_text = _read(wiki_index[stem])
        doc = fm.parse(wiki_text)
        if doc is None:
            skipped.append((stem, "Wiki frontmatter 파싱 불가"))
            continue
        til_text = _read(src)
        gen = tilsync.build_note(src, folder, policy, mapping)
        wiki_sources = fm.get_list(doc, "source")
        same = equivalent(doc.body, gen.body)

        unresolved: list[str] = []
        if same:
            new_text = til_text
        else:
            # 제목 원본은 TIL(spec 5.1): Wiki title은 동기화가 TIL 값으로 덮는다
            doc.body = doc.body.lstrip("\n")
            ported, unresolved = tilsync.reverse_port(fm.render(doc), gen.title, folder_of, folder)
            new_text = _til_frontmatter_prefix(til_text) + ported
        present = tilsync.extract_sources(new_text)
        source_append: list[str] = []
        if wiki_sources and not tilsync._SOURCE_SECTION.search(new_text):
            source_append = list(wiki_sources)
            new_text = append_sources(new_text, source_append)
        missing_sources = [u for u in wiki_sources if u not in present and u not in source_append]
        if same and not source_append:
            equal_count += 1
            continue

        new_path = out / "new" / folder / src.name
        _write(new_path, new_text)
        diff_lines = list(
            difflib.unified_diff(
                til_text.splitlines(keepends=True),
                new_text.splitlines(keepends=True),
                fromfile=f"a/{folder}/{src.name}",
                tofile=f"b/{folder}/{src.name}",
            )
        )
        _write(out / f"{stem}.diff", "".join(diff_lines))
        changed = sum(
            1 for ln in diff_lines if ln[:1] in "+-" and not ln.startswith(("+++", "---"))
        )

        # 새 원문을 다시 생성했을 때 Wiki 본문(+붙인 출처)과 동등한지
        rt_path = out / "_roundtrip" / folder / src.name
        _write(rt_path, new_text)
        gen2 = tilsync.build_note(rt_path, folder, policy, mapping)
        intended = fm.parse(wiki_text).body
        if source_append:
            intended = append_sources(intended, source_append)
        roundtrip_ok = equivalent(intended, gen2.body) and (
            not source_append or gen2.sources == source_append
        )

        notes[stem] = {
            "folder": folder,
            "til_file": str(src.relative_to(paths["til"])),
            "til_sha": _sha(til_text),
            "wiki_body_sha": tilsync.body_sha(fm.parse(wiki_text).body),
            "new_file": str(new_path.relative_to(out)),
            "body_changed": not same,
            "source_append": source_append,
            "missing_sources": missing_sources,
            "changed_lines": changed,
            # Wiki가 갈라진 뒤 TIL도 고쳐졌으면 역이관이 TIL 변경을 되돌린다(검토 필요)
            "base": wiki_base(
                paths["til"], src, til_text, fm.parse(wiki_text).body, out, policy, mapping
            ),
            "roundtrip_ok": roundtrip_ok,
            "unresolved": [
                {"link": link, "text": _link_text(link), "github": _github_url(link, til_index, base)}
                for link in dict.fromkeys(unresolved)
            ],
        }

    retired = sorted(s for s in til_index if s not in wiki_index)
    plan = {
        "til": str(paths["til"]),
        "wiki": str(paths["wiki"]),
        "github_base": base,
        "equal": equal_count,
        "notes": notes,
        "retired": retired,
        "skipped": skipped,
    }
    _write(out / "plan.json", json.dumps(plan, ensure_ascii=False, indent=2) + "\n")
    _write(out / "unresolved.md", _render_unresolved(notes))
    _write(out / "summary.md", _render_summary(plan))
    print(f"plan: 이관 대상 {len(notes)}편, 동등 {equal_count}편, retired 후보 {len(retired)}편 → {out}")
    return 0


def wiki_base(
    til: Path, src: Path, til_text: str, wiki_body: str, out: Path, policy, mapping
) -> dict:
    """Wiki 본문이 갈라져 나온 TIL 버전을 추정한다.

    작업트리 + 커밋 이력의 각 버전을 build_note로 만들어 Wiki 본문과 줄 단위
    유사도(빈 줄 제외)가 가장 높은 버전(동률이면 최신)을 기준으로 본다. ``commits_after``가
    0보다 크면 Wiki가 갈라진 뒤 TIL도 고쳐졌다는 뜻이고, ``exact``면 Wiki는
    그 옛 버전과 내용 동등(Wiki 수정 없음)하다.
    """
    folder = src.parent.name
    rel = str(src.relative_to(til))
    versions = [(None, "작업트리", til_text)]
    for commit, date, text in til_history(til, rel):
        if text != versions[-1][2]:
            versions.append((commit, date, text))
    def content_lines(text: str) -> list[str]:
        return [ln.rstrip() for ln in text.splitlines() if ln.strip()]

    wiki_lines = content_lines(wiki_body)
    best = None
    for i, (commit, date, text) in enumerate(versions):
        tmp = out / "_history" / (commit or "worktree") / folder / src.name
        _write(tmp, text)
        body = tilsync.build_note(tmp, folder, policy, mapping).body
        ratio = difflib.SequenceMatcher(None, wiki_lines, content_lines(body), autojunk=False).ratio()
        if best is None or ratio > best[0]:
            best = (ratio, i, commit, date, equivalent(wiki_body, body))
    ratio, index, commit, date, exact = best
    return {
        "commit": commit,
        "date": date,
        "commits_after": index,
        "similarity": round(ratio, 3),
        "exact": exact and index > 0,
    }


def _cell(text: str) -> str:
    return text.replace("|", "\\|")


def _render_unresolved(notes: dict) -> str:
    rows = [
        "| 노트 | 링크 | 일반 텍스트화 | GitHub 절대 링크 |",
        "|---|---|---|---|",
    ]
    for stem, n in notes.items():
        for u in n["unresolved"]:
            gh = u["github"] or "불가(TIL에 없는 대상 → 일반 텍스트)"
            rows.append(f"| {stem} | `{_cell(u['link'])}` | {_cell(u['text'])} | {gh} |")
    return "\n".join(rows) + "\n"


def _render_summary(plan: dict) -> str:
    notes = plan["notes"]
    body = [n for n in notes.values() if n["body_changed"]]
    src_only = [s for s, n in notes.items() if n["source_append"]]
    folders = Counter(n["folder"] for n in notes.values())
    top = sorted(notes.items(), key=lambda kv: (-kv[1]["changed_lines"], kv[0]))[:10]
    unresolved = sum(len(n["unresolved"]) for n in notes.values())
    bad = [s for s, n in notes.items() if not n["roundtrip_ok"]]
    missing = [(s, n["missing_sources"]) for s, n in notes.items() if n["missing_sources"]]
    diverged = [(s, n) for s, n in notes.items() if n["base"]["commits_after"] > 0]

    lines = [
        "# TIL 역이관 plan 요약",
        "",
        f"- 이관 대상: {len(notes)}편 (본문 역이관 {len(body)}편, 출처 추가 {len(src_only)}편)",
        f"- 이미 동등해 건너뜀: {plan['equal']}편",
        f"- unresolved 링크: {unresolved}건",
        f"- Wiki가 갈라진 뒤 TIL도 고쳐진 노트: {len(diverged)}편 (아래 절 확인)",
        f"- build-state에서 retired로 기록할 TIL 노트(Wiki에 없음): {len(plan['retired'])}편",
        f"- GitHub 링크 기준: {plan['github_base'] or '없음(origin이 GitHub 아님)'}",
        "",
        "## 폴더별 편수",
        "",
        "| 폴더 | 편수 |",
        "|---|---|",
        *[f"| {f} | {c} |" for f, c in sorted(folders.items(), key=lambda kv: (-kv[1], kv[0]))],
        "",
        "## 변경 줄 수 상위 10편",
        "",
        "| 노트 | 폴더 | 변경 줄 |",
        "|---|---|---|",
        *[f"| {s} | {n['folder']} | {n['changed_lines']} |" for s, n in top],
        "",
        "## unresolved 링크",
        "",
        "제안 처리: `--unresolved text`(일반 텍스트화) 또는 `--unresolved github`"
        "(TIL에 있는 대상만 GitHub 절대 링크, 없는 대상은 일반 텍스트).",
        "",
        _render_unresolved(notes).rstrip("\n"),
        "",
        "## Wiki가 갈라진 뒤 TIL도 고쳐진 노트 (역이관하면 TIL 변경이 되돌려짐 → 검토 필요)",
        "",
        "Wiki 본문과 가장 닮은 TIL 버전(작업트리+커밋 이력)이 최신이 아닌 노트."
        " 유형 '옛 TIL 사본'은 Wiki 수정이 없어 역이관이 TIL 변경만 되돌리므로 `--only`에서 뺀다"
        "(build-state가 Wiki 본문 해시로 기록해 다음 sync가 Wiki를 새 TIL로 맞춘다).",
        "",
        "| 노트 | Wiki 기준 TIL 버전 | 이후 TIL 커밋 | 유사도 | 유형 | 변경 줄 |",
        "|---|---|---|---|---|---|",
        *[
            f"| {s} | {n['base']['date']} {(n['base']['commit'] or '')[:7]} | {n['base']['commits_after']} "
            f"| {n['base']['similarity']} | {'옛 TIL 사본' if n['base']['exact'] else '양쪽 수정'} "
            f"| {n['changed_lines']} |"
            for s, n in diverged
        ],
        "",
        "## Wiki에만 source가 있는 노트 (TIL 끝에 `## 출처` 추가)",
        "",
        *([f"- {s}" for s in src_only] or ["- 없음"]),
        "",
    ]
    if missing:
        lines += [
            "## Wiki source 중 새 원문 `## 출처`에 없는 URL (자동 추가 안 함)",
            "",
            *[f"- {s}: {', '.join(urls)}" for s, urls in missing],
            "",
        ]
    lines += [
        "## 왕복 검증 (새 원문 → build_note → Wiki 본문과 동등)",
        "",
        "- 모두 동등" if not bad else f"- 동등하지 않음 {len(bad)}편:",
        *[f"  - {s}" for s in bad],
        "",
        "## retired 후보 (TIL에만 있음)",
        "",
        *([f"- {s}" for s in plan["retired"]] or ["- 없음"]),
        "",
    ]
    if plan["skipped"]:
        lines += ["## 건너뛴 노트", "", *[f"- {s}: {why}" for s, why in plan["skipped"]], ""]
    return "\n".join(lines)


# ------------------------------------------------------------------
# apply
# ------------------------------------------------------------------


def _load_plan(out: Path, paths: dict) -> dict:
    plan_path = out / "plan.json"
    if not plan_path.exists():
        raise UsageError(f"plan.json 없음({plan_path}) → 먼저 --plan")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    for key, cur in (("til", paths["til"]), ("wiki", paths["wiki"])):
        if not _same_path(Path(plan[key]), cur):
            raise UsageError(f"plan의 {key} 경로({plan[key]})가 현재({cur})와 다름")
    return plan


def cmd_apply(out: Path, paths: dict, only: list[str] | None, mode: str | None) -> int:
    plan = _load_plan(out, paths)
    notes = plan["notes"]
    if only is not None:
        unknown = [s for s in only if s not in notes]
        if unknown:
            raise UsageError(f"--only에 plan에 없는 노트: {', '.join(unknown)}")
        selected = [s for s in notes if s in set(only)]
    else:
        selected = list(notes)
    if mode is None and any(notes[s]["unresolved"] for s in selected):
        raise UsageError("unresolved 링크가 있음 → --unresolved text|github 지정 필요")

    applied: list[str] = []
    failures: list[tuple[str, str]] = []
    for stem in selected:
        n = notes[stem]
        target = paths["til"] / n["til_file"]
        try:
            current = _read(target)
        except OSError as exc:
            failures.append((stem, f"읽기 실패: {exc}"))
            continue
        if _sha(current) != n["til_sha"]:
            failures.append((stem, "plan 뒤 TIL 파일이 바뀜 → 쓰지 않음(다시 --plan)"))
            continue
        text = _read(out / n["new_file"])
        if n["unresolved"]:
            text = resolve_unresolved(text, mode, {u["link"]: u for u in n["unresolved"]})
        try:
            _write(target, text)
        except OSError as exc:
            failures.append((stem, f"쓰기 실패: {exc}"))
            continue
        applied.append(stem)

    # 이전 실행(다른 --only, 재실행)에서 적용한 편도 남긴다
    applied_path = out / "applied.json"
    previous = json.loads(applied_path.read_text(encoding="utf-8")) if applied_path.exists() else []
    recorded = sorted(set(previous) | set(applied))
    _write(applied_path, json.dumps(recorded, ensure_ascii=False) + "\n")
    print(f"apply: {len(applied)}편 씀")
    for stem, why in failures:
        print(f"  ❌ {stem}: {why}")
    return 1 if failures else 0


# ------------------------------------------------------------------
# build-state
# ------------------------------------------------------------------


def cmd_build_state(out: Path, paths: dict) -> int:
    state_path = paths["state"]
    if state_path.exists():
        raise UsageError(f"state 파일이 이미 있음({state_path}) → 덮어쓰지 않음")
    planned = _load_plan(out, paths)["notes"]
    applied_path = out / "applied.json"
    applied = set(json.loads(applied_path.read_text(encoding="utf-8"))) if applied_path.exists() else set()
    policy, mapping, til_index, wiki_index = _load_all(paths)

    notes: dict[str, dict] = {}
    pending: list[str] = []
    skipped: list[str] = []
    wiki_changed: list[str] = []
    for stem, srcs in sorted(til_index.items()):
        wiki_path = wiki_index.get(stem)
        if wiki_path is None:
            notes[stem] = {"status": "retired"}
            continue
        if len(srcs) > 1:
            skipped.append(stem)
            continue
        doc = fm.parse(_read(wiki_path))
        if doc is None:
            skipped.append(stem)
            continue
        wiki_sha = tilsync.body_sha(doc.body)
        plan_note = planned.get(stem)
        if plan_note is not None and plan_note["wiki_body_sha"] != wiki_sha:
            # plan 뒤 Wiki가 바뀜 → 기록하지 않음(sync가 충돌로 보고, 다시 plan 필요)
            wiki_changed.append(stem)
            continue
        gen = tilsync.build_note(srcs[0], srcs[0].parent.name, policy, mapping)
        old_copy = plan_note is not None and plan_note["base"]["exact"]
        if stem in applied or old_copy or equivalent(doc.body, gen.body):
            # TIL이 Wiki 본문을 담고 있거나(이관·동등) Wiki가 옛 TIL 사본(Wiki 수정 없음)
            # → 다음 sync가 Wiki 본문을 TIL 생성 본문으로 교체
            sha = wiki_sha
        else:
            # 이관 안 함 → Wiki 수정이 덮이지 않도록 TIL 생성 본문 해시(sync가 "이관 필요" 보고)
            sha = tilsync.body_sha(gen.body)
            pending.append(stem)
        notes[stem] = {"body_sha": sha, "status": "synced"}

    tilsync.save_state(state_path, {"version": 2, "notes": notes})
    synced = sum(1 for e in notes.values() if e["status"] == "synced")
    print(f"build-state: synced {synced}, retired {len(notes) - synced} → {state_path}")
    if pending:
        print(f"  이관 필요로 남는 노트 {len(pending)}편: {', '.join(pending)}")
    if wiki_changed:
        print(
            f"  plan 이후 Wiki 수정됨 — 다시 plan 필요(state에 기록 안 함) {len(wiki_changed)}편: "
            f"{', '.join(wiki_changed)}"
        )
    if skipped:
        print(f"  기록하지 않은 노트(중복 이름·파싱 불가) {len(skipped)}편: {', '.join(skipped)}")
    return 0


# ------------------------------------------------------------------
# main
# ------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="TIL <- Wiki 최초 이관")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--plan", action="store_true", help="읽기 전용: diff·요약 생성")
    group.add_argument("--apply", action="store_true", help="plan대로 TIL 파일 쓰기")
    group.add_argument("--build-state", action="store_true", help="state v2 생성")
    parser.add_argument("--out", required=True, type=Path, help="plan 결과 디렉터리")
    parser.add_argument("--only", help="apply할 노트 stem 목록(쉼표 구분)")
    parser.add_argument("--unresolved", choices=("text", "github"), help="unresolved 링크 처리")
    parser.add_argument("--real", action="store_true", help="실제 TIL·Wiki 경로 쓰기 허용(사용자 승인 후)")
    args = parser.parse_args(argv)

    action = "plan" if args.plan else "apply" if args.apply else "build-state"
    try:
        paths = resolve_paths(action, args.real)
        out = args.out.expanduser()
        if action == "plan":
            return cmd_plan(out, paths)
        _check_out(out, paths)
        if action == "apply":
            only = [_nfc(s.strip()) for s in args.only.split(",") if s.strip()] if args.only else None
            return cmd_apply(out, paths, only, args.unresolved)
        return cmd_build_state(out, paths)
    except UsageError as exc:
        print(f"til_backport: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
