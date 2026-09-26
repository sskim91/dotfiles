"""vaultkit.tags — 태그 정규화(normalize_tags)와 위반 판정(tag_violations) 테스트.

apply·register·TIL 동기화가 공통으로 이 모듈을 거치므로, 멱등성
(n(n(x)) == n(x))이 다른 무엇보다 중요하다. 그래서 실제
``load_policy()``가 반환하는 정책을 그대로 써서, 정책에 있는 모든
rename 키/값·drop 항목·conditional 태그·각 domain의 하위 태그가
7종 scope 전부에서 두 번 정규화해도 결과가 바뀌지 않는지 확인한다.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from vaultkit import Policy, load_policy
from vaultkit.tags import normalize_tags, tag_violations

_ALL_SCOPES = (
    "til-source",
    "wiki-only",
    "projects",
    "archive",
    "sources",
    "templates",
    "inbox",
)


class TestNormalizeTagsIdempotent(unittest.TestCase):
    """실제 정책 전체를 훑는 멱등성 테스트."""

    @classmethod
    def setUpClass(cls):
        cls.policy = load_policy()

    def test_idempotent_on_all_known_tags(self):
        policy = self.policy
        candidate_tags: list[str] = []
        candidate_tags.extend(policy.rename.keys())
        candidate_tags.extend(policy.rename.values())
        candidate_tags.extend(policy.drop)
        candidate_tags.extend(item["tag"] for item in policy.conditional)
        candidate_tags.extend(f"{domain}/sub" for domain in policy.domains)
        candidate_tags.extend(policy.single_allowed)

        for scope in _ALL_SCOPES:
            for tag in candidate_tags:
                with self.subTest(scope=scope, tag=tag):
                    once = normalize_tags([tag], policy, scope)
                    twice = normalize_tags(once, policy, scope)
                    self.assertEqual(
                        twice,
                        once,
                        f"scope={scope!r} tag={tag!r}: n(n(x))={twice!r} != n(x)={once!r}",
                    )

            # 전체를 한 리스트로 넣은 경우도 함께 확인(리스트 차원 상호작용 포함).
            with self.subTest(scope=scope, tag="<all-at-once>"):
                once = normalize_tags(candidate_tags, policy, scope)
                twice = normalize_tags(once, policy, scope)
                self.assertEqual(twice, once)


class TestNormalizeTagsScopes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = load_policy()

    def test_projects_keeps_facets(self):
        result = normalize_tags(
            ["work/genos", "type/onboarding"], self.policy, "projects"
        )
        self.assertEqual(result, ["work/genos", "type/onboarding"])

    def test_outside_projects_drops_facets(self):
        result = normalize_tags(
            ["work/genos", "type/onboarding"], self.policy, "wiki-only"
        )
        self.assertEqual(result, [])

    def test_conditional_ai_with_other_ai_prefix(self):
        result = normalize_tags(["ai", "ai/rag"], self.policy, "wiki-only")
        self.assertEqual(result, ["ai/rag"])

    def test_conditional_ai_without_other_ai_prefix(self):
        result = normalize_tags(["ai"], self.policy, "wiki-only")
        self.assertEqual(result, ["ai/llm"])

    def test_wiki_only_drops_til(self):
        result = normalize_tags(["til", "kubernetes/pod"], self.policy, "wiki-only")
        self.assertEqual(result, ["kubernetes/pod"])

    def test_wiki_til_untouched(self):
        # wiki-til은 TIL 원본이 이미 정규화되어 있으므로, 여기서는 손대지 않고
        # 입력을 그대로 돌려준다(Task 10 --til-mapping이 별도로 처리).
        result = normalize_tags(["role/fde", "til"], self.policy, "wiki-til")
        self.assertEqual(result, ["role/fde", "til"])

    def test_til_source_applies_rename_drop_conditional_only(self):
        # til-source: rename -> drop -> conditional까지만. facet 접두사 삭제와
        # til 삭제는 적용하지 않는다.
        result = normalize_tags(
            ["role/fde", "shinhan", "ai", "til"], self.policy, "til-source"
        )
        self.assertEqual(result, ["work/fde", "ai/llm", "til"])

    def test_dedup_preserves_first_occurrence_order(self):
        result = normalize_tags(
            ["kubernetes/pod", "role/fde", "work/fde"], self.policy, "til-source"
        )
        # role/fde -> work/fde로 rename되어 이미 있던 work/fde와 중복되므로
        # 첫 등장(두 번째 자리, rename된 자리) 기준으로 한 번만 남는다.
        self.assertEqual(result, ["kubernetes/pod", "work/fde"])

    def test_unknown_scope_raises(self):
        with self.assertRaises(ValueError):
            normalize_tags(["ai"], self.policy, "not-a-real-scope")

    def test_conditional_missing_key_raises_instead_of_inserting_none(self):
        # policy.py 로더가 conditional 항목의 네 키(tag/if_other_prefix/
        # then/else)를 모두 필수로 검증하므로, tags.py는 검증된 값만 믿고
        # 바로 인덱싱한다. 검증을 우회해 만든 malformed 정책이 들어오면
        # 조용히 None을 끼워넣는 대신 KeyError로 즉시 드러나야 한다.
        malformed_policy = Policy(
            domains=self.policy.domains,
            facets=self.policy.facets,
            single_allowed=self.policy.single_allowed,
            rename={},
            drop=frozenset(),
            conditional=[{"tag": "ai", "if_other_prefix": "ai/"}],
            drop_outside_projects=self.policy.drop_outside_projects,
            frontmatter={},
            topics={},
            til_folder_domain={},
            moc={},
            hubs={},
            genos_subfolders={},
            vault_root=Path("/nonexistent"),
            til_root=Path("/nonexistent"),
            skill_roots=[],
        )
        with self.assertRaises(KeyError):
            normalize_tags(["ai"], malformed_policy, "wiki-only")


class TestTagViolations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = load_policy()

    def test_violation_reasons(self):
        self.assertEqual(len(tag_violations(["kubernetes"], self.policy, "wiki-only")), 1)
        self.assertEqual(len(tag_violations(["zzz/a"], self.policy, "wiki-only")), 1)
        self.assertEqual(len(tag_violations(["ai/llm/x"], self.policy, "wiki-only")), 1)
        self.assertEqual(len(tag_violations(["cs/untagged"], self.policy, "wiki-only")), 1)

    def test_no_violation_for_clean_tags(self):
        self.assertEqual(tag_violations(["kubernetes/pod"], self.policy, "wiki-only"), [])
        self.assertEqual(tag_violations(["til"], self.policy, "wiki-only"), [])

    def test_projects_allows_facets(self):
        self.assertEqual(tag_violations(["work/genos"], self.policy, "projects"), [])

    def test_projects_facet_disallowed_outside_projects(self):
        self.assertEqual(len(tag_violations(["work/genos"], self.policy, "wiki-only")), 1)

    def test_whitespace_is_trimmed_before_comparison(self):
        self.assertEqual(tag_violations([" kubernetes/pod "], self.policy, "wiki-only"), [])

    def test_uppercase_tag_is_outside_domains(self):
        # 정책이 소문자이므로 대문자 태그는 domains 밖 위반으로 보고된다.
        self.assertEqual(len(tag_violations(["Kubernetes/pod"], self.policy, "wiki-only")), 1)

    def test_unknown_scope_raises(self):
        with self.assertRaises(ValueError):
            tag_violations(["ai"], self.policy, "not-a-real-scope")


if __name__ == "__main__":
    unittest.main()
