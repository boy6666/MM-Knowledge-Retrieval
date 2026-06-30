# Domain Docs Layout

Multi-context project. A `CONTEXT-MAP.md` at the repo root serves as the entry point, pointing to per-context `CONTEXT.md` files.

## Contexts

| Context | Path | Coverage |
|---------|------|---------|
| Backend | `backend/CONTEXT.md` | FastAPI backend — routers, services, models, data pipeline |
| AI / LLM Core | `ai-core/CONTEXT.md` | LLM service, vector search engine, RAG pipeline, data processor |
| Frontend | `frontend/CONTEXT.md` | Vue 3 + Element Plus — pages, components, stores, routing |

## Consumer rules

Skills that read these files (`improve-codebase-architecture`, `diagnosing-bugs`, `tdd`) follow these rules:

1. **Start at `CONTEXT-MAP.md`** to determine which contexts exist and which one the current work belongs to.
2. **Read only the relevant context's `CONTEXT.md`** — do not load all contexts simultaneously.
3. **ADR lookup**: architectural decisions live in `docs/adr/` at the repo root. If a decision spans multiple contexts, it lives at the root; if it's specific to one context, it lives under that context's `docs/adr/`.
4. **Cross-context changes**: when a change touches two or more contexts (e.g. adding a backend API endpoint and consuming it from the frontend), read both `CONTEXT.md` files before proposing edits.

## Domain doc state

- `CONTEXT-MAP.md`: ❌ not yet written
- `backend/CONTEXT.md`: ❌ not yet written
- `ai-core/CONTEXT.md`: ❌ not yet written
- `frontend/CONTEXT.md`: ❌ not yet written
- `docs/adr/`: ❌ not yet created

> All four `CONTEXT.md` files and `docs/adr/` are empty stubs — they need to be authored before skills that depend on them can work effectively.
