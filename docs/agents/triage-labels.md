# Triage Labels

Five canonical labels that drive the triage state machine. All use default names.

| Role | Label | When applied |
|------|-------|-------------|
| Needs triage | `needs-triage` | New issue/PR — maintainer needs to evaluate |
| Needs info | `needs-info` | Waiting on reporter for more details |
| Ready for agent | `ready-for-agent` | Fully specified — an AFK agent can pick it up with no human context |
| Ready for human | `ready-for-human` | Requires human judgment or implementation |
| Wontfix | `wontfix` | Will not be actioned |

## State machine

```
[opened]
    │
    ▼
needs-triage ──► ready-for-agent ──► [done / closed]
    │                                    ▲
    ├──► needs-info ──► (reporter responds) ──► needs-triage
    │
    ├──► ready-for-human ──► [human works]
    │
    └──► wontfix ──► [closed]
```

- Every new issue starts as `needs-triage`.
- `needs-info` blocks progress until the reporter adds the missing information, then it cycles back to `needs-triage`.
- `ready-for-agent` and `ready-for-human` are terminal triage states — the issue has been evaluated and routed.
- `wontfix` is a rejection state — closed after application.

## Label management

Labels are created on first use via `gh label create`. No pre-existing labels in this repo — all five will be created as needed.
