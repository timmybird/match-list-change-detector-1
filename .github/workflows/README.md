# GitHub Actions Workflows

This directory contains GitHub Actions workflow configurations for CI/CD and other automated tasks.

## Active Workflows

- `ci.yml`: Runs tests, linting, and documentation builds
- `security.yml`: Runs security checks including CodeQL, bandit, and dependency review

## Disabled Workflows

- `labeler.yml.disabled`: Automatically labels PRs based on file changes (currently disabled due to permission issues)

## Notes

- The labeler workflow has been disabled because it requires permissions to create labels
- If you want to re-enable it, rename it back to `labeler.yml` and ensure the repository has the necessary labels created
