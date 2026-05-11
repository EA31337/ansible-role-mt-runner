# AGENTS.md

Persistent context for autonomous agents working on this Ansible role.

For project overview and install instructions, see [README.md](README.md).

## Setup & Environment Invariants

- Ansible role: `ea31337.mt_runner`
- Supported OS: Debian/Ubuntu
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
| `docs/FACTS.mmd` | Project canonical facts (Mindmap) |
| `docs/FLOWS.mmd` | Project flow logic (Flowchart) |
| `molecule/default/molecule.yml` | Default Molecule scenario config |
| `molecule/default/converge.yml` | Converge playbook (all scenarios) |
| `molecule/default/create.yml` | Custom Docker create (proxy CA injection) |
| `molecule/default/destroy.yml` | Custom Docker destroy playbook |
| `molecule/default/prepare.yml` | Container preparation (sudo, Python, certs) |
| `molecule/default/verify.yml` | Verification playbook |
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
| `debian-latest` | `ghcr.io/ea31337/ansible-role-xvfb:1.0.4-debian-latest` | Wine/Xvfb-enabled image |
| `ubuntu-jammy` | `ghcr.io/ea31337/ansible-role-xvfb:1.0.4-ubuntu-jammy` | Wine/Xvfb-enabled image |
| `ubuntu-noble` | `ghcr.io/ea31337/ansible-role-xvfb:1.0.4-ubuntu-noble` | Wine/Xvfb-enabled image |

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
molecule test -s default --platform-name ubuntu-noble

# Step-by-step debugging (useful for troubleshooting)
molecule destroy -s default              # clean up any leftover state
molecule create -s default               # build images + start containers
molecule prepare -s default              # install Python, sudo, CA certs
molecule converge -s default             # run the role
molecule idempotence -s default          # verify idempotency (no changes)
molecule verify -s default               # run verification playbook
molecule destroy -s default              # clean up

# Syntax check only (fast validation)
molecule syntax -s default
```

### Step-by-step Testing With Timeout

For CI or automated environments, use timeouts:

```bash
# Test a single platform with timeout (15 minutes)
timeout 900 molecule test -s default --platform-name ubuntu-noble

# If converge fails, debug interactively:
molecule create -s default --platform-name ubuntu-noble
molecule converge -s default --platform-name ubuntu-noble
# (inspect container state, then clean up)
molecule destroy -s default
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

### GitHub Actions Molecule report step fails with summary size limit

- **Root cause**: GitHub job summaries are capped at 1 MiB, but full Molecule HTML-to-Markdown conversions can exceed it.
- **Fix**: Upload full Molecule HTML reports as workflow artifacts and append only a concise filtered summary
  (e.g., Play Recap, errors, and warnings) to `$GITHUB_STEP_SUMMARY`.

### Molecule report `EACCES: permission denied`

- **Root cause**: The report file generated by `gofrolist/molecule-action` is owned by root with restricted permissions
  because it is created inside a Docker container.
- **Fix**: Run `sudo chown "$USER":"$USER"` on the report file before attempting to read it (for summary) or upload it.

### molecule-docker broken conditionals deprecation

- **Root cause**: `molecule-docker` create/destroy playbooks use patterns that trigger deprecation warnings
  in newer `ansible-core`.
- **Workaround**: Scenario configs set `allow_broken_conditionals: true` in `provisioner.config_options.defaults`.

### MetaTrader setup download fails

- **Root cause**: `download.mql5.com` blocked by network policy or DNS failure inside Docker.
- **Fix**: Ensure `download.mql5.com` is accessible. Setup URL is configurable via `metatrader_setup_url`.

### Platform installer shows "Sorry, something went wrong"

- **Root cause**: The setup bootstrapper is a small stub that downloads platform files at runtime.
  If CDN servers are blocked, the installer fails.
- **Fix**: Ensure all hosts in the [Required Hosts](#required-hosts) table are allowlisted.

### Debugging the MT5 installer

When the installer hangs or fails inside a container, use these steps:

```bash
# 1. Install xdotool in the container
docker exec CONTAINER apt-get install -y -q xdotool

# 2. List all visible X windows
docker exec -e DISPLAY=:0 CONTAINER \
  bash -c 'for wid in $(xdotool search --onlyvisible --name "." 2>/dev/null); do
    echo "Window $wid: $(xdotool getwindowname $wid 2>/dev/null)"
  done'

# 3. Take a screenshot of the X display
docker exec CONTAINER apt-get install -y -q imagemagick
docker exec -e DISPLAY=:0 CONTAINER import -window root /tmp/screen.png
docker cp CONTAINER:/tmp/screen.png ./screen.png

# 4. Check running Wine/MT5 processes
docker exec CONTAINER ps aux | grep -E "mt5|terminal|wine" | grep -v defunct
```

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

### Editing Files

- Max line length: 120 characters (enforced by `.yamllint` and `.markdownlint.yaml`).
- YAML indentation: 2 spaces.
- End all files with a newline.
- Keep lists and keys in lexicographical order when possible.

### Adding or Modifying Workflows

- Workflows live in `.github/workflows/`.
- Use `actionlint` to validate workflow syntax.
- `paths-ignore` excludes `**.md`, `**.cfg`, `.*`, `LICENSE` from triggers.

## Firewall Issues

If network requests fail during molecule tests:

- Refer to <https://gh.io/copilot/firewall-config> for agent firewall setup.
- Do not work around blocked URLs; request allowlisting instead.

### Required Hosts

| Host | Purpose |
| ---- | ------- |
| `cdn.mql5.com` | CDN (MT5 platform files) |
| `dl.winehq.org` | WineHQ APT repository |
| `download.mql5.com` | MetaTrader setup executable download |
| `galaxy.ansible.com` | Ansible Galaxy collections |
| `github.com` | Dependency downloads |
| `mt5-trade.metaquotes.net` | Trade server (installer backend) |
| `raw.githubusercontent.com` | Static asset downloads |
| `trade.mql5.com` | Trade server (registration) |
| `web.archive.org` | Fallback download mirror |
| `www.mql5.com` | Main website (installer backend) |

## References

- Project documentation: [README.md](README.md)
- Project canonical facts: [docs/FACTS.mmd](docs/FACTS.mmd)
- Project flow logic: [docs/FLOWS.mmd](docs/FLOWS.mmd)
- Org baseline: <https://github.com/Cogni-AI-OU/.github/blob/main/AGENTS.md>
- Agents.md standard: <https://agents.md/>
