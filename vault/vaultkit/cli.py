"""vaultkit 명령줄 진입점.

``python3 -m vaultkit <명령>`` 또는 ``python3 ~/.dotfiles/vault/vk <명령>``.
명령: ``check [--json]``, ``apply [--dry-run] [--til-mapping] [--backup-dir DIR]``,
``register <file>...``, ``derive-maps``.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from .apply import ApplyRefused, run_apply
from .check import run_check
from .policy import load_policy
from .register import derive_maps, register_note


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vk", description="Obsidian vault 정책 점검·적용")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="정책 위반 점검(읽기 전용, 위반 시 exit 1)")
    check.add_argument("--json", action="store_true", help="JSON으로 출력")

    apply = sub.add_parser("apply", help="기계적 수정 적용")
    apply.add_argument("--dry-run", action="store_true", help="쓰지 않고 바뀔 파일만 보고")
    apply.add_argument("--til-mapping", action="store_true", help="TIL tag-mapping.json도 정규화")
    apply.add_argument(
        "--backup-dir",
        type=Path,
        help="백업 루트(기본 VAULTKIT_BACKUP_DIR 또는 ~/.local/state/vaultkit/backups)",
    )

    register = sub.add_parser("register", help="노트를 MOC/허브에 등록")
    register.add_argument("files", nargs="+", type=Path)

    sub.add_parser("derive-maps", help="현재 vault에서 moc/hubs/genos_subfolders 추천값 출력")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    policy = load_policy()

    if args.command == "check":
        report = run_check(policy)
        for warning in report.warnings:
            print(f"경고: {warning}", file=sys.stderr)
        if args.json:
            payload = {"findings": [asdict(f) for f in report.findings], "counts": report.counts()}
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            for f in report.findings:
                print(f"[{f.kind}] {f.path}: {f.detail}")
            summary = ", ".join(f"{k} {n}" for k, n in report.counts().items()) or "위반 없음"
            print(f"합계: {summary}")
        return report.exit_code

    if args.command == "apply":
        return _apply(policy, args)

    if args.command == "register":
        for path in args.files:
            r = register_note(path.expanduser().resolve(), policy, dry_run=False)
            print(f"{r.status}\t{path}\t{r.target or '-'}\t{r.section or '-'}\t{r.line or '-'}")
        return 0

    if args.command == "derive-maps":
        print(json.dumps(derive_maps(policy), ensure_ascii=False, indent=2))
        return 0

    return 2


def _apply(policy, args) -> int:
    backup: list[Path] = []

    def announce(path: Path) -> None:
        backup.append(path)
        print(f"백업 위치: {path}", file=sys.stderr, flush=True)

    try:
        result = run_apply(
            policy,
            dry_run=args.dry_run,
            til_mapping=args.til_mapping,
            backup_root=args.backup_dir,
            on_backup_dir=announce,
        )
        for warning in result.warnings:
            print(f"경고: {warning}", file=sys.stderr)
        prefix = "변경 예정" if args.dry_run else "변경"
        for rel in result.changed:
            print(f"{prefix}: {rel}")
        for rel in result.skipped_unparseable:
            print(f"건너뜀(파싱 불가): {rel}")
        for rel in result.empty_after_normalize:
            print(f"건너뜀(empty-after-normalize): {rel}")
        print(
            f"{prefix} {len(result.changed)}건, 파싱 불가 {len(result.skipped_unparseable)}건, "
            f"empty-after-normalize {len(result.empty_after_normalize)}건"
        )
        return 0
    except ApplyRefused as exc:
        print(f"vk apply: {exc}", file=sys.stderr)
        return 2
    finally:
        # 정상 종료든 예외든 백업 경로를 마지막에 다시 보인다
        if backup:
            print(f"백업: {backup[0]}", flush=True)
