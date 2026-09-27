"""vaultkit.check / vaultkit.apply 테스트.

kind별 위반을 하나씩 심은 미니 vault를 tempfile로 만들어 검증한다.
실제 vault·TIL은 전혀 건드리지 않는다(백업 위치도 ``VAULTKIT_BACKUP_DIR``을
테스트 임시 폴더로 바꿔 격리한다 — 기본값 ``~/.local/state``에 쓰지 않도록).
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from vaultkit import cli
from vaultkit.apply import ApplyRefused, backup_root, run_apply
from vaultkit.check import KINDS, Finding, Report, run_check
from vaultkit.policy import Policy

RULE_DOC = "vault/references/note-rules.md"


def _make_policy(root: Path, *, skill_roots: list[Path] | None = None) -> Policy:
    return Policy(
        domains=frozenset({"kubernetes", "python", "ai"}),
        facets=frozenset({"work", "customer", "feature"}),
        single_allowed=frozenset({"til", "moc"}),
        rename={"k8s/old": "kubernetes/basics"},
        drop=frozenset({"junk"}),
        conditional=[],
        drop_outside_projects=frozenset({"work/", "customer/"}),
        frontmatter={
            "Wiki": {
                "order": ["title", "source", "topics", "related_notes", "tags", "created"],
                "required": ["title", "tags"],
            },
            "Projects": {"order": ["source", "related_notes", "tags", "created"], "required": ["tags"]},
            "Sources": {"order": ["title", "source", "related_notes", "tags", "created"], "required": ["tags"]},
            "Archive": {"order": ["source", "related_notes", "tags", "created"], "required": []},
        },
        topics={"ai": "AI", "devops": "DevOps", "computer-science": "Computer Science"},
        til_folder_domain={},
        moc={"kubernetes/*": ["MOC-Kubernetes", "핵심 리소스"]},
        hubs={"Projects/GenonAI/GenOS": {"hub": "00 GenOS 시작하기", "section_by_subfolder": True}},
        genos_subfolders={},
        vault_root=root / "vault",
        til_root=root / "TIL",
        skill_roots=skill_roots if skill_roots is not None else [],
    )


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def _note(title: str, tags: list[str], body: str = "요약 문장이다.\n", extra: str = "") -> str:
    tag_lines = "".join(f"  - {t}\n" for t in tags)
    return f'---\ntitle: "{title}"\n{extra}tags:\n{tag_lines}---\n{body}'


def _snapshot(root: Path) -> dict[str, bytes]:
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


class _TempVaultCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.vault = self.root / "vault"
        self.vault.mkdir()
        (self.root / "TIL").mkdir()
        self.backups = self.root / "backups"
        env = mock.patch.dict(
            os.environ, {"TMPDIR": str(self.root / "tmp"), "VAULTKIT_BACKUP_DIR": str(self.backups)}
        )
        env.start()
        self.addCleanup(env.stop)
        (self.root / "tmp").mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()


class CheckTest(_TempVaultCase):
    def _build_check_vault(self) -> Policy:
        v = self.vault
        _write(
            v / "Wiki/_MOC/MOC-Kubernetes.md",
            "# K8s\n\nWiki의 노트 3개를 묶은 목차다.\n\n## 핵심 리소스\n\n"
            "- [[Good-Wiki]] — 좋은 노트\n- [[Dup-Note]] — 중복\n- [[My-Til]] — til\n",
        )
        _write(
            v / "Wiki/_MOC/MOC-Python.md",
            "# Py\n\nWiki의 노트 5개를 묶은 목차다.\n\n## 기본\n\n- [[Dup-Note]] — 중복\n",
        )
        _write(v / "Wiki/Good-Wiki.md", _note("Good", ["kubernetes/basics"]))
        _write(v / "Wiki/Dup-Note.md", _note("Dup", ["kubernetes/basics"]))
        _write(v / "Wiki/Bad-Tag.md", _note("Bad", ["python/a/b"]))
        _write(v / "Wiki/Bad-Order.md", '---\ntags:\n  - python/x\ntitle: "x"\n---\n본문.\n')
        _write(v / "Wiki/Bad-Topic.md", _note("T", ["python/x"], extra="topics:\n  - Ai\n"))
        _write(v / "Wiki/Broken.md", "---\ntitle: x\ntags:\n  - python/x\n본문만 있고 닫힘 없음\n")
        _write(v / "Templates/Tpl.md", "---\ncreated: {{date}}\n")
        _write(v / "Wiki/Unregistered.md", _note("U", ["kubernetes/basics"]))
        _write(v / "Wiki/Linker.md", _note("L", ["python/x"], body="[[Nowhere]] 와 [[Good-Wiki]] ![[pic.png]]\n"))
        _write(v / "Attachments/pic.png", "png")
        _write(v / "Archive/Old.md", "---\ntags:\n  - python/x\n---\n[[Nowhere-Archive]]\n")
        _write(v / "Wiki/My-Til.md", _note("My Til", ["til", "kubernetes/basics"]))
        _write(self.root / "TIL/kubernetes/My-Til.md", "# My Til\n")
        _write(v / "Wiki/Only-Til.md", _note("Only", ["til", "python/x"]))
        _write(
            v / "Projects/GenonAI/GenOS/00 GenOS 시작하기.md",
            "# GenOS\n\n## 01 온보딩\n\n- [[기존]] — 기존\n",
        )
        _write(v / "Projects/GenonAI/GenOS/01 온보딩/Hub-Missing.md", "---\ntags:\n  - kubernetes/x\n---\n요약이다.\n")
        # scope other: 어떤 위반이 있어도 무시된다.
        _write(v / "Attachments/Weird.md", "---\ntags:\n  - BAD\n---\n[[Nowhere-Other]]\n")

        skills_a = self.root / "skills-a"
        skills_b = self.root / "skills-b"
        _write(skills_a / "til/SKILL.md", "# til\n")
        _write(skills_b / "til/SKILL.md", "# til\n")
        _write(skills_a / "obsidian-note/SKILL.md", f"see {RULE_DOC}\n")
        _write(skills_b / "obsidian-note/SKILL.md", f"see {RULE_DOC}\n")
        _write(skills_a / "not-listed/SKILL.md", "# x\n")
        _write(skills_b / "not-listed/SKILL.md", "# x\n")
        return _make_policy(self.root, skill_roots=[skills_a, skills_b])

    def test_check_flags_each_kind(self) -> None:
        policy = self._build_check_vault()
        report = run_check(policy)
        got = {(f.kind, f.path) for f in report.findings}

        expected = {
            ("tag", "Wiki/Bad-Tag.md"),
            ("frontmatter", "Wiki/Bad-Order.md"),
            ("frontmatter", "Wiki/Bad-Topic.md"),
            ("unparseable", "Wiki/Broken.md"),
            ("moc-missing", "Wiki/Unregistered.md"),
            ("moc-duplicate", "Dup-Note"),
            ("hub-missing", "Projects/GenonAI/GenOS/01 온보딩/Hub-Missing.md"),
            ("count", "Wiki/_MOC/MOC-Python.md"),
            ("link", "Wiki/Linker.md"),
            ("wiki-only-til-tag", "Wiki/Only-Til.md"),
            ("skill-drift", "til"),
        }
        self.assertTrue(expected <= got, sorted(expected - got))

        paths = {f.path for f in report.findings}
        self.assertNotIn("Templates/Tpl.md", paths)
        self.assertNotIn("Archive/Old.md", {f.path for f in report.findings if f.kind == "link"})
        self.assertNotIn("Attachments/Weird.md", paths)
        self.assertNotIn(("skill-drift", "obsidian-note"), got)
        self.assertNotIn(("skill-drift", "not-listed"), got)
        # wiki-til 노트는 til 태그를 가져도 wiki-only-til-tag가 아니다.
        self.assertNotIn(("wiki-only-til-tag", "Wiki/My-Til.md"), got)
        # 링크 대상: 존재하는 md·비-md는 깨진 링크가 아니다.
        link_details = [f.detail for f in report.findings if f.kind == "link" and f.path == "Wiki/Linker.md"]
        self.assertEqual(link_details, ["[[Nowhere]]"])
        # 예약 kind는 아직 보고하지 않는다.
        kinds = {f.kind for f in report.findings}
        self.assertNotIn("til-body-edited", kinds)
        self.assertNotIn("name-conflict", kinds)
        self.assertTrue({"til-body-edited", "name-conflict"} <= set(KINDS))
        self.assertTrue(kinds <= set(KINDS))
        self.assertEqual(report.exit_code, 1)
        self.assertEqual(report.warnings, [])

    def test_clean_vault_exit_zero(self) -> None:
        _write(
            self.vault / "Wiki/_MOC/MOC-Kubernetes.md",
            "# K8s\n\nWiki의 노트 1개를 묶은 목차다.\n\n## 핵심 리소스\n\n- [[Good]] — g\n",
        )
        _write(self.vault / "Wiki/Good.md", _note("Good", ["kubernetes/basics"]))
        report = run_check(_make_policy(self.root))
        self.assertEqual(report.findings, [])
        self.assertEqual(report.exit_code, 0)

    def test_missing_til_root_warns_and_treats_wiki_as_wiki_only(self) -> None:
        (self.root / "TIL").rmdir()
        _write(self.vault / "Wiki/Til-Tagged.md", _note("T", ["til", "python/x"]))
        report = run_check(_make_policy(self.root))
        self.assertEqual(len(report.warnings), 1)
        self.assertIn(("wiki-only-til-tag", "Wiki/Til-Tagged.md"), {(f.kind, f.path) for f in report.findings})

    def test_nfd_filename_matches_nfc_link(self) -> None:
        import unicodedata

        nfd_name = unicodedata.normalize("NFD", "한글-노트") + ".md"
        _write(self.vault / "Sources" / nfd_name, "---\ntags:\n  - python/x\n---\n본문\n")
        _write(self.vault / "Sources/Linker.md", "---\ntags:\n  - python/x\n---\n[[한글-노트]] [[한글-노트.md|x]]\n")
        report = run_check(_make_policy(self.root))
        self.assertEqual([f for f in report.findings if f.kind == "link"], [])

    def test_til_stems_skip_hidden_and_scripts_dirs(self) -> None:
        _write(self.root / "TIL/.github/Hidden-Readme.md", "# x\n")
        _write(self.root / "TIL/scripts/Script-Doc.md", "# x\n")
        _write(self.root / "TIL/python/Real-Til.md", "# x\n")
        for name in ("Hidden-Readme", "Script-Doc", "Real-Til"):
            _write(self.vault / f"Wiki/{name}.md", _note(name, ["til", "python/x"]))
        report = run_check(_make_policy(self.root))
        til_tag = {f.path for f in report.findings if f.kind == "wiki-only-til-tag"}
        self.assertEqual(til_tag, {"Wiki/Hidden-Readme.md", "Wiki/Script-Doc.md"})

    def test_check_tag_empty(self) -> None:
        _write(self.vault / "Wiki/Empty-List.md", '---\ntitle: "E"\ntags: []\n---\n본문\n')
        _write(self.vault / "Wiki/No-Tags.md", '---\ntitle: "N"\n---\n본문\n')
        _write(self.vault / "Projects/Misc/No-Tags-P.md", "---\ncreated: 2026-01-01\n---\n본문\n")
        _write(self.vault / "Wiki/Has-Tags.md", _note("H", ["python/x"]))
        _write(self.vault / "Sources/Empty-S.md", '---\ntitle: "S"\ntags: []\n---\n본문\n')
        report = run_check(_make_policy(self.root))
        empty = {f.path for f in report.findings if f.kind == "tag-empty"}
        self.assertEqual(empty, {"Wiki/Empty-List.md", "Wiki/No-Tags.md", "Projects/Misc/No-Tags-P.md"})
        self.assertIn("tag-empty", KINDS)

    def test_report_counts(self) -> None:
        report = Report(findings=[Finding("tag", "a", "x"), Finding("tag", "b", "y"), Finding("link", "a", "z")])
        self.assertEqual(report.counts(), {"link": 1, "tag": 2})


class ApplyTest(_TempVaultCase):
    def _build_apply_vault(self) -> Policy:
        v = self.vault
        _write(
            v / "Wiki/_MOC/MOC-Kubernetes.md",
            "# K8s\n\nWiki의 노트 1개를 묶은 목차다.\n\n## 핵심 리소스\n\n- [[Good]] — g\n",
        )
        _write(v / "Wiki/Good.md", _note("Good", ["kubernetes/basics"]))
        # wiki-only: rename 태그 + topics 표기 + 순서 위반 + 미등록.
        _write(
            v / "Wiki/Messy.md",
            '---\ntags:\n  - k8s/old\n  - til\ntopics:\n  - Ai\n  - Computer-science\ntitle: "Messy"\n---\n'
            "메시 노트 요약이다.\r\n본문 끝\n",
        )
        # projects: 인라인 리스트 + drop 태그.
        _write(v / "Projects/Misc/P.md", "---\ncreated: 2026-01-01\ntags: [junk, work/genon]\n---\n본문\n")
        # archive: 고객사 facet은 Projects 밖이므로 삭제.
        _write(v / "Archive/A.md", "---\ntags:\n  - customer/x\n  - python/y\n---\n본문\n")
        # wiki-til: 절대 쓰지 않는다.
        _write(self.root / "TIL/kubernetes/Til-Note.md", "# Til\n")
        _write(v / "Wiki/Til-Note.md", '---\ntags:\n  - k8s/old\ntitle: "Til"\n---\n본문\n')
        # 파싱 불가: 건드리지 않는다.
        _write(v / "Sources/Broken.md", "---\ntags:\n  - k8s/old\n")
        # frontmatter 없는 파일은 그대로.
        _write(v / "_Inbox/Plain.md", "그냥 메모\n")
        return _make_policy(self.root)

    def test_apply_then_apply_is_noop(self) -> None:
        policy = self._build_apply_vault()
        first = run_apply(policy, dry_run=False)
        self.assertIn("Wiki/Messy.md", first.changed)
        self.assertIn("Projects/Misc/P.md", first.changed)
        self.assertIn("Archive/A.md", first.changed)
        self.assertIn("Wiki/_MOC/MOC-Kubernetes.md", first.changed)

        messy = (self.vault / "Wiki/Messy.md").read_bytes().decode("utf-8")
        self.assertEqual(
            messy,
            '---\ntitle: "Messy"\ntopics:\n  - AI\n  - Computer Science\ntags:\n  - kubernetes/basics\n---\n'
            "메시 노트 요약이다.\r\n본문 끝\n",
        )
        self.assertEqual(
            (self.vault / "Projects/Misc/P.md").read_text(encoding="utf-8"),
            "---\ntags:\n  - work/genon\ncreated: 2026-01-01\n---\n본문\n",
        )
        moc = (self.vault / "Wiki/_MOC/MOC-Kubernetes.md").read_text(encoding="utf-8")
        self.assertIn("- [[Messy]] — 메시 노트 요약이다.", moc)
        self.assertIn("노트 3개를", moc)
        self.assertIn("- [[Til-Note]]", moc)  # MOC 등록은 노트가 아니라 MOC를 쓴다.

        second = run_apply(policy, dry_run=False)
        self.assertEqual(second.changed, [])
        self.assertIsNone(second.backup_dir)

    def test_apply_dry_run_writes_nothing(self) -> None:
        policy = self._build_apply_vault()
        before = _snapshot(self.root)
        result = run_apply(policy, dry_run=True)
        self.assertIn("Wiki/Messy.md", result.changed)
        self.assertIn("Wiki/_MOC/MOC-Kubernetes.md", result.changed)
        self.assertIsNone(result.backup_dir)
        self.assertEqual(_snapshot(self.root), before)

    def test_apply_skips_unparseable(self) -> None:
        policy = self._build_apply_vault()
        before = (self.vault / "Sources/Broken.md").read_bytes()
        result = run_apply(policy, dry_run=False)
        self.assertEqual(result.skipped_unparseable, ["Sources/Broken.md"])
        self.assertNotIn("Sources/Broken.md", result.changed)
        self.assertEqual((self.vault / "Sources/Broken.md").read_bytes(), before)

    def test_apply_backup_created(self) -> None:
        policy = self._build_apply_vault()
        originals = {rel: (self.vault / rel).read_bytes() for rel in ("Wiki/Messy.md", "Wiki/_MOC/MOC-Kubernetes.md")}
        result = run_apply(policy, dry_run=False)
        self.assertIsNotNone(result.backup_dir)
        self.assertEqual(result.backup_dir.parent, self.backups)
        for rel, data in originals.items():
            self.assertEqual((result.backup_dir / rel).read_bytes(), data)
        for rel in result.changed:
            self.assertTrue((result.backup_dir / rel).is_file(), rel)

    def test_wiki_til_notes_never_written_by_apply(self) -> None:
        policy = self._build_apply_vault()
        before = (self.vault / "Wiki/Til-Note.md").read_bytes()
        result = run_apply(policy, dry_run=False)
        self.assertNotIn("Wiki/Til-Note.md", result.changed)
        self.assertEqual((self.vault / "Wiki/Til-Note.md").read_bytes(), before)

    def test_til_mapping_normalized_idempotent(self) -> None:
        policy = self._build_apply_vault()
        mapping = self.root / "TIL/tag-mapping.json"
        _write(
            mapping,
            '{\n  "b-note": ["k8s/old", "junk", "customer/x", "work/genon"],\n  "a-note": ["python/x"],\n'
            '  "s-note": "k8s/old",\n  "t-note": "python/x"\n}\n',
        )
        first = run_apply(policy, dry_run=False, til_mapping=True)
        self.assertIn(str(mapping), first.changed)
        data = json.loads(mapping.read_text(encoding="utf-8"))
        self.assertEqual(list(data), ["b-note", "a-note", "s-note", "t-note"])
        # til-source scope: facet 태그는 TIL 원본에서 지우지 않는다.
        self.assertEqual(data["b-note"], ["kubernetes/basics", "customer/x", "work/genon"])
        # 문자열 값은 1원소 리스트로 취급(문자 단위로 쪼개지 않음), 그대로면 문자열 유지.
        self.assertEqual(data["s-note"], ["kubernetes/basics"])
        self.assertEqual(data["t-note"], "python/x")
        self.assertEqual(data["a-note"], ["python/x"])
        self.assertEqual(mapping.read_text(encoding="utf-8"), json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        self.assertTrue((first.backup_dir / "TIL/tag-mapping.json").is_file())

        after_first = mapping.read_bytes()
        second = run_apply(policy, dry_run=False, til_mapping=True)
        self.assertEqual(second.changed, [])
        self.assertEqual(mapping.read_bytes(), after_first)

    def test_apply_skips_note_emptied_by_normalize(self) -> None:
        policy = self._build_apply_vault()
        # Projects 밖 facet만 있어 정규화하면 빈 목록 → 쓰지 않고 보고(순서 위반도 고치지 않음).
        emptied = '---\ntags:\n  - customer/x\n  - work/genon\ntitle: "E"\n---\n본문\n'
        _write(self.vault / "Wiki/Emptied.md", emptied)
        # 원래 비어 있던 tags는 대상이 아니다(순서만 고친다).
        _write(self.vault / "Archive/Was-Empty.md", "---\ntags: []\nsource: x\n---\n본문\n")
        dry = run_apply(policy, dry_run=True)
        self.assertEqual(dry.empty_after_normalize, ["Wiki/Emptied.md"])
        self.assertNotIn("Wiki/Emptied.md", dry.changed)
        real = run_apply(policy, dry_run=False)
        self.assertEqual(real.empty_after_normalize, ["Wiki/Emptied.md"])
        self.assertNotIn("Wiki/Emptied.md", real.changed)
        self.assertEqual((self.vault / "Wiki/Emptied.md").read_text(encoding="utf-8"), emptied)
        self.assertIn("Archive/Was-Empty.md", real.changed)

    def test_apply_refuses_without_til_root(self) -> None:
        policy = self._build_apply_vault()
        for p in sorted((self.root / "TIL").rglob("*"), reverse=True):
            p.unlink() if p.is_file() else p.rmdir()
        (self.root / "TIL").rmdir()
        before = _snapshot(self.root)
        with self.assertRaises(ApplyRefused):
            run_apply(policy, dry_run=False)
        self.assertEqual(_snapshot(self.root), before)
        dry = run_apply(policy, dry_run=True)
        self.assertEqual(len(dry.warnings), 1)
        self.assertIn("til_root", dry.warnings[0])

    def test_backup_root_precedence(self) -> None:
        home = self.root / "home"
        with mock.patch.dict(os.environ, {"HOME": str(home)}):
            os.environ.pop("VAULTKIT_BACKUP_DIR")
            self.assertEqual(backup_root(), home / ".local/state/vaultkit/backups")
            os.environ["VAULTKIT_BACKUP_DIR"] = "~/bk"
            self.assertEqual(backup_root(), home / "bk")
            self.assertEqual(backup_root(Path("~/explicit")), home / "explicit")

    def test_backup_dir_announced_before_first_write(self) -> None:
        policy = self._build_apply_vault()
        original = (self.vault / "Wiki/Messy.md").read_bytes()
        seen: list[tuple[Path, bytes]] = []
        explicit = self.root / "explicit-backups"
        result = run_apply(
            policy,
            dry_run=False,
            backup_root=explicit,
            on_backup_dir=lambda d: seen.append((d, (self.vault / "Wiki/Messy.md").read_bytes())),
        )
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0][0], result.backup_dir)
        self.assertEqual(result.backup_dir.parent, explicit)
        self.assertEqual(seen[0][1], original)  # 알림 시점에는 아직 쓰지 않음
        self.assertFalse(self.backups.exists())

    def test_til_mapping_not_touched_without_flag(self) -> None:
        policy = self._build_apply_vault()
        mapping = self.root / "TIL/tag-mapping.json"
        _write(mapping, '{"n": ["k8s/old"]}\n')
        run_apply(policy, dry_run=False)
        self.assertEqual(mapping.read_text(encoding="utf-8"), '{"n": ["k8s/old"]}\n')


class CliRegisterTest(_TempVaultCase):
    def test_register_updates_moc_counts(self) -> None:
        moc = self.vault / "Wiki/_MOC/MOC-Kubernetes.md"
        _write(moc, "# K8s\n\nWiki의 노트 1개를 묶은 목차다.\n\n## 핵심 리소스\n\n- [[Old]] — o\n")
        _write(self.vault / "Wiki/Old.md", _note("Old", ["kubernetes/basics"]))
        note = self.vault / "Wiki/New.md"
        _write(note, _note("New", ["kubernetes/basics"]))
        policy = _make_policy(self.root)
        with mock.patch.object(cli, "load_policy", return_value=policy), contextlib.redirect_stdout(io.StringIO()):
            code = cli.main(["register", str(note)])
        self.assertEqual(code, 0)
        text = moc.read_text(encoding="utf-8")
        self.assertIn("- [[New]]", text)
        self.assertIn("노트 2개를", text)


class CliApplyTest(_TempVaultCase):
    def _policy(self) -> Policy:
        _write(self.vault / "Wiki/Messy.md", '---\ntags:\n  - k8s/old\ntitle: "M"\n---\n본문\n')
        return _make_policy(self.root)

    def _main(self, *argv: str, policy: Policy) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(cli, "load_policy", return_value=policy), contextlib.redirect_stdout(
            out
        ), contextlib.redirect_stderr(err):
            code = cli.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_backup_dir_option_and_output(self) -> None:
        policy = self._policy()
        target = self.root / "opt-backups"
        code, out, err = self._main("apply", "--backup-dir", str(target), policy=policy)
        self.assertEqual(code, 0)
        dirs = list(target.iterdir())
        self.assertEqual(len(dirs), 1)
        self.assertIn(f"백업 위치: {dirs[0]}", err)
        self.assertIn(f"백업: {dirs[0]}", out)
        self.assertTrue((dirs[0] / "Wiki/Messy.md").is_file())

    def test_backup_dir_printed_again_on_error(self) -> None:
        policy = self._policy()
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(cli, "load_policy", return_value=policy), mock.patch(
            "vaultkit.apply._counts", side_effect=RuntimeError("boom")
        ), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            with self.assertRaises(RuntimeError):
                cli.main(["apply"])
        dirs = list(self.backups.iterdir())
        self.assertEqual(len(dirs), 1)
        self.assertIn(f"백업 위치: {dirs[0]}", err.getvalue())
        self.assertIn(f"백업: {dirs[0]}", out.getvalue())

    def test_refuses_without_til_root(self) -> None:
        policy = self._policy()
        (self.root / "TIL").rmdir()
        before = _snapshot(self.vault)
        code, out, err = self._main("apply", policy=policy)
        self.assertEqual(code, 2)
        self.assertIn("til_root", err)
        self.assertEqual(_snapshot(self.vault), before)
        self.assertFalse(self.backups.exists())
        code, out, err = self._main("apply", "--dry-run", policy=policy)
        self.assertEqual(code, 0)
        self.assertIn("경고", err)
        self.assertIn("변경 예정: Wiki/Messy.md", out)

    def test_empty_after_normalize_reported(self) -> None:
        _write(self.vault / "Wiki/Emptied.md", '---\ntitle: "E"\ntags:\n  - customer/x\n---\n본문\n')
        code, out, _err = self._main("apply", "--dry-run", policy=_make_policy(self.root))
        self.assertEqual(code, 0)
        self.assertIn("건너뜀(empty-after-normalize): Wiki/Emptied.md", out)


if __name__ == "__main__":
    unittest.main()
