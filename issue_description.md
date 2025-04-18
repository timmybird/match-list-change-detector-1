# Update CONTRIBUTING.md with AI-specific guidelines and automate reminders

## Description

When working with AI agents, they sometimes miss important context that's ingrained in the muscle memory of seasoned developers. To address this, we should:

1. Update CONTRIBUTING.md with a section specifically aimed at AI agents
2. Add a mechanism to automatically include reminders about CONTRIBUTING.md in issues and PRs
3. Consider using GitHub Actions to automatically add comments with contributing guidelines to new issues and PRs if they don't already contain references to CONTRIBUTING.md

## Benefits

- Ensures AI agents follow project guidelines even when not explicitly instructed
- Provides consistent guidance across all contributions
- Reduces the need for humans to repeatedly remind AI agents about project conventions
- Improves code quality and consistency

## Implementation Ideas

- Add an "AI Agent Guidelines" section to CONTRIBUTING.md
- Create a GitHub Action that checks new issues and PRs for references to CONTRIBUTING.md
- If no reference is found, automatically add a comment with key guidelines
- Update issue and PR templates to include references to CONTRIBUTING.md

## Related

This would help with all contributions, but especially those involving AI agents like Claude, ChatGPT, etc.
