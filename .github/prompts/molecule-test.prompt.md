# Molecule Test Runner

Run all Molecule scenarios and report results as a table.

## Instructions

1. Install dependencies (if not already present):

   ```bash
   ansible-galaxy collection install -r requirements.yml
   ```

2. For each platform, run each Molecule step individually
   to isolate failures. Since Molecule runs all platforms together,
   if a single platform fails (e.g., Alpine TLS in sandboxed
   environments), comment it out in `molecule.yml` temporarily and
   re-run the step for the remaining platforms:

   ```bash
   molecule destroy
   molecule create
   molecule converge
   molecule idempotence
   molecule verify
   molecule destroy
   ```

3. Record every step outcome (PASS pass, FAIL fail, SKIP skipped).

4. Report results in a **Step x Platform** table (see template below).

## Scenario

| Scenario | Notes |
| --- | --- |
| `default` | Basic mt_runner installation |

## Platforms

| Container | Image | Notes |
| --- | --- | --- |
| `alpine-latest` | `i386/alpine:latest` | 32-bit Alpine; uses `apk` |
| `debian-latest` | `debian:latest` | Uses `apt` |
| `nixos-latest` | `nixos/nix:latest` | Custom Dockerfile; uses `nix-env` |
| `ubuntu-jammy` | `ubuntu:jammy` | Uses `apt` |
| `ubuntu-noble` | `ubuntu:noble` | Uses `apt` |
| `ubuntu-latest` | `ubuntu:latest` | Uses `apt` |

## Results Template

Fill in each cell after running the tests.
Use PASS for pass, FAIL for fail, SKIP for skipped.

### Step-Level Results

| Platform | create | prepare | converge | idempotence | verify |
| --- | :---: | :---: | :---: | :---: | :---: |
| `alpine-latest` | | | | | |
| `debian-latest` | | | | | |
| `nixos-latest` | | | | | |
| `ubuntu-jammy` | | | | | |
| `ubuntu-noble` | | | | | |
| `ubuntu-latest` | | | | | |

## Troubleshooting

- If Alpine fails with TLS errors, check that `dl-cdn.alpinelinux.org`
  is reachable and CA certificates are valid in the Docker build context.
- If NixOS fails with SSL errors, check `Dockerfile.j2` CA cert injection
  and ensure `channels.nixos.org` is reachable.
- If NixOS fails with `path escapes from parent`, the `Dockerfile.j2`
  template should convert `/etc/passwd` and `/etc/group` symlinks to
  relative paths via `realpath --relative-to`.
- If molecule-docker create/destroy fails with broken conditionals,
  ensure `allow_broken_conditionals: true` is set in `molecule.yml`
  under `provisioner.config_options.defaults`.
- Refer to [AGENTS.md](../../AGENTS.md) for the full troubleshooting matrix.
