import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ttkbootstrap import Style
from openai_helper import send_prompt
from dotenv import load_dotenv

load_dotenv()

app = tk.Tk()
app.title("Codex Desktop Assistant")
app.geometry("900x600")

style = Style("darkly")

# ---------------- Menu ----------------

def open_settings():
    messagebox.showinfo("Settings", "This will allow you to set your API key in a future update.")

menu_bar = tk.Menu(app)
settings_menu = tk.Menu(menu_bar, tearoff=0)
settings_menu.add_command(label="Set API Key", command=open_settings)
menu_bar.add_cascade(label="⚙️ Settings", menu=settings_menu)
app.config(menu=menu_bar)

# ---------------- Layout ----------------
main_pane = ttk.PanedWindow(app, orient="horizontal")
main_pane.pack(fill="both", expand=True)

left_frame = ttk.Frame(main_pane)
right_frame = ttk.Frame(main_pane)
main_pane.add(left_frame, weight=1)
main_pane.add(right_frame, weight=1)

# === Prompt Section ===
prompt_frame = ttk.LabelFrame(left_frame, text="Prompt")
prompt_frame.pack(fill="both", expand=False, padx=10, pady=10)

prompt_entry = tk.Text(prompt_frame, height=6, wrap="word")
prompt_entry.pack(fill="both", expand=True, padx=5, pady=5)

# Task and Model selectors
option_frame = ttk.Frame(prompt_frame)
option_frame.pack(fill="x", padx=5, pady=5)

task_label = ttk.Label(option_frame, text="Task:")
task_label.pack(side="left")

task_var = tk.StringVar()
task_dropdown = ttk.Combobox(option_frame, textvariable=task_var, state="readonly")
task_dropdown["values"] = ["Custom", "Explain Code", "Generate Commit Message", "Refactor"]
task_dropdown.current(0)
task_dropdown.pack(side="left", padx=(10, 0))

model_label = ttk.Label(option_frame, text="Model:")
model_label.pack(side="left", padx=(20, 0))

model_var = tk.StringVar()
model_dropdown = ttk.Combobox(option_frame, textvariable=model_var, state="readonly")
model_dropdown["values"] = ["gpt-3.5-turbo", "gpt-4"]
model_dropdown.current(0)
model_dropdown.pack(side="left", padx=(10, 0))

# === Project Context Section ===
context_frame = ttk.LabelFrame(left_frame, text="Project Context")
context_frame.pack(fill="both", expand=True, padx=10, pady=(0,10))

context_controls = ttk.Frame(context_frame)
context_controls.pack(fill="x", pady=5)

# create controls
load_btn = ttk.Button(context_controls, text="Load Project Folder")
load_btn.pack(side="left")

context_count_label = ttk.Label(context_controls, text="0 files")
context_count_label.pack(side="left", padx=10)

use_context_var = tk.BooleanVar(value=True)
use_context_cb = ttk.Checkbutton(context_controls, text="Use project context", variable=use_context_var)
use_context_cb.pack(side="left")

# Scrollable list of files with checkboxes

files_canvas = tk.Canvas(context_frame, highlightthickness=0)
files_scroll = ttk.Scrollbar(context_frame, orient="vertical", command=files_canvas.yview)
files_list_container = ttk.Frame(files_canvas)
files_list_container.bind(
    "<Configure>", lambda e: files_canvas.configure(scrollregion=files_canvas.bbox("all"))
)
files_canvas.create_window((0, 0), window=files_list_container, anchor="nw")
files_canvas.configure(yscrollcommand=files_scroll.set)
files_canvas.pack(side="left", fill="both", expand=True)
files_scroll.pack(side="right", fill="y")

file_vars = {}
project_root = ""
context_summary = {}

# Preview area
preview_frame = ttk.LabelFrame(context_frame, text="Preview")
preview_frame.pack(fill="both", expand=True, padx=5, pady=5)
preview_text = tk.Text(preview_frame, height=10, wrap="word")
preview_text.pack(side="left", fill="both", expand=True)
preview_scroll = ttk.Scrollbar(preview_frame, command=preview_text.yview)
preview_scroll.pack(side="right", fill="y")
preview_text.configure(yscrollcommand=preview_scroll.set)

# ----- Functions -----

def preview_file(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            data = f.read()
    except Exception as e:
        data = f"[Error reading file] {e}"
    preview_text.delete("1.0", tk.END)
    preview_text.insert(tk.END, data[:10000])
    if len(data) > 10000:
        preview_text.insert(tk.END, "\n... (truncated)")


def approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def update_context_count():
    count = sum(1 for v in file_vars.values() if v.get())
    context_count_label.config(text=f"{count} files")


def summarize_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception as e:
        return f"[Error reading file] {e}"
    if len(content) > 15000:
        content = content[:15000]
    prompt = f"Summarize the purpose of this file in 1–2 sentences:\n\n{content}"
    summary, _ = send_prompt(prompt, model=model_var.get())
    return summary.strip()


def save_context_cache(folder: str):
    cache_path = os.path.join(folder, "project_context.json")
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(context_summary, f, indent=2)
    except Exception:
        pass


def load_context_cache(folder: str):
    cache_path = os.path.join(folder, "project_context.json")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return None


def load_folder():
    global project_root, context_summary
    folder = filedialog.askdirectory()
    if not folder:
        return
    project_root = folder
    # clear current list
    for child in files_list_container.winfo_children():
        child.destroy()
    file_vars.clear()
    context_summary = load_context_cache(folder) or {}
    status_var.set("🔍 Scanning project...")
    app.update()
    for root_dir, dirs, files in os.walk(folder):
        for name in files:
            if not name.lower().endswith((".py", ".md", ".txt", ".json")):
                continue
            path = os.path.join(root_dir, name)
            try:
                if os.path.getsize(path) > 100 * 1024:
                    continue
            except OSError:
                continue
            rel_path = os.path.relpath(path, folder)
            var = tk.BooleanVar(value=True)
            cb = ttk.Checkbutton(files_list_container, text=rel_path, variable=var,
                                 command=lambda p=path: preview_file(p))
            cb.pack(anchor="w")
            file_vars[path] = var
            var.trace_add("write", lambda *args: update_context_count())
            if rel_path not in context_summary:
                summary = summarize_file(path)
                context_summary[rel_path] = summary
    preview_text.delete("1.0", tk.END)
    save_context_cache(folder)
    update_context_count()
    status_var.set("✅ Project loaded")

load_btn.configure(command=load_folder)

# === Status and Controls ===
status_var = tk.StringVar()
status_label = ttk.Label(left_frame, textvariable=status_var)
status_label.pack(pady=5)

cost_var = tk.StringVar()
cost_label = ttk.Label(left_frame, textvariable=cost_var)
cost_label.pack()


def copy_response_to_clipboard():
    content = output_text.get("1.0", tk.END).strip()
    if content:
        app.clipboard_clear()
        app.clipboard_append(content)
        app.update()
        status_var.set("✅ Response copied to clipboard.")


def get_contextualized_prompt(user_prompt: str) -> str:
    if not use_context_var.get() or not context_summary:
        return user_prompt
    entries = []
    token_total = 0
    for path, var in file_vars.items():
        if not var.get():
            continue
        rel = os.path.relpath(path, project_root) if project_root else path
        summary = context_summary.get(rel)
        if not summary:
            continue
        tokens = approx_tokens(rel) + approx_tokens(summary)
        if token_total + tokens > 3000:
            messagebox.showwarning("Context truncated", "Context exceeds 3000 tokens. Truncating to top files.")
            break
        token_total += tokens
        entries.append(f"{rel}\n{summary}")
    context_text = "\n\n".join(entries)
    return f"{context_text}\n\n{user_prompt}" if context_text else user_prompt


def generate_response():
    task = task_var.get()
    user_prompt = prompt_entry.get("1.0", tk.END).strip()
    if not user_prompt:
        status_var.set("⚠️ Please enter a prompt.")
        return
    if task == "Explain Code":
        base_prompt = f"Explain what this code does:\n{user_prompt}"
    elif task == "Generate Commit Message":
        base_prompt = f"Write a git commit message for the following change:\n{user_prompt}"
    elif task == "Refactor":
        base_prompt = f"Refactor this code and improve readability:\n{user_prompt}"
    else:
        base_prompt = user_prompt
    final_prompt = get_contextualized_prompt(base_prompt)
    output_text.delete("1.0", tk.END)
    status_var.set("💬 Thinking... please wait.")
    app.update()
    selected_model = model_var.get()
    result, usage = send_prompt(final_prompt, model=selected_model)
    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, result)
    status_var.set("✅ Done.")
    if usage:
        from openai_helper import estimate_cost
        cost = estimate_cost(usage, selected_model)
        cost_var.set(f"Tokens: {usage.total_tokens} | Est. cost: ${cost:.4f}")
    else:
        cost_var.set("⚠️ Token info unavailable.")

ask_btn = ttk.Button(left_frame, text="Ask", command=generate_response)
ask_btn.pack(pady=(0,10))

copy_btn = ttk.Button(left_frame, text="📋 Copy", command=copy_response_to_clipboard)
copy_btn.pack(pady=(0,10))


def summarize_project():
    if not context_summary:
        messagebox.showinfo("No Project", "Load a project folder first.")
        return
    summaries = "\n\n".join(f"{name}\n{summary}" for name, summary in context_summary.items())
    prompt = f"What is the purpose of this project based on the following files?\n\n{summaries}"
    output_text.delete("1.0", tk.END)
    status_var.set("💬 Thinking... please wait.")
    app.update()
    selected_model = model_var.get()
    result, usage = send_prompt(prompt, model=selected_model)
    output_text.insert(tk.END, result)
    status_var.set("✅ Done.")
    if usage:
        from openai_helper import estimate_cost
        cost = estimate_cost(usage, selected_model)
        cost_var.set(f"Tokens: {usage.total_tokens} | Est. cost: ${cost:.4f}")
    else:
        cost_var.set("⚠️ Token info unavailable.")

summarize_btn = ttk.Button(left_frame, text="Summarize Project", command=summarize_project)
summarize_btn.pack(pady=(0,10))

# === Output Section ===
output_frame = ttk.LabelFrame(right_frame, text="Response")
output_frame.pack(fill="both", expand=True, padx=10, pady=10)

output_text = tk.Text(output_frame, wrap="word")
output_text.pack(side="left", fill="both", expand=True)
output_scroll = ttk.Scrollbar(output_frame, command=output_text.yview)
output_scroll.pack(side="right", fill="y")
output_text.configure(yscrollcommand=output_scroll.set)

app.mainloop()
