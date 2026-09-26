"""vaultkit.frontmatter 파서·편집기 테스트.

실제 vault 노트 3종 형태(Wiki TIL형, Projects형, Clipper형)를 짧게 발췌한
문자열 리터럴로 라운드트립을 검증한다. 테스트는 vault 경로에 의존하지 않는다.
"""

from __future__ import annotations

import unittest

from vaultkit.frontmatter import (
    get_list,
    parse,
    render,
    reorder,
    set_list,
    set_scalar,
)

# Wiki/Kubernetes-Pod.md 실측 발췌(따옴표 title, 멀티라인 source, 따옴표 related_notes).
WIKI_TIL_SAMPLE = (
    "---\n"
    'title: "Kubernetes Pod"\n'
    "source:\n"
    "  - https://kubernetes.io/docs/concepts/workloads/pods/\n"
    "  - https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/\n"
    "topics:\n"
    "  - Kubernetes\n"
    "related_notes:\n"
    '  - "[[Kubernetes-ReplicaSet-Deployment]]"\n'
    "tags:\n"
    "  - kubernetes/pod\n"
    "  - til\n"
    "---\n"
    "Docker 컨테이너가 있는데, 왜 Kubernetes는 굳이 \"Pod\"라는 개념을 만들었을까?\n"
    "\n"
    "## 결론부터 말하면\n"
)

# Projects/GenonAI/.../00 삼성증권 시작하기.md 실측 발췌
# (source 단일 항목 리스트, created 스칼라, related_notes 다건).
PROJECTS_SAMPLE = (
    "---\n"
    "source:\n"
    '  - "삼성증권 폴더 노트 38편 (2026-09-26 정리)"\n'
    "related_notes:\n"
    '  - "[[삼성증권_AIDP_GenOS_연계_개발계획서_설계서]]"\n'
    '  - "[[00 GenOS 시작하기]]"\n'
    "tags:\n"
    "  - work/genos\n"
    "  - customer/samsung-securities\n"
    "created: 2026-09-26\n"
    "---\n"
    "\n"
    "> [!summary] 한 줄 결론\n"
    "> 삼성증권 AI 데이터플랫폼 연계 프로젝트다.\n"
)

# Sources/Clippings/... 실측 발췌 (source 단일 문자열 스칼라, author 리스트, published).
CLIPPER_SAMPLE = (
    "---\n"
    "title: Spring Statemachine 이론부터 토이 프로젝트까지\n"
    "source: https://dev.gmarket.com/52\n"
    "author:\n"
    '  - "G마켓 기술블로그"\n'
    "published: 2022-11-09\n"
    "created: 2026-04-11\n"
    "tags:\n"
    "  - clippings\n"
    "---\n"
    "약간 특이한 자판기가 있습니다.\n"
)


class RoundtripTests(unittest.TestCase):
    def test_roundtrip_untouched_is_byte_identical(self):
        for sample in (WIKI_TIL_SAMPLE, PROJECTS_SAMPLE, CLIPPER_SAMPLE):
            doc = parse(sample)
            self.assertIsNotNone(doc)
            self.assertEqual(render(doc), sample)


class SetListTests(unittest.TestCase):
    def test_set_list_changes_only_that_block(self):
        doc = parse(WIKI_TIL_SAMPLE)
        set_list(doc, "topics", ["Kubernetes", "Container"])
        out = render(doc)

        # 변경 대상 블록만 바뀌어야 한다.
        self.assertIn("topics:\n  - Kubernetes\n  - Container\n", out)

        # 앞뒤 다른 키·본문은 원본과 바이트 동일해야 한다.
        prefix = WIKI_TIL_SAMPLE.split("topics:")[0]
        self.assertTrue(out.startswith(prefix))
        # related_notes 이후(본문 포함)는 원본 그대로.
        original_tail = WIKI_TIL_SAMPLE[WIKI_TIL_SAMPLE.index("related_notes:") :]
        out_tail = out[out.index("related_notes:") :]
        self.assertEqual(original_tail, out_tail)


class ReorderTests(unittest.TestCase):
    def test_reorder_keeps_unknown_keys_after(self):
        text = (
            "---\n"
            "aliases:\n"
            "  - a\n"
            "updated: 2026-01-01\n"
            "query: something\n"
            "tags:\n"
            "  - foo\n"
            "---\n"
            "body\n"
        )
        doc = parse(text)
        self.assertIsNotNone(doc)
        reorder(doc, ["tags", "aliases"])
        self.assertEqual(doc.order, ["tags", "aliases", "updated", "query"])
        out = render(doc)
        # 순서만 바뀌고 내용은 그대로 남아야 한다.
        self.assertIn("tags:\n  - foo\n", out)
        self.assertIn("updated: 2026-01-01\n", out)
        self.assertIn("query: something\n", out)


class UnsupportedTests(unittest.TestCase):
    def test_unsupported_returns_none_nested_dict(self):
        text = "---\na:\n  b: 1\n---\nbody\n"
        self.assertIsNone(parse(text))

    def test_unsupported_returns_none_block_scalar(self):
        text = "---\na: |\n  line one\n---\nbody\n"
        self.assertIsNone(parse(text))

    def test_unsupported_returns_none_no_closing_delimiter(self):
        text = "---\ntags:\n  - foo\nbody without closing\n"
        self.assertIsNone(parse(text))

    def test_unsupported_returns_none_inline_list(self):
        text = "---\ntags: [foo, bar]\n---\nbody\n"
        self.assertIsNone(parse(text))


class StringTagsTests(unittest.TestCase):
    def test_string_tags_read_as_list(self):
        text = "---\ntags: foo\n---\nbody\n"
        doc = parse(text)
        self.assertIsNotNone(doc)
        self.assertEqual(get_list(doc, "tags"), ["foo"])


class NoFrontmatterTests(unittest.TestCase):
    def test_no_frontmatter_create_block(self):
        text = "# 제목\n\n본문입니다.\n"
        doc = parse(text)
        self.assertIsNotNone(doc)
        self.assertFalse(doc.has_fm)
        self.assertEqual(doc.fields, {})
        self.assertEqual(doc.order, [])
        self.assertEqual(doc.body, text)

        set_list(doc, "tags", ["til"])
        out = render(doc)
        self.assertEqual(
            out,
            "---\ntags:\n  - til\n---\n" + text,
        )


class BodyPreservationTests(unittest.TestCase):
    def test_body_preserved_with_nfd_text(self):
        import unicodedata

        nfd_body = unicodedata.normalize("NFD", "한글 본문 테스트")
        text = "---\ntags:\n  - til\n---\n" + nfd_body + "\n"
        doc = parse(text)
        self.assertIsNotNone(doc)
        # 본문 바이트가 NFC로 정규화되지 않고 원본 그대로 보존돼야 한다.
        self.assertEqual(doc.body, nfd_body + "\n")
        self.assertEqual(render(doc), text)

    def test_dashes_in_body_not_confused(self):
        text = (
            "---\n"
            "tags:\n"
            "  - til\n"
            "---\n"
            "본문 시작\n"
            "\n"
            "---\n"
            "\n"
            "본문 끝, 수평선 위 텍스트\n"
        )
        doc = parse(text)
        self.assertIsNotNone(doc)
        self.assertEqual(
            doc.body,
            "본문 시작\n\n---\n\n본문 끝, 수평선 위 텍스트\n",
        )
        self.assertEqual(render(doc), text)


class CrlfTests(unittest.TestCase):
    def test_crlf_preserved(self):
        text = (
            "---\r\n"
            "tags:\r\n"
            "  - til\r\n"
            "title: hello\r\n"
            "---\r\n"
            "본문\r\n"
        )
        doc = parse(text)
        self.assertIsNotNone(doc)
        set_list(doc, "tags", ["til", "new"])
        out = render(doc)
        # 건드리지 않은 라인은 \r\n 유지.
        self.assertIn("title: hello\r\n", out)
        self.assertIn("본문\r\n", out)
        # 새로 쓴 라인도 \r\n을 따라야 한다.
        self.assertIn("tags:\r\n  - til\r\n  - new\r\n", out)


class QuotingTests(unittest.TestCase):
    def test_set_list_quotes_wikilink_items(self):
        doc = parse(WIKI_TIL_SAMPLE)
        set_list(doc, "related_notes", ["[[Other-Note]]"])
        out = render(doc)
        self.assertIn('related_notes:\n  - "[[Other-Note]]"\n', out)

    def test_set_list_quotes_special_chars_only_when_needed(self):
        doc = parse(WIKI_TIL_SAMPLE)
        set_list(doc, "tags", ["plain", "has: colon", "has#hash"])
        out = render(doc)
        self.assertIn(
            'tags:\n  - plain\n  - "has: colon"\n  - "has#hash"\n', out
        )

    def test_get_list_strips_outer_quotes(self):
        doc = parse(WIKI_TIL_SAMPLE)
        self.assertEqual(
            get_list(doc, "related_notes"), ["[[Kubernetes-ReplicaSet-Deployment]]"]
        )


class SetScalarNoOpTests(unittest.TestCase):
    def test_set_scalar_same_value_keeps_original_raw(self):
        doc = parse(WIKI_TIL_SAMPLE)
        set_scalar(doc, "title", "Kubernetes Pod")
        out = render(doc)
        # 값이 실질적으로 같으면 원본 라인(따옴표 포함)을 그대로 유지한다.
        self.assertIn('title: "Kubernetes Pod"\n', out)

    def test_set_list_converts_scalar_form_to_list(self):
        # 문자열 스칼라(tags: foo)에 같은 값을 set_list해도, 리스트 출력 형식
        # (key:\n  - item)으로 정규화돼야 한다 — 내용이 같다고 스칼라 형태를
        # 그대로 두면 브리프의 표준 출력 형식을 벗어난다.
        text = "---\ntags: foo\n---\nbody\n"
        doc = parse(text)
        set_list(doc, "tags", ["foo"])
        out = render(doc)
        self.assertEqual(out, "---\ntags:\n  - foo\n---\nbody\n")


if __name__ == "__main__":
    unittest.main()
