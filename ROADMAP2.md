# AIIDE – Roadmap 2.0

## Goal

Release a public, intuitive, single-user AI coding assistant within 1 month that intelligently builds context, reduces API costs, edits files, integrates with Git, and provides clear real-time feedback.

---

## Core Pillars

1. **Prompt → Code with Context** – Project-aware completions that understand local files.
2. **Context Engine v1** – Smart, condensed context building with token optimization.
3. **Spend Guardrails** – Token and cost limits with preflight estimates and warnings.
4. **Activity Console** – Live event stream with filters, cost tracking, and logs.
5. **File & Git Integration** – Create, edit, move files, and manage changes with Git.
6. **Polished, Simple UI** – Intuitive layout with visual metaphors and minimal complexity.

---

## Context Engine v1 – Smart Token Reduction

- **Phase A: Collect** – Gather recent edits, open files, prompted paths, ignore globs.
- **Phase B: Rank** – Prioritize by relevance (recency, path match, file type weight).
- **Phase C: Condense** – Strip boilerplate, summarize important APIs, keep constraints.
- **Phase D: Pack** – Allocate token budget (critical files > related APIs > repo summary).
- **Phase E: Shrink** – Iteratively condense further if over budget.
- **Transparency** – Log inclusions/exclusions to Activity Console.

---

## Spend Guardrails

- **Caps:** Per-request max tokens & £, daily £ cap.
- **Preflight:** Show estimated tokens/cost before send, confirm if above thresholds.
- **Postflight:** Show actual tokens/cost used and daily total.
- **Override:** Allow manual bypass if necessary.

---

## File & Git Workflow

- **Proposal Format:** Model outputs unified diff.
- **Preview:** Side-by-side diff with “Apply” and backup before overwrite.
- **Git Integration:** Initialize repo, create branches, stage, commit with AI-generated message, revert last apply.

---

## UI Simplification

- **Top Bar:** Prompt field, model select, send button.
- **Left Panel:** Project file tree with search.
- **Center Panel:** Tabs – *Answer*, *Diffs*, *Console*.
- **Bottom Bar (fixed):** Status (model • tokens • £), caps indicator, settings cog.
- **Settings Menu:** Provider selection, caps, context mode (Light/Smart/Full), ignore patterns.

---

## Non-OpenAI Providers to Support

- Anthropic (Claude 3.x)
- Google Gemini (1.5)
- Mistral (Large, Codestral)
- Cohere (Command-R)
- OpenRouter (multi-model routing)

---

## Tech & Packaging

- **Language:** Python 3.x  
- **UI:** Tkinter + ttkbootstrap  
- **Packaging:**  
  - Windows – PyInstaller / Nuitka  
  - macOS – PyInstaller or py2app (codesign & notarize)  
  - Linux – PyInstaller or AppImage  
- **Git:** `subprocess` calls or `GitPython`
- **Settings:** Local JSON in user config dir
- **Providers:** Abstracted interface for model switching

---

## Performance & Security

- Ignore list for large/unnecessary files (.git, node_modules, dist, .env by default)
- Local-only processing before API call
- Redaction rules for sensitive data
- Summaries cached for faster repeat requests (optional)

---

## 4-Week Build Plan

### Week 1 – Foundations

- Provider abstraction (OpenAI first, stubs for others)
- Token/cost estimator + caps + preflight dialog
- Activity Console integration
- File IO layer (read/write/move + backup)

### Week 2 – Context Engine v1

- File collector, ranker, condense-to-budget
- Ignore list + transparency in console
- Pack/shrink logic for budget enforcement

### Week 3 – Diffs & Git

- Diff preview, apply, revert
- Git ops: branch, commit, error handling
- UI polish: tabbed views, fixed status bar

### Week 4 – Polish & Release

- macOS/Linux builds + signing
- Onboarding flow
- Crash fixes and performance checks
- Public beta release
