# AGENTS.md

This repository uses [Cogni AI](https://github.com/Cogni-AI-OU) agents to help maintain and develop the project.

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

### Running Tests

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

## References

For project overview and install instructions, see [README.md](README.md).
