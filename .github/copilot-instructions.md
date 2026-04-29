# Copilot Instructions for ansible-role-mt-runner

You are expected to be an expert in:

- Ansible
- Python
- Jinja2
- Molecule
- Linux (Debian/Ubuntu)
- YAML

## Code Standards

- Avoid writing trailing whitespace
- Follow PEP 8 for Python
- Include docstrings and type hints where applicable
- Maintain consistent YAML indentation
- Optimize for readability first, performance second
- Prefer modular, DRY approaches and list comprehensions when appropriate
- Use environment variables for configuration, never hardcode sensitive info
- Write clean, documented, error-handling code with appropriate logging

## General Approach

- Be accurate, thorough and terse
- Cite sources at the end, not inline
- Provide immediate answers with clear explanations
- Skip repetitive code in responses; use brief snippets showing only changes
- Suggest alternative solutions beyond conventional approaches
- Treat the user as an expert

## Ansible Guidelines

- Ensure idempotency in all tasks
- Ensure indentation is correct, especially for YAML files
- Follow standard role structure: tasks/, handlers/, templates/, defaults/, meta/
- Use ansible-lint and write Molecule tests for verification
- Use descriptive task names and include helpful comments

## Ansible Linting

Ensure enforcing the following rules:

- fqcn[keyword]: Avoid `collections` keyword by using FQCN for all plugins, modules, roles and playbooks

## Formatting Guidelines

### YAML

Follow the YAML rules defined in `.yamllint`:

- yaml[empty-lines]: Avoid too many blank lines
- yaml[indentation]: Avoid wrong indentation
- yaml[line-length]: No long lines (max. 120 characters)
- yaml[new-line-at-end-of-file]: Enforce new line character at the end of file
- yaml[truthy]: Truthy value should be one of [false, true]
- Ensure items are in lexicographical order when possible.
- When writing inline code, add a new line at the end to maintain proper
  indentation

To verify locally, run `yamllint .` or `pre-commit run yamllint -a`.

### Markdown

Follow the Markdown rules defined in `.markdownlint.yaml`:

- MD013: Line length max 120 characters
- MD033: Inline HTML allowed only for `<details>` elements
- MD046: Consistent code block style

To verify locally, run `pre-commit run markdownlint -a`.

## Project Specifics

This role installs and runs trading platform on Debian/Ubuntu:

- **Debian/Ubuntu**: Uses apt package manager

### Key Variables

Variables are defined in `defaults/main.yml` (user-facing) and
`vars/main.yml` (internal).

Notes:

- On variable changes, update `defaults/main.yml` and `README.md` accordingly.

### Devcontainer Guidance

Project utilizes Codespaces with config at `.devcontainer/devcontainer.json`
and requirements at `.devcontainer/requirements.txt`.

- Treat the repository devcontainer as the default controller environment.
- Keep controller dependency installation in the devcontainer configuration
  so Molecule scenarios can assume those tools are already available.
- If dependencies are missing, update `.devcontainer/requirements.txt`
  instead of adding per-run install steps.

## Testing Approach

- Use Molecule with Docker driver
- GitHub Actions run pre-commit checks (`.pre-commit-config.yaml`) and
  Molecule (`molecule/`)
- Service management uses supervisord
- Formatting rules: `.yamllint` (YAML) and `.markdownlint.yaml` (Markdown)

### Running Tests

```bash
# Full molecule test (all scenarios)
molecule test

# Single scenario
molecule test -s default

# Individual steps
molecule create -s default
molecule converge -s default
molecule verify -s default
molecule destroy -s default

# Linting
yamllint .
ansible-lint
pre-commit run -a
```
