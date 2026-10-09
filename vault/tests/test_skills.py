"""노트 관련 스킬 문서(Claude판·Codex판)가 공통 규칙 문서를 가리키는지 검증한다.

dotfiles checkout 안의 파일만 읽는다(실제 vault·TIL은 읽지 않는다).
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from vaultkit.check import NOTE_SKILLS, RULE_DOC_REF

DOTFILES = Path(__file__).resolve().parents[2]
SKILL_ROOTS = (DOTFILES / ".claude" / "skills", DOTFILES / ".codex" / "skills")
RULE_DOC = DOTFILES / RULE_DOC_REF

# 스킬 폴더 안 모든 .md에서 0건이어야 하는 문자열.
FORBIDDEN = (
    "GenOS 지식 MOC",
    "GenOS 카테고리별 읽는 순서",
    "GenOS 학습 로드맵",
    "agentic-notes",
    "learning-tracker",
    "Wiki/_INDEX.md",
    'VAULT="~/',
)


def _skill_md_files(root: Path, name: str) -> list[Path]:
    return sorted((root / name).rglob("*.md"))


class RuleDocTest(unittest.TestCase):
    def test_rule_doc_exists_and_is_short(self):
        self.assertTrue(RULE_DOC.is_file(), RULE_DOC)
        text = RULE_DOC.read_text(encoding="utf-8")
        self.assertLessEqual(len(text.splitlines()), 200)
        self.assertNotIn("§", text)
        self.assertIn("vk register", text)
        self.assertIn("vault-policy.json", text)


class SkillDocsTest(unittest.TestCase):
    def test_every_note_skill_points_to_rule_doc(self):
        for root in SKILL_ROOTS:
            for name in NOTE_SKILLS:
                with self.subTest(root=root.parent.name, skill=name):
                    skill_md = root / name / "SKILL.md"
                    self.assertTrue(skill_md.is_file(), skill_md)
                    self.assertIn(RULE_DOC_REF, skill_md.read_text(encoding="utf-8"))

    def test_forbidden_strings_absent(self):
        for root in SKILL_ROOTS:
            for name in NOTE_SKILLS:
                for path in _skill_md_files(root, name):
                    text = path.read_text(encoding="utf-8")
                    for bad in FORBIDDEN:
                        with self.subTest(file=str(path.relative_to(DOTFILES)), bad=bad):
                            self.assertNotIn(bad, text)

    def test_no_section_sign_in_note_skills(self):
        for root in SKILL_ROOTS:
            for name in NOTE_SKILLS:
                for path in _skill_md_files(root, name):
                    with self.subTest(file=str(path.relative_to(DOTFILES))):
                        self.assertNotIn("§", path.read_text(encoding="utf-8"))

    def test_youtube_summarizer_has_no_link_section(self):
        for root in SKILL_ROOTS:
            with self.subTest(root=root.parent.name):
                text = (root / "youtube-summarizer" / "SKILL.md").read_text(encoding="utf-8")
                self.assertNotIn("## 연결 고리", text)

    def test_translate_article_tag_example_has_no_til(self):
        for root in SKILL_ROOTS:
            with self.subTest(root=root.parent.name):
                text = (root / "translate-article" / "SKILL.md").read_text(encoding="utf-8")
                self.assertNotIn("[til", text)
                self.assertIn("translation", text)

    def test_genos_capture_uses_hub_and_subfolders(self):
        for root in SKILL_ROOTS:
            with self.subTest(root=root.parent.name):
                text = (root / "genos-knowledge-capture" / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn("00 GenOS 시작하기", text)
                self.assertIn("genos_subfolders", text)
                self.assertTrue(
                    (root / "genos-knowledge-capture" / "references" / "explanation-example.md").is_file()
                )

    def test_patch_notes_use_version_summary_table(self):
        for root in SKILL_ROOTS:
            with self.subTest(root=root.parent.name):
                text = (root / "write-genos-patch-notes" / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn("GenOS 버전별 변경 요약", text)

    def test_post_write_linking_vault_and_exclusions(self):
        for root in SKILL_ROOTS:
            with self.subTest(root=root.parent.name):
                text = (root / "obsidian-note" / "references" / "post-write-linking.md").read_text(
                    encoding="utf-8"
                )
                self.assertIn(
                    'VAULT="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/Note"', text
                )
                for excluded in ("_Inbox/Vault-Index.md", "Archive/", "Wiki/_MOC/"):
                    self.assertIn(excluded, text)
                self.assertIn("## 남은 질문", text)
                self.assertNotIn("## 더 알아보기", text)

    def test_first_matching_tag_rule_is_documented(self):
        # register.py는 tags를 앞에서부터 보고 처음 매칭되는 태그로 허브·MOC 섹션을 정한다.
        phrase = "처음 매칭되는 태그"
        self.assertIn(phrase, RULE_DOC.read_text(encoding="utf-8"))
        for root in SKILL_ROOTS:
            for rel in (
                "genos-knowledge-capture/SKILL.md",
                "genos-knowledge-capture/references/note-format.md",
                "obsidian-note/SKILL.md",
            ):
                with self.subTest(root=root.parent.name, file=rel):
                    self.assertIn(phrase, (root / rel).read_text(encoding="utf-8"))

    def test_genos_tag_example_puts_feature_before_type(self):
        for root in SKILL_ROOTS:
            with self.subTest(root=root.parent.name):
                text = (root / "genos-knowledge-capture" / "references" / "note-format.md").read_text(
                    encoding="utf-8"
                )
                self.assertLess(text.index("  - feature/<기능>"), text.index("  - type/pattern"))

    def test_vault_linter_uses_vk(self):
        for root in SKILL_ROOTS:
            with self.subTest(root=root.parent.name):
                text = (root / "vault-linter" / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn("vk check", text)
                self.assertIn("vk apply --dry-run", text)
                self.assertIn("productivity/vault-maintenance", text)
                self.assertNotIn("  - vault/maintenance", text)


class TilTitleRuleTest(unittest.TestCase):
    """til 스킬 제목 규칙: 핵심 기술명으로 시작 (spec 2026-10-09-til-title-prefix-design.md 6절)."""

    def _til(self, root: Path, rel: str) -> str:
        return (root / "til" / rel).read_text(encoding="utf-8")

    def test_skill_md_title_rule(self):
        for root in SKILL_ROOTS:
            with self.subTest(root=root.parent.name):
                text = self._til(root, "SKILL.md")
                self.assertIn("# <기술명> — <부제>", text)
                self.assertIn("제목이 핵심 기술명으로 시작하는가?", text)
                self.assertNotIn("`# 제목` (호기심 유발)", text)
                self.assertIn("`# Spring CGLIB — 왜 CGLIB 프록시를 기본으로 선택했을까?`", text)
                self.assertIn("`Spring-CGLIB-왜-CGLIB-프록시를-기본으로-선택했을까.md`", text)
                self.assertNotIn("`# 왜 Spring은 CGLIB을 선택했을까?`", text)

    def test_skill_md_special_chars_cover_dash_and_backtick(self):
        for root in SKILL_ROOTS:
            with self.subTest(root=root.parent.name):
                rule = next(
                    line for line in self._til(root, "SKILL.md").splitlines() if line.startswith("**특수문자 처리:**")
                )
                self.assertIn("—", rule)
                self.assertIn("백틱", rule)

    def test_template_title_line(self):
        for root in SKILL_ROOTS:
            with self.subTest(root=root.parent.name):
                first = next(
                    line for line in self._til(root, "assets/til-template.md").splitlines() if line.startswith("# ")
                )
                self.assertEqual(first, "# [기술명] — [부제]")

    def test_shared_files_identical(self):
        claude, codex = SKILL_ROOTS
        for rel in ("references/writing-style-guide.md", "assets/til-template.md"):
            with self.subTest(file=rel):
                self.assertEqual((claude / "til" / rel).read_bytes(), (codex / "til" / rel).read_bytes())

    def test_style_guide_title_examples(self):
        for root in SKILL_ROOTS:
            with self.subTest(root=root.parent.name):
                text = self._til(root, "references/writing-style-guide.md")
                section = text.split("## 1. 제목", 1)[1].split("\n## 2.", 1)[0]
                quoted = re.findall(r'"([^"\n]+)"', section)
                self.assertGreaterEqual(sum("—" in q for q in quoted), 3, quoted)
                self.assertEqual([q for q in quoted if q.startswith("왜 ")], [])


if __name__ == "__main__":
    unittest.main()
