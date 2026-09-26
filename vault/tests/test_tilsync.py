"""vaultkit.tilsync — TIL -> Wiki 동기화 순수 로직 테스트.

판정표(spec 5.2)는 데이터 손실과 직결되므로 각 분기를 개별 테스트로
고정한다. 특히 Wiki에서 지운 노트가 되살아나지 않는지(review focus 4),
Wiki 본문 수정이 body_sha 갱신으로 가려지지 않는지를 확인한다.
"""

from __future__ import annotations

import json
import os
import tempfile
import unicodedata
import unittest
from pathlib import Path

from vaultkit import frontmatter as fm
from vaultkit import load_policy
from vaultkit.tilsync import (
    Decision,
    Generated,
    body_sha,
    build_note,
    load_state,
    merge,
    reverse_port,
    save_state,
)

TODAY = "2026-09-27"


def _gen(**overrides) -> Generated:
    base = dict(
        stem="note",
        title="노트 제목",
        sources=["https://example.com/a"],
        topics=["AI"],
        tags=["ai/llm", "til"],
        til_links=["[[other]]"],
        body="본문 첫 줄\n\n## 절\n내용\n",
    )
    base.update(overrides)
    return Generated(**base)


def _synced(body: str) -> dict:
    return {"body_sha": body_sha(body), "status": "synced"}


class _TmpDirCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, rel: str, text: str) -> Path:
        path = self.tmp / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path


class TestMergeDecisionTable(unittest.TestCase):
    """spec 5.2 판정표."""

    def test_create_when_absent_and_no_state(self):
        gen = _gen()
        d = merge(gen, None, None, TODAY)
        self.assertIsInstance(d, Decision)
        self.assertEqual(d.action, "create")
        self.assertEqual(d.entry, {"body_sha": body_sha(gen.body), "status": "synced"})
        expected = (
            "---\n"
            "title: 노트 제목\n"
            "source:\n"
            "  - https://example.com/a\n"
            "topics:\n"
            "  - AI\n"
            "related_notes:\n"
            '  - "[[other]]"\n'
            "tags:\n"
            "  - ai/llm\n"
            "  - til\n"
            f"created: {TODAY}\n"
            "---\n" + gen.body
        )
        self.assertEqual(d.text, expected)

    def test_create_omits_empty_source_and_related(self):
        d = merge(_gen(sources=[], til_links=[]), None, None, TODAY)
        doc = fm.parse(d.text)
        self.assertEqual(doc.order, ["title", "topics", "tags", "created"])

    def test_retired_not_recreated(self):
        d = merge(_gen(), None, {"status": "retired"}, TODAY)
        self.assertEqual(d.action, "skip-retired")
        self.assertIsNone(d.text)
        self.assertEqual(d.entry, {"status": "retired"})

    def test_retired_with_existing_wiki_untouched(self):
        existing = "---\ntitle: x\n---\n사용자 노트\n"
        d = merge(_gen(), existing, {"status": "retired"}, TODAY)
        self.assertEqual(d.action, "skip-retired")
        self.assertIsNone(d.text)
        self.assertEqual(d.entry, {"status": "retired"})

    def test_deleted_in_wiki_becomes_retire(self):
        d = merge(_gen(), None, _synced("옛 본문\n"), TODAY)
        self.assertEqual(d.action, "retire")
        self.assertIsNone(d.text)
        self.assertEqual(d.entry, {"status": "retired"})

    def test_unknown_status_entry_is_conflict_not_create(self):
        for entry in ({"body_sha": "abc"}, {"status": "weird"}):
            d = merge(_gen(), None, entry, TODAY)
            self.assertEqual(d.action, "conflict")
            self.assertIsNone(d.text)
            self.assertEqual(d.entry, entry)

    def test_conflict_when_wiki_only_same_name(self):
        existing = "---\ntitle: 내 노트\ntags:\n  - ai/llm\n---\nWiki 전용 본문\n"
        d = merge(_gen(), existing, None, TODAY)
        self.assertEqual(d.action, "conflict")
        self.assertIsNone(d.text)
        self.assertIsNone(d.entry)
        self.assertIn("충돌", d.message)

    def test_conflict_when_frontmatter_unparseable(self):
        existing = "---\ntitle: x\nmeta:\n  nested: 1\n---\n본문\n"
        d = merge(_gen(), existing, _synced("본문\n"), TODAY)
        self.assertEqual(d.action, "conflict")
        self.assertIsNone(d.text)
        self.assertIn("frontmatter 파싱 불가", d.message)

    def test_update_preserves_related_and_created(self):
        old_body = "옛 본문\n"
        existing = (
            "---\n"
            'title: "옛 제목"\n'
            "source: https://old.example.com\n"
            "topics:\n"
            "  - Ai\n"
            "related_notes:\n"
            '  - "[[wiki-added]]"\n'
            '  - "[[other]]"\n'
            "tags:\n"
            "  - ai/old\n"
            "  - til\n"
            "created: 2025-01-01\n"
            "aliases:\n"
            "  - 별칭\n"
            "---\n" + old_body
        )
        gen = _gen(til_links=["[[other]]", "[[new-link]]"])
        d = merge(gen, existing, _synced(old_body), TODAY)
        self.assertEqual(d.action, "update")
        self.assertEqual(d.entry, {"body_sha": body_sha(gen.body), "status": "synced"})
        doc = fm.parse(d.text)
        self.assertEqual(doc.body, gen.body)
        self.assertEqual(fm.get_list(doc, "title"), ["노트 제목"])
        self.assertEqual(fm.get_list(doc, "source"), ["https://example.com/a"])
        self.assertEqual(fm.get_list(doc, "topics"), ["AI"])
        self.assertEqual(fm.get_list(doc, "tags"), ["ai/llm", "til"])
        self.assertEqual(
            fm.get_list(doc, "related_notes"),
            ["[[wiki-added]]", "[[other]]", "[[new-link]]"],
        )
        self.assertEqual(fm.get_list(doc, "created"), ["2025-01-01"])
        self.assertEqual(fm.get_list(doc, "aliases"), ["별칭"])
        self.assertEqual(
            doc.order,
            ["title", "source", "topics", "related_notes", "tags", "created", "aliases"],
        )

    def test_update_related_dedup_is_nfc(self):
        nfd = unicodedata.normalize("NFD", "[[한글-노트]]")
        existing = f'---\ntitle: x\nrelated_notes:\n  - "{nfd}"\n---\n옛\n'
        gen = _gen(til_links=[unicodedata.normalize("NFC", "[[한글-노트]]")])
        d = merge(gen, existing, _synced("옛\n"), TODAY)
        doc = fm.parse(d.text)
        self.assertEqual(len(fm.get_list(doc, "related_notes")), 1)

    def test_update_adds_created_when_missing(self):
        existing = "---\ntitle: x\n---\n옛\n"
        d = merge(_gen(), existing, _synced("옛\n"), TODAY)
        self.assertEqual(fm.get_list(fm.parse(d.text), "created"), [TODAY])

    def test_update_removes_source_when_til_has_none(self):
        existing = "---\ntitle: x\nsource: https://old\n---\n옛\n"
        d = merge(_gen(sources=[]), existing, _synced("옛\n"), TODAY)
        self.assertNotIn("source", fm.parse(d.text).order)

    def test_body_edited_in_wiki_frontmatter_only(self):
        edited_body = "사용자가 Wiki에서 고친 본문\n"
        existing = "---\ntitle: 옛 제목\ntags:\n  - til\n---\n" + edited_body
        entry = _synced("동기화 당시 본문\n")
        d = merge(_gen(), existing, entry, TODAY)
        self.assertEqual(d.action, "frontmatter-only")
        doc = fm.parse(d.text)
        self.assertEqual(doc.body, edited_body)
        self.assertEqual(fm.get_list(doc, "title"), ["노트 제목"])
        # body_sha는 절대 전진시키지 않는다: 다음 TIL 변경이 Wiki 수정을 덮으면 안 됨.
        self.assertEqual(d.entry, entry)
        self.assertIn("TIL로 이관 필요", d.message)

    def test_body_edited_and_frontmatter_already_merged_keeps_guard(self):
        gen = _gen()
        entry = _synced("동기화 당시 본문\n")
        first = merge(gen, "---\ntitle: x\n---\n고친 본문\n", entry, TODAY)
        d = merge(gen, first.text, entry, TODAY)
        self.assertEqual(d.action, "frontmatter-only")
        self.assertIsNone(d.text)
        self.assertEqual(d.entry, entry)
        self.assertIn("TIL로 이관 필요", d.message)

    def test_unchanged_returns_no_text(self):
        gen = _gen()
        created = merge(gen, None, None, TODAY)
        # 다른 날 다시 돌려도 created는 기존 값 유지 → 바이트 동일.
        d = merge(gen, created.text, created.entry, "2027-01-01")
        self.assertEqual(d.action, "unchanged")
        self.assertIsNone(d.text)
        self.assertEqual(d.entry, {"body_sha": body_sha(gen.body), "status": "synced"})

    def test_body_sha_ignores_trailing_whitespace_and_nfd(self):
        a = unicodedata.normalize("NFD", "한글 줄  \n둘째\t\n\n\n")
        b = "한글 줄\n둘째"
        self.assertEqual(body_sha(a), body_sha(b))
        self.assertNotEqual(body_sha("a\n\nb"), body_sha("a\nb"))


class TestBuildNote(_TmpDirCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = load_policy()

    def test_basic_extraction_and_title_removed(self):
        src = self.write(
            "ai/Some-Note.md",
            "# 제목입니다\n\n본문 [다른](./Other-Note.md) 참조.\n\n## 출처\n\n"
            "- [공식 문서](https://example.com/doc)\n",
        )
        gen = build_note(src, "ai", self.policy, {"Some-Note": ["ai/llm"]})
        self.assertEqual(gen.stem, "Some-Note")
        self.assertEqual(gen.title, "제목입니다")
        self.assertEqual(gen.sources, ["https://example.com/doc"])
        self.assertEqual(gen.til_links, ["[[Other-Note]]"])
        self.assertTrue(gen.body.startswith("본문 [[Other-Note|다른]] 참조."))
        self.assertEqual(gen.tags, ["ai/llm", "til"])

    def test_angle_bracket_source_extracted(self):
        src = self.write(
            "ai/n.md",
            "# t\n\n본문 <https://not-a-source.example.com>\n\n## 출처\n\n"
            "- [A](https://a.example.com/x)\n"
            "- Holtzman (2020). <https://arxiv.org/abs/1904.09751>\n\n"
            "## 다음 절\n\n<https://after.example.com>\n",
        )
        gen = build_note(src, "ai", self.policy, {})
        self.assertEqual(
            gen.sources,
            ["https://a.example.com/x", "https://arxiv.org/abs/1904.09751"],
        )

    def test_numbered_source_heading_not_matched(self):
        src = self.write("ai/n.md", "# t\n\n## 11. 출처\n\n- <https://x.example.com>\n")
        self.assertEqual(build_note(src, "ai", self.policy, {}).sources, [])

    def test_untagged_fallback_uses_folder_domain(self):
        src = self.write("computer-science/n.md", "# t\n본문\n")
        gen = build_note(src, "computer-science", self.policy, {})
        self.assertEqual(gen.tags, ["cs/untagged", "til"])
        src2 = self.write("python/n.md", "# t\n본문\n")
        self.assertEqual(
            build_note(src2, "python", self.policy, {}).tags, ["python/untagged", "til"]
        )

    def test_mapping_lookup_uses_nfc_stem(self):
        nfd_name = unicodedata.normalize("NFD", "한글-노트") + ".md"
        src = self.write("ai/" + nfd_name, "# t\n본문\n")
        gen = build_note(src, "ai", self.policy, {"한글-노트": ["ai/agent"]})
        self.assertEqual(gen.stem, "한글-노트")
        self.assertEqual(gen.tags, ["ai/agent", "til"])

    def test_topics_display_map(self):
        src = self.write("ai/n.md", "# t\n본문\n")
        self.assertEqual(build_note(src, "ai", self.policy, {}).topics, ["AI"])
        src2 = self.write("unknown-folder/n.md", "# t\n본문\n")
        self.assertEqual(
            build_note(src2, "unknown-folder", self.policy, {}).topics, ["unknown-folder"]
        )

    def test_other_folder_link_and_anchor_converted(self):
        src = self.write(
            "devops/n.md",
            "# t\n\n[쿠버\n네티스](../kubernetes/K8s-Probe.md) "
            "[K8s-Probe](../kubernetes/K8s-Probe.md) [절](./a.md#h)\n",
        )
        gen = build_note(src, "devops", self.policy, {})
        self.assertEqual(
            gen.body, "[[K8s-Probe|쿠버\n네티스]] [[K8s-Probe]] [[a#h|절]]\n"
        )
        self.assertEqual(gen.til_links, ["[[K8s-Probe]]", "[[a]]"])

    def test_link_in_table_row_escapes_pipe(self):
        src = self.write("ai/n.md", "# t\n\n| 항목 | [설명](./a.md) |\n|---|---|\n")
        gen = build_note(src, "ai", self.policy, {})
        self.assertEqual(gen.body, "| 항목 | [[a\\|설명]] |\n|---|---|\n")

    def test_links_in_code_not_converted(self):
        body = "```\n[x](./a.md)\n```\n\n`[y](./b.md)` [z](./c.md)\n"
        src = self.write("ai/n.md", "# t\n\n" + body)
        gen = build_note(src, "ai", self.policy, {})
        self.assertEqual(gen.body, "```\n[x](./a.md)\n```\n\n`[y](./b.md)` [[c|z]]\n")
        self.assertEqual(gen.til_links, ["[[c]]"])

    def test_backtick_label_link_converted(self):
        src = self.write("web/n.md", "# t\n\n[`web/a...`](a.md) 와 `[y](./b.md)`\n")
        gen = build_note(src, "web", self.policy, {})
        self.assertEqual(gen.body, "[[a|`web/a...`]] 와 `[y](./b.md)`\n")
        self.assertEqual(gen.til_links, ["[[a]]"])

    def test_existing_til_frontmatter_stripped(self):
        src = self.write("ai/n.md", "---\nfoo: bar\n---\n# t\n본문\n")
        gen = build_note(src, "ai", self.policy, {})
        self.assertEqual(gen.title, "t")
        self.assertEqual(gen.body, "본문\n")


class TestReversePort(unittest.TestCase):
    INDEX = {"a": "ai", "k8s-note": "kubernetes", "한글-노트": "ai", "llms.txt-AI": "ai"}

    def _wiki(self, body: str) -> str:
        return "---\ntitle: T\ntags:\n  - til\n---\n" + body

    def test_reverse_port_links(self):
        body = (
            "[[a]] [[a|b]] [[a#h|b]] [[k8s-note|쿠버]] [[missing]] "
            "[[llms.txt-AI]] [[#로컬 절]] ![[img.png]]\n"
        )
        til, unresolved = reverse_port(self._wiki(body), "T", self.INDEX, "ai")
        self.assertEqual(
            til,
            "# T\n\n[a](./a.md) [b](./a.md) [b](./a.md#h) "
            "[쿠버](../kubernetes/k8s-note.md) [[missing]] [[llms.txt-AI]] "
            "[[#로컬 절]] ![[img.png]]\n",
        )
        self.assertEqual(
            unresolved,
            ["[[missing]]", "[[llms.txt-AI]]", "[[#로컬 절]]", "![[img.png]]"],
        )

    def test_reverse_port_nfd_target_found(self):
        nfd = unicodedata.normalize("NFD", "한글-노트")
        til, unresolved = reverse_port(self._wiki(f"[[{nfd}|x]]\n"), "T", self.INDEX, "ai")
        self.assertEqual(unresolved, [])
        self.assertIn("(./", til)

    def test_reverse_port_skips_code(self):
        body = "```\n[[a]]\n```\n`[[a]]`\n"
        til, unresolved = reverse_port(self._wiki(body), "T", self.INDEX, "ai")
        self.assertEqual(til, "# T\n\n" + body)
        self.assertEqual(unresolved, [])

    def test_reverse_port_backtick_alias(self):
        til, unresolved = reverse_port(self._wiki("[[a|`코드 별칭`]]\n"), "T", self.INDEX, "ai")
        self.assertEqual(til, "# T\n\n[`코드 별칭`](./a.md)\n")
        self.assertEqual(unresolved, [])

    def test_reverse_port_table_escaped_pipe(self):
        body = "| x | [[a\\|별칭]] |\n"
        til, _ = reverse_port(self._wiki(body), "T", self.INDEX, "ai")
        self.assertEqual(til, "# T\n\n| x | [별칭](./a.md) |\n")


class TestRoundtrip(_TmpDirCase):
    def test_reverse_then_build_roundtrip(self):
        policy = load_policy()
        wiki_body = (
            "소개 [[a]] 와 [[a|별칭]], [[a#h|절]], [[k8s-note|쿠버\n네티스]].\n\n"
            "| 표 | [[k8s-note\\|K8s]] |\n|---|---|\n\n"
            "```\n[[a]] 코드\n```\n\n## 출처\n\n- [공식](https://example.com)\n"
        )
        wiki = "---\ntitle: 제목\ntags:\n  - til\n---\n" + wiki_body
        index = {"a": "ai", "k8s-note": "kubernetes", "n": "ai"}
        til_text, unresolved = reverse_port(wiki, "제목", index, "ai")
        self.assertEqual(unresolved, [])
        src = self.write("ai/n.md", til_text)
        gen = build_note(src, "ai", policy, {})
        self.assertEqual(gen.body, wiki_body)
        self.assertEqual(gen.title, "제목")


class TestState(_TmpDirCase):
    def test_absent_state_is_empty_v2(self):
        self.assertEqual(load_state(self.tmp / "none.json"), {"version": 2, "notes": {}})

    def test_v1_state_is_empty_v2(self):
        p = self.write("s.json", json.dumps({"note": "abc123"}))
        self.assertEqual(load_state(p), {"version": 2, "notes": {}})

    def test_v2_state_loaded(self):
        state = {"version": 2, "notes": {"n": {"status": "retired"}}}
        p = self.write("s.json", json.dumps(state))
        self.assertEqual(load_state(p), state)

    def test_corrupt_state_raises(self):
        p = self.write("s.json", "{not json")
        with self.assertRaises(ValueError):
            load_state(p)

    def test_save_state_atomic(self):
        p = self.tmp / "state.json"
        state = {"version": 2, "notes": {"한글": {"status": "retired"}}}
        save_state(p, state)
        self.assertEqual(load_state(p), state)
        self.assertIn("한글", p.read_text(encoding="utf-8"))

        with self.assertRaises(TypeError):
            save_state(p, {"version": 2, "notes": {"x": object()}})
        self.assertEqual(load_state(p), state)
        self.assertEqual(sorted(os.listdir(self.tmp)), ["state.json"])


if __name__ == "__main__":
    unittest.main()
