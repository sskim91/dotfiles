"""vaultkit.register 테스트.

실제 vault의 MOC/허브/패치노트 표 구조를 흉내 낸 미니 vault를 tempfile로
만들어 검증한다. 실제 vault는 이 테스트에서 전혀 건드리지 않는다.
"""

from __future__ import annotations

import tempfile
import unicodedata
import unittest
from pathlib import Path

from vaultkit.policy import Policy
from vaultkit.register import (
    RegisterResult,
    _insert_into_section,
    derive_maps,
    register_note,
    summary_line,
    update_counts,
)


def _nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def _make_policy(vault_root: Path, *, moc=None, hubs=None) -> Policy:
    return Policy(
        domains=frozenset({"kubernetes", "python", "ai"}),
        facets=frozenset({"work", "customer", "feature", "type"}),
        single_allowed=frozenset({"til", "moc"}),
        rename={},
        drop=frozenset(),
        conditional=[],
        drop_outside_projects=frozenset(),
        frontmatter={},
        topics={},
        til_folder_domain={},
        moc=moc or {},
        hubs=hubs or {},
        genos_subfolders={},
        vault_root=vault_root,
        til_root=vault_root / "_til",
        skill_roots=[],
    )


_WIKI_NOTE = """---
title: "{title}"
tags:
  - {tag}
---
{body}
"""


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


MOC_KUBERNETES = """---
title: "Kubernetes MOC"
tags:
  - moc
---
# Kubernetes

Wiki의 Kubernetes 노트 1개를 주제별로 묶은 목차다.

## 핵심 리소스

- [[기존-노트]] — 기존 노트 설명

## 다른 절

- [[Other-Note]] — 다른 절 노트
"""


class RegisterWikiMocTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.vault_root = Path(self._tmp.name).resolve()
        _write(
            self.vault_root / "Wiki" / "_MOC" / "MOC-Kubernetes.md",
            MOC_KUBERNETES,
        )
        self.moc = {"kubernetes/*": ["MOC-Kubernetes", "핵심 리소스"]}
        self.policy = _make_policy(self.vault_root, moc=self.moc)

    def _write_note(self, filename: str, *, tag: str, body: str) -> Path:
        path = self.vault_root / "Wiki" / filename
        _write(
            path,
            _WIKI_NOTE.format(title=filename, tag=tag, body=body),
        )
        return path

    def test_adds_to_section_end(self):
        note = self._write_note(
            "새-노트.md",
            tag="kubernetes/pod",
            body="Pod란 무엇인가? 컨테이너를 감싸는 최소 배포 단위다.",
        )

        result = register_note(note, self.policy)

        self.assertEqual(result.status, "added")
        self.assertEqual(result.target, "MOC-Kubernetes")
        self.assertEqual(result.section, "핵심 리소스")
        self.assertEqual(
            result.line, "- [[새-노트]] — Pod란 무엇인가?"
        )

        target_text = (
            self.vault_root / "Wiki" / "_MOC" / "MOC-Kubernetes.md"
        ).read_text(encoding="utf-8")
        lines = target_text.splitlines()
        idx_existing = next(
            i for i, l in enumerate(lines) if l.startswith("- [[기존-노트]]")
        )
        idx_new = next(
            i for i, l in enumerate(lines) if l.startswith("- [[새-노트]]")
        )
        idx_next_section = next(
            i for i, l in enumerate(lines) if l.startswith("## 다른 절")
        )
        # 새 줄은 기존 절의 마지막 항목 바로 다음, 다음 절 헤딩보다 앞이어야 한다.
        self.assertEqual(idx_new, idx_existing + 1)
        self.assertLess(idx_new, idx_next_section)

    def test_exists_not_duplicated(self):
        # MOC에는 NFC로 "[[기존-노트]]"가 있다. 실제 파일명은 NFD로 저장한다.
        nfd_name = unicodedata.normalize("NFD", "기존-노트") + ".md"
        note_path = self.vault_root / "Wiki" / nfd_name
        _write(
            note_path,
            _WIKI_NOTE.format(
                title="기존-노트", tag="kubernetes/pod", body="이미 등록된 노트다."
            ),
        )

        result = register_note(note_path, self.policy)

        self.assertEqual(result.status, "exists")
        self.assertEqual(result.target, "MOC-Kubernetes")

    def test_exists_check_scans_all_moc_files(self):
        # 태그 매핑은 MOC-Kubernetes를 가리키지만, 노트는 실제로 이미
        # 다른 MOC 파일(MOC-Other)에 등록돼 있다 — 컨트롤러 fix 1.
        _write(
            self.vault_root / "Wiki" / "_MOC" / "MOC-Other.md",
            """---
title: "Other MOC"
tags:
  - moc
---
# Other

Wiki의 기타 노트 1개를 주제별로 묶은 목차다.

## 엉뚱한 절

- [[다른곳-노트]] — 이미 다른 MOC에 등록된 노트
""",
        )
        note_path = self.vault_root / "Wiki" / "다른곳-노트.md"
        _write(
            note_path,
            _WIKI_NOTE.format(
                title="다른곳-노트", tag="kubernetes/pod", body="본문이다."
            ),
        )
        kubernetes_moc_before = (
            self.vault_root / "Wiki" / "_MOC" / "MOC-Kubernetes.md"
        ).read_text(encoding="utf-8")
        other_moc_before = (
            self.vault_root / "Wiki" / "_MOC" / "MOC-Other.md"
        ).read_text(encoding="utf-8")

        result = register_note(note_path, self.policy)

        self.assertEqual(result.status, "exists")
        self.assertEqual(result.target, "MOC-Other")
        self.assertEqual(result.section, "엉뚱한 절")
        # 두 파일 모두 바뀌지 않아야 한다(태그가 가리키는 MOC-Kubernetes에
        # 중복 등록되면 안 된다).
        self.assertEqual(
            kubernetes_moc_before,
            (self.vault_root / "Wiki" / "_MOC" / "MOC-Kubernetes.md").read_text(
                encoding="utf-8"
            ),
        )
        self.assertEqual(
            other_moc_before,
            (self.vault_root / "Wiki" / "_MOC" / "MOC-Other.md").read_text(
                encoding="utf-8"
            ),
        )

    def test_unclassified_when_no_mapping(self):
        note = self._write_note(
            "매핑없는-노트.md",
            tag="python/asyncio",
            body="asyncio는 왜 필요한가? 동시성을 다루는 방법 중 하나다.",
        )

        result = register_note(note, self.policy)

        self.assertEqual(
            RegisterResult("unclassified", None, None, None), result
        )

    def test_tag_order_picks_earlier_tags_wildcard_over_later_exact(self):
        # 브리프: "태그를 순서대로 보며 정확 일치 키, 없으면 domain/* 키로
        # 결정" — 태그 전체에 대해 정확 일치를 먼저 다 훑고(2-pass) 그 다음
        # 와일드카드를 보는 방식이 아니라, 앞 태그부터 하나씩
        # (정확→도메인 와일드카드)를 확인해 첫 매치에서 멈추는 1-pass
        # 방식임을 고정한다.
        moc = {
            "kubernetes/*": ["MOC-Kubernetes", "핵심 리소스"],
            "python/asyncio": ["MOC-Kubernetes", "다른 절"],
        }
        policy = _make_policy(self.vault_root, moc=moc)
        note = self._write_note(
            "우선순위-노트.md",
            tag="kubernetes/pod",
            body="이 노트는 두 번째 태그도 갖는다.",
        )
        # 두 번째 태그(정확 일치 대상)를 frontmatter에 덧붙인다.
        text = note.read_text(encoding="utf-8")
        text = text.replace(
            "  - kubernetes/pod\n", "  - kubernetes/pod\n  - python/asyncio\n"
        )
        note.write_text(text, encoding="utf-8")

        result = register_note(note, policy)

        # 첫 태그 kubernetes/pod의 도메인 와일드카드가 이겨야 한다.
        self.assertEqual(result.section, "핵심 리소스")

    def test_register_twice_is_noop(self):
        note = self._write_note(
            "두번-노트.md",
            tag="kubernetes/service",
            body="Service는 무엇인가? 파드 집합에 붙는 안정적 이름이다.",
        )

        first = register_note(note, self.policy)
        target_path = self.vault_root / "Wiki" / "_MOC" / "MOC-Kubernetes.md"
        text_after_first = target_path.read_text(encoding="utf-8")

        second = register_note(note, self.policy)
        text_after_second = target_path.read_text(encoding="utf-8")

        self.assertEqual(first.status, "added")
        self.assertEqual(second.status, "exists")
        self.assertEqual(text_after_first, text_after_second)
        self.assertEqual(text_after_second.count("[[두번-노트]]"), 1)

    def test_dry_run_does_not_write(self):
        note = self._write_note(
            "드라이런-노트.md",
            tag="kubernetes/pod",
            body="드라이런 테스트다. 파일이 바뀌면 안 된다.",
        )
        target_path = self.vault_root / "Wiki" / "_MOC" / "MOC-Kubernetes.md"
        before = target_path.read_text(encoding="utf-8")

        result = register_note(note, self.policy, dry_run=True)

        after = target_path.read_text(encoding="utf-8")
        self.assertEqual(result.status, "added")
        self.assertEqual(before, after)

    def test_insert_into_missing_trailing_newline_does_not_corrupt(self):
        # 리뷰 repro: 파일이 줄바꿈 없이 끝나면 새 줄이 기존 마지막 줄에
        # 그대로 붙었다 — 컨트롤러 fix 2.
        text = "# M\n\n## A\n\n- [[x]] — y"  # 끝에 개행 없음

        result = _insert_into_section(text, "A", "- [[new]] — z")

        self.assertIsNotNone(result)
        lines = result.splitlines()
        self.assertIn("- [[x]] — y", lines)
        self.assertIn("- [[new]] — z", lines)
        # 기존 항목이 새 항목과 붙어서 깨지면 안 된다.
        self.assertNotIn("y- [[new]]", result)

    def test_register_note_appends_newline_when_moc_file_lacks_trailing_newline(
        self,
    ):
        # 삽입 대상 절이 파일의 "마지막" 절이어야 버그가 재현된다(끝에
        # 개행이 없으면 마지막 줄만 영향을 받으므로).
        moc = {"kubernetes/*": ["MOC-Kubernetes", "다른 절"]}
        policy = _make_policy(self.vault_root, moc=moc)

        target_path = self.vault_root / "Wiki" / "_MOC" / "MOC-Kubernetes.md"
        text = target_path.read_text(encoding="utf-8")
        self.assertTrue(text.endswith("\n"))
        # 실제 vault처럼 끝에 개행이 없는 상황을 재현한다.
        target_path.write_text(text.rstrip("\n"), encoding="utf-8")

        note = self._write_note(
            "끝줄바꿈없음-노트.md",
            tag="kubernetes/pod",
            body="파일 끝에 개행이 없는 상태에서 추가된다.",
        )

        result = register_note(note, policy)

        self.assertEqual(result.status, "added")
        new_text = target_path.read_text(encoding="utf-8")
        lines = new_text.splitlines()
        self.assertIn("- [[Other-Note]] — 다른 절 노트", lines)
        self.assertIn(
            "- [[끝줄바꿈없음-노트]] — 파일 끝에 개행이 없는 상태에서 추가된다.",
            lines,
        )
        self.assertNotIn("다른 절 노트- [[끝줄바꿈없음-노트]]", new_text)


class SummaryLineTest(unittest.TestCase):
    def test_summary_line_skips_callout_and_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "노트.md"
            _write(
                path,
                """---
title: "노트"
tags:
  - kubernetes/pod
---

> [!summary] 한 줄 결론
> 이 줄은 callout이라 제외돼야 한다.

```
code line 1
should be skipped.
```

실제 첫 문단입니다. 두 번째 문장은 무시된다.
""",
            )

            result = summary_line(path)

            self.assertEqual(result, "실제 첫 문단입니다.")

    def test_summary_line_truncates_over_60_chars(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "긴노트.md"
            long_sentence = "가" * 70
            _write(path, f"---\ntitle: \"x\"\ntags:\n  - til\n---\n{long_sentence}\n")

            result = summary_line(path)

            self.assertEqual(len(result), 61)  # 60자 + "…"
            self.assertTrue(result.endswith("…"))

    def test_summary_line_resolves_wikilinks_to_plain_text(self):
        # 요약에 위키링크가 그대로 남으면 이후 exists 판정이 그 노트를
        # 잘못 "이미 등록됨"으로 오판할 수 있다 — 컨트롤러 fix 4.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "노트.md"
            _write(
                path,
                "---\ntitle: \"x\"\ntags:\n  - til\n---\n"
                "이 개념은 [[다른-노트]]와 [[또다른-노트|별칭]]에서 다룬다. "
                "두 번째 문장은 무시된다.\n",
            )

            result = summary_line(path)

            self.assertEqual(
                result, "이 개념은 다른-노트와 별칭에서 다룬다."
            )
            self.assertNotIn("[[", result)
            self.assertNotIn("]]", result)


PATCHNOTE_TABLE = """---
title: "GenOS 버전별 변경 요약"
tags:
  - moc
---
# GenOS 버전별 변경 요약

## 버전별 한눈에 보기

| 버전 | 비교 기준 | 핵심 변경 (한 줄) | 고객사 업데이트 주의 |
|---|---|---|---|
| [[GenOS v1.9.0 패치노트\\|v1.9.0]] | v1.8.8 → v1.9.0 | 기존 변경 A | 주의 A |
| [[GenOS v1.9.3 패치노트\\|v1.9.3]] | v1.9.2.1 → v1.9.3.4 | 기존 변경 B | 주의 B |
| [[GenOS v2.0.0 패치노트\\|v2.0.0]] | v1.9.3.4 → v2.0.0 | 기존 변경 C | 주의 C |

## 굵직한 흐름

- 어떤 흐름 설명
"""

GENOS_HUB = """---
title: "GenOS 시작하기"
tags:
  - moc
---
# GenOS 시작하기

## 01 온보딩

- [[GenOS 온보딩 노트]] — 온보딩 설명

## 02 아키텍처

- [[GenOS 아키텍처 노트]] — 아키텍처 설명

## 패치노트

- [[GenOS 버전별 변경 요약]] — 패치노트 허브
"""


class RegisterProjectHubTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.vault_root = Path(self._tmp.name).resolve()

        self.hubs = {
            "Projects/GenonAI/GenOS": {
                "hub": "00 GenOS 시작하기",
                "section_by_subfolder": True,
            },
            "Projects/GenonAI/GenOS/패치노트": {
                "hub": "GenOS 버전별 변경 요약",
                "mode": "patchnote-table",
            },
            "Projects/GenonAI/삼성증권": {
                "hub": "00 삼성증권 시작하기",
                "section_by_tag": {"feature/aidp": "AIDP 제공 API·인증"},
            },
        }
        self.policy = _make_policy(self.vault_root, hubs=self.hubs)

        _write(
            self.vault_root
            / "Projects/GenonAI/GenOS"
            / "00 GenOS 시작하기.md",
            GENOS_HUB,
        )
        _write(
            self.vault_root
            / "Projects/GenonAI/GenOS/패치노트"
            / "GenOS 버전별 변경 요약.md",
            PATCHNOTE_TABLE,
        )

    def test_patchnote_table_row_sorted(self):
        note_path = (
            self.vault_root
            / "Projects/GenonAI/GenOS/패치노트"
            / "GenOS v1.9.4 패치노트.md"
        )
        _write(
            note_path,
            "---\ntitle: \"v1.9.4\"\ntags:\n  - work/genos\n---\n"
            "v1.9.4는 무엇을 담았나? 안정화 릴리스다.\n",
        )

        result = register_note(note_path, self.policy)

        self.assertEqual(result.status, "added")
        self.assertEqual(result.target, "GenOS 버전별 변경 요약")

        target_text = (
            self.vault_root
            / "Projects/GenonAI/GenOS/패치노트"
            / "GenOS 버전별 변경 요약.md"
        ).read_text(encoding="utf-8")
        lines = [l for l in target_text.splitlines() if l.startswith("|")]
        version_lines = [l for l in lines if "패치노트\\|" in l]

        idx_193 = next(i for i, l in enumerate(version_lines) if "v1.9.3]]" in l)
        idx_194 = next(i for i, l in enumerate(version_lines) if "v1.9.4]]" in l)
        idx_200 = next(i for i, l in enumerate(version_lines) if "v2.0.0]]" in l)

        self.assertEqual(idx_194, idx_193 + 1)
        self.assertEqual(idx_200, idx_194 + 1)
        self.assertIn("v1.9.4는 무엇을 담았나?", target_text)

    def test_patchnote_hub_itself_is_skipped(self):
        hub_note_path = (
            self.vault_root
            / "Projects/GenonAI/GenOS/패치노트"
            / "GenOS 버전별 변경 요약.md"
        )
        result = register_note(hub_note_path, self.policy)
        self.assertEqual(
            RegisterResult("skipped", None, None, None), result
        )

    def test_project_note_outside_any_hub_is_unclassified(self):
        # spec D3: 대응(허브) 없으면 skipped가 아니라 unclassified로
        # 보고한다 — 컨트롤러 fix 3.
        note_path = (
            self.vault_root / "Projects/GenonAI/모르는고객사" / "노트.md"
        )
        _write(
            note_path,
            "---\ntitle: \"x\"\ntags:\n  - work/genos\n---\n어느 허브에도 속하지 않는다.\n",
        )

        result = register_note(note_path, self.policy)

        self.assertEqual(
            RegisterResult("unclassified", None, None, None), result
        )

    def test_genos_subfolder_section(self):
        note_path = (
            self.vault_root
            / "Projects/GenonAI/GenOS/01 온보딩"
            / "새 온보딩 노트.md"
        )
        _write(
            note_path,
            "---\ntitle: \"x\"\ntags:\n  - work/genos\n---\n온보딩 관련 설명이다.\n",
        )

        result = register_note(note_path, self.policy)

        self.assertEqual(result.status, "added")
        self.assertEqual(result.section, "01 온보딩")

    def test_genos_note_outside_subfolder_is_unclassified(self):
        note_path = self.vault_root / "Projects/GenonAI/GenOS" / "루트 노트.md"
        _write(
            note_path,
            "---\ntitle: \"x\"\ntags:\n  - work/genos\n---\n루트 바로 아래 노트다.\n",
        )

        result = register_note(note_path, self.policy)

        self.assertEqual(
            RegisterResult("unclassified", None, None, None), result
        )

    def test_customer_hub_section_by_tag(self):
        _write(
            self.vault_root
            / "Projects/GenonAI/삼성증권"
            / "00 삼성증권 시작하기.md",
            "---\ntitle: \"x\"\ntags:\n  - moc\n---\n# 삼성증권 시작하기\n\n"
            "## AIDP 제공 API·인증\n\n- [[기존 AIDP 노트]] — 기존 설명\n",
        )
        note_path = (
            self.vault_root / "Projects/GenonAI/삼성증권" / "새 AIDP 노트.md"
        )
        _write(
            note_path,
            "---\ntitle: \"x\"\ntags:\n  - feature/aidp\n---\nAIDP 새 설명이다.\n",
        )

        result = register_note(note_path, self.policy)

        self.assertEqual(result.status, "added")
        self.assertEqual(result.target, "00 삼성증권 시작하기")
        self.assertEqual(result.section, "AIDP 제공 API·인증")

    def test_customer_hub_no_tag_match_is_unclassified(self):
        _write(
            self.vault_root
            / "Projects/GenonAI/삼성증권"
            / "00 삼성증권 시작하기.md",
            "---\ntitle: \"x\"\ntags:\n  - moc\n---\n# 삼성증권 시작하기\n\n"
            "## AIDP 제공 API·인증\n\n- [[기존 AIDP 노트]] — 기존 설명\n",
        )
        note_path = (
            self.vault_root / "Projects/GenonAI/삼성증권" / "매칭없는 노트.md"
        )
        _write(
            note_path,
            "---\ntitle: \"x\"\ntags:\n  - work/genos\n---\n매칭되지 않는 태그다.\n",
        )

        result = register_note(note_path, self.policy)

        self.assertEqual(
            RegisterResult("unclassified", None, None, None), result
        )


MOC_A = """---
title: "A"
tags:
  - moc
---
# A

Wiki의 A 노트 3개를 주제별로 묶은 목차다.

## 절1

- [[A1]] — 설명1
- [[A2]] — 설명2
"""

MOC_B = """---
title: "B"
tags:
  - moc
---
# B

Wiki의 B 노트 1개를 주제별로 묶은 목차다.

## 절1

- [[B1]] — 설명1
"""

INDEX_MOC = """---
title: "Wiki MOC"
tags:
  - moc
---
# Wiki MOC

Wiki 노트 8개를 2개 분야로 나눈 최상위 목차다.

- [[MOC-A]] — 3개 (절1)
- [[MOC-B]] — 5개 (절1)
"""


class UpdateCountsTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.vault_root = Path(self._tmp.name).resolve()
        _write(self.vault_root / "Wiki/_MOC/MOC-A.md", MOC_A)
        _write(self.vault_root / "Wiki/_MOC/MOC-B.md", MOC_B)
        _write(self.vault_root / "Wiki/_MOC/00-Wiki-MOC.md", INDEX_MOC)
        self.policy = _make_policy(self.vault_root)

    def test_update_counts(self):
        changed = update_counts(self.policy)

        moc_a_text = (self.vault_root / "Wiki/_MOC/MOC-A.md").read_text(
            encoding="utf-8"
        )
        index_text = (self.vault_root / "Wiki/_MOC/00-Wiki-MOC.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("노트 2개를", moc_a_text)  # 실제 2개(A1, A2)로 정정
        self.assertIn("— 2개 (절1)", index_text)
        self.assertIn("노트 3개를", index_text)  # 2(A) + 1(B) = 3
        self.assertEqual(
            {p.name for p in changed},
            {"MOC-A.md", "00-Wiki-MOC.md"},
        )

    def test_update_counts_dry_run_does_not_write(self):
        before = (self.vault_root / "Wiki/_MOC/MOC-A.md").read_text(
            encoding="utf-8"
        )

        changed = update_counts(self.policy, dry_run=True)

        after = (self.vault_root / "Wiki/_MOC/MOC-A.md").read_text(
            encoding="utf-8"
        )
        self.assertEqual(before, after)
        self.assertIn(self.vault_root / "Wiki/_MOC/MOC-A.md", changed)

    def test_update_counts_noop_when_already_correct(self):
        update_counts(self.policy)
        changed_again = update_counts(self.policy)
        self.assertEqual(changed_again, [])

    def test_update_counts_nfd_moc_filename_matches_nfc_index_link(self):
        # 실측 vault처럼 MOC 파일명이 디스크에는 NFD로, 00-Wiki-MOC의
        # 링크 텍스트는 NFC로 있는 상황을 재현한다.
        nfd_stem = unicodedata.normalize("NFD", "MOC-네트워크")
        _write(
            self.vault_root / "Wiki/_MOC" / f"{nfd_stem}.md",
            """---
title: "네트워크 MOC"
tags:
  - moc
---
# 네트워크

Wiki의 네트워크 노트 9개를 주제별로 묶은 목차다.

## 절1

- [[N1]] — 설명
""",
        )
        _write(
            self.vault_root / "Wiki/_MOC/00-Wiki-MOC.md",
            INDEX_MOC.replace(
                "- [[MOC-B]] — 5개 (절1)\n",
                "- [[MOC-B]] — 5개 (절1)\n- [[MOC-네트워크]] — 9개 (절1)\n",
            ),
        )

        update_counts(self.policy)

        index_text = (self.vault_root / "Wiki/_MOC/00-Wiki-MOC.md").read_text(
            encoding="utf-8"
        )
        moc_text = (
            self.vault_root / "Wiki/_MOC" / f"{nfd_stem}.md"
        ).read_text(encoding="utf-8")

        self.assertIn("— 1개 (절1)", index_text)  # NFC 링크 텍스트로도 갱신됨
        self.assertNotIn("— 9개 (절1)", index_text)
        self.assertIn("노트 1개를", moc_text)


class DeriveMapsTest(unittest.TestCase):
    def test_derive_moc_votes_majority_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault_root = Path(tmp).resolve()
            _write(
                vault_root / "Wiki/_MOC/MOC-Kubernetes.md",
                """---
title: "K8s"
tags:
  - moc
---
# Kubernetes

Wiki의 Kubernetes 노트 2개를 주제별로 묶은 목차다.

## 핵심 리소스

- [[K1]] — 설명
- [[K2]] — 설명
""",
            )
            _write(
                vault_root / "Wiki/K1.md",
                "---\ntitle: \"K1\"\ntags:\n  - kubernetes/pod\n  - work/genos\n---\n본문\n",
            )
            _write(
                vault_root / "Wiki/K2.md",
                "---\ntitle: \"K2\"\ntags:\n  - kubernetes/pod\n---\n본문\n",
            )
            policy = _make_policy(vault_root)

            result = derive_maps(policy)

            self.assertEqual(
                result["moc"]["kubernetes/pod"], ["MOC-Kubernetes", "핵심 리소스"]
            )
            self.assertEqual(
                result["moc"]["kubernetes/*"], ["MOC-Kubernetes", "핵심 리소스"]
            )
            # work/genos 같은 범용 태그는 제외돼야 한다.
            self.assertNotIn("work/genos", result["moc"])
            self.assertNotIn("work/*", result["moc"])

    def test_derive_genos_subfolders_top5(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault_root = Path(tmp).resolve()
            hubs = {
                "Projects/GenonAI/GenOS": {
                    "hub": "00 GenOS 시작하기",
                    "section_by_subfolder": True,
                }
            }
            sub = vault_root / "Projects/GenonAI/GenOS/01 온보딩"
            _write(
                sub / "n1.md",
                "---\ntitle: \"x\"\ntags:\n  - type/onboarding\n  - work/genos\n---\n본문\n",
            )
            _write(
                sub / "n2.md",
                "---\ntitle: \"x\"\ntags:\n  - type/onboarding\n---\n본문\n",
            )
            policy = _make_policy(vault_root, hubs=hubs)

            result = derive_maps(policy)

            self.assertIn("01 온보딩", result["genos_subfolders"])
            self.assertIn(
                "type/onboarding", result["genos_subfolders"]["01 온보딩"]
            )
            self.assertNotIn(
                "work/genos", result["genos_subfolders"]["01 온보딩"]
            )

    def test_derive_genos_subfolders_excludes_other_hub_subfolder(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault_root = Path(tmp).resolve()
            hubs = {
                "Projects/GenonAI/GenOS": {
                    "hub": "00 GenOS 시작하기",
                    "section_by_subfolder": True,
                },
                "Projects/GenonAI/GenOS/패치노트": {
                    "hub": "GenOS 버전별 변경 요약",
                    "mode": "patchnote-table",
                },
            }
            _write(
                vault_root / "Projects/GenonAI/GenOS/패치노트/v1.md",
                "---\ntitle: \"x\"\ntags:\n  - feature/release-notes\n---\n본문\n",
            )
            policy = _make_policy(vault_root, hubs=hubs)

            result = derive_maps(policy)

            self.assertNotIn("패치노트", result["genos_subfolders"])


if __name__ == "__main__":
    unittest.main()
