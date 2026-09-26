"""vault-linter의 vault-index.py가 만드는 frontmatter가 정책과 멱등인지 검증한다.

`vk apply`가 고친 태그를 인덱스 재생성이 되돌리지 않도록, 생성 frontmatter에
inbox 규칙(태그 정규화·필드 정렬)을 적용해도 바뀌지 않아야 한다.
스크립트는 import만 하고 main()은 부르지 않으므로 실제 vault에 쓰지 않는다.
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

from vaultkit import frontmatter
from vaultkit.apply import _fix_note
from vaultkit.policy import load_policy
from vaultkit.tags import normalize_tags

DOTFILES = Path(__file__).resolve().parents[2]
SCRIPTS = [
    DOTFILES / tool / "skills" / "vault-linter" / "scripts" / "vault-index.py"
    for tool in (".claude", ".codex")
]


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(f"vault_index_{path.parts[-5].lstrip('.')}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class VaultIndexFrontmatterTest(unittest.TestCase):
    def setUp(self):
        self.policy = load_policy()

    def test_frontmatter_is_idempotent_under_inbox_rules(self):
        for path in SCRIPTS:
            with self.subTest(script=str(path)):
                module = _load(path)
                text = module.render_frontmatter("2026-09-27") + "\n# Vault Index\n"
                doc = frontmatter.parse(text)
                self.assertIsNotNone(doc)
                self.assertEqual(frontmatter.get_list(doc, "tags"), ["productivity/vault-maintenance"])
                self.assertEqual(frontmatter._unquote(doc.fields.get("title")), "Vault Index")
                tags = frontmatter.get_list(doc, "tags")
                self.assertEqual(normalize_tags(tags, self.policy, scope="inbox"), tags)
                # apply의 inbox 처리(태그 정규화 + 정렬) 결과가 원문과 같아야 한다.
                self.assertEqual(_fix_note(frontmatter.parse(text), "inbox", self.policy), text)
                # inbox 전용 order가 없으므로 Wiki order로 정렬해도 그대로여야 한다.
                wiki = frontmatter.parse(text)
                frontmatter.reorder(wiki, self.policy.frontmatter["Wiki"]["order"])
                self.assertEqual(frontmatter.render(wiki), text)

    def test_claude_and_codex_scripts_are_identical(self):
        claude, codex = (p.read_bytes() for p in SCRIPTS)
        self.assertEqual(claude, codex)


if __name__ == "__main__":
    unittest.main()
