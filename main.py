import os
import json
import time
import threading
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from ttkbootstrap import Style
from dotenv import load_dotenv

from openai_helper import send_prompt, get_usage, estimate_cost, set_project_dir
from utils import approx_tokens, file_hash

load_dotenv()

BASE_DIR = os.path.dirname(__file__)
STATE_PATH = os.path.join(BASE_DIR, 'state.json')
SETTINGS_PATH = os.path.join(BASE_DIR, 'settings.json')
HISTORY_PATH = os.path.join(BASE_DIR, 'history.json')
PROJECTS_DIR = os.path.join(BASE_DIR, 'codex_projects')
os.makedirs(PROJECTS_DIR, exist_ok=True)

settings = {
    'use_project_context': True,
    'show_prompt_cost': True,
    'auto_load_last_project': True,
    'include_history': False,
    'theme': 'darkly',
    'last_project': '',
}
current_project_dir = ''
if os.path.exists(SETTINGS_PATH):
    try:
        with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
            settings.update(json.load(f))
    except Exception:
        pass

app = tk.Tk()
app.title('Codex Desktop Assistant')
app.geometry('900x600')
style = Style(settings.get('theme', 'darkly'))

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
        'project_dir': current_project_dir,
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


def save_project_files():
    if not current_project_dir:
        return
    try:
        with open(os.path.join(current_project_dir, 'context_summary.json'), 'w', encoding='utf-8') as f:
            json.dump(context_summary, f, indent=2)
        with open(os.path.join(current_project_dir, 'settings.json'), 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
        with open(os.path.join(current_project_dir, 'project_summary.txt'), 'w', encoding='utf-8') as f:
            f.write(f"Files summarized: {len(context_summary)}\n")
    except Exception:
        pass


def _write_proj_meta(name: str, root_path: str, folder: str):
    meta_path = os.path.join(folder, f"{name}.codexproj")
    try:
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump({'name': name, 'root': root_path}, f, indent=2)
    except Exception:
        pass


def new_project():
    name = tk.simpledialog.askstring('New Project', 'Project name:')
    if not name:
        return
    folder = os.path.join(PROJECTS_DIR, name)
    os.makedirs(folder, exist_ok=True)
    _write_proj_meta(name, '', folder)
    global current_project_dir
    current_project_dir = folder
    settings['last_project'] = folder
    save_settings()
    set_project_dir(folder)
    status_var.set('🆕 Project created')

def _load_project_file(file_path: str):
    folder = os.path.dirname(file_path)
    global current_project_dir, project_root, context_summary
    current_project_dir = folder
    settings['last_project'] = folder
    save_settings()
    set_project_dir(folder)
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        project_root = meta.get('root', '')
    except Exception:
        project_root = ''
    try:
        with open(os.path.join(folder, 'context_summary.json'), 'r', encoding='utf-8') as f:
            context_summary = json.load(f)
        context_count_label.config(text=f"{len(context_summary)} files summarized")
    except Exception:
        context_summary = {}
    refresh_history_panel()
    update_usage_display()

    if project_root and os.path.isdir(project_root):
        status_var.set('🔍 Scanning project...')
        threading.Thread(target=_scan_thread, args=(project_root,)).start()
    else:
        status_var.set('📁 Project loaded')


def load_project():
    file_path = filedialog.askopenfilename(initialdir=PROJECTS_DIR, filetypes=[('Codex Project', '*.codexproj')])
    if file_path:
        _load_project_file(file_path)


def save_project_as():
    name = tk.simpledialog.askstring('Save Project As', 'Project name:')
    if not name:
        return
    folder = os.path.join(PROJECTS_DIR, name)
    os.makedirs(folder, exist_ok=True)
    global current_project_dir
    current_project_dir = folder
    _write_proj_meta(name, project_root, folder)
    save_project_files()
    set_project_dir(folder)
    settings['last_project'] = folder
    save_settings()
    status_var.set('💾 Project saved')


def open_last_project():
    last = settings.get('last_project')
    if settings.get('auto_load_last_project') and last and os.path.isdir(last):
        for name in os.listdir(last):
            if name.endswith('.codexproj'):
                _load_project_file(os.path.join(last, name))
                break


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
                save_project_files()
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




# ----- UI Layout -----
project_frame = ttk.Frame(app)
project_frame.pack(fill='x', padx=10, pady=5)
ttk.Button(project_frame, text='New Project', command=new_project).pack(side='left', padx=2)
ttk.Button(project_frame, text='Load Project', command=load_project).pack(side='left', padx=2)
ttk.Button(project_frame, text='Save Project As', command=save_project_as).pack(side='left', padx=2)
load_btn = ttk.Button(project_frame, text='Load Folder', command=choose_folder)
load_btn.pack(side='left', padx=10)
context_count_label = ttk.Label(project_frame, text='0 files summarized')
context_count_label.pack(side='left', padx=10)

tabs = ttk.Notebook(app)
tabs.pack(fill='both', expand=True, padx=10, pady=10)

# ----- Prompt Tab -----
prompt_tab = ttk.Frame(tabs)
tabs.add(prompt_tab, text='Prompt')

prompt_entry = tk.Text(prompt_tab, height=6, wrap='word')
prompt_entry.pack(side='left', fill='both', expand=True, padx=5, pady=5)
prompt_scroll = ttk.Scrollbar(prompt_tab, command=prompt_entry.yview)
prompt_scroll.pack(side='right', fill='y')
prompt_entry.configure(yscrollcommand=prompt_scroll.set)

option_frame = ttk.Frame(prompt_tab)
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

ask_btn = ttk.Button(prompt_tab, text='Ask', command=generate_response)
ask_btn.pack(pady=5)

# ----- Response Tab -----
response_tab = ttk.Frame(tabs)
tabs.add(response_tab, text='Response')
output_text = tk.Text(response_tab, wrap='word')
output_text.pack(side='left', fill='both', expand=True)
output_scroll = ttk.Scrollbar(response_tab, command=output_text.yview)
output_scroll.pack(side='right', fill='y')
output_text.configure(yscrollcommand=output_scroll.set)
copy_btn = ttk.Button(response_tab, text='📋 Copy', command=lambda: app.clipboard_append(output_text.get('1.0', tk.END)))
copy_btn.pack(pady=5)

# ----- History Tab -----
history_tab = ttk.Frame(tabs)
tabs.add(history_tab, text='History')
history_text = tk.Text(history_tab, wrap='word', state='disabled')
history_text.pack(side='left', fill='both', expand=True)
history_scroll = ttk.Scrollbar(history_tab, command=history_text.yview)
history_scroll.pack(side='right', fill='y')
history_text.configure(yscrollcommand=history_scroll.set)

# ----- Settings Tab -----
settings_tab = ttk.Frame(tabs)
tabs.add(settings_tab, text='Settings')
use_context_cb = ttk.Checkbutton(settings_tab, text='Use project context', variable=use_context_var)
use_context_cb.pack(anchor='w', padx=10, pady=5)
history_cb = ttk.Checkbutton(settings_tab, text='Include chat history', variable=include_history_var)
history_cb.pack(anchor='w', padx=10, pady=5)
cost_var = tk.BooleanVar(value=settings['show_prompt_cost'])
auto_var = tk.BooleanVar(value=settings['auto_load_last_project'])
theme_var = tk.BooleanVar(value=settings.get('theme', 'darkly') == 'darkly')

def apply_setting(var, key, refresh=False):
    settings[key] = var.get() if not isinstance(var.get(), bool) else var.get()
    save_settings()
    if refresh:
        update_usage_display()

ttk.Checkbutton(settings_tab, text='Show individual prompt cost', variable=cost_var,
                command=lambda: apply_setting(cost_var, 'show_prompt_cost', True)).pack(anchor='w', padx=10, pady=5)
ttk.Checkbutton(settings_tab, text='Auto-load last project on startup', variable=auto_var,
                command=lambda: apply_setting(auto_var, 'auto_load_last_project')).pack(anchor='w', padx=10, pady=5)

def toggle_theme():
    settings['theme'] = 'darkly' if theme_var.get() else 'flatly'
    style.theme_use(settings['theme'])
    save_settings()

ttk.Checkbutton(settings_tab, text='Dark theme', variable=theme_var, command=toggle_theme).pack(anchor='w', padx=10, pady=5)

footer = ttk.Frame(app)
footer.pack(side='bottom', fill='x')
usage_label = ttk.Label(footer, textvariable=usage_var)
usage_label.pack(side='right', padx=10, pady=5)
status_label = ttk.Label(footer, textvariable=status_var)
status_label.pack(side='left', padx=10, pady=5)

# ----- Auto load state -----
state = load_state()
if state:
    use_context_var.set(state.get('use_context', settings['use_project_context']))

open_last_project()
update_usage_display()
refresh_history_panel()

app.after(100, _process_progress_queue)
app.mainloop()
