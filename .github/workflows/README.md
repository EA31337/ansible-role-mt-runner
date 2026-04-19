# GitHub Workflows

This directory contains GitHub Actions workflows for the project.

## Workflows

### Check Workflow

The `check.yml` workflow calls the reusable
[Check workflow](https://github.com/EA31337/.github/blob/master/.github/workflows/check.yml)
from the `EA31337/.github` repository. It runs on pull requests, pushes, and a
weekly schedule to ensure code quality and correctness.

Jobs (provided by the reusable workflow):

- **actionlint**: Validates GitHub Actions workflow files
- **link-checker**: Checks for broken links in Markdown files using Lychee
- **pre-commit**: Runs pre-commit hooks for code formatting and linting

### Cogni AI Agent Workflow

The `cogni-ai-agent.yml` workflow provides an integration with the
[Cogni AI Agent](https://github.com/Cogni-AI-OU/cogni-ai-agent-action)
for autonomous issue resolution and PR review.

It triggers on issue and pull request comments, as well as `workflow_dispatch`.
It utilizes the `Cogni-AI-OU/cogni-ai-agent-action` and allows specifying
various AI models to fulfill requests.

The workflow includes a concurrency configuration that prevents concurrent runs
on the same PR/issue to avoid push conflicts, while allowing parallel runs on
the default branch.

*Note: Requires `OPENCODE_API_KEY` secret to be set in repository settings.*

### Molecule Workflow

The `molecule.yml` workflow runs
[Molecule](https://molecule.readthedocs.io/) tests for the Ansible role.
It tests multiple scenarios (default, mt4, mt5-ea) using Docker containers.
