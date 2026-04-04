#!/usr/bin/env python3
"""compile-state.py — Wiki Compiler의 결정적 상태 관리 스크립트

compile-state.json 읽기/쓰기, 변경 감지, 통계 산출을 결정적으로 처리.
자연어 해석에 의존하지 않고 정확한 diff와 상태 업데이트를 보장한다.
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def load_state(state_path: Path) -> dict:
    """compile-state.json 로드. 없으면 빈 상태 반환."""
    if state_path.exists():
        return json.loads(state_path.read_text(encoding="utf-8"))
    return {"project": "", "last_compiled": None, "processed_files": {}, "stats": {}}


def cmd_diff(raw_dir: Path, state_path: Path) -> None:
    """변경된 raw 파일 목록 출력 (JSON)."""
    state = load_state(state_path)
    processed = state.get("processed_files", {})

    changed = []
    new = []
    unchanged = []

    for md_file in sorted(raw_dir.glob("*.md")):
        rel_path = f"raw/{md_file.name}"
        mtime = datetime.fromtimestamp(
            md_file.stat().st_mtime, tz=timezone.utc
        ).isoformat()

        if rel_path not in processed:
            new.append({"path": rel_path, "modified_at": mtime})
        elif processed[rel_path].get("modified_at", "") < mtime:
            changed.append({"path": rel_path, "modified_at": mtime})
        else:
            unchanged.append(rel_path)

    result = {
        "new": new,
        "changed": changed,
        "unchanged": unchanged,
        "total_raw": len(new) + len(changed) + len(unchanged),
        "needs_compile": len(new) + len(changed),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_update(
    raw_dir: Path, state_path: Path, project_name: str, concepts_json: str
) -> None:
    """컴파일 완료 후 상태 업데이트."""
    state = load_state(state_path)
    now = datetime.now(tz=timezone.utc).isoformat()

    concepts_map = json.loads(concepts_json) if concepts_json else {}
    # concepts_map: {"raw/article-1.md": ["concept-a", "concept-b"]}

    state["project"] = project_name
    state["last_compiled"] = now

    for md_file in sorted(raw_dir.glob("*.md")):
        rel_path = f"raw/{md_file.name}"
        mtime = datetime.fromtimestamp(
            md_file.stat().st_mtime, tz=timezone.utc
        ).isoformat()
        state["processed_files"][rel_path] = {
            "modified_at": mtime,
            "compiled_at": now,
            "concepts": concepts_map.get(rel_path, []),
        }

    print(json.dumps(state, indent=2, ensure_ascii=False))


def cmd_stats(wiki_dir: Path) -> None:
    """wiki 디렉토리의 통계 산출."""
    concepts_dir = wiki_dir / "concepts"
    total_words = 0
    total_concepts = 0

    if concepts_dir.exists():
        for md_file in concepts_dir.glob("*.md"):
            text = md_file.read_text(encoding="utf-8")
            total_words += len(text.split())
            total_concepts += 1

    result = {
        "total_concepts": total_concepts,
        "total_words": total_words,
        "concepts": [f.stem for f in sorted(concepts_dir.glob("*.md"))]
        if concepts_dir.exists()
        else [],
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="Wiki Compiler State Manager")
    sub = parser.add_subparsers(dest="command", required=True)

    p_diff = sub.add_parser("diff", help="Show changed raw files since last compile")
    p_diff.add_argument("raw_dir", type=Path)
    p_diff.add_argument(
        "--state",
        type=Path,
        default=Path("wiki/_meta/compile-state.json"),
    )

    p_update = sub.add_parser("update", help="Update state after compilation")
    p_update.add_argument("raw_dir", type=Path)
    p_update.add_argument("--state", type=Path, default=Path("wiki/_meta/compile-state.json"))
    p_update.add_argument("--project", required=True)
    p_update.add_argument("--concepts", default="{}", help='JSON: {"raw/file.md": ["concept"]}')

    p_stats = sub.add_parser("stats", help="Calculate wiki statistics")
    p_stats.add_argument("wiki_dir", type=Path)

    args = parser.parse_args()

    if args.command == "diff":
        cmd_diff(args.raw_dir, args.state)
    elif args.command == "update":
        cmd_update(args.raw_dir, args.state, args.project, args.concepts)
    elif args.command == "stats":
        cmd_stats(args.wiki_dir)


if __name__ == "__main__":
    main()
