# AGENTS.md

Persistent context for autonomous agents working on this Ansible role.

For project overview and install instructions, see [README.md](README.md).

## Setup & Environment Invariants

- Ansible role: `ea31337.mt_runner`
- Supported OS: Alpine, Debian/Ubuntu, NixOS (Nix)
- Driver: Docker (Molecule)
- Python 3.10+ required; install via `pip install -r .devcontainer/requirements.txt`
- Collections: `community.docker`, `community.general`, `ansible.posix`
- `community.docker` MUST be installed before Molecule can create/destroy
  containers.
- Install dependencies: `ansible-galaxy role install -r requirements.yml --force` and
  `ansible-galaxy collection install -r requirements.yml -p collections`

## Key Files & Context Injection

| Path | Purpose |
| ---- | ------- |
| `tasks/main.yml` | Role entry point; manages MetaTrader runner |
| `molecule/default/molecule.yml` | Default Molecule scenario config |
| `molecule/default/converge.yml` | Converge playbook (all scenarios) |
| `molecule/default/create.yml` | Custom Docker create (proxy CA injection) |
| `molecule/default/destroy.yml` | Custom Docker destroy playbook |
| `molecule/default/prepare.yml` | Container preparation (sudo, Python, certs) |
| `molecule/default/verify.yml` | Verification playbook |
| `molecule/resources/playbooks/Dockerfile.j2` | NixOS/Alpine container Dockerfile template |
| `requirements.yml` | Ansible Galaxy collection + role dependencies |
| `ansible.cfg` | Ansible configuration (collections_path, callbacks) |
| `.github/workflows/molecule.yml` | CI: Molecule test matrix |
| `.pre-commit-config.yaml` | Pre-commit hooks (yamllint, ansible-lint, etc.) |
| `.ansible-lint` | Ansible-lint configuration |
| `.yamllint` | YAML lint rules (max line length 120) |
| `.markdownlint.yaml` | Markdown lint rules (max line length 120) |

## Agent Directives

- MUST use FQCN for all modules (`ansible.builtin.*`, `community.general.*`).
- MUST keep YAML keys sorted alphabetically in config files when possible.
- MUST ensure idempotency in all Ansible tasks.
- MUST wrap lines at 120 characters (YAML and Markdown).
- MUST end files with a newline character.
- MUST use `true`/`false` for truthy values (not `yes`/`no`).
- MUST run `yamllint .` and `ansible-lint` before committing YAML changes.
- NEVER hardcode sensitive information; use variables.
- NEVER remove or modify unrelated tests.
- NEVER use `git add .` without verifying staged files.
- On variable changes, update both `defaults/main.yml` and `README.md`.

## Agent Directives (Contract Style)

- **NEVER** mock roles or modules, or use `exclude_paths` for `molecule/` and `tests/` as a workaround for issues.
- All issues **MUST** be resolved correctly at the root cause.
- Adhere strictly to project conventions and established standards.

## Project Invariants

- This project is an Ansible role for MetaTrader runner.
- It uses Molecule for testing and ansible-lint for linting.
- It depends on `community.docker` and `community.general` collections.

## Molecule Scenarios

| Scenario | Notes |
| -------- | ----- |
| `default` | Default MT runner setup tests |
| `mt4` | MT4 specific runner tests |
| `mt5-ea` | MT5 with EA specific tests |

### Platforms

| Container | Image | Notes |
| --------- | ----- | ----- |
| `alpine-latest` | `i386/alpine:latest` | Custom Dockerfile build |
| `debian-latest` | `debian:latest` | Standard image |
| `nixos-latest` | `nixos/nix:latest` | Custom Dockerfile build |
| `ubuntu-jammy` | `ubuntu:jammy` | Standard image |
| `ubuntu-noble` | `ubuntu:noble` | Standard image |
| `ubuntu-latest` | `ubuntu:latest` | Standard image |

### Running Tests

```bash
# Install dependencies first
pip install -r .devcontainer/requirements.txt
ansible-galaxy role install -r requirements.yml --force
ansible-galaxy collection install -r requirements.yml -p collections

# Full test (all scenarios)
molecule test

# Single scenario
molecule test -s default

# Single platform in a scenario
molecule test -s default --platform-name ubuntu-latest

# Syntax check only (fast validation)
molecule syntax -s default
```

## Testing & Verification Gates

- `molecule syntax` — YAML + playbook syntax validation
- `molecule converge` — full role execution on all containers
- `molecule idempotence` — re-run must produce zero changes
- `molecule verify` — asserts role functionality
- `yamllint .` — YAML lint (config: `.yamllint`)
- `ansible-lint` — Ansible best practices (config: `.ansible-lint`)
- `pre-commit run -a` — all pre-commit hooks

## Troubleshooting Matrix

### `community.docker.docker_container` module not found

- **Root cause**: `community.docker` collection not installed.
- **Fix**: Run `ansible-galaxy collection install -r requirements.yml`.

### NixOS Docker build SSL failures

- **Root cause**: Missing CA bundles break `nix-channel --update`.
- **Fix**: Custom `create.yml` injects host CA certificates.

### NixOS containerd symlink error

- **Root cause**: `path escapes from parent` due to absolute symlinks.
- **Fix**: Use `realpath --relative-to` in `Dockerfile.j2`.

## Common Tasks

### Before Each Commit

- Verify changes: `git diff --no-color`.
- NEVER use `git add .` without reviewing staged files.
- Run linters: `pre-commit run -a`.
- Run `molecule syntax` to catch playbook errors early.

### Linting and Validation

```bash
# All pre-commit checks
pre-commit run -a

# Individual checks
pre-commit run yamllint -a
pre-commit run ansible-lint -a
pre-commit run markdownlint -a
pre-commit run j2lint -a
pre-commit run actionlint -a
```

## References

- Project documentation: [README.md](README.md)
- Org baseline: <https://github.com/Cogni-AI-OU/.github/blob/main/AGENTS.md>
- Agents.md standard: <https://agents.md/>
