# Molecule Test Runner

Run all Molecule scenarios and report results as a table.

## Instructions

1. Install dependencies (if not already present):

   ```bash
   ansible-galaxy collection install -r requirements.yml
   ```

2. For each platform, run each Molecule step individually to isolate failures.
   Since Molecule runs all platforms together, if a single platform fails,
   comment it out in `molecule.yml` temporarily and re-run the step for the
   remaining platforms:

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
| `mt-runner-debian-latest` | `ghcr.io/ea31337/ansible-role-xvfb:1.0.4-debian-latest` | Uses `apt` |
| `mt-runner-ubuntu-jammy` | `ghcr.io/ea31337/ansible-role-xvfb:1.0.4-ubuntu-jammy` | Uses `apt` |
| `mt-runner-ubuntu-noble` | `ghcr.io/ea31337/ansible-role-xvfb:1.0.4-ubuntu-noble` | Uses `apt` |

Platform names are prefixed with the role name (`mt-runner-`) because Molecule's Docker
driver names each container exactly after its platform. Generic names such as
`debian-latest` would collide with concurrent Molecule runs of other roles.

## Results Template

Fill in each cell after running the tests.
Use PASS for pass, FAIL for fail, SKIP for skipped.

### Step-Level Results

| Platform | create | prepare | converge | idempotence | verify |
| --- | :---: | :---: | :---: | :---: | :---: |
| `mt-runner-debian-latest` | | | | | |
| `mt-runner-ubuntu-jammy` | | | | | |
| `mt-runner-ubuntu-noble` | | | | | |

## Troubleshooting

- If molecule-docker create/destroy fails with broken conditionals,
  ensure `allow_broken_conditionals: true` is set in `molecule.yml`
  under `provisioner.config_options.defaults`.
- Refer to [AGENTS.md](../../AGENTS.md) for the full troubleshooting matrix.
