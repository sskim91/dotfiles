# Git Configuration

`includeIf` 기반 디렉터리별 identity 전환은 `.gitconfig`에 그대로 있다. 이 문서는 코드만 보고는 알 수 없는 두 계정 운용 절차를 기록한다.

## Multi-Account GitHub (Personal + Company)

Personal GitHub uses HTTPS via `gh` CLI (active account = `sskim91`). Company GitHub uses SSH with a host alias so a second account can authenticate without `gh auth switch`:

- Generate company key: `ssh-keygen -t ed25519 -C "<company-email>" -f ~/.ssh/company-git`
- Register `~/.ssh/company-git.pub` on the company GitHub account
- Add `Host github.com-company` block to `~/.ssh/config` (see `.ssh-config.example`)
- Clone company repos with the aliased URL: `git@github.com-company:<org>/<repo>.git`
- Place company repos under `~/work/` — `includeIf` then auto-applies company author identity

`includeIf` handles **author email** only; SSH host alias handles **authentication**. Both layers are required for full automation (HTTPS+`gh` cannot do directory-based auth).

To add a new directory-based identity:
```gitconfig
# In .gitconfig
[includeIf "gitdir:~/new-path/"]
    path = .gitconfig_newname
```
