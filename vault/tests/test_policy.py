import json
import tempfile
import unittest
from pathlib import Path

from vaultkit import PolicyError, load_policy, scope_of


def _minimal_policy_dict(**overrides):
    """검증 로직만 겨냥한 최소 유효 policy dict를 만든다."""
    base = {
        "version": 1,
        "tags": {
            "domains": [],
            "project_facets": [],
            "single_segment_allowed": [],
            "drop_outside_projects_prefixes": [],
            "rename": {},
            "drop": [],
            "conditional": [],
        },
        "frontmatter": {},
        "topics": {},
        "til_folder_domain": {},
        "moc": {},
        "hubs": {},
        "genos_subfolders": {},
        "paths": {
            "vault_root": "~/vault-root",
            "til_root": "~/til-root",
            "skill_roots": [],
        },
    }
    for key, value in overrides.items():
        if key == "tags":
            base["tags"].update(value)
        else:
            base[key] = value
    return base


def _write_policy(tmp_path: Path, policy_dict: dict) -> Path:
    policy_path = tmp_path / "vault-policy.json"
    policy_path.write_text(json.dumps(policy_dict), encoding="utf-8")
    return policy_path


class TestLoadPolicy(unittest.TestCase):
    def test_loads_default_policy(self):
        policy = load_policy()
        self.assertIn("cs", policy.domains)
        self.assertNotIn("design-pattern", policy.domains)
        # paths.vault_root / til_root의 "~" 확장은 로더 책임이다.
        self.assertEqual(policy.til_root, Path.home() / "dev" / "TIL")
        self.assertFalse(str(policy.vault_root).startswith("~"))

    def test_rejects_chained_rename(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            policy_dict = _minimal_policy_dict(
                tags={
                    "domains": ["a", "b", "c"],
                    "rename": {"a/x": "b/y", "b/y": "c/z"},
                }
            )
            policy_path = _write_policy(tmp_path, policy_dict)
            with self.assertRaises(PolicyError) as cm:
                load_policy(policy_path)
            self.assertIn("a/x", str(cm.exception))

    def test_rejects_target_outside_domains(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            policy_dict = _minimal_policy_dict(
                tags={
                    "domains": ["a"],
                    "rename": {"a/x": "zzz/y"},
                }
            )
            policy_path = _write_policy(tmp_path, policy_dict)
            with self.assertRaises(PolicyError) as cm:
                load_policy(policy_path)
            self.assertIn("a/x", str(cm.exception))


class TestScopeOf(unittest.TestCase):
    def test_scope_of(self):
        self.assertEqual(scope_of("Wiki/x.md", True), "wiki-til")
        self.assertEqual(scope_of("Wiki/x.md", False), "wiki-only")
        self.assertEqual(scope_of("Wiki/_MOC/MOC-A.md", False), "other")
        self.assertEqual(scope_of("Projects/GenonAI/a.md", False), "projects")


if __name__ == "__main__":
    unittest.main()
