"""최초 이관 스크립트(``vault/scripts/til_backport.py``) 테스트.

스크립트를 subprocess로 실행하고 ``TIL_PATH``/``OBSIDIAN_PATH``/
``VAULTKIT_POLICY``/``SYNC_STATE_PATH``로 임시 TIL·vault만 가리킨다.
plan -> apply -> build-state -> TIL sync script full 두 번의 수렴을 확인한다.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unicodedata
import unittest
from pathlib import Path

VAULT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(VAULT_DIR))

from vaultkit import frontmatter as fm
from vaultkit.tilsync import _same_content, body_sha

BACKPORT = VAULT_DIR / "scripts" / "til_backport.py"
SYNC_SCRIPT = Path(
    os.environ.get("TIL_SYNC_SCRIPT", Path.home() / "dev/TIL/.githooks/sync-to-obsidian.py")
)
_SYNC_OK = SYNC_SCRIPT.exists() and 'os.environ.get("OBSIDIAN_PATH")' in SYNC_SCRIPT.read_text(
    encoding="utf-8"
)

REPO_URL = "https://github.com/octo/til-test.git"

# A: 링크 표기만 다름(동등) / B: Wiki에서 본문 수정 + 여러 링크 / C: Wiki에만 source
# E: Wiki에서 본문 수정(--only 테스트용) / D: TIL에만 있음(retired)
TIL_A = "# 에이 제목\n\n에이 본문. [비 노트](../java/노트B.md) 참고.\n"
WIKI_A_BODY = "\n에이 본문. [[노트B|비 노트]] 참고.\n"
TIL_B = "# 비 제목\n\n비 원래 본문.\n"
WIKI_B_BODY = (
    "\n비 원래 본문.\n\nWiki에서 추가한 문단. [[노트A]]와 [[노트C#절|씨]] 참고.\n"
    "Wiki 전용 [[WikiOnly|위키 노트]]도 있다.\n\n"
    "| 열 | 링크 |\n|---|---|\n| x | [[노트A\\|에이]] |\n\n"
    "```\n[[코드-안]]\n```\n"
)
TIL_C = "# 씨 제목\n\n## 절\n\n씨 본문.\n"
WIKI_C_BODY = "\n## 절\n\n씨 본문.\n"
TIL_E = "# 이 제목\n\n이 원래 본문.\n"
WIKI_E_BODY = "\n이 원래 본문.\n\nWiki에서 고친 문장.\n"
TIL_D = "# 디 제목\n\n디 본문.\n"


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def _nfd(s: str) -> str:
    return unicodedata.normalize("NFD", s)


def _eq(a: str, b: str) -> bool:
    """tilsync 내용 동등 + frontmatter 뒤 빈 줄 차이 무시(이관 스크립트 기준)."""
    return _same_content(a.lstrip("\n"), b.lstrip("\n"))


class BackportTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.til = self.root / "TIL"
        self.vault = self.root / "vault"
        self.wiki = self.vault / "Wiki"
        self.out = self.root / "out"
        self.state_path = self.wiki / ".til-sync-state.json"
        (self.wiki / "_MOC").mkdir(parents=True)
        self.til.mkdir()
        (self.til / "tag-mapping.json").write_text("{}", encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(self.til)], check=True)
        subprocess.run(
            ["git", "-C", str(self.til), "remote", "add", "origin", REPO_URL], check=True
        )

        raw = json.loads((VAULT_DIR / "vault-policy.json").read_text(encoding="utf-8"))
        raw["paths"]["vault_root"] = str(self.vault)
        raw["paths"]["til_root"] = str(self.til)
        self.policy_path = self.root / "policy.json"
        self.policy_path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")

        self.paths = {
            "노트A": self.til_note("python", "노트A", TIL_A),
            "노트B": self.til_note("java", "노트B", TIL_B),
            "노트C": self.til_note("python", "노트C", TIL_C),
            "노트E": self.til_note("python", "노트E", TIL_E),
            "노트D": self.til_note("python", "노트D", TIL_D),
        }
        self.wiki_note(_nfd("노트A"), WIKI_A_BODY)  # 디스크 파일명 NFD
        self.wiki_note("노트B", WIKI_B_BODY)
        self.wiki_note(
            "노트C", WIKI_C_BODY, source="source:\n  - https://example.com/c\n  - https://example.com/c2\n"
        )
        self.wiki_note("노트E", WIKI_E_BODY)
        self.wiki_note("WikiOnly", "\n위키 전용.\n")
        self.wiki_before = {p.name: p.read_bytes() for p in self.wiki.glob("*.md")}

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # -- helpers ---------------------------------------------------------

    def til_note(self, folder: str, name: str, text: str) -> Path:
        d = self.til / folder
        d.mkdir(exist_ok=True)
        p = d / f"{name}.md"
        p.write_text(text, encoding="utf-8")
        return p

    def wiki_note(self, filename: str, body: str, source: str = "") -> Path:
        p = self.wiki / f"{filename}.md"
        p.write_text(
            f'---\ntitle: "x"\n{source}topics:\n  - Python\ntags:\n  - python/basics\n  - til\n'
            f"created: 2026-01-01\n---\n{body}",
            encoding="utf-8",
        )
        return p

    def env(self, **extra: str) -> dict:
        env = dict(os.environ)
        env.update(
            TIL_PATH=str(self.til),
            OBSIDIAN_PATH=str(self.wiki),
            VAULTKIT_PATH=str(VAULT_DIR),
            VAULTKIT_POLICY=str(self.policy_path),
            SYNC_STATE_PATH=str(self.state_path),
        )
        for key, value in extra.items():
            if value is None:
                env.pop(key, None)
            else:
                env[key] = value
        return env

    def call(self, *args: str, expect: int = 0, script: Path = BACKPORT, **env) -> subprocess.CompletedProcess:
        proc = subprocess.run(
            [sys.executable, str(script), *args],
            capture_output=True,
            text=True,
            env=self.env(**env),
            cwd=self.root,
        )
        self.assertEqual(proc.returncode, expect, proc.stdout + proc.stderr)
        return proc

    def plan(self) -> dict:
        self.call("--plan", "--out", str(self.out))
        return json.loads((self.out / "plan.json").read_text(encoding="utf-8"))

    def wiki_body(self, stem: str) -> str:
        path = next(p for p in self.wiki.glob("*.md") if _nfc(p.stem) == stem)
        return fm.parse(path.read_text(encoding="utf-8")).body

    def sync_counts(self, proc: subprocess.CompletedProcess) -> dict:
        counts = {}
        for line in proc.stdout.splitlines():
            key, sep, value = line.strip().partition(": ")
            if sep and value.isdigit():
                counts[key] = int(value)
        return counts

    # -- plan ------------------------------------------------------------

    def test_plan_writes_only_out_dir(self) -> None:
        til_before = {p: p.read_bytes() for p in self.til.rglob("*.md")}
        plan = self.plan()
        self.assertEqual({p: p.read_bytes() for p in self.til.rglob("*.md")}, til_before)
        self.assertEqual({p.name: p.read_bytes() for p in self.wiki.glob("*.md")}, self.wiki_before)
        self.assertFalse(self.state_path.exists())

        notes = plan["notes"]
        self.assertEqual(set(notes), {"노트B", "노트C", "노트E"})  # 노트A는 동등 → 건너뜀
        for stem in notes:
            self.assertTrue((self.out / f"{stem}.diff").exists(), stem)
        self.assertFalse((self.out / "노트A.diff").exists())
        self.assertEqual(plan["retired"], ["노트D"])
        self.assertTrue(all(n["roundtrip_ok"] for n in notes.values()), notes)

        b = notes["노트B"]
        self.assertEqual(b["folder"], "java")
        links = {u["link"]: u for u in b["unresolved"]}
        self.assertEqual(set(links), {"[[WikiOnly|위키 노트]]"})
        self.assertIsNone(links["[[WikiOnly|위키 노트]]"]["github"])
        new_b = (self.out / "new" / "java" / "노트B.md").read_text(encoding="utf-8")
        self.assertIn("[노트A](../python/노트A.md)", new_b)
        self.assertIn("[씨](../python/노트C.md#절)", new_b)
        self.assertIn("[에이](../python/노트A.md)", new_b)
        self.assertIn("[[코드-안]]", new_b)
        self.assertTrue(new_b.startswith("# 비 제목\n\n"), new_b)

        c = notes["노트C"]
        self.assertEqual(c["source_append"], ["https://example.com/c", "https://example.com/c2"])
        new_c = (self.out / "new" / "python" / "노트C.md").read_text(encoding="utf-8")
        self.assertTrue(new_c.endswith("## 출처\n\n- <https://example.com/c>\n- <https://example.com/c2>\n"), new_c)

        diff = (self.out / "노트E.diff").read_text(encoding="utf-8")
        self.assertIn("+Wiki에서 고친 문장.", diff)
        summary = (self.out / "summary.md").read_text(encoding="utf-8")
        self.assertIn("[[WikiOnly\\|위키 노트]]", summary)  # 표 안 | 이스케이프
        self.assertIn("노트C", summary)
        self.assertIn("모두 동등", summary)

    def test_plan_github_suggestion_for_til_target(self) -> None:
        # 정방향이 다시 인식할 수 없는 stem(TIL에는 있음) → GitHub 절대 링크 제안
        self.til_note("python", "물음표?", "# 물음표\n\n본문.\n")
        self.wiki_note("노트E", WIKI_E_BODY + "\n[[물음표?|질문]] 링크.\n")
        plan = self.plan()
        links = {u["link"]: u for u in plan["notes"]["노트E"]["unresolved"]}
        self.assertEqual(
            links["[[물음표?|질문]]"]["github"],
            "https://github.com/octo/til-test/blob/main/python/%EB%AC%BC%EC%9D%8C%ED%91%9C%3F.md",
        )

    def git_commit(self, message: str) -> None:
        git = ["git", "-C", str(self.til), "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.run([*git, "add", "-A"], check=True)
        subprocess.run([*git, "commit", "-q", "-m", message], check=True)

    def test_plan_flags_til_changed_after_wiki_base(self) -> None:
        # 노트F: Wiki는 옛 TIL 사본(Wiki 수정 없음) / 노트E: Wiki·TIL 양쪽 수정
        self.til_note("python", "노트F", "# 에프\n\n옛 내용.\n")
        self.wiki_note("노트F", "\n옛 내용.\n")
        self.git_commit("init")
        self.paths["노트E"].write_text(TIL_E + "\nTIL에서 나중에 고침.\n", encoding="utf-8")
        (self.til / "python" / "노트F.md").write_text("# 에프\n\n새 내용.\n", encoding="utf-8")
        self.git_commit("later")

        notes = self.plan()["notes"]
        f, e, b = notes["노트F"]["base"], notes["노트E"]["base"], notes["노트B"]["base"]
        self.assertEqual((f["commits_after"], f["exact"]), (1, True))
        self.assertEqual((e["commits_after"], e["exact"]), (1, False))
        self.assertEqual(b["commits_after"], 0)
        summary = (self.out / "summary.md").read_text(encoding="utf-8")
        self.assertIn("| 노트F |", summary)
        self.assertIn("옛 TIL 사본", summary)
        self.assertIn("| 노트E |", summary)

    def test_plan_refuses_out_inside_til_or_wiki(self) -> None:
        for bad in (self.til / "plan", self.wiki / "plan"):
            proc = self.call("--plan", "--out", str(bad), expect=2)
            self.assertIn("--out", proc.stderr)
            self.assertFalse(bad.exists())

    # -- guard -----------------------------------------------------------

    def test_apply_and_build_state_require_env(self) -> None:
        self.plan()
        for var in ("TIL_PATH", "OBSIDIAN_PATH"):
            proc = self.call("--apply", "--out", str(self.out), "--unresolved", "text", expect=2, **{var: None})
            self.assertIn(var, proc.stderr)
        proc = self.call("--build-state", "--out", str(self.out), expect=2, SYNC_STATE_PATH=None)
        self.assertIn("SYNC_STATE_PATH", proc.stderr)
        self.assertFalse((self.out / "applied.json").exists())
        self.assertFalse(self.state_path.exists())
        self.assertEqual(self.paths["노트B"].read_text(encoding="utf-8"), TIL_B)

    def test_apply_refuses_real_paths_without_flag(self) -> None:
        self.plan()
        real_til = str(Path.home() / "dev/TIL")
        proc = self.call(
            "--apply", "--out", str(self.out), "--unresolved", "text", expect=2, TIL_PATH=real_til
        )
        self.assertIn("실제 경로", proc.stderr)
        self.assertFalse((self.out / "applied.json").exists())

    def test_apply_requires_unresolved_choice(self) -> None:
        self.plan()
        proc = self.call("--apply", "--out", str(self.out), expect=2)
        self.assertIn("--unresolved", proc.stderr)
        self.assertEqual(self.paths["노트B"].read_text(encoding="utf-8"), TIL_B)

    # -- apply -----------------------------------------------------------

    def test_apply_unresolved_text(self) -> None:
        self.plan()
        self.call("--apply", "--out", str(self.out), "--unresolved", "text")
        new_b = self.paths["노트B"].read_text(encoding="utf-8")
        self.assertIn("Wiki 전용 위키 노트도 있다.", new_b)
        self.assertIn("[[코드-안]]", new_b)  # 코드 안은 그대로
        self.assertNotIn("[[WikiOnly", new_b)
        self.assertEqual(
            json.loads((self.out / "applied.json").read_text(encoding="utf-8")),
            ["노트B", "노트C", "노트E"],
        )

    def test_apply_unresolved_github(self) -> None:
        self.til_note("python", "물음표?", "# 물음표\n\n본문.\n")
        self.wiki_note("노트E", WIKI_E_BODY + "\n[[물음표?|질문]] 링크.\n")
        self.plan()
        self.call("--apply", "--out", str(self.out), "--unresolved", "github")
        new_e = self.paths["노트E"].read_text(encoding="utf-8")
        self.assertIn(
            "[질문](https://github.com/octo/til-test/blob/main/python/%EB%AC%BC%EC%9D%8C%ED%91%9C%3F.md)",
            new_e,
        )
        # TIL에 없는 대상은 github 모드에서도 일반 텍스트
        self.assertIn("Wiki 전용 위키 노트도 있다.", self.paths["노트B"].read_text(encoding="utf-8"))

    def test_apply_only_and_stale_til(self) -> None:
        self.plan()
        self.paths["노트C"].write_text(TIL_C + "\n계획 뒤에 고침.\n", encoding="utf-8")
        proc = self.call(
            "--apply", "--out", str(self.out), "--only", "노트B,노트C", "--unresolved", "text", expect=1
        )
        self.assertIn("노트C", proc.stdout + proc.stderr)
        self.assertNotEqual(self.paths["노트B"].read_text(encoding="utf-8"), TIL_B)
        self.assertEqual(self.paths["노트E"].read_text(encoding="utf-8"), TIL_E)
        self.assertEqual(
            self.paths["노트C"].read_text(encoding="utf-8"), TIL_C + "\n계획 뒤에 고침.\n"
        )
        self.assertEqual(json.loads((self.out / "applied.json").read_text(encoding="utf-8")), ["노트B"])

    def test_apply_only_unknown_stem(self) -> None:
        self.plan()
        proc = self.call("--apply", "--out", str(self.out), "--only", "없는노트", "--unresolved", "text", expect=2)
        self.assertIn("없는노트", proc.stderr)

    # -- build-state -----------------------------------------------------

    def test_build_state(self) -> None:
        self.plan()
        self.call("--apply", "--out", str(self.out), "--only", "노트B,노트C", "--unresolved", "text")
        self.call("--build-state", "--out", str(self.out))
        state = json.loads(self.state_path.read_text(encoding="utf-8"))
        self.assertEqual(state["version"], 2)
        notes = state["notes"]
        self.assertEqual(notes["노트D"], {"status": "retired"})
        self.assertNotIn("WikiOnly", notes)
        for stem in ("노트A", "노트B", "노트C"):  # 동등 또는 이관 완료 → Wiki 본문 해시
            self.assertEqual(notes[stem], {"status": "synced", "body_sha": body_sha(self.wiki_body(stem))})
        # 이관하지 않은 노트 → TIL 생성 본문 해시(Wiki 수정이 덮이지 않음)
        self.assertEqual(notes["노트E"]["status"], "synced")
        self.assertNotEqual(notes["노트E"]["body_sha"], body_sha(self.wiki_body("노트E")))
        # 이미 있으면 덮어쓰지 않는다
        self.call("--build-state", "--out", str(self.out), expect=2)

    # -- 전체 흐름 -------------------------------------------------------

    @unittest.skipUnless(_SYNC_OK, f"환경변수 덮어쓰기를 지원하는 sync script 없음: {SYNC_SCRIPT}")
    def test_full_flow_converges(self) -> None:
        self.plan()
        predicted = {
            stem: fm.parse(p.read_text(encoding="utf-8")).body
            for stem, p in ((_nfc(p.stem), p) for p in self.wiki.glob("*.md"))
        }
        self.call("--apply", "--out", str(self.out), "--only", "노트B,노트C", "--unresolved", "text")
        self.call("--build-state", "--out", str(self.out))

        first = self.sync_counts(self.call("--verbose", script=SYNC_SCRIPT))
        self.assertEqual(first["conflict"], 0)
        self.assertEqual(first["frontmatter-only"], 1)  # 노트E: 이관 안 함 → 이관 필요
        second_proc = self.call(script=SYNC_SCRIPT)
        second = self.sync_counts(second_proc)
        self.assertEqual(second["unchanged"], 3, second_proc.stdout)
        self.assertEqual(second["frontmatter-only"], 1)
        self.assertEqual(second["skip-retired"], 1)
        self.assertEqual(second["create"] + second["update"] + second["conflict"], 0)
        self.assertFalse((self.wiki / "노트D.md").exists())

        self.assertTrue(_eq(self.wiki_body("노트A"), predicted["노트A"]))
        self.assertTrue(
            _eq(
                self.wiki_body("노트B"),
                predicted["노트B"].replace("[[WikiOnly|위키 노트]]", "위키 노트"),
            )
        )
        self.assertTrue(
            _eq(
                self.wiki_body("노트C"),
                predicted["노트C"] + "\n## 출처\n\n- <https://example.com/c>\n- <https://example.com/c2>\n",
            )
        )
        self.assertEqual(self.wiki_body("노트E"), WIKI_E_BODY)  # 이관 안 한 Wiki 수정 보존
        c_doc = fm.parse(next(p for p in self.wiki.glob("*.md") if _nfc(p.stem) == "노트C").read_text(encoding="utf-8"))
        self.assertEqual(fm.get_list(c_doc, "source"), ["https://example.com/c", "https://example.com/c2"])
        self.assertEqual((self.wiki / "WikiOnly.md").read_bytes(), self.wiki_before["WikiOnly.md"])


if __name__ == "__main__":
    unittest.main()
