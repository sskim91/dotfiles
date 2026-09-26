"""TIL git hook 동기화 스크립트(``~/dev/TIL/.githooks/sync-to-obsidian.py``) 테스트.

스크립트를 subprocess로 실행하고, ``TIL_PATH``/``OBSIDIAN_PATH``/
``VAULTKIT_POLICY``/``SYNC_STATE_PATH`` 환경변수로 임시 TIL·vault를 가리킨다.
실제 TIL·Wiki는 전혀 건드리지 않는다. 임시 policy는 실제 ``vault-policy.json``
사본에서 ``paths.vault_root``만 임시 vault로 바꾼 것이다(register가 임시 MOC를 쓰도록).
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unicodedata
import unittest
from pathlib import Path

VAULT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(VAULT_DIR))

from vaultkit import frontmatter as fm
from vaultkit.tilsync import body_sha

SCRIPT = Path(os.environ.get("TIL_SYNC_SCRIPT", Path.home() / "dev/TIL/.githooks/sync-to-obsidian.py"))

MOC_PYTHON = """---
title: MOC-Python
tags:
  - moc
---

## 언어 기초·문법

- [[기존-노트]] — 기존 설명.

## 기타
"""


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def _nfd(s: str) -> str:
    return unicodedata.normalize("NFD", s)


# 환경변수 덮어쓰기를 모르는 옛 스크립트는 실제 Wiki에 state를 쓰므로 실행하지 않는다.
_SCRIPT_OK = SCRIPT.exists() and 'os.environ.get("OBSIDIAN_PATH")' in SCRIPT.read_text(encoding="utf-8")


@unittest.skipUnless(_SCRIPT_OK, f"환경변수 덮어쓰기를 지원하는 sync script 없음: {SCRIPT}")
class TilScriptTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.til = self.root / "TIL"
        self.vault = self.root / "vault"
        self.wiki = self.vault / "Wiki"
        (self.wiki / "_MOC").mkdir(parents=True)
        (self.wiki / "_MOC" / "MOC-Python.md").write_text(MOC_PYTHON, encoding="utf-8")
        self.til.mkdir()
        (self.til / "tag-mapping.json").write_text("{}", encoding="utf-8")
        self.state_path = self.wiki / ".til-sync-state.json"
        self.backups = self.root / "backups"

        raw = json.loads((VAULT_DIR / "vault-policy.json").read_text(encoding="utf-8"))
        raw["paths"]["vault_root"] = str(self.vault)
        raw["paths"]["til_root"] = str(self.til)
        self.policy_path = self.root / "policy.json"
        self.policy_path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")

    def tearDown(self) -> None:
        self.wiki.chmod(stat.S_IRWXU)
        for p in self.root.rglob("*"):
            if p.is_file():
                p.chmod(stat.S_IRUSR | stat.S_IWUSR)
        self._tmp.cleanup()

    # -- helpers ---------------------------------------------------------

    def env(self, **extra: str) -> dict:
        env = dict(os.environ)
        env.update(
            TIL_PATH=str(self.til),
            OBSIDIAN_PATH=str(self.wiki),
            VAULTKIT_PATH=str(VAULT_DIR),
            VAULTKIT_POLICY=str(self.policy_path),
            VAULTKIT_BACKUP_DIR=str(self.backups),  # 기본 ~/.local/state에 쓰지 않도록
        )
        env.pop("SYNC_STATE_PATH", None)
        env.update(extra)
        return env

    def run_script(self, *args: str, **env: str) -> subprocess.CompletedProcess:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            capture_output=True,
            text=True,
            env=self.env(**env),
            cwd=self.root,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        return proc

    def til_note(self, folder: str, name: str, body: str = "본문 첫 문장입니다.\n") -> Path:
        d = self.til / folder
        d.mkdir(exist_ok=True)
        p = d / f"{name}.md"
        p.write_text(f"# {name} 제목\n\n{body}", encoding="utf-8")
        return p

    def write_state(self, notes: dict) -> None:
        self.state_path.write_text(
            json.dumps({"version": 2, "notes": notes}, ensure_ascii=False), encoding="utf-8"
        )

    def read_state(self) -> dict:
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def wiki_note(self, filename: str, body: str, tags: str = "  - python/basics\n  - til\n") -> Path:
        p = self.wiki / f"{filename}.md"
        p.write_text(
            f'---\ntitle: "x"\ntopics:\n  - Python\ntags:\n{tags}created: 2026-01-01\n---\n{body}',
            encoding="utf-8",
        )
        return p

    def wiki_md_names(self) -> set[str]:
        return {_nfc(p.name) for p in self.wiki.glob("*.md")}

    # -- tests -----------------------------------------------------------

    def test_script_skips_without_vaultkit(self) -> None:
        self.write_state({})
        self.til_note("python", "노트A")
        proc = self.run_script(VAULTKIT_PATH=str(self.root / "no-vaultkit"))
        self.assertIn("vaultkit 없음 — 동기화 건너뜀", proc.stdout)
        self.assertEqual(self.wiki_md_names(), set())

    def test_script_refuses_without_state(self) -> None:
        self.til_note("python", "노트A")
        proc = self.run_script()
        self.assertIn("state 없음 — 이관(Task 8) 전에는 --dry-run만 허용", proc.stdout)
        self.assertEqual(self.wiki_md_names(), set())
        self.assertFalse(self.state_path.exists())

    def test_script_refuses_v1_state(self) -> None:
        self.state_path.write_text(json.dumps({"노트A": "abc"}), encoding="utf-8")
        self.til_note("python", "노트A")
        proc = self.run_script()
        self.assertIn("state 없음", proc.stdout)
        self.assertEqual(self.wiki_md_names(), set())
        self.assertEqual(json.loads(self.state_path.read_text(encoding="utf-8")), {"노트A": "abc"})

    def test_dry_run_without_state_judges_only(self) -> None:
        self.til_note("python", "노트A")
        proc = self.run_script("--dry-run")
        self.assertIn("create: 1", proc.stdout)
        self.assertEqual(self.wiki_md_names(), set())
        self.assertFalse(self.state_path.exists())

    def test_script_dry_run_writes_nothing(self) -> None:
        self.write_state({})
        self.til_note("python", "노트A")
        before_state = self.state_path.read_bytes()
        proc = self.run_script("--dry-run", "--verbose")
        self.assertTrue(proc.stdout.startswith("🔄 TIL → Obsidian 동기화 (full, dry-run)"), proc.stdout)
        self.assertIn("create: 1", proc.stdout)
        self.assertIn("노트A", proc.stdout)
        self.assertEqual(self.wiki_md_names(), set())
        self.assertEqual(self.state_path.read_bytes(), before_state)
        self.assertEqual((self.wiki / "_MOC" / "MOC-Python.md").read_text(encoding="utf-8"), MOC_PYTHON)
        self.assertFalse(self.backups.exists())

    def test_create_registers_moc(self) -> None:
        self.write_state({})
        self.til_note("python", "노트A")
        proc = self.run_script()
        self.assertIn("create: 1", proc.stdout)
        self.assertIn("노트A.md", self.wiki_md_names())
        moc = (self.wiki / "_MOC" / "MOC-Python.md").read_text(encoding="utf-8")
        self.assertIn("- [[노트A]] — 본문 첫 문장입니다.", moc)
        entry = self.read_state()["notes"]["노트A"]
        self.assertEqual(entry["status"], "synced")
        text = (self.wiki / "노트A.md").read_text(encoding="utf-8")
        self.assertEqual(entry["body_sha"], body_sha(fm.parse(text).body))

    def test_unclassified_reported(self) -> None:
        self.write_state({})
        self.til_note("zzz-unknown", "노트Z")
        proc = self.run_script()
        self.assertIn("📋 MOC 미분류", proc.stdout)
        self.assertIn("노트Z", proc.stdout.split("📋 MOC 미분류", 1)[1])

    def test_agents_md_excluded(self) -> None:
        self.write_state({})
        self.til_note("python", "노트A")
        (self.til / "python" / "AGENTS.md").write_text("# agents\n", encoding="utf-8")
        (self.til / "AGENTS.md").write_text("# agents\n", encoding="utf-8")
        self.run_script()
        self.assertEqual(self.wiki_md_names(), {"노트A.md"})
        self.assertNotIn("AGENTS", self.read_state()["notes"])

    def test_write_failure_not_recorded(self) -> None:
        old_body = "\n옛 본문.\n"
        locked = self.wiki_note("노트A", old_body)
        self.write_state(
            {"노트A": {"body_sha": body_sha(old_body), "status": "synced"}}
        )
        self.til_note("python", "노트A", "새 본문.\n")
        self.til_note("python", "노트B")
        locked.chmod(stat.S_IRUSR)
        proc = self.run_script()
        self.assertIn("노트A", proc.stdout)
        self.assertIn("실패", proc.stdout)
        notes = self.read_state()["notes"]
        self.assertEqual(notes["노트A"], {"body_sha": body_sha(old_body), "status": "synced"})
        self.assertEqual(notes["노트B"]["status"], "synced")  # 다른 노트는 기록됨

    def test_update_replaces_body_and_keeps_related(self) -> None:
        old_body = "\n옛 본문.\n"
        p = self.wiki_note("노트A", old_body)
        text = p.read_text(encoding="utf-8").replace(
            "tags:", 'related_notes:\n  - "[[Wiki전용]]"\ntags:', 1
        )
        p.write_text(text, encoding="utf-8")
        self.write_state({"노트A": {"body_sha": body_sha(old_body), "status": "synced"}})
        self.til_note("python", "노트A", "새 본문.\n")
        proc = self.run_script("--verbose")
        self.assertIn("update: 1", proc.stdout)
        new = p.read_text(encoding="utf-8")
        self.assertIn("새 본문.", new)
        self.assertIn("[[Wiki전용]]", new)
        self.assertEqual(self.read_state()["notes"]["노트A"]["body_sha"], body_sha("새 본문.\n"))

    def test_update_backs_up_existing_file_first(self) -> None:
        old_body = "\n옛 본문.\n"
        p = self.wiki_note(_nfd("노트A"), old_body)  # 디스크 파일명 NFD
        original = p.read_bytes()
        self.write_state({"노트A": {"body_sha": body_sha(old_body), "status": "synced"}})
        self.til_note("python", "노트A", "새 본문.\n")
        self.til_note("python", "노트B")  # create: 기존 파일 없음 → 백업 대상 아님
        proc = self.run_script()
        dirs = list(self.backups.iterdir())
        self.assertEqual(len(dirs), 1)
        self.assertTrue(dirs[0].name.startswith("til-sync-"), dirs[0].name)
        self.assertIn(str(dirs[0]), proc.stdout)
        backed = list(dirs[0].iterdir())
        self.assertEqual([_nfc(b.name) for b in backed], ["노트A.md"])
        self.assertEqual(backed[0].read_bytes(), original)
        self.assertIn("새 본문.", p.read_text(encoding="utf-8"))
        self.assertEqual(self.wiki_md_names(), {"노트A.md", "노트B.md"})
        self.assertEqual([x.name for x in self.wiki.iterdir() if x.name.endswith(".tmp")], [])

    def test_create_only_makes_no_backup(self) -> None:
        self.write_state({})
        self.til_note("python", "노트A")
        self.run_script()
        self.assertFalse(self.backups.exists())

    def test_readonly_wiki_dir_keeps_original_intact(self) -> None:
        old_body = "\n옛 본문.\n"
        p = self.wiki_note("노트A", old_body)
        original = p.read_bytes()
        state = self.root / "state.json"
        entry = {"body_sha": body_sha(old_body), "status": "synced"}
        state.write_text(json.dumps({"version": 2, "notes": {"노트A": entry}}), encoding="utf-8")
        self.til_note("python", "노트A", "새 본문.\n")
        self.wiki.chmod(stat.S_IRUSR | stat.S_IXUSR)  # 임시 파일을 만들 수 없음
        proc = self.run_script(SYNC_STATE_PATH=str(state))
        self.wiki.chmod(stat.S_IRWXU)
        self.assertIn("쓰기 실패", proc.stdout)
        self.assertEqual(p.read_bytes(), original)
        self.assertEqual([x.name for x in self.wiki.iterdir() if x.name.endswith(".tmp")], [])
        self.assertEqual(json.loads(state.read_text(encoding="utf-8"))["notes"]["노트A"], entry)

    def test_create_refuses_case_only_wiki_match(self) -> None:
        p = self.wiki_note("foo-bar", "\nWiki 전용 본문.\n", tags="  - python/basics\n")
        before = p.read_bytes()
        self.write_state({})
        self.til_note("python", "Foo-Bar")
        proc = self.run_script()
        self.assertIn("conflict: 1", proc.stdout)
        self.assertIn("대소문자", proc.stdout)
        self.assertEqual(p.read_bytes(), before)
        self.assertNotIn("Foo-Bar", self.read_state()["notes"])
        self.assertFalse(self.backups.exists())

    def test_frontmatter_only_reported(self) -> None:
        self.wiki_note("노트A", "\nWiki에서 고친 본문.\n")
        self.write_state({"노트A": {"body_sha": body_sha("\n옛 본문.\n"), "status": "synced"}})
        self.til_note("python", "노트A", "TIL 본문.\n")
        proc = self.run_script()
        self.assertIn("⚠️ 이관 필요(Wiki 본문 수정됨)", proc.stdout)
        self.assertIn("노트A", proc.stdout.split("이관 필요", 1)[1])
        self.assertIn("Wiki에서 고친 본문.", (self.wiki / "노트A.md").read_text(encoding="utf-8"))
        self.assertEqual(self.read_state()["notes"]["노트A"]["body_sha"], body_sha("\n옛 본문.\n"))

    def test_nfd_wiki_file_found_not_retired(self) -> None:
        stem = "한글노트"
        old_body = "\n옛 본문.\n"
        self.wiki_note(_nfd(stem), old_body)
        self.write_state({stem: {"body_sha": body_sha(old_body), "status": "synced"}})
        self.til_note("python", stem, "새 본문.\n")
        proc = self.run_script()
        self.assertIn("update: 1", proc.stdout)
        self.assertNotIn("retire: 1", proc.stdout)
        self.assertNotIn("create: 1", proc.stdout)
        files = list(self.wiki.glob("*.md"))
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].name, f"{_nfd(stem)}.md")  # 기존 파일에 썼다
        self.assertIn("새 본문.", files[0].read_text(encoding="utf-8"))
        self.assertEqual(self.read_state()["notes"][stem]["status"], "synced")

    def test_retire_when_wiki_deleted(self) -> None:
        self.write_state({"노트A": {"body_sha": "x", "status": "synced"}})
        self.til_note("python", "노트A")
        proc = self.run_script()
        self.assertIn("retire: 1", proc.stdout)
        self.assertEqual(self.wiki_md_names(), set())
        self.assertEqual(self.read_state()["notes"]["노트A"], {"status": "retired"})
        # 다음 실행에서도 되살아나지 않는다
        proc = self.run_script()
        self.assertIn("skip-retired: 1", proc.stdout)
        self.assertEqual(self.wiki_md_names(), set())

    def test_duplicate_stem_conflict(self) -> None:
        self.write_state({})
        self.til_note("python", "같은이름")
        self.til_note("java", "같은이름")
        proc = self.run_script()
        self.assertIn("conflict: 1", proc.stdout)
        self.assertIn("같은이름", proc.stdout.split("⚠️ 충돌", 1)[1])
        self.assertEqual(self.wiki_md_names(), set())
        self.assertNotIn("같은이름", self.read_state()["notes"])

    def test_til_deleted_reported_without_state_change(self) -> None:
        self.wiki_note("사라진노트", "\n본문.\n")
        notes = {"사라진노트": {"body_sha": body_sha("\n본문.\n"), "status": "synced"}}
        self.write_state(notes)
        proc = self.run_script()
        self.assertIn("TIL에서 삭제됨", proc.stdout)
        self.assertIn("사라진노트", proc.stdout)
        self.assertEqual(self.read_state()["notes"], notes)
        self.assertEqual(self.wiki_md_names(), {"사라진노트.md"})

    def test_wiki_only_note_untouched(self) -> None:
        p = self.wiki_note("Wiki전용", "\n본문.\n")
        before = p.read_bytes()
        self.write_state({})
        self.run_script()
        self.assertEqual(p.read_bytes(), before)
        self.assertEqual(self.read_state()["notes"], {})

    def test_state_path_env_override(self) -> None:
        other = self.root / "state-elsewhere.json"
        other.write_text(json.dumps({"version": 2, "notes": {}}), encoding="utf-8")
        self.til_note("python", "노트A")
        self.run_script(SYNC_STATE_PATH=str(other))
        self.assertFalse(self.state_path.exists())
        self.assertIn("노트A", json.loads(other.read_text(encoding="utf-8"))["notes"])

    @unittest.skipUnless(shutil.which("git"), "git 없음")
    def test_diff_mode_only_head_changes(self) -> None:
        self.write_state({})
        self.til_note("python", "노트A")
        self.til_note("python", "노트C")  # 커밋 a에만 있고 b에서는 안 바뀜, state에도 없음
        git = ["git", "-C", str(self.til), "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.hooksPath=/dev/null"]
        subprocess.run(["git", "init", "-q", str(self.til)], check=True)
        subprocess.run([*git, "add", "-A"], check=True)
        subprocess.run([*git, "commit", "-qm", "a"], check=True)
        self.til_note("python", "노트B")
        (self.til / "AGENTS.md").write_text("# agents\n", encoding="utf-8")
        (self.til / "python" / "노트A.md").unlink()
        subprocess.run([*git, "add", "-A"], check=True)
        subprocess.run([*git, "commit", "-qm", "b"], check=True)
        proc = self.run_script("--diff")
        self.assertTrue(proc.stdout.startswith("🔄 TIL → Obsidian 동기화 (diff)"), proc.stdout)
        self.assertEqual(self.wiki_md_names(), {"노트B.md"})  # 노트C는 diff 대상 아님
        self.assertNotIn("노트C", self.read_state()["notes"])
        # 대조: 같은 조건에서 full 모드는 노트C를 만든다
        proc = self.run_script()
        self.assertTrue(proc.stdout.startswith("🔄 TIL → Obsidian 동기화 (full)"), proc.stdout)
        self.assertEqual(self.wiki_md_names(), {"노트B.md", "노트C.md"})

    def test_failed_frontmatter_only_reported_only_as_failure(self) -> None:
        locked = self.wiki_note("노트A", "\nWiki에서 고친 본문.\n")
        entry = {"body_sha": body_sha("\n옛 본문.\n"), "status": "synced"}
        self.write_state({"노트A": entry})
        self.til_note("python", "노트A", "TIL 본문.\n")
        locked.chmod(stat.S_IRUSR)
        proc = self.run_script()
        self.assertIn("❌ 실패", proc.stdout)
        self.assertNotIn("이관 필요", proc.stdout)
        self.assertIn("frontmatter-only: 0", proc.stdout)
        self.assertEqual(self.read_state()["notes"]["노트A"], entry)

    def test_vaultkit_import_error_other_than_importerror(self) -> None:
        broken = self.root / "broken-vaultkit"
        (broken / "vaultkit").mkdir(parents=True)
        (broken / "vaultkit" / "__init__.py").write_text("raise RuntimeError('boom')\n", encoding="utf-8")
        self.write_state({})
        self.til_note("python", "노트A")
        proc = self.run_script(VAULTKIT_PATH=str(broken))
        self.assertIn("vaultkit 없음 — 동기화 건너뜀", proc.stdout)
        self.assertIn("RuntimeError: boom", proc.stdout)
        self.assertEqual(self.wiki_md_names(), set())


if __name__ == "__main__":
    unittest.main()
