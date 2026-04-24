# AGENTS.md

## Project Invariants

- **Role Name:** `ea31337.mt_runner`
- **Primary Purpose:** MetaTrader runner (MT4/MT5) for Ansible.
- **Key Technologies:** Ansible, Wine, MetaTrader, Docker, Molecule.

## Repository Layout

| File/Directory | Description |
| --- | --- |
| `tasks/` | Main Ansible tasks for the role |
| `molecule/default/` | Default Molecule scenario for testing |
| `molecule/resources/playbooks/Dockerfile.j2` | NixOS container build template |
| `requirements.yml` | Ansible Galaxy collection dependencies |
| `.pre-commit-config.yaml` | Pre-commit hooks (yamllint, ansible-lint, j2lint, etc.) |
| `.github/prompts/molecule-test.prompt.md` | Step-by-step Molecule test runner prompt |
| `.ansible-lint` | Ansible-lint configuration |
| `.yamllint` | YAML lint rules (max line length 120) |
| `.markdownlint.yaml` | Markdown lint rules (max line length 120) |

## Development Workflows

### Testing Workflows

When asked to run molecule test, follow the step-by-step instructions in
[`.github/prompts/molecule-test.prompt.md`](.github/prompts/molecule-test.prompt.md).

```bash
# Full test suite (all platforms)
molecule test
```

### Troubleshooting Molecule

> Alpine container fails with TLS/SSL errors

- Root cause: Missing or outdated CA certificates in the environment.
- Fix: Ensure `ca-certificates` are updated or use the `create.yml` proxy CA discovery.

> NixOS container fails with `path escapes from parent`

- Root cause: Symlinks for `/etc/passwd` or `/etc/group` pointing outside build context.
- Fix: Use `realpath --relative-to` in `Dockerfile.j2` to make them relative.

> Molecule Docker driver fails with broken conditionals

- Root cause: Use of `lookup('env', 'HOME')` or similar in playbooks.
- Fix: Enable `allow_broken_conditionals: true` in `molecule.yml`.

## Agent Directives

- MUST use FQCN for all modules (`ansible.builtin.*`, `community.general.*`).
- MUST keep YAML keys sorted alphabetically in config files when possible.
- MUST ensure idempotency in all Ansible tasks.
- MUST wrap lines at 120 characters (YAML and Markdown).
- MUST end files with a newline character.
- MUST use `true`/`false` for truthy values (not `yes`/`no`).
- MUST run `yamllint .` and `ansible-lint` before committing YAML changes.
- NEVER mock roles or modules, or use `exclude_paths` for `molecule/` and `tests/` as a workaround for issues.
- NEVER hardcode sensitive information; use variables.
- NEVER remove or modify unrelated tests.
- NEVER use `git add .` without verifying staged files.
- On variable changes, update both `defaults/main.yml` and `README.md`.

## Agent Directives (Contract Style)

- **NEVER** mock roles or modules, or use `exclude_paths` for `molecule/` and `tests/` as a workaround for issues.
- All issues **MUST** be resolved correctly at the root cause.
- Adhere strictly to project conventions and established standards.

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

### Running Tests

```bash
# Install dependencies first
pip install -r .devcontainer/requirements.txt
ansible-galaxy role install -r requirements.yml --force
ansible-galaxy collection install -r requirements.yml -p collections

# Full test suite (all platforms)
molecule test

# Single scenario
molecule test -s default

# Syntax check only (fast validation)
molecule syntax -s default
```

## References

For project overview and install instructions, see [README.md](README.md).
