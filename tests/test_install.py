"""Exercise installer sections without running package installers or touching HOME.

Run: python3 -m unittest discover -s tests -v
Only external installer commands are replaced; filesystem and Git operations are real.
"""

import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

INSTALLER = Path(__file__).resolve().parents[1] / "install.sh"
SOURCE = INSTALLER.read_text()


def section(title):
    match = re.search(r"^# " + re.escape(title) + r"\n#-+\n", SOURCE, re.MULTILINE)
    if match is None:
        raise AssertionError(f"Installer section missing: {title}")
    return SOURCE[match.end() :].split("\n#---", 1)[0]


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="install-regression-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "home"
        self.repo = self.home / ".dotfiles"
        self.repo.mkdir(parents=True)
        self.env = dict(os.environ)
        self.env.update(
            INSTALL_TEST_HOME=str(self.home),
            DOTFILES=str(self.repo),
            XDG_CONFIG_HOME=str(self.home / "xdg"),
            XDG_DATA_HOME=str(self.home / "data"),
            GIT_CONFIG_GLOBAL=str(self.home / ".gitconfig"),
            GIT_CONFIG_NOSYSTEM="1",
            DOTFILES_SELF_UPDATED="",
        )

    def write(self, path, content="existing", executable=False):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        if executable:
            path.chmod(0o755)

    def run_code(self, code):
        # Keep production shell options/traps, but never assign the real HOME.
        prelude = SOURCE.split("export DOTFILES=", 1)[0]
        script = prelude + "\n" + section("Helper functions") + "\n" + code
        script = script.replace("${HOME}", "${INSTALL_TEST_HOME}").replace(
            "$HOME", "$INSTALL_TEST_HOME"
        )
        return subprocess.run(
            ["/bin/bash", "-c", script],
            env=self.env,
            cwd=self.root,
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
        )

    def git(self, *args, cwd=None):
        return subprocess.check_output(
            [
                "git",
                "-c",
                "user.name=Installer Test",
                "-c",
                "user.email=installer@example.invalid",
                *args,
            ],
            cwd=cwd or self.repo,
            env=self.env,
            text=True,
            stderr=subprocess.PIPE,
        ).strip()

    def git_fixture(self):
        self.git("init", "-b", "main")
        self.write(self.repo / "tracked", "base")
        self.git("add", "tracked")
        self.git("commit", "-m", "base")
        remote = self.root / "remote.git"
        self.git("clone", "--bare", str(self.repo), str(remote))
        self.git("remote", "add", "origin", str(remote))
        return remote

    def test_existing_git_config_gets_include_once_and_preserves_local_override(self):
        self.write(self.home / ".gitconfig", "[user]\n name = Local User\n")
        self.write(self.repo / "git/.gitconfig", "[user]\n name = Base User\n")
        for name in (".gitconfig_personal", ".gitconfig_company", ".gitignore_global"):
            self.write(self.repo / "git" / name, "")
        code = 'git() { if [ "$1" = lfs ]; then return 0; fi; command git "$@"; }\n'
        code += section("Install global Git configuration")
        for _ in range(2):
            result = self.run_code(code)
            self.assertEqual(result.returncode, 0, result.stderr)
        config = self.home / ".gitconfig"
        self.assertIn("[include]", config.read_text())
        includes = self.git(
            "config", "--file", str(config), "--get-all", "include.path"
        )
        self.assertEqual(len(includes.splitlines()), 1)
        self.assertEqual(
            self.git("config", "--file", str(config), "user.name"), "Local User"
        )
        # Includes precede the host layer so local overrides retain precedence.
        self.assertLess(
            config.read_text().index("[include]"), config.read_text().index("[user]")
        )

    def test_link_failure_is_not_success(self):
        self.write(self.repo / "source")
        result = self.run_code(
            'ln() { return 42; }\nlink_file "$DOTFILES/source" "$INSTALL_TEST_HOME/target"'
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("✓ target", result.stdout)

    def test_backup_failure_preserves_target(self):
        self.write(self.repo / "source")
        self.write(self.home / "target", "keep me")
        result = self.run_code(
            'mv() { return 42; }\nlink_file "$DOTFILES/source" "$INSTALL_TEST_HOME/target"'
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.home / "target").read_text(), "keep me")

    def test_missing_source_is_failure(self):
        result = self.run_code(
            'link_file "$DOTFILES/missing" "$INSTALL_TEST_HOME/target"'
        )
        self.assertNotEqual(result.returncode, 0)

    def test_xdg_config_links_are_created_in_requested_root(self):
        for name in ("nvim", "ghostty", "kitty", "yazi"):
            (self.repo / ".config" / name).mkdir(parents=True)
        result = self.run_code(section("Link .config directories"))
        self.assertEqual(result.returncode, 0, result.stderr)
        for name in ("nvim", "ghostty", "kitty", "yazi"):
            self.assertTrue((self.home / "xdg" / name).is_symlink())

    def test_nvim_failure_preserves_data_and_does_not_mark_success(self):
        old_paths = [
            ".local/share/nvim/user",
            ".local/state/nvim/session",
            ".cache/nvim/cache",
        ]
        for path in old_paths:
            self.write(self.home / path)
        result = self.run_code(
            "nvim() { return 42; }\n" + section("Neovim / LazyVim setup")
        )
        for path in old_paths:
            self.assertTrue((self.home / path).exists(), path)
            self.assertEqual((self.home / path).read_text(), "existing")
        self.assertFalse((self.home / ".local/share/nvim/.lazyvim-installed").exists())
        self.assertFalse((self.home / "data/nvim/.lazyvim-installed").exists())
        self.assertNotIn("✓ LazyVim plugins installed", result.stdout)

    def test_nvim_success_uses_xdg_data_root(self):
        result = self.run_code(
            "nvim() { return 0; }\n" + section("Neovim / LazyVim setup")
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.home / "data/nvim/.lazyvim-installed").exists())

    def test_nvim_setup_keeps_tracked_lockfile_and_restores_plugins(self):
        # lazy.nvim rewrites the tracked lazy-lock.json while installing, which
        # left the checkout dirty so the next self-update refused to run.
        lock = self.repo / ".config/nvim/lazy-lock.json"
        self.write(lock, "original")
        code = (
            'nvim() { printf "%s\\n" "$@" >> "$INSTALL_TEST_HOME/nvim-args"; '
            'case "$*" in *restore*) ;; '
            '*) echo clobbered > "$DOTFILES/.config/nvim/lazy-lock.json" ;; esac; }\n'
        )
        result = self.run_code(code + section("Neovim / LazyVim setup"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(lock.read_text(), "original")
        args = (self.home / "nvim-args").read_text()
        self.assertIn("Lazy! restore", args)
        self.assertNotIn("Lazy! sync", args)
        self.assertNotIn("Lazy! update", args)
        # `Lazy! clean` rewrites the lockfile from the installed commits, so a
        # restore after it would pin plugins to whatever pass 1 cloned.
        self.assertLess(args.index("Lazy! restore"), args.index("Lazy! clean"))

    def test_nvim_install_failure_keeps_lockfile_still_restores_and_fails(self):
        # Pass 1 failing must not skip the restore pass or count as success.
        lock = self.repo / ".config/nvim/lazy-lock.json"
        self.write(lock, "original")
        code = (
            'nvim() { printf "%s\\n" "$@" >> "$INSTALL_TEST_HOME/nvim-args"; '
            'case "$*" in *restore*) return 0 ;; esac; '
            'echo clobbered > "$DOTFILES/.config/nvim/lazy-lock.json"; return 42; }\n'
        )
        result = self.run_code(code + section("Neovim / LazyVim setup"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(lock.read_text(), "original")
        self.assertIn("Lazy! restore", (self.home / "nvim-args").read_text())
        self.assertNotIn("✓ LazyVim plugins installed", result.stdout)
        self.assertFalse((self.home / "data/nvim/.lazyvim-installed").exists())

    @unittest.skipUnless(
        shutil.which("nvim"), "Neovim required for real exit-code regression"
    )
    def test_real_nvim_missing_lazy_does_not_mark_success(self):
        # Real Neovim normally exits 0 even when :Lazy is an unknown command.
        code = 'nvim() { command nvim -u NONE -i NONE "$@"; }\n'
        result = self.run_code(code + section("Neovim / LazyVim setup"))
        self.assertFalse((self.home / "data/nvim/.lazyvim-installed").exists())
        self.assertNotIn("✓ LazyVim plugins installed", result.stdout)

    def test_mise_activation_failure_stops_downstream(self):
        code = "mise() { return 42; }\nnpm() { echo WRONG_NPM_RAN; }\n"
        result = self.run_code(
            code + section("Install LSP server binaries (npm-based)")
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("WRONG_NPM_RAN", result.stdout)

    def test_tpm_sees_repository_tmux_config(self):
        self.write(self.repo / ".tmux.conf", "set -g @plugin 'example/plugin'\n")
        self.write(
            self.home / ".tmux/plugins/tpm/bin/install_plugins",
            '#!/bin/bash\ntest -L "$INSTALL_TEST_HOME/.tmux.conf"\n',
            executable=True,
        )
        result = self.run_code(section("Tmux Plugin Manager"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.home / ".tmux.conf").is_symlink())

    def test_self_update_rejects_working_branch(self):
        self.git_fixture()
        self.git("checkout", "-b", "feature")
        result = self.run_code(section("Update dotfiles itself"))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.git("branch", "--show-current"), "feature")

    def test_self_update_rejects_dirty_checkout(self):
        self.git_fixture()
        self.write(self.repo / "tracked", "local edits")
        result = self.run_code(section("Update dotfiles itself"))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.repo / "tracked").read_text(), "local edits")

    def test_self_update_failure_stops_installation(self):
        self.git_fixture()
        self.git("remote", "set-url", "origin", str(self.root / "absent.git"))
        result = self.run_code(
            section("Update dotfiles itself") + "\necho DOWNSTREAM_RAN\n"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("DOWNSTREAM_RAN", result.stdout)

    def test_self_update_fast_forwards_and_executes_new_script_once(self):
        remote = self.git_fixture()
        publisher = self.root / "publisher"
        self.git("clone", str(remote), str(publisher))
        self.write(
            publisher / "install.sh",
            '#!/bin/bash\ntest "$DOTFILES_SELF_UPDATED" = 1 || exit 3\nprintf "%s" "$1" > "$DOTFILES/reexecuted"\n',
        )
        self.git("add", "install.sh", cwd=publisher)
        self.git("commit", "-m", "new installer", cwd=publisher)
        self.git("push", "origin", "main", cwd=publisher)
        result = self.run_code(
            "set -- preserved-argument\n"
            + section("Update dotfiles itself")
            + "\necho OLD_SCRIPT_CONTINUED\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.repo / "reexecuted").read_text(), "preserved-argument")
        self.assertNotIn("OLD_SCRIPT_CONTINUED", result.stdout)

    def test_self_update_divergence_preserves_local_commit(self):
        remote = self.git_fixture()
        publisher = self.root / "publisher"
        self.git("clone", str(remote), str(publisher))
        self.write(publisher / "upstream", "remote commit")
        self.git("add", "upstream", cwd=publisher)
        self.git("commit", "-m", "upstream", cwd=publisher)
        self.git("push", "origin", "main", cwd=publisher)
        self.write(self.repo / "local", "local commit")
        self.git("add", "local")
        self.git("commit", "-m", "local")
        before = self.git("rev-parse", "HEAD")
        # Host preferences must not turn self-update into a rebase/autostash.
        self.git("config", "pull.rebase", "true")
        result = self.run_code(section("Update dotfiles itself"))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.git("rev-parse", "HEAD"), before)
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_optional_failure_runs_remaining_steps_and_returns_partial(self):
        result = self.run_code(
            'run_optional "broken dependency" /usr/bin/false\n'
            'printf kept-going > "$INSTALL_TEST_HOME/continued"\n'
            + section("Installation summary")
        )
        self.assertEqual((self.home / "continued").read_text(), "kept-going")
        self.assertEqual(result.returncode, 2)
        self.assertIn("broken dependency", result.stderr)
        self.assertNotIn("✅", result.stdout)

    def test_optional_success_returns_complete(self):
        result = self.run_code(
            'run_optional "dependency" /usr/bin/true\n'
            + section("Installation summary")
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("✅", result.stdout)

    def test_required_failure_stops_before_summary(self):
        result = self.run_code("/usr/bin/false\n" + section("Installation summary"))
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("✅", result.stdout)

    def test_existing_directory_is_backed_up_before_link_and_rerun(self):
        self.write(self.home / "target/precious", "preserve")
        (self.repo / "source").mkdir()
        for _ in range(2):
            result = self.run_code(
                'link_file "$DOTFILES/source" "$INSTALL_TEST_HOME/target"'
            )
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.home / "target").is_symlink())
        backups = list(self.home.glob("target.backup.*/target/precious"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(), "preserve")

    def test_invalid_git_config_is_not_overwritten(self):
        original = "[invalid syntax\n"
        self.write(self.home / ".gitconfig", original)
        result = self.run_code(section("Install global Git configuration"))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.home / ".gitconfig").read_text(), original)

    def test_claude_download_failure_is_not_success(self):
        code = """command() {
            if [ "$1" = -v ] && [ "$2" = claude ]; then return 1; fi
            builtin command "$@"
        }
        curl() { return 22; }
        """ + section("Install Claude Code (native binary)")
        result = self.run_code(code)
        self.assertNotIn("✓ Claude Code installed", result.stdout)
        self.assertNotEqual(result.returncode, 0)

    def test_full_installer_with_external_commands_isolated_can_run_twice(self):
        # Exercise section ordering and errexit across the entire script. Package
        # managers/installers are no-ops; links, backups and Git config are real.
        for directory in (
            ".config/nvim",
            ".config/ghostty",
            ".config/kitty",
            ".config/yazi",
            ".claude/hooks",
            ".claude/output-styles",
            ".claude/rules",
            ".claude/skills",
            ".codex/skills",
            ".codex/hooks",
            ".codex/rules",
            ".gemini/antigravity-cli/hooks",
        ):
            (self.repo / directory).mkdir(parents=True, exist_ok=True)
        for filename in (
            ".zshenv",
            ".zshrc",
            ".zprofile",
            ".vimrc",
            ".tmux.conf",
            "git/.gitconfig_personal",
            "git/.gitconfig_company",
            "git/.gitignore_global",
            "scripts/admin-api-token.sh",
            ".claude/settings.json",
            ".claude/CLAUDE.md",
            ".claude/spinner-tips.json",
            ".claude/docs/working-style.md",
            ".codex/config.toml.example",
            ".codex/config/global.json",
            ".codex/AGENTS.md",
            ".gemini/antigravity-cli/settings.json",
            ".gemini/antigravity-cli/mcp_config.json",
            ".gemini/antigravity-cli/hooks.json",
            ".config/karabiner/my_custom_key.json",
            ".config/ruff/ruff.toml",
            ".config/zed/settings.json",
        ):
            self.write(self.repo / filename, "")
        for filename in (".claude/setup-mcp.sh", ".codex/setup-mcp.sh"):
            self.write(self.repo / filename, "#!/bin/bash\nexit 0\n", executable=True)
        for directory in (
            ".oh-my-zsh/custom/plugins/zsh-syntax-highlighting",
            ".oh-my-zsh/custom/plugins/zsh-autosuggestions",
            ".oh-my-zsh/custom/plugins/zsh-completions",
            ".oh-my-zsh/custom/plugins/alias-tips",
            ".oh-my-zsh/custom/plugins/you-should-use",
            "fzf-git.sh",
        ):
            (self.home / directory).mkdir(parents=True, exist_ok=True)
        self.write(self.home / ".oh-my-zsh/themes/dracula.zsh-theme", "")
        self.write(
            self.home / ".tmux/plugins/tpm/bin/install_plugins",
            '#!/bin/bash\ntest -L "$INSTALL_TEST_HOME/.tmux.conf"\n',
            executable=True,
        )
        self.write(self.home / ".codex/config.toml", "# keep runtime state\n")
        fake_bin = self.root / "bin"
        for name in (
            "xcode-select",
            "brew",
            "agy",
            "mise",
            "uv",
            "poetry",
            "npm",
            "codex",
            "claude",
            "ya",
            "pre-commit",
            "nvim",
            "chsh",
            "git-lfs",
        ):
            self.write(fake_bin / name, "#!/bin/bash\nexit 0\n", executable=True)
        # A surprise download/clone must fail, never reach a network installer.
        self.write(fake_bin / "curl", "#!/bin/bash\nexit 99\n", executable=True)
        real_git = shutil.which("git")
        self.write(
            fake_bin / "git",
            '#!/bin/bash\ncase "$1" in lfs) exit 0;; clone) exit 99;; esac\n'
            f'exec "{real_git}" "$@"\n',
            executable=True,
        )
        self.env["PATH"] = f"{fake_bin}:/usr/bin:/bin"
        for _ in range(2):
            result = self.run_code(SOURCE)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(
            (self.home / ".codex/config.toml").read_text(), "# keep runtime state\n"
        )
        self.assertTrue((self.home / "xdg/nvim").is_symlink())


if __name__ == "__main__":
    unittest.main()
