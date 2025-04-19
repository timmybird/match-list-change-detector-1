# GitHub Actions Workflows

This directory contains GitHub Actions workflow configurations for CI/CD and other automated tasks.

## Active Workflows

- `ci.yml`: Runs tests, linting, and documentation builds
- `security.yml`: Runs security checks including CodeQL, bandit, and dependency review

## Removed Workflows

- The Pull Request Labeler workflow has been completely removed due to persistent permission issues

## Notes

- The labeler workflow has been completely removed because it requires permissions to create labels
- If you want to add it back in the future, ensure the repository has the necessary labels created first
