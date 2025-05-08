# Ansible Role: MT Runner

[![CodeRabbit PR Reviews](https://img.shields.io/coderabbit/prs/github/EA31337/ansible-role-mt-runner?utm_source=oss&utm_medium=github&utm_campaign=EA31337%2Fansible-role-mt-runner&labelColor=171717&color=FF570A&link=https%3A%2F%2Fcoderabbit.ai&label=CodeRabbit+PR+Reviews)](https://github.com/EA31337/ansible-role-mt-runner/pulls)
[![License](https://img.shields.io/badge/license-MIT-brightgreen.svg)](LICENSE)

Ansible role to run tests using MT platform.

## Requirements

This role requires:

- Ansible
- Python
- Administrative/root access on target hosts
- One of the following operating systems:
  - Alpine Linux
  - Debian/Ubuntu
  - NixOS or systems with Nix package manager

## Install

To install this role, you can use the following terminal command:

```shell
ansible-galaxy install git+https://github.com/EA31337/ansible-role-mt-runner.git
```

## Role Variables

For available variables,
check [`defaults/main.yml`](defaults/main.yml).

## Testing

### Docker

To test on Docker containers, run:

```shell
ansible-playbook -i tests/inventory/docker-containers.yml tests/playbooks/docker-containers.yml
```

### Molecule

To test using Molecule, run:

```shell
molecule test
```

## License

GNU GPL v3

See: [LICENSE](./LICENSE)
