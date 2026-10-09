"""TIL 노트 이름 변경 이관 스크립트(``vault/scripts/til_rename.py``) 테스트.

순수 함수는 모듈을 직접 불러와 검사하고, CLI는 subprocess로 실행하면서
``TIL_PATH``/``OBSIDIAN_PATH``/``SYNC_STATE_PATH``로 임시 TIL·vault만 가리킨다.
spec: ~/.dotfiles/docs/superpowers/specs/2026-10-09-til-title-prefix-design.md
"""

from __future__ import annotations

import hashlib
import importlib.util
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
from vaultkit import load_policy, tilsync

RENAME = VAULT_DIR / "scripts" / "til_rename.py"
SYNC_SCRIPT = Path(
    os.environ.get("TIL_SYNC_SCRIPT", Path.home() / "dev/TIL/.githooks/sync-to-obsidian.py")
)
_SYNC_OK = SYNC_SCRIPT.exists() and 'os.environ.get("OBSIDIAN_PATH")' in SYNC_SCRIPT.read_text(
    encoding="utf-8"
)

_spec = importlib.util.spec_from_file_location("til_rename", RENAME)
assert _spec is not None and _spec.loader is not None
tr = importlib.util.module_from_spec(_spec)
sys.modules["til_rename"] = tr
_spec.loader.exec_module(tr)


def _nfd(s: str) -> str:
    return unicodedata.normalize("NFD", s)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _mapping(path: Path, rows: list[dict]) -> Path:
    path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    return path


class NameTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.til = self.root / "TIL"
        self.vault = self.root / "Note"
        (self.vault / "Wiki").mkdir(parents=True)
        _write(self.til / "db" / "커버링-인덱스.md", "# 커버링 인덱스\n\n본문\n")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_to_stem_spec_examples(self) -> None:
        cases = {
            "Redis XFetch — 왜 락 없이도 캐시 스탬피드를 막을까": "Redis-XFetch-왜-락-없이도-캐시-스탬피드를-막을까",
            "Helm — 내 첫 Helm Chart, `helm create`부터 `helm install`까지": "Helm-내-첫-Helm-Chart-helm-create부터-helm-install까지",
            "DAU/MAU — 왜 서비스 회사는 그 정의에 그토록 집착할까?": "DAU-MAU-왜-서비스-회사는-그-정의에-그토록-집착할까",
            "OAuth 2.1 — 브라우저는": "OAuth-2.1-브라우저는",
            "Index Break-Even Point — 옵티마이저": "Index-Break-Even-Point-옵티마이저",
            "A 'b' \"c\" -- d": "A-b-c-d",
        }
        for h1, stem in cases.items():
            with self.subTest(h1=h1):
                self.assertEqual(tr.to_stem(h1), stem)

    def test_load_renames_reads_old_h1(self) -> None:
        m = _mapping(
            self.root / "m.json",
            [{"folder": "db", "old": "커버링-인덱스", "h1": "Covering Index — 커버링 인덱스"}],
        )
        self.assertEqual(
            tr.load_renames(m, self.til),
            [
                tr.Rename(
                    folder="db",
                    old="커버링-인덱스",
                    new="Covering-Index-커버링-인덱스",
                    old_h1="커버링 인덱스",
                    new_h1="Covering Index — 커버링 인덱스",
                )
            ],
        )

    def test_load_renames_rejects_missing_old(self) -> None:
        m = _mapping(self.root / "m.json", [{"folder": "db", "old": "없는-노트", "h1": "X — 없음"}])
        with self.assertRaises(tr.UsageError):
            tr.load_renames(m, self.til)

    def test_load_renames_rejects_duplicate_new(self) -> None:
        _write(self.til / "db" / "복합.md", "# 복합\n")
        m = _mapping(
            self.root / "m.json",
            [
                {"folder": "db", "old": "커버링-인덱스", "h1": "Index — 같음"},
                {"folder": "db", "old": "복합", "h1": "index — 같음"},
            ],
        )
        with self.assertRaises(tr.UsageError):
            tr.load_renames(m, self.til)

    def test_load_renames_rejects_stem_outside_tilsync_pattern(self) -> None:
        m = _mapping(self.root / "m.json", [{"folder": "db", "old": "커버링-인덱스", "h1": "A — 비%율"}])
        with self.assertRaises(tr.UsageError):
            tr.load_renames(m, self.til)

    def test_load_renames_matches_nfd_filename(self) -> None:
        _write(self.til / "sec" / _nfd("키-유도-함수.md"), "# 키 유도 함수\n")
        m = _mapping(self.root / "m.json", [{"folder": "sec", "old": "키-유도-함수", "h1": "KDF — 키 유도 함수"}])
        [r] = tr.load_renames(m, self.til)
        self.assertEqual((r.old, r.new, r.old_h1), ("키-유도-함수", "KDF-키-유도-함수", "키 유도 함수"))

    def test_check_collisions(self) -> None:
        m = _mapping(
            self.root / "m.json",
            [{"folder": "db", "old": "커버링-인덱스", "h1": "Covering Index — 커버링 인덱스"}],
        )
        renames = tr.load_renames(m, self.til)
        self.assertEqual(tr.check_collisions(renames, self.til, self.vault), [])
        _write(self.vault / "Sources" / "covering-index-커버링-인덱스.md", "x\n")
        self.assertEqual(len(tr.check_collisions(renames, self.til, self.vault)), 1)


COVER = tr.Rename(
    folder="db",
    old="커버링-인덱스",
    new="Covering-Index-커버링-인덱스",
    old_h1="커버링 인덱스",
    new_h1="Covering Index — 커버링 인덱스",
)


class TilRewriteTest(unittest.TestCase):
    def test_replace_h1_only_first(self) -> None:
        self.assertEqual(
            tr.replace_h1("# 옛\n\n## 절\n# 코드 아님\n", "새 — 부제"),
            "# 새 — 부제\n\n## 절\n# 코드 아님\n",
        )
        self.assertEqual(
            tr.replace_h1("---\ntitle: x\n---\n# 옛\n본문\n", "새 — 부제"),
            "---\ntitle: x\n---\n# 새 — 부제\n본문\n",
        )
        with self.assertRaises(tr.UsageError):
            tr.replace_h1("본문만\n", "새")

    def test_rewrite_link_forms(self) -> None:
        text = "[a](./커버링-인덱스.md) [b](../db/커버링-인덱스.md#절) [c](커버링-인덱스.md)\n"
        new, count, _ = tr.rewrite_til_links(text, [COVER])
        self.assertEqual(
            new,
            "[a](./Covering-Index-커버링-인덱스.md) [b](../db/Covering-Index-커버링-인덱스.md#절) "
            "[c](Covering-Index-커버링-인덱스.md)\n",
        )
        self.assertEqual(count, 3)

    def test_label_equal_to_old_h1_becomes_new_h1(self) -> None:
        new, _, unmatched = tr.rewrite_til_links("[커버링 인덱스](./커버링-인덱스.md)", [COVER])
        self.assertEqual(new, "[Covering Index — 커버링 인덱스](./Covering-Index-커버링-인덱스.md)")
        self.assertEqual(unmatched, [])

    def test_label_equal_to_old_stem_becomes_new_stem(self) -> None:
        new, _, unmatched = tr.rewrite_til_links("[커버링-인덱스](./커버링-인덱스.md)", [COVER])
        self.assertEqual(new, "[Covering-Index-커버링-인덱스](./Covering-Index-커버링-인덱스.md)")
        self.assertEqual(unmatched, [])

    def test_label_mismatch_reported(self) -> None:
        new, count, unmatched = tr.rewrite_til_links("[커버링](./커버링-인덱스.md)", [COVER])
        self.assertEqual(new, "[커버링](./Covering-Index-커버링-인덱스.md)")
        self.assertEqual(count, 1)
        self.assertEqual(unmatched, ["커버링-인덱스: 커버링"])

    def test_code_untouched(self) -> None:
        text = "```\n[x](./커버링-인덱스.md)\n```\n`[y](./커버링-인덱스.md)`\n"
        new, count, _ = tr.rewrite_til_links(text, [COVER])
        self.assertEqual((new, count), (text, 0))

    def test_prefix_extended_stem_untouched(self) -> None:
        text = "[y](./커버링-인덱스-심화.md)\n"
        new, count, _ = tr.rewrite_til_links(text, [COVER])
        self.assertEqual((new, count), (text, 0))


class VaultRewriteTest(unittest.TestCase):
    def test_wikilink_forms(self) -> None:
        text = (
            "[[커버링-인덱스]] ![[커버링-인덱스]] [[커버링-인덱스|별칭]]\n"
            "| a | [[커버링-인덱스\\|표]] |\n"
            "[[커버링-인덱스#절]] [[커버링-인덱스#절|둘]]\n"
        )
        new, count = tr.rewrite_wikilinks(text, [COVER])
        n = COVER.new
        self.assertEqual(
            new,
            f"[[{n}]] ![[{n}]] [[{n}|별칭]]\n| a | [[{n}\\|표]] |\n[[{n}#절]] [[{n}#절|둘]]\n",
        )
        self.assertEqual(count, 6)

    def test_wikilink_prefix_extended_untouched(self) -> None:
        text = "[[커버링-인덱스-심화]] [[커버링-인덱스-심화|x]]\n"
        self.assertEqual(tr.rewrite_wikilinks(text, [COVER]), (text, 0))

    def test_wikilink_nfd_target(self) -> None:
        new, count = tr.rewrite_wikilinks(_nfd("[[커버링-인덱스]]"), [COVER])
        self.assertEqual((new, count), (f"[[{COVER.new}]]", 1))

    def test_frontmatter_only(self) -> None:
        text = '---\nrelated_notes: ["[[커버링-인덱스]]"]\n---\n본문 [[커버링-인덱스]]\n'
        new, count = tr.rewrite_frontmatter_links(text, [COVER])
        self.assertEqual(new, f'---\nrelated_notes: ["[[{COVER.new}]]"]\n---\n본문 [[커버링-인덱스]]\n')
        self.assertEqual(count, 1)
        self.assertEqual(tr.rewrite_frontmatter_links("본문 [[커버링-인덱스]]\n", [COVER]), ("본문 [[커버링-인덱스]]\n", 0))

    def test_vault_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            wiki = vault / "Wiki"
            text = "---\ntitle: 커버링 인덱스\n---\n\n본문\n"
            _write(wiki / "커버링-인덱스.md", text)
            sha = tilsync.body_sha(fm.parse(text).body)
            state = {"version": 2, "notes": {"커버링-인덱스": {"status": "synced", "body_sha": sha}}}
            self.assertEqual(tr.vault_scope(wiki / "커버링-인덱스.md", wiki, state), "frontmatter")
            _write(wiki / "커버링-인덱스.md", text + "Wiki에서 추가한 문단\n")
            self.assertEqual(tr.vault_scope(wiki / "커버링-인덱스.md", wiki, state), "full")
            _write(vault / "_Inbox" / "x.md", "[[커버링-인덱스]]\n")
            self.assertEqual(tr.vault_scope(vault / "_Inbox" / "x.md", wiki, state), "full")
            _write(wiki / "Wiki-전용.md", "---\ntitle: w\n---\n본문\n")
            self.assertEqual(tr.vault_scope(wiki / "Wiki-전용.md", wiki, state), "full")


class KeysTest(unittest.TestCase):
    def test_move_keys_preserves_order_and_values(self) -> None:
        moved = tr.move_keys({"a": 1, "커버링-인덱스": [2], "z": 3}, [COVER])
        self.assertEqual(list(moved.items()), [("a", 1), (COVER.new, [2]), ("z", 3)])

    def test_move_keys_retired_status_kept(self) -> None:
        moved = tr.move_keys({"커버링-인덱스": {"status": "retired"}}, [COVER])
        self.assertEqual(moved, {COVER.new: {"status": "retired"}})

    def test_move_keys_nfd_key(self) -> None:
        moved = tr.move_keys({_nfd("커버링-인덱스"): 1, _nfd("다른-노트"): 2}, [COVER])
        self.assertEqual(list(moved), [COVER.new, _nfd("다른-노트")])

    def test_move_keys_missing_old_is_noop(self) -> None:
        self.assertEqual(tr.move_keys({"a": 1}, [COVER]), {"a": 1})


AGENT_OLD = "효과적인-에이전트-구축하기"
TIL_COVER = "# 커버링 인덱스\n\n커버링 본문.\n"
TIL_COMPOSITE = "# 복합\n\n[커버링 인덱스](./커버링-인덱스.md)와 [커버링](커버링-인덱스.md) 참고.\n"
TIL_AGENT = "# 효과적인 에이전트 구축하기\n\n에이전트 본문.\n"
INBOX = "# 인덱스\n\n- [[커버링-인덱스]]\n"


def _tree(root: Path, skip: Path | None = None) -> set[tuple[str, str]]:
    """root 아래 모든 파일의 (상대경로 NFC, sha256)."""
    out = set()
    for p in root.rglob("*"):
        if p.is_file() and not (skip and skip in p.parents):
            out.add((unicodedata.normalize("NFC", str(p.relative_to(root))), hashlib.sha256(p.read_bytes()).hexdigest()))
    return out


class FixtureMixin:
    """임시 TIL·vault: 이름 변경 대상 2편(커버링 synced, 에이전트 retired)과 참조 노트."""

    def make_fixture(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.til = self.root / "TIL"
        self.vault = self.root / "Note"
        self.wiki = self.vault / "Wiki"
        self.out = self.root / "out"
        self.state_path = self.wiki / ".til-sync-state.json"
        self.wiki.mkdir(parents=True)

        _write(self.til / "db" / "커버링-인덱스.md", TIL_COVER)
        _write(self.til / "db" / "복합.md", TIL_COMPOSITE)
        _write(self.til / "agent" / f"{AGENT_OLD}.md", TIL_AGENT)
        mapping = {"커버링-인덱스": ["database/index"], "복합": ["database/index"], AGENT_OLD: ["ai/agent"]}
        _write(self.til / "tag-mapping.json", json.dumps(mapping, ensure_ascii=False, indent=2) + "\n")

        raw = json.loads((VAULT_DIR / "vault-policy.json").read_text(encoding="utf-8"))
        raw["paths"]["vault_root"] = str(self.vault)
        raw["paths"]["til_root"] = str(self.til)
        self.policy_path = self.root / "policy.json"
        self.policy_path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
        policy = load_policy(self.policy_path)

        notes = {}
        for folder, stem in (("db", "커버링-인덱스"), ("db", "복합")):
            gen = tilsync.build_note(self.til / folder / f"{stem}.md", folder, policy, mapping)
            decision = tilsync.merge(gen, None, None, "2026-10-09", policy)
            text = decision.text
            if stem == "커버링-인덱스":  # Wiki에서 단 related_notes(Wiki 소유 필드)
                doc = fm.parse(text)
                fm.set_list(doc, "related_notes", ["[[복합]]"])
                text = fm.render(doc)
            _write(self.wiki / f"{stem}.md", text)
            notes[stem] = decision.entry
        notes[AGENT_OLD] = {"status": "retired"}
        tilsync.save_state(self.state_path, {"version": 2, "notes": notes})
        _write(self.vault / "_Inbox" / "Vault-Index.md", INBOX)

        self.mapping = _mapping(
            self.root / "mapping.json",
            [
                {"folder": "db", "old": "커버링-인덱스", "h1": "Covering Index — 커버링 인덱스"},
                {"folder": "agent", "old": AGENT_OLD, "h1": "AI Agent — 효과적인 에이전트 구축하기"},
            ],
        )

    def env(self, **extra) -> dict:
        env = dict(os.environ)
        env.update(
            TIL_PATH=str(self.til),
            OBSIDIAN_PATH=str(self.wiki),
            SYNC_STATE_PATH=str(self.state_path),
            VAULTKIT_PATH=str(VAULT_DIR),
            VAULTKIT_POLICY=str(self.policy_path),
            VAULTKIT_BACKUP_DIR=str(self.root / "backups"),
        )
        for key, value in extra.items():
            if value is None:
                env.pop(key, None)
            else:
                env[key] = value
        return env

    def call(self, *args: str, expect: int = 0, script: Path = RENAME, **env) -> subprocess.CompletedProcess:
        proc = subprocess.run(
            [sys.executable, str(script), *args],
            capture_output=True,
            text=True,
            env=self.env(**env),
            cwd=self.root,
        )
        self.assertEqual(proc.returncode, expect, proc.stdout + proc.stderr)  # type: ignore[attr-defined]
        return proc

    def plan(self) -> dict:
        self.call("--plan", "--mapping", str(self.mapping), "--out", str(self.out))
        return json.loads((self.out / "plan.json").read_text(encoding="utf-8"))


class PlanCliTest(FixtureMixin, unittest.TestCase):
    def setUp(self) -> None:
        self.make_fixture()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_plan_counts(self) -> None:
        self.assertEqual(
            self.plan()["counts"],
            {
                "renames": 2,
                "til_links": 2,
                "til_link_files": 1,
                "vault_links": 2,
                "vault_body_left": 2,
                "tag_keys": 2,
                "wiki_renames": 1,
            },
        )

    def test_plan_reports_unmatched_label(self) -> None:
        self.assertEqual(self.plan()["til_unmatched"], ["db/복합.md: 커버링-인덱스: 커버링"])
        self.assertIn("db/복합.md: 커버링-인덱스: 커버링", (self.out / "summary.md").read_text(encoding="utf-8"))

    def test_plan_is_read_only(self) -> None:
        before = _tree(self.root)
        self.plan()
        self.assertEqual(_tree(self.root, skip=self.out), before)

    def test_plan_refuses_out_inside_til_or_vault(self) -> None:
        for out in (self.til / "out", self.wiki / "out", self.vault / "_Inbox" / "out"):
            with self.subTest(out=out):
                self.call("--plan", "--mapping", str(self.mapping), "--out", str(out), expect=2)


NEW_COVER = "Covering-Index-커버링-인덱스"
NEW_AGENT = "AI-Agent-효과적인-에이전트-구축하기"


def _sync_counts(proc: subprocess.CompletedProcess) -> dict:
    counts = {}
    for line in proc.stdout.splitlines():
        key, sep, value = line.strip().partition(": ")
        if sep and value.isdigit():
            counts[key] = int(value)
    return counts


class ApplyCliTest(FixtureMixin, unittest.TestCase):
    def setUp(self) -> None:
        self.make_fixture()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def apply(self, expect: int = 0) -> subprocess.CompletedProcess:
        return self.call("--apply", "--mapping", str(self.mapping), "--out", str(self.out), expect=expect)

    def test_apply_requires_env_and_real_flag(self) -> None:
        # plan 없는 out을 써서, 가드가 틀려도 실제 데이터에는 쓰지 않고 exit 1로 끝나게 한다
        empty = self.root / "empty-out"
        args = ("--apply", "--mapping", str(self.mapping), "--out", str(empty))
        for env in (
            {"TIL_PATH": None},
            {"OBSIDIAN_PATH": None},
            {"TIL_PATH": str(tr.REAL_TIL)},
            {"OBSIDIAN_PATH": str(tr.REAL_WIKI), "SYNC_STATE_PATH": None},
        ):
            with self.subTest(env=env):
                proc = self.call(*args, expect=2, **env)
                self.assertIn("--real", proc.stderr)

    def test_apply_refuses_without_or_stale_plan(self) -> None:
        self.apply(expect=1)
        self.plan()
        self.mapping.write_text(self.mapping.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        self.apply(expect=1)
        self.assertTrue((self.til / "db" / "커버링-인덱스.md").exists())

    def test_apply_til_side(self) -> None:
        self.plan()
        self.apply()
        new = self.til / "db" / f"{NEW_COVER}.md"
        self.assertEqual(new.read_text(encoding="utf-8").splitlines()[0], "# Covering Index — 커버링 인덱스")
        self.assertFalse((self.til / "db" / "커버링-인덱스.md").exists())
        self.assertEqual(
            (self.til / "db" / "복합.md").read_text(encoding="utf-8"),
            f"# 복합\n\n[Covering Index — 커버링 인덱스](./{NEW_COVER}.md)와 [커버링]({NEW_COVER}.md) 참고.\n",
        )
        mapping = json.loads((self.til / "tag-mapping.json").read_text(encoding="utf-8"))
        self.assertEqual(list(mapping), [NEW_COVER, "복합", NEW_AGENT])

    def test_apply_vault_side(self) -> None:
        self.plan()
        self.apply()
        self.assertTrue((self.wiki / f"{NEW_COVER}.md").exists())
        self.assertFalse((self.wiki / "커버링-인덱스.md").exists())
        self.assertFalse((self.wiki / f"{NEW_AGENT}.md").exists())
        notes = tilsync.load_state(self.state_path)["notes"]
        self.assertEqual(notes[NEW_COVER]["status"], "synced")
        self.assertEqual(notes[NEW_AGENT], {"status": "retired"})
        self.assertNotIn("커버링-인덱스", notes)
        self.assertNotIn(AGENT_OLD, notes)
        head, body = tr._split_frontmatter((self.wiki / "복합.md").read_text(encoding="utf-8"))
        self.assertIn(f"[[{NEW_COVER}]]", head)
        self.assertNotIn("[[커버링-인덱스]]", head)
        self.assertIn("[[커버링-인덱스|커버링 인덱스]]", body)
        self.assertEqual((self.vault / "_Inbox" / "Vault-Index.md").read_text(encoding="utf-8"), f"# 인덱스\n\n- [[{NEW_COVER}]]\n")

    @unittest.skipUnless(_SYNC_OK, "TIL sync script(환경변수 지원판) 없음")
    def test_apply_then_sync_converges(self) -> None:
        self.plan()
        self.apply()
        dry = _sync_counts(self.call("--dry-run", script=SYNC_SCRIPT))
        self.assertEqual((dry.get("create"), dry.get("conflict"), dry.get("frontmatter-only")), (0, 0, 0), dry)
        self.call(script=SYNC_SCRIPT)
        self.assertIn(f"[[{NEW_COVER}|", (self.wiki / "복합.md").read_text(encoding="utf-8"))
        self.assertFalse((self.wiki / f"{NEW_AGENT}.md").exists())
        again = _sync_counts(self.call("--dry-run", script=SYNC_SCRIPT))
        self.assertEqual(again.get("update"), 0, again)

    def test_apply_nfd_wiki_filename(self) -> None:
        (self.wiki / "커버링-인덱스.md").rename(self.wiki / _nfd("커버링-인덱스.md"))
        self.plan()
        self.apply()
        self.assertEqual([unicodedata.normalize("NFC", p.stem) for p in self.wiki.glob("Covering*.md")], [NEW_COVER])
        self.assertFalse(any(unicodedata.normalize("NFC", p.stem) == "커버링-인덱스" for p in self.wiki.glob("*.md")))
        self.assertIn(NEW_COVER, tilsync.load_state(self.state_path)["notes"])

    def test_apply_never_deletes(self) -> None:
        before = len(_tree(self.root))
        self.plan()
        after_plan = len(_tree(self.root, skip=self.out))
        self.apply()
        self.assertEqual(after_plan, before)
        self.assertEqual(len(_tree(self.root, skip=self.out)), before)


class VerifyRestoreTest(FixtureMixin, unittest.TestCase):
    def setUp(self) -> None:
        self.make_fixture()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def apply(self) -> None:
        self.plan()
        self.call("--apply", "--mapping", str(self.mapping), "--out", str(self.out))

    def verify(self, *extra: str, expect: int) -> subprocess.CompletedProcess:
        return self.call("--verify", "--mapping", str(self.mapping), "--out", str(self.out), *extra, expect=expect)

    def test_verify_passes_after_apply(self) -> None:
        self.apply()
        proc = self.verify(expect=0)
        self.assertNotIn("FAIL", proc.stdout)
        self.assertEqual(sum(line.startswith("PASS") for line in proc.stdout.splitlines()), 5, proc.stdout)

    def test_verify_fails_on_leftover(self) -> None:
        self.apply()
        inbox = self.vault / "_Inbox" / "Vault-Index.md"
        inbox.write_text(inbox.read_text(encoding="utf-8") + "- [[커버링-인덱스]]\n", encoding="utf-8")
        proc = self.verify(expect=1)
        self.assertIn("FAIL 5", proc.stdout)

    def test_verify_fails_before_apply(self) -> None:
        self.plan()
        proc = self.verify(expect=1)
        self.assertIn("FAIL 1", proc.stdout)

    @unittest.skipUnless(_SYNC_OK, "TIL sync script(환경변수 지원판) 없음")
    def test_verify_strict_after_sync(self) -> None:
        self.apply()
        self.verify("--strict", expect=1)
        self.verify(expect=0)
        self.call(script=SYNC_SCRIPT)
        self.verify("--strict", expect=0)

    def test_restore_roundtrip(self) -> None:
        before = _tree(self.root)
        self.apply()
        self.assertNotEqual(_tree(self.root, skip=self.out), before)
        self.call("--restore", "--out", str(self.out))
        self.assertEqual(_tree(self.root, skip=self.out), before)

    def test_restore_requires_env_and_real_flag(self) -> None:
        proc = self.call("--restore", "--out", str(self.root / "empty-out"), expect=2, TIL_PATH=None)
        self.assertIn("--real", proc.stderr)


class ReuseOutTest(FixtureMixin, unittest.TestCase):
    """한 번 apply한 --out은 다시 plan·apply하지 않는다(백업·작업 기록 보존, 리뷰 Critical 1)."""

    def setUp(self) -> None:
        self.make_fixture()

    def tearDown(self) -> None:
        (self.vault / "_Inbox").chmod(0o755)
        self._tmp.cleanup()

    def apply(self, expect: int = 0) -> subprocess.CompletedProcess:
        return self.call("--apply", "--mapping", str(self.mapping), "--out", str(self.out), expect=expect)

    def test_reused_out_refused_after_apply(self) -> None:
        self.plan()
        self.apply()
        journal = (self.out / "journal.json").read_bytes()
        proc = self.call("--plan", "--mapping", str(self.mapping), "--out", str(self.out), expect=2)
        self.assertIn("--restore", proc.stderr)
        self.apply(expect=2)
        self.assertEqual((self.out / "journal.json").read_bytes(), journal)

    def test_partial_failure_then_restore(self) -> None:
        before = _tree(self.root)
        self.plan()
        (self.vault / "_Inbox").chmod(0o555)  # vault 쓰기 도중 실패
        proc = self.apply(expect=1)
        self.assertIn("--restore", proc.stderr)
        self.call("--plan", "--mapping", str(self.mapping), "--out", str(self.out), expect=2)
        self.apply(expect=2)
        (self.vault / "_Inbox").chmod(0o755)
        self.call("--restore", "--out", str(self.out))
        self.assertEqual(_tree(self.root, skip=self.out), before)

    def test_apply_writes_git_paths(self) -> None:
        self.plan()
        self.apply()
        lines = (self.out / "git-paths.txt").read_text(encoding="utf-8").splitlines()
        self.assertEqual(
            lines,
            sorted(
                [
                    "agent/효과적인-에이전트-구축하기.md",
                    f"agent/{NEW_AGENT}.md",
                    "db/복합.md",
                    "db/커버링-인덱스.md",
                    f"db/{NEW_COVER}.md",
                    "tag-mapping.json",
                ]
            ),
        )


if __name__ == "__main__":
    unittest.main()
