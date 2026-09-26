"""vaultkit — Obsidian vault / TIL 노트 정책 도구 모음.

``vault-policy.json`` 하나를 유일한 규칙 원본으로 삼아, vault·TIL 동기화·
스킬이 공통으로 참조하는 태그·frontmatter·등록 규칙을 로드하고 검증한다.
"""

from .policy import Policy, PolicyError, load_policy, scope_of

__all__ = ["Policy", "PolicyError", "load_policy", "scope_of"]
