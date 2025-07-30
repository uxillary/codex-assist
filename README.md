# Codex Desktop Assistant 🧠💻

A simple Python GUI powered by OpenAI's GPT models. This tool lets you automate and speed up repetitive development tasks like:

- Generating commit messages
- Explaining code
- Refactoring snippets
- Creating PR instructions
- And more (custom prompts supported)

---

## 🔧 Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/your-username/codex-desktop-assistant.git
   cd codex-desktop-assistant
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create a `.env` file** with your OpenAI API key:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```

---

## 🚀 Run the App

```bash
python main.py
```

---

## 📦 Requirements

- Python 3.7+
- [OpenAI API key](https://platform.openai.com/account/api-keys)
- Packages:
  - `openai`
  - `ttkbootstrap`
  - `python-dotenv`

---

## 🛣 Roadmap

- [ ] Prompt templates for common dev tasks
- [ ] Model selector (`gpt-3.5-turbo`, `gpt-4-turbo`)
- [ ] Display token usage and estimated cost
- [ ] Drag-and-drop file input
- [ ] Persistent history/logging
- [ ] Syntax highlighting for output
- [ ] Task buttons: "Create PR", "Fix Bug", "Explain Code", etc.

---

## 📄 License

MIT — Free to use, modify, and distribute.

---

## 🙌 Contributing

Pull requests welcome! You can fork the repo, make changes, and open a PR with improvements or new features.

---

## 📜 Changelog

See [docs/CHANGELOG.md](docs/CHANGELOG.md) for a history of notable changes. Please update this file with a short note whenever you add or modify features.
