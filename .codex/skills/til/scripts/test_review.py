"""Exercise review orchestration with local CLI stand-ins, without model calls."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RUNNER = Path(__file__).with_name("review.py")
PASS = "## Blocker\n없음\n\n## Refinement\n없음\n\n## Insight\n없음\n\nSTATUS: PASS\n"
FAIL = "## Blocker\n잘못된 인과관계. 조건을 명시하세요.\n\n## Refinement\n없음\n\n## Insight\n없음\n\nSTATUS: FAIL\n"
FAKE = r"""
import json, os, pathlib, sys, time
name = pathlib.Path(sys.argv[0]).name
config = json.loads(pathlib.Path(os.environ["REVIEW_FIXTURE"]).read_text())
prompt = sys.stdin.read() if name == "claude" else sys.argv[sys.argv.index("--print") + 1]
root = pathlib.Path(os.environ["REVIEW_CAPTURE"])
(root / (name + ".json")).write_text(json.dumps({"argv": sys.argv[1:], "prompt": prompt, "cwd": os.getcwd()}))
if config.get("barrier"):
    other = "agy" if name == "claude" else "claude"
    until = time.monotonic() + 3
    while not (root / (other + ".json")).exists():
        if time.monotonic() > until:
            sys.exit(9)
        time.sleep(0.01)
item = config[name]
time.sleep(item.get("sleep", 0))
print(item["text"], end="")
sys.exit(item.get("exit", 0))
"""


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        for name in ("claude", "agy"):
            executable = self.bin / name
            executable.write_text(f"#!{sys.executable}\n" + FAKE)
            executable.chmod(0o700)
        self.document = self.root / "학습 노트.md"
        self.original = "# 원자성\n트랜잭션은 모두 반영되거나 모두 취소됩니다.\n"
        self.document.write_text(self.original)
        self.fixture = self.root / "fixture.json"
        self.output = self.root / "result"
        self.env = dict(
            os.environ,
            PATH=str(self.bin),
            REVIEW_FIXTURE=str(self.fixture),
            REVIEW_CAPTURE=str(self.root),
        )

    def run_review(
        self, claude=PASS, agy=PASS, *, exit_code=0, sleep=0, timeout=5, barrier=False
    ):
        self.assertTrue(RUNNER.is_file(), "교차 검토 실행기가 아직 없습니다")
        self.fixture.write_text(
            json.dumps(
                {
                    "claude": {"text": claude, "exit": exit_code, "sleep": sleep},
                    "agy": {"text": agy},
                    "barrier": barrier,
                }
            )
        )
        result = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                str(self.document),
                "--output-dir",
                str(self.output),
                "--timeout",
                str(timeout),
            ],
            env=self.env,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(self.document.read_text(), self.original)
        return result, json.loads((self.output / "result.json").read_text())

    def test_parallel_review_delivers_document_and_preserves_source(self):
        result, report = self.run_review(barrier=True)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(report["status"], "PASS")
        for name in ("claude", "agy"):
            capture = json.loads((self.root / (name + ".json")).read_text())
            self.assertIn(self.original, capture["prompt"])
            self.assertNotEqual(capture["cwd"], str(self.document.parent))
            self.assertNotIn("--dangerously-skip-permissions", capture["argv"])
        claude_args = json.loads((self.root / "claude.json").read_text())["argv"]
        self.assertEqual(
            claude_args[claude_args.index("--tools") + 1], "WebSearch,WebFetch"
        )
        agy_args = json.loads((self.root / "agy.json").read_text())["argv"]
        self.assertEqual(agy_args[agy_args.index("--mode") + 1], "plan")
        self.assertNotIn("--disable-slash-commands", agy_args)

    def test_blocker_produces_fail(self):
        result, report = self.run_review(agy=FAIL)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(report["status"], "FAIL")

    def test_malformed_and_contradictory_results_are_errors(self):
        for value in (
            "",
            "STATUS: PASS",
            FAIL.replace("STATUS: FAIL", "STATUS: PASS"),
            PASS + "STATUS: FAIL\n",
        ):
            with self.subTest(value=value):
                self.output = (
                    self.root / f"result-{len(list(self.root.glob('result*')))}"
                )
                result, report = self.run_review(claude=value)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(report["status"], "ERROR")

    def test_nonzero_exit_overrides_pass_and_fail(self):
        result, report = self.run_review(agy=FAIL, exit_code=7)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report["status"], "ERROR")
        self.assertEqual(report["reviews"]["claude"]["status"], "ERROR")

    def test_duplicate_blocker_cannot_hide_under_pass(self):
        malformed = PASS.replace(
            "## Insight", "## Blocker\n중대한 사실 오류\n\n## Insight"
        )
        result, report = self.run_review(claude=malformed)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report["status"], "ERROR")

    def test_timeout_keeps_other_review(self):
        result, report = self.run_review(sleep=3, timeout=1)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report["reviews"]["antigravity"]["status"], "PASS")
        self.assertIn("timeout", report["reviews"]["claude"]["error"])

    def test_missing_cli_is_error(self):
        (self.bin / "claude").unlink()
        result, report = self.run_review()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(report["reviews"]["claude"]["status"], "ERROR")


if __name__ == "__main__":
    unittest.main()
