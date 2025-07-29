import os
import json
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ttkbootstrap import Style
from dotenv import load_dotenv

from openai_helper import send_prompt, get_usage
from utils import approx_tokens, file_hash

load_dotenv()

STATE_PATH = os.path.join(os.path.dirname(__file__), 'state.json')

app = tk.Tk()
app.title('Codex Desktop Assistant')
app.geometry('900x600')
style = Style('darkly')

# ----- State -----
project_root = ''
context_summary = {}


def load_state():
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception:
            pass
    return {}


def save_state():
    state = {
        'last_folder': project_root,
        'context_summary': context_summary,
        'use_context': use_context_var.get(),
    }
    usage = get_usage()
    state['total_tokens'] = usage['total_tokens']
    state['total_cost'] = usage['total_cost']
    try:
        with open(STATE_PATH, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass


# ----- Usage Display -----
usage_var = tk.StringVar()
status_var = tk.StringVar()


def update_usage_display():
    u = get_usage()
    usage_var.set(f"Session: {u['session_tokens']} tokens (${u['session_cost']:.4f}) | "
                   f"Total: {u['total_tokens']} tokens (${u['total_cost']:.4f})")


# ----- Context Handling -----

def load_summary_cache(folder: str):
    path = os.path.join(folder, 'summaries.json')
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_summary_cache(folder: str, data: dict):
    path = os.path.join(folder, 'summaries.json')
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


summary_cache = {}


def summarize_file(path: str) -> str:
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        return f"[Error reading file] {e}"
    if len(content) > 15000:
        content = content[:15000]
    prompt = f"Summarize the purpose of this file in 1–2 sentences:\n\n{content}"
    summary, _ = send_prompt(prompt)
    return summary.strip()


def scan_folder(folder: str):
    global project_root, context_summary, summary_cache
    project_root = folder
    summary_cache = load_summary_cache(folder)
    context_summary = {}
    for root, _, files in os.walk(folder):
        for name in files:
            if not name.lower().endswith(('.py', '.md', '.txt', '.json')):
                continue
            path = os.path.join(root, name)
            try:
                if os.path.getsize(path) > 100 * 1024:
                    continue
            except OSError:
                continue
            rel = os.path.relpath(path, folder)
            h = file_hash(path)
            cached = summary_cache.get(rel)
            if cached and cached.get('hash') == h:
                summary = cached['summary']
            else:
                summary = summarize_file(path)
                summary_cache[rel] = {'hash': h, 'summary': summary}
            context_summary[rel] = summary
    save_summary_cache(folder, summary_cache)
    context_count_label.config(text=f"{len(context_summary)} files summarized")
    status_var.set('✅ Project loaded')
    save_state()


def choose_folder():
    folder = filedialog.askdirectory()
    if folder:
        status_var.set('🔍 Scanning project...')
        app.update()
        scan_folder(folder)


# ----- Prompt Handling -----

use_context_var = tk.BooleanVar(value=True)


def build_prompt(user_prompt: str) -> str:
    if not use_context_var.get() or not context_summary:
        return user_prompt
    entries = []
    token_total = 0
    for rel, summary in context_summary.items():
        tokens = approx_tokens(rel) + approx_tokens(summary)
        if token_total + tokens > 3000:
            break
        token_total += tokens
        entries.append(f"{rel}: {summary}")
    if not entries:
        return user_prompt
    context_text = 'context\n' + '\n'.join(entries)
    return f"{context_text}\n\n{user_prompt}"


def generate_response():
    user_prompt = prompt_entry.get('1.0', tk.END).strip()
    if not user_prompt:
        status_var.set('⚠️ Please enter a prompt.')
        return
    task = task_var.get()
    if task == 'Explain Code':
        base_prompt = f"Explain what this code does:\n{user_prompt}"
    elif task == 'Generate Commit Message':
        base_prompt = f"Write a git commit message for the following change:\n{user_prompt}"
    elif task == 'Refactor':
        base_prompt = f"Refactor this code and improve readability:\n{user_prompt}"
    else:
        base_prompt = user_prompt
    final_prompt = build_prompt(base_prompt)
    output_text.delete('1.0', tk.END)
    status_var.set('💬 Thinking... please wait.')
    app.update()
    model = model_var.get()
    result, _ = send_prompt(final_prompt, model=model)
    output_text.insert(tk.END, result)
    status_var.set('✅ Done.')
    update_usage_display()
    save_state()


# ----- History Viewer -----

def show_history():
    try:
        with open(os.path.join(os.path.dirname(__file__), 'history.json'), 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        data = []
    win = tk.Toplevel(app)
    win.title('History')
    txt = tk.Text(win, wrap='word')
    txt.pack(fill='both', expand=True)
    for item in data[-100:]:
        ts = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(item['ts']))
        line = (f"[{ts}] {item['model']} {item['tokens']}t (${item['cost']:.4f})\n"
                f"Prompt: {item['prompt'][:200]}\nResponse: {item['response'][:200]}\n\n")
        txt.insert(tk.END, line)
    txt.configure(state='disabled')


# ----- UI Layout -----
main_pane = ttk.PanedWindow(app, orient='horizontal')
main_pane.pack(fill='both', expand=True)
left = ttk.Frame(main_pane)
right = ttk.Frame(main_pane)
main_pane.add(left, weight=1)
main_pane.add(right, weight=1)

context_frame = ttk.LabelFrame(left, text='Project Context')
context_frame.pack(fill='x', padx=10, pady=10)
load_btn = ttk.Button(context_frame, text='Load Folder', command=choose_folder)
load_btn.pack(side='left', padx=5, pady=5)
context_count_label = ttk.Label(context_frame, text='0 files summarized')
context_count_label.pack(side='left', padx=10)
use_context_cb = ttk.Checkbutton(context_frame, text='Use project context', variable=use_context_var)
use_context_cb.pack(side='left')

prompt_frame = ttk.LabelFrame(left, text='Prompt')
prompt_frame.pack(fill='both', expand=True, padx=10, pady=(0,10))

prompt_entry = tk.Text(prompt_frame, height=6, wrap='word')
prompt_entry.pack(fill='both', expand=True, padx=5, pady=5)

option_frame = ttk.Frame(prompt_frame)
option_frame.pack(fill='x', padx=5, pady=5)

task_var = tk.StringVar(value='Custom')
task_dropdown = ttk.Combobox(option_frame, textvariable=task_var, state='readonly')
task_dropdown['values'] = ['Custom', 'Explain Code', 'Generate Commit Message', 'Refactor']
task_dropdown.current(0)
task_dropdown.pack(side='left')

model_var = tk.StringVar(value='gpt-3.5-turbo')
model_dropdown = ttk.Combobox(option_frame, textvariable=model_var, state='readonly')
model_dropdown['values'] = ['gpt-3.5-turbo', 'gpt-4']
model_dropdown.current(0)
model_dropdown.pack(side='left', padx=10)

ask_btn = ttk.Button(left, text='Ask', command=generate_response)
ask_btn.pack(pady=5)
copy_btn = ttk.Button(left, text='📋 Copy', command=lambda: app.clipboard_append(output_text.get('1.0', tk.END)))
copy_btn.pack(pady=5)

output_frame = ttk.LabelFrame(right, text='Response')
output_frame.pack(fill='both', expand=True, padx=10, pady=10)
output_text = tk.Text(output_frame, wrap='word')
output_text.pack(side='left', fill='both', expand=True)
output_scroll = ttk.Scrollbar(output_frame, command=output_text.yview)
output_scroll.pack(side='right', fill='y')
output_text.configure(yscrollcommand=output_scroll.set)

footer = ttk.Frame(app)
footer.pack(side='bottom', fill='x')
usage_label = ttk.Label(footer, textvariable=usage_var)
usage_label.pack(side='right', padx=10, pady=5)
status_label = ttk.Label(footer, textvariable=status_var)
status_label.pack(side='left', padx=10, pady=5)

# menu item for history
menu = tk.Menu(app)
menu.add_command(label='🕑 History', command=show_history)
app.config(menu=menu)

# ----- Auto load state -----
state = load_state()
if state:
    use_context_var.set(state.get('use_context', True))
    last = state.get('last_folder')
    if last and os.path.isdir(last):
        status_var.set('🔍 Scanning project...')
        app.update()
        scan_folder(last)
update_usage_display()

app.mainloop()
