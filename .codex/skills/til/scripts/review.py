"""Run independent Claude/Antigravity TIL reviews; exit 0=PASS, 1=FAIL, 2=ERROR."""

import argparse
import hashlib
import json
import math
import os
import re
import signal
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

RUBRIC = Path(__file__).resolve().parent.parent / "references" / "review-rubric.md"


def review_status(text):
    """Reject incomplete, contradictory, or ambiguous model verdicts."""
    headings = re.findall(r"^## ([^\n]+)", text, re.MULTILINE)
    if [heading.strip() for heading in headings] != [
        "Blocker",
        "Refinement",
        "Insight",
    ]:
        raise ValueError("응답 형식 오류: 검토 섹션의 중복, 누락 또는 순서 오류")
    match = re.fullmatch(
        r"\s*## Blocker\s*\n(.+?)\n## Refinement\s*\n(.+?)\n"
        r"## Insight\s*\n(.+?)\nSTATUS: (PASS|FAIL)\s*",
        text,
        re.DOTALL,
    )
    if not match or len(re.findall(r"^STATUS:", text, re.MULTILINE)) != 1:
        raise ValueError("응답 형식 오류: 세 섹션과 마지막 STATUS가 필요합니다")
    blocker, refinement, insight, status = match.groups()
    if not all(part.strip() for part in (blocker, refinement, insight)):
        raise ValueError("응답 형식 오류: 빈 검토 섹션")
    if (blocker.strip() == "없음") != (status == "PASS"):
        raise ValueError("Blocker와 STATUS가 모순됩니다")
    return status


def invoke(name, command, prompt, output, timeout, stdin=False):
    """Use an isolated cwd, retain logs, and terminate the process group on timeout."""
    stdout_path = output / f"{name}.md"
    stderr_path = output / f"{name}.stderr.log"
    result = {"status": "ERROR", "report": str(stdout_path), "stderr": str(stderr_path)}
    with tempfile.TemporaryDirectory(prefix=f"til-{name}-") as cwd:
        try:
            with (
                stdout_path.open("w", encoding="utf-8") as stdout,
                stderr_path.open("w", encoding="utf-8") as stderr,
            ):
                process = subprocess.Popen(
                    command,
                    stdin=subprocess.PIPE if stdin else subprocess.DEVNULL,
                    stdout=stdout,
                    stderr=stderr,
                    text=True,
                    cwd=cwd,
                    start_new_session=True,
                )
                try:
                    process.communicate(
                        input=prompt if stdin else None, timeout=timeout
                    )
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.communicate()
                    result["error"] = (
                        f"timeout after {timeout:g}s; 자동 재시도하지 않았습니다"
                    )
                    return result
            result["exit_code"] = process.returncode
            if process.returncode != 0:
                result["error"] = (
                    f"CLI exit {process.returncode}; stderr 로그를 확인하세요"
                )
            else:
                result["status"] = review_status(
                    stdout_path.read_text(encoding="utf-8")
                )
        except (OSError, ValueError) as error:
            result["error"] = str(error)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document", type=Path, help="검토할 단일 TIL Markdown 파일")
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="새 결과 디렉터리 (기본: 임시 디렉터리, 결과 보존)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=240,
        help="리뷰어별 제한 초 (기본: 240, 재시도 없음)",
    )
    parser.add_argument("--claude-model", help="생략하면 Claude CLI 설정 사용")
    parser.add_argument("--antigravity-model", help="생략하면 agy 설정 사용")
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("--timeout은 양의 유한한 값이어야 합니다")
    document = args.document.expanduser().resolve()
    if document.suffix.lower() != ".md" or document.name in {
        "AGENTS.md",
        "CLAUDE.md",
        "GEMINI.md",
    }:
        parser.error("에이전트 설정 파일이 아닌 TIL .md 파일을 지정하세요")
    try:
        snapshot = document.read_bytes()
        body = snapshot.decode("utf-8")
        if not body.strip():
            parser.error("빈 문서는 검토하지 않습니다")
        rubric = RUBRIC.read_text(encoding="utf-8")
        if args.output_dir:
            output = args.output_dir.expanduser().resolve()
            output.mkdir(mode=0o700, parents=True, exist_ok=False)
        else:
            output = Path(tempfile.mkdtemp(prefix="til-review-"))
    except (OSError, UnicodeError) as error:
        parser.error(str(error))

    digest = hashlib.sha256(snapshot).hexdigest()
    (output / "document.md").write_bytes(snapshot)
    context = f"오늘 날짜: {datetime.now(timezone.utc).astimezone().date().isoformat()}\n{rubric}\n\n--- TIL_DOCUMENT_START ---\n{body}\n--- TIL_DOCUMENT_END ---\n"
    claude_prompt = (
        "당신은 Claude 사실 검증 리뷰어입니다. Claude 전용 역할을 수행하세요.\n"
        + context
    )
    agy_prompt = (
        "당신은 Antigravity 논리 검증 리뷰어입니다. Antigravity 전용 역할을 수행하세요.\n"
        + context
    )
    claude = [
        "claude",
        "--print",
        "--output-format",
        "text",
        "--no-session-persistence",
        "--tools",
        "WebSearch,WebFetch",
        "--allowedTools",
        "WebSearch,WebFetch",
        "--strict-mcp-config",
        "--setting-sources",
        "user",
        "--settings",
        '{"disableAllHooks":true}',
        "--disable-slash-commands",
    ]
    # agy disables --mode when --disable-slash-commands is present.
    agy = ["agy", "--mode", "plan", "--sandbox"]
    if args.claude_model:
        claude.extend(["--model", args.claude_model])
    if args.antigravity_model:
        agy.extend(["--model", args.antigravity_model])
    agy.extend(["--print", agy_prompt])

    print(f"리뷰 결과: {output}", flush=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(
            invoke, "claude", claude, claude_prompt, output, args.timeout, True
        )
        second = pool.submit(
            invoke, "antigravity", agy, agy_prompt, output, args.timeout
        )
        reviews = {"claude": first.result(), "antigravity": second.result()}
    statuses = {review["status"] for review in reviews.values()}
    status = (
        "ERROR" if "ERROR" in statuses else "FAIL" if "FAIL" in statuses else "PASS"
    )
    report = {
        "document": str(document),
        "sha256": digest,
        "status": status,
        "reviews": reviews,
    }
    try:
        unchanged = document.read_bytes() == snapshot
    except OSError:
        unchanged = False
    if not unchanged:
        report.update(
            status="ERROR",
            error="리뷰 중 원본이 변경되었습니다. 현재 문서에 대한 검토가 아닙니다",
        )
    (output / "result.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    for name, review in reviews.items():
        print(f"\n=== {name}: {review['status']} ===")
        print(
            Path(review["report"]).read_text(encoding="utf-8", errors="replace")
            if Path(review["report"]).exists()
            else ""
        )
        if review.get("error"):
            print(review["error"])
    if report.get("error"):
        print(report["error"])
    print(f"\nOVERALL: {report['status']}")
    return {"PASS": 0, "FAIL": 1, "ERROR": 2}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
