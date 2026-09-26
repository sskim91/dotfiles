"""vaultkit.links 테스트."""

from __future__ import annotations

import unittest

from vaultkit.links import wikilinks


class WikilinksTest(unittest.TestCase):
    def test_wikilinks_ignores_code_and_escaped_pipe_and_anchor(self) -> None:
        text = (
            "---\n"
            'related_notes:\n  - "[[FM-Link]]"\n'
            "---\n"
            "본문 [[Plain]] 과 [[Alias|보이는 이름]] 그리고 [[Heading#절]].\n"
            "| 표 | 칸 |\n|---|---|\n| [[Table-Note\\|v1.0]] | x |\n"
            "같은 노트 [[#로컬 제목]] 는 제외.\n"
            "인라인 `[[Inline-Code]]` 제외.\n"
            "```python\nx = '[[Fenced-Code]]'\n```\n"
            "~~~\n[[Tilde-Code]]\n~~~\n"
            "임베드 ![[image.png]] 와 [[folder/Deep Note|d]].\n"
        )
        self.assertEqual(
            wikilinks(text),
            ["FM-Link", "Plain", "Alias", "Heading", "Table-Note", "image.png", "Deep Note"],
        )

    def test_empty_and_whitespace_targets_skipped(self) -> None:
        self.assertEqual(wikilinks("[[]] [[ ]] [[#only]]"), [])


if __name__ == "__main__":
    unittest.main()
