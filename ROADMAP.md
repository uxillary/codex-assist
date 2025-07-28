# 🚀 Codex Desktop Assistant: Roadmap to Surpass Web-Based Codex

This roadmap outlines how to evolve the local Codex Desktop Assistant into a powerful alternative to browser-based Codex/Copilot tools by focusing on practical, focused features developers actually need.

---

## ✅ Core Feature Set (Already Working)

- Model selection (`gpt-3.5-turbo`, `gpt-4`)
- Custom or task-based prompt injection
- Status feedback and user messaging
- Token and cost estimation
- Local GUI app (Tkinter + ttkbootstrap)

---

## 🛣️ Roadmap Features

### 1. 🗂️ Local File Awareness / Repo Indexing

**Goal:** Allow the assistant to scan and selectively read from local files or directories.

**Steps:**
- Add “Select Folder” button
- Use `os.walk()` to read `.py`, `.md`, `.json`, etc.
- Populate a list or tree view of files
- Allow user to click to preview or include in the prompt

---

### 2. 📁 Smart Git Integration (PR and Commit)

**Goal:** Make Codex actively part of your Git workflow.

**Steps:**
- Auto-stage files or let user choose modified files
- Button: “Generate commit message”
- Button: “Generate PR description”
- Optional: Use GitHub CLI (`gh`) to automate PR creation

---

### 3. 🧩 Multi-File Code Suggestion Mode

**Goal:** Let Codex suggest multiple file outputs at once.

**Steps:**
- Prompt with: “Create 3 files for a FastAPI app”
- Layout: Output each file in a separate tab or section
- Include: “Copy” or “Save to File” buttons for each

---

### 4. 🧠 File Summary Caching

**Goal:** Add pseudo-memory by summarizing project files.

**Steps:**
- Run Codex: “Summarize this file in 1 sentence”
- Save file summaries in `summaries.json`
- Include summaries when prompting Codex for help with repo-level decisions

---

### 5. 📊 Usage Tracker

**Goal:** Track per-session and per-project token and cost usage.

**Steps:**
- Add session summary bar
- Save historical logs: `session_log.json`
- Display: total prompts, tokens, estimated cost

---

### 6. 🧪 Plugin Tools & Power Prompts

**Goal:** Add task-specific tools built around Codex.

Tools:
- Generate README.md
- Auto-generate test cases for selected file
- Create `.env.example` from `.env`
- Generate Dockerfile
- Convert language (Python → JavaScript)

---

## 🧰 Internal Ideas / Notes

- Use `tkinter.filedialog` for file selection
- Use tabbed interface (`ttk.Notebook`) for multi-file view
- Use subprocess to run git or `gh` commands
- Create configuration mode for repo preferences

---

## 🧪 Stretch Goals

- Code diff comparison before/after AI refactor
- Offline support with local models or fallback to cached completions
- Theme switcher (light/dark/custom)

---

## 📌 Current Priority Recommendation

**Start with:**
1. Local file reader + preview panel
2. “Generate README.md” button
3. Git commit message + PR message generator

---

Pull requests and issue suggestions welcome!
