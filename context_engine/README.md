# Codex Assist Context Engine

This package implements a lightweight, four layer memory system for the demo `codex-assist` app.

## Layers
- **Active Context (AC)** – rolling window of the last conversational turns.
- **Decision Ledger (DL)** – structured YAML of decisions, constraints, todos, prefs and ids.
- **Facts Store (FS)** – extractive / abstractive snippets with embeddings for retrieval.
- **Cold Archive (CA)** – raw transcript history kept in SQLite.

## Quick start
```bash
python -m context_engine.cli ingest --user "We chose Astro; add loader" --assistant "Done; TODO confetti"
python -m context_engine.cli compose --next "Improve loader feedback"
python -m context_engine.cli stats
```

## Embedders
The engine accepts any object implementing `Embedder`. `HashEmbedder` is the default. An `OpenAIEmbedder`
adapter is provided; set `OPENAI_API_KEY` in the environment to use it.

## Token budgeting
Token counts use `tiktoken` when available and fall back to a simple word split. Functions `len_tokens` and
`cap_to_tokens` help enforce budgets.

## Design rationale
- **Structured > prose** – DL is kept as YAML for deterministic merging.
- **Two‑track summaries** – both extractive and abstractive snippets are stored for richer retrieval.
- **Temporal decay** – AC trims to the most recent pairs; DL trims oldest entries when over budget.
