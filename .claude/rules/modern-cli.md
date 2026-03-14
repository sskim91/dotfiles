# Modern CLI Tools

When using Bash tool, prefer these modern alternatives:

| Instead of | Use | Example |
|-----------|-----|---------|
| `find` | `fd` | `fd -e py` (respects .gitignore) |
| `tree` | `eza --tree` | `eza --tree --level=2 --group-directories-first` |
| `du` | `dust` | `dust -d 2` (visual directory sizes, depth 2) |
| `df` | `duf` | `duf` (disk/partition overview) |
| `sed` | `sd` | `sd 'from' 'to' file` (multi-file: `fd -e py -x sd 'old' 'new'`) |
| `curl` (API) | `http` | `http GET https://api.example.com/users` (httpie) |
| `ps aux \| grep` | `procs` | `procs python` (keyword is positional arg) |
| `time` | `hyperfine` | `hyperfine 'cmd1' 'cmd2'` (statistical benchmark) |
| `dig` | `doggo` | `doggo example.com A AAAA MX` (clean DNS lookup) |

## JSON/YAML/TOML Processing

- `jq` for JSON: `jq '.key' file.json`
- `yq` for structured data: supports YAML, JSON, TOML, XML, CSV, TSV, HCL, INI, properties (auto-detects by extension)
  - Query: `yq '.key' file.yaml` / `yq '.section.key' config.toml`
  - Format conversion: `yq -o json '.' config.toml` (TOML→JSON)
  - Note: TOML output (`-o toml`) requires root to be a mapping — use `-o json` or `-o yaml` for scalar/array results

## fd over find

- Respects `.gitignore` automatically — use `-I` to bypass
- `-H` shows hidden files, `-I` shows gitignored files
- Simpler syntax: `fd pattern` vs `find . -name "pattern"`

```bash
fd -e py                       # find *.py files
fd -HI 'DS_Store' -x rm        # find and delete .DS_Store (-H hidden, -I no-ignore)
fd --changed-within 1h         # files modified in last 1 hour
```

## sd + fd for bulk replace

`sd` is most useful combined with `fd` for multi-file operations:

```bash
# replace across all .py files
fd -e py -x sd 'old_func' 'new_func'

# replace in specific directory
fd -e yaml . k8s/ -x sd 'v1.0' 'v2.0'
```

## httpie over curl

In non-interactive environments (like Bash tool), use `--ignore-stdin` for requests with body data:

```bash
# GET with auth header
http GET https://api.example.com/users Authorization:"Bearer $TOKEN"

# POST with JSON body (--ignore-stdin required in non-interactive contexts)
http --ignore-stdin POST https://api.example.com/users name=john email=john@example.com
```

## hyperfine for benchmarks

```bash
# compare two commands with statistical analysis
hyperfine 'fd -e py' 'find . -name "*.py"'

# with warmup runs and JSON export
hyperfine --warmup 3 --export-json result.json 'cmd1' 'cmd2'
```

## doggo for DNS

```bash
# query multiple record types
doggo example.com A AAAA MX

# specific DNS server
doggo example.com A @8.8.8.8

# JSON output for scripting
doggo example.com A --json
```

## Notes

- Built-in tools (Read, Grep, Glob, Edit) are ALWAYS preferred over Bash equivalents
- These rules only apply when Bash is genuinely needed (builds, git, system commands, piped processing)
