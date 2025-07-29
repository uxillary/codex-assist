import os
import json
import time
import threading
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ttkbootstrap import Style
from dotenv import load_dotenv

from openai_helper import send_prompt, get_usage, estimate_cost
from utils import approx_tokens, file_hash

load_dotenv()

BASE_DIR = os.path.dirname(__file__)
STATE_PATH = os.path.join(BASE_DIR, 'state.json')
SETTINGS_PATH = os.path.join(BASE_DIR, 'settings.json')
HISTORY_PATH = os.path.join(BASE_DIR, 'history.json')

app = tk.Tk()
app.title('Codex Desktop Assistant')
app.geometry('900x600')
style = Style('darkly')

# ----- State -----
project_root = ''
context_summary = {}
settings = {
    'use_project_context': True,
    'show_session_short': False,
    'show_prompt_cost': True,
    'auto_load_last_project': True,
    'include_history': False,
}


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


def load_settings():
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                settings.update(json.load(f))
        except Exception:
            pass


def save_settings():
    try:
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
    except Exception:
        pass


# load persisted settings after helper functions are defined
load_settings()


# ----- Usage Display -----
usage_var = tk.StringVar()
last_prompt_cost = 0.0
status_var = tk.StringVar()


def _format_tokens(t: int) -> str:
    if not settings.get('show_session_short'):
        return str(t)
    if t >= 1_000_000:
        return f"{t/1_000_000:.1f}M"
    if t >= 1_000:
        return f"{t/1_000:.1f}k"
    return str(t)


def update_usage_display():
    u = get_usage()
    session_tok = _format_tokens(u['session_tokens'])
    total_tok = _format_tokens(u['total_tokens'])
    prompt_cost_txt = ''
    if settings.get('show_prompt_cost'):
        prompt_cost_txt = f"Prompt: ${last_prompt_cost:.4f} | "
    usage_var.set(f"{prompt_cost_txt}Session: {session_tok}t (${u['session_cost']:.4f}) | "
                   f"Total: {total_tok}t (${u['total_cost']:.4f})")


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
progress_queue = queue.Queue()


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


def scan_folder(folder: str, progress=None):
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
            if progress:
                progress(len(context_summary))
    save_summary_cache(folder, summary_cache)
    if progress:
        progress(len(context_summary), done=True)


def _scan_thread(folder: str):
    def progress(count, done=False):
        progress_queue.put((count, done))

    scan_folder(folder, progress)


def _process_progress_queue():
    try:
        while True:
            count, done = progress_queue.get_nowait()
            context_count_label.config(text=f"{count} files summarized")
            if done:
                status_var.set('✅ Project loaded')
                load_btn.config(state='normal')
                ask_btn.config(state='normal')
                app.config(cursor='arrow')
                save_state()
                save_settings()
    except queue.Empty:
        pass
    app.after(100, _process_progress_queue)


def choose_folder():
    folder = filedialog.askdirectory()
    if folder:
        load_btn.config(state='disabled')
        ask_btn.config(state='disabled')
        app.config(cursor='wait')
        status_var.set('🔍 Scanning project...')
        t = threading.Thread(target=_scan_thread, args=(folder,))
        t.start()


# ----- Prompt Handling -----

use_context_var = tk.BooleanVar(value=settings['use_project_context'])
include_history_var = tk.BooleanVar(value=settings['include_history'])

def _var_changed(name, index, mode, key, var):
    settings[key] = var.get()
    save_settings()

use_context_var.trace_add('write', lambda *a: _var_changed(*a, key='use_project_context', var=use_context_var))
include_history_var.trace_add('write', lambda *a: _var_changed(*a, key='include_history', var=include_history_var))


def build_prompt(user_prompt: str) -> str:
    parts = []
    token_total = 0
    if use_context_var.get() and context_summary:
        for rel, summary in context_summary.items():
            tokens = approx_tokens(rel) + approx_tokens(summary)
            if token_total + tokens > 3000:
                break
            token_total += tokens
            parts.append(f"{rel}: {summary}")
        if parts:
            parts = ['context'] + parts
    if include_history_var.get():
        try:
            with open(HISTORY_PATH, 'r', encoding='utf-8') as f:
                hist = json.load(f)
        except Exception:
            hist = []
        for item in hist[-5:]:
            text = f"User: {item['prompt']}\nAssistant: {item['response']}"
            parts.append(text)
    parts.append(user_prompt)
    return '\n\n'.join(parts)


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
    result, usage = send_prompt(final_prompt, model=model, task=task)
    global last_prompt_cost
    last_prompt_cost = estimate_cost(usage, model) if usage else 0.0
    output_text.insert(tk.END, result)
    status_var.set('✅ Done.')
    update_usage_display()
    refresh_history_panel()
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
        line = (f"[{ts}] {item.get('model', '')} {item.get('tokens', 0)}t (${item.get('cost', 0):.4f})\n"
                f"Prompt: {item.get('prompt', '')[:200]}\nResponse: {item.get('response', '')[:200]}\n\n")
        txt.insert(tk.END, line)
    txt.configure(state='disabled')


def refresh_history_panel():
    try:
        with open(HISTORY_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        data = []
    history_text.configure(state='normal')
    history_text.delete('1.0', tk.END)
    for item in data[-50:]:
        ts = time.strftime('%H:%M:%S', time.localtime(item['ts']))
        task = item.get('task', 'N/A')
        line = f"[{ts}] {task} -> {item.get('model', '')}\n{item.get('response', '')}\n\n"
        history_text.insert(tk.END, line)
    history_text.configure(state='disabled')


def open_settings():
    win = tk.Toplevel(app)
    win.title('Settings')
    def apply_main():
        settings['use_project_context'] = use_context_var.get()
        settings['include_history'] = include_history_var.get()
        save_settings()
        update_usage_display()

    ttk.Checkbutton(win, text='Use project context', variable=use_context_var,
                    command=apply_main).pack(anchor='w', padx=10, pady=5)
    ttk.Checkbutton(win, text='Include chat history', variable=include_history_var,
                    command=apply_main).pack(anchor='w', padx=10, pady=5)
    short_var = tk.BooleanVar(value=settings['show_session_short'])
    cost_var = tk.BooleanVar(value=settings['show_prompt_cost'])
    auto_var = tk.BooleanVar(value=settings['auto_load_last_project'])
    def apply(var, key):
        settings[key] = var.get()
        save_settings()
        update_usage_display()

    ttk.Checkbutton(win, text='Show session stats in short format', variable=short_var,
                    command=lambda: apply(short_var, 'show_session_short')).pack(anchor='w', padx=10, pady=5)
    ttk.Checkbutton(win, text='Show individual prompt cost', variable=cost_var,
                    command=lambda: apply(cost_var, 'show_prompt_cost')).pack(anchor='w', padx=10, pady=5)
    ttk.Checkbutton(win, text='Auto-load last project on startup', variable=auto_var,
                    command=lambda: apply(auto_var, 'auto_load_last_project')).pack(anchor='w', padx=10, pady=5)


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

right_tabs = ttk.Notebook(right)
right_tabs.pack(fill='both', expand=True, padx=10, pady=10)

output_frame = ttk.Frame(right_tabs)
history_frame = ttk.Frame(right_tabs)
right_tabs.add(output_frame, text='Response')
right_tabs.add(history_frame, text='History')

output_text = tk.Text(output_frame, wrap='word')
output_text.pack(side='left', fill='both', expand=True)
output_scroll = ttk.Scrollbar(output_frame, command=output_text.yview)
output_scroll.pack(side='right', fill='y')
output_text.configure(yscrollcommand=output_scroll.set)

history_text = tk.Text(history_frame, wrap='word', state='disabled')
history_text.pack(side='left', fill='both', expand=True)
history_scroll = ttk.Scrollbar(history_frame, command=history_text.yview)
history_scroll.pack(side='right', fill='y')
history_text.configure(yscrollcommand=history_scroll.set)

footer = ttk.Frame(app)
footer.pack(side='bottom', fill='x')
usage_label = ttk.Label(footer, textvariable=usage_var)
usage_label.pack(side='right', padx=10, pady=5)
status_label = ttk.Label(footer, textvariable=status_var)
status_label.pack(side='left', padx=10, pady=5)

# menu item for history
menu = tk.Menu(app)
menu.add_command(label='🕑 History', command=show_history)
menu.add_command(label='⚙️ Settings', command=lambda: open_settings())
app.config(menu=menu)

# ----- Auto load state -----
state = load_state()
if state:
    use_context_var.set(state.get('use_context', settings['use_project_context']))
    last = state.get('last_folder')
    if settings.get('auto_load_last_project') and last and os.path.isdir(last):
        load_btn.config(state='disabled')
        ask_btn.config(state='disabled')
        app.config(cursor='wait')
        status_var.set('🔍 Scanning project...')
        threading.Thread(target=_scan_thread, args=(last,)).start()
update_usage_display()
refresh_history_panel()

app.after(100, _process_progress_queue)
app.mainloop()
