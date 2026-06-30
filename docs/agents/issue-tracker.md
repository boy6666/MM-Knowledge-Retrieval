# Issue Tracker

- **Tracker**: GitHub Issues
- **CLI**: `gh`
- **PRs as triage surface**: Yes — external PRs are pulled into the triage queue and run through the same labels and states as issues (collaborators' in-flight PRs are left alone).

## Location

Issues live at: https://github.com/boy6666/MM-Knowledge-Retrieval/issues

## Commands

When the `gh` CLI is available, use:

```bash
# List open issues
gh issue list

# Create an issue
gh issue create --title "..." --body "..."

# View an issue
gh issue view <number>

# Add a label
gh issue edit <number> --add-label "<label>"

# Close an issue
gh issue close <number>
```

For PR triage:

```bash
# List open pull requests
gh pr list --state open

# View a PR
gh pr view <number>
```

## Notes

- Issues are the primary surface for bugs, feature requests, and task tracking.
- External PRs enter the same triage pipeline as issues.
- All triage state transitions are managed via labels (see `triage-labels.md`).
