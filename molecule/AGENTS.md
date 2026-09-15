# Molecule Testing

Molecule scenarios, the platform matrix, how to run the tests, and Molecule-specific
troubleshooting for this role.

## Molecule Scenarios

| Scenario | Notes |
| -------- | ----- |
| `default` | Default MT runner setup tests |
| `mt4` | MT4 specific runner tests |
| `mt5-ea` | MT5 with EA specific tests |

### Platforms (all scenarios)

Each scenario (`default`, `mt4`, `mt5-ea`) defines the same three platforms:

| Container | Image | Notes |
| --------- | ----- | ----- |
| `mt-runner-default-debian-latest` | `ghcr.io/ea31337/ansible-role-xvfb:1.0.4-debian-latest` | Wine/Xvfb image |
| `mt-runner-default-ubuntu-jammy` | `ghcr.io/ea31337/ansible-role-xvfb:1.0.4-ubuntu-jammy` | Wine/Xvfb image |
| `mt-runner-default-ubuntu-noble` | `ghcr.io/ea31337/ansible-role-xvfb:1.0.4-ubuntu-noble` | Wine/Xvfb image |
| `mt-runner-mt4-debian-latest` | `ghcr.io/ea31337/ansible-role-xvfb:1.0.4-debian-latest` | Wine/Xvfb image |
| `mt-runner-mt4-ubuntu-jammy` | `ghcr.io/ea31337/ansible-role-xvfb:1.0.4-ubuntu-jammy` | Wine/Xvfb image |
| `mt-runner-mt4-ubuntu-noble` | `ghcr.io/ea31337/ansible-role-xvfb:1.0.4-ubuntu-noble` | Wine/Xvfb image |
| `mt-runner-mt5-ea-debian-latest` | `ghcr.io/ea31337/ansible-role-xvfb:1.0.4-debian-latest` | Wine/Xvfb image |
| `mt-runner-mt5-ea-ubuntu-jammy` | `ghcr.io/ea31337/ansible-role-xvfb:1.0.4-ubuntu-jammy` | Wine/Xvfb image |
| `mt-runner-mt5-ea-ubuntu-noble` | `ghcr.io/ea31337/ansible-role-xvfb:1.0.4-ubuntu-noble` | Wine/Xvfb image |

Platform names follow the `<role>-<scenario>-<platform>` convention (here
`mt-runner-<scenario>-`) because Molecule's Docker driver names each container exactly
after its platform. Generic names such as `debian-latest` would collide with
concurrent Molecule runs of other roles, and role-only names would collide across
scenarios of the same role.

### Running Tests

Molecule and Ansible are installed via the project `Pipfile`, so run every command through `pipenv`
(they are not on `PATH`).

```bash
# Install dependencies first
pip install -r .devcontainer/requirements.txt
ansible-galaxy role install -r requirements.yml --force
ansible-galaxy collection install -r requirements.yml -p collections

# Full test (all scenarios)
pipenv run molecule test

# Single scenario
pipenv run molecule test -s default

# Single platform in a scenario
pipenv run molecule test -s default --platform-name mt-runner-default-ubuntu-noble

# Step-by-step debugging (useful for troubleshooting)
pipenv run molecule destroy -s default              # clean up any leftover state
pipenv run molecule create -s default               # build images + start containers
pipenv run molecule prepare -s default              # install Python, sudo, CA certs
pipenv run molecule converge -s default             # run the role
pipenv run molecule idempotence -s default          # verify idempotency (no changes)
pipenv run molecule verify -s default               # run verification playbook
pipenv run molecule destroy -s default              # clean up

# Syntax check only (fast validation)
pipenv run molecule syntax -s default
```

### Step-by-step Testing With Timeout

For CI or automated environments, use timeouts:

```bash
# Test a single platform with timeout (15 minutes)
timeout 900 pipenv run molecule test -s default --platform-name mt-runner-default-ubuntu-noble

# If converge fails, debug interactively:
pipenv run molecule create -s default --platform-name mt-runner-default-ubuntu-noble
pipenv run molecule converge -s default --platform-name mt-runner-default-ubuntu-noble
# (inspect container state, then clean up)
pipenv run molecule destroy -s default
```

### Sandboxed / firewalled environments

Molecule defaults work on GitHub Actions runners with direct internet access. In sandboxed or
firewalled environments (no outbound NAT on the default Docker bridge, or a resolver that returns
non-routable IPv6 addresses), opt in with these environment variables:

- `MOLECULE_DOCKER_NETWORK=host` - Docker network used for both containers and image builds.
  Required where the default bridge has no outbound NAT.
- `MOLECULE_DOCKER_FORCE_IPV4=true` - prefer IPv4 for DNS resolution inside containers. Required
  where the resolver returns IPv6 addresses that are not routable.
- `MOLECULE_XVFB_DISPLAY_BASE=90` - assign a unique X display per host (base + host index).
  Required when containers share the host network namespace (`MOLECULE_DOCKER_NETWORK=host`) and
  the host already runs an X server on `:0`.

Example invocation:

```bash
MOLECULE_DOCKER_NETWORK=host MOLECULE_DOCKER_FORCE_IPV4=true MOLECULE_XVFB_DISPLAY_BASE=90 \
  pipenv run molecule test -s default
```

## Molecule Gates

- `pipenv run molecule syntax` - YAML + playbook syntax validation
- `pipenv run molecule converge` - full role execution on all containers
- `pipenv run molecule idempotence` - re-run must produce zero changes
- `pipenv run molecule verify` - asserts role functionality

## Troubleshooting Matrix

### Molecule prepare fails with DNS resolution errors

> `Temporary failure resolving 'deb.debian.org'` (or `azure.archive.ubuntu.com`), followed by
> `E: Unable to locate package python3` during the `prepare` step.

- **Root cause**: `docker0` has lost the `bridge` network's configured gateway address, so containers
  on the default bridge have no working gateway and cannot resolve DNS or reach the network.
- **Check**: `ip -4 addr show docker0` vs
  `docker network inspect bridge --format '{{range .IPAM.Config}}{{.Gateway}}{{end}}'`.
  If the gateway address is missing from `docker0`, this is the cause.
- **Fix (durable)**: `sudo systemctl restart docker` recreates `docker0` with the configured gateway.
  This restarts the daemon and stops any running containers.
- **Fix (non-disruptive, not persistent)**: `sudo ip addr add 172.17.0.1/16 dev docker0`
  (use the gateway reported by the check above).
- **Workaround (no sudo)**: run the tests on the host network, which bypasses the broken bridge.

```bash
MOLECULE_DOCKER_NETWORK=host \
MOLECULE_DOCKER_FORCE_IPV4=true \
MOLECULE_XVFB_DISPLAY_BASE=90 \
pipenv run molecule test
```

### `community.docker.docker_container` module not found

- **Root cause**: `community.docker` collection not installed.
- **Fix**: Run `ansible-galaxy collection install -r requirements.yml`.

### GitHub Actions Molecule report step fails with summary size limit

- **Root cause**: GitHub job summaries are capped at 1 MiB, but full Molecule HTML-to-Markdown conversions can exceed it.
- **Fix**: Upload full Molecule HTML reports as workflow artifacts and append only a concise filtered summary
  (e.g., Play Recap, errors, and warnings) to `$GITHUB_STEP_SUMMARY`.

### Molecule report `EACCES: permission denied`

- **Root cause**: The report file, `roles`, or `collections` directories generated by `gofrolist/molecule-action` are
  owned by root with restricted permissions because they are created inside a Docker container.
- **Fix**: Run `sudo chown -R "$USER":"$USER"` on the affected files and directories before cleanup or upload.

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
- **Fix**: Ensure all hosts in the [Required Hosts](../AGENTS.md#required-hosts) table are allowlisted.

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
