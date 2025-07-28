import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from ttkbootstrap import Style
from openai_helper import send_prompt
from dotenv import load_dotenv
import os

load_dotenv()

# Set up the main app window
app = tk.Tk()
app.title("Codex Desktop Assistant")
app.geometry("700x540")

# Apply modern theme
style = Style("darkly")

# --- Menu Bar with Settings ---
def open_settings():
    messagebox.showinfo("Settings", "This will allow you to set your API key in a future update.")

menu_bar = tk.Menu(app)
settings_menu = tk.Menu(menu_bar, tearoff=0)
settings_menu.add_command(label="Set API Key", command=open_settings)
menu_bar.add_cascade(label="⚙️ Settings", menu=settings_menu)
app.config(menu=menu_bar)

# --- Prompt Input ---
prompt_label = ttk.Label(app, text="Your Prompt:")
prompt_label.pack(pady=(10, 0))

prompt_entry = tk.Text(app, height=6, wrap="word")
prompt_entry.pack(padx=10, pady=(0, 10), fill="x")

# --- Task Selector ---
task_frame = ttk.Frame(app)
task_frame.pack(padx=10, pady=(0, 10), fill="x")

task_label = ttk.Label(task_frame, text="Task:")
task_label.pack(side="left")

task_var = tk.StringVar()
task_dropdown = ttk.Combobox(task_frame, textvariable=task_var, state="readonly")
task_dropdown["values"] = ["Custom", "Explain Code", "Generate Commit Message", "Refactor"]
task_dropdown.current(0)
task_dropdown.pack(side="left", padx=(10, 0))

# --- GPT Model ---
model_label = ttk.Label(task_frame, text="Model:")
model_label.pack(side="left", padx=(20, 0))

model_var = tk.StringVar()
model_dropdown = ttk.Combobox(task_frame, textvariable=model_var, state="readonly")
model_dropdown["values"] = ["gpt-3.5-turbo", "gpt-4"]
model_dropdown.current(0)

model_dropdown.pack(side="left", padx=(10, 0))

# --- File Selector ---
file_frame = ttk.Frame(app)
file_frame.pack(padx=10, pady=(0, 10), fill="x")

def open_file():
    path = filedialog.askopenfilename(
        filetypes=[("Python", "*.py"), ("Text", "*.txt"), ("All files", "*.*")]
    )
    if path:
        selected_file_var.set(os.path.basename(path))
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                app.file_contents = f.read()
        except Exception as e:
            app.file_contents = f"[Error reading file] {e}"
        file_preview.delete("1.0", tk.END)
        file_preview.insert(tk.END, app.file_contents)
    else:
        selected_file_var.set("No file selected")
        app.file_contents = ""
        file_preview.delete("1.0", tk.END)

open_file_btn = ttk.Button(file_frame, text="Open File", command=open_file)
open_file_btn.pack(side="left")

selected_file_var = tk.StringVar(value="No file selected")
selected_file_label = ttk.Label(file_frame, textvariable=selected_file_var)
selected_file_label.pack(side="left", padx=(10, 0))

file_preview_frame = ttk.Frame(app)
file_preview_frame.pack(padx=10, pady=(0, 10), fill="both", expand=True)

file_preview = tk.Text(file_preview_frame, height=10, wrap="word")
file_preview.pack(side="left", fill="both", expand=True)

file_scrollbar = ttk.Scrollbar(file_preview_frame, command=file_preview.yview)
file_scrollbar.pack(side="right", fill="y")
file_preview.config(yscrollcommand=file_scrollbar.set)

def insert_file_into_prompt():
    content = getattr(app, "file_contents", "")
    if content:
        prompt_entry.insert(tk.END, content)
        status_var.set("✅ File inserted into prompt.")
    else:
        status_var.set("⚠️ No file loaded.")

insert_btn = ttk.Button(app, text="Insert file into prompt", command=insert_file_into_prompt)
insert_btn.pack(pady=(0, 10))

# --- Status Label ---
status_var = tk.StringVar()
status_label = ttk.Label(app, textvariable=status_var)
status_label.pack(pady=(0, 5))

# --- Token Cost Label ---
cost_var = tk.StringVar()
cost_label = ttk.Label(app, textvariable=cost_var)
cost_label.pack(pady=(0, 5))

# --- Copy answer text ---
def copy_response_to_clipboard():
    content = output_text.get("1.0", tk.END).strip()
    if content:
        app.clipboard_clear()
        app.clipboard_append(content)
        app.update()
        status_var.set("✅ Response copied to clipboard.")

# --- Ask Button ---
def generate_response():
    task = task_var.get()
    user_prompt = prompt_entry.get("1.0", tk.END).strip()

    if not user_prompt:
        status_var.set("⚠️ Please enter a prompt.")
        return

    if task == "Explain Code":
        final_prompt = f"Explain what this code does:\n{user_prompt}"
    elif task == "Generate Commit Message":
        final_prompt = f"Write a git commit message for the following change:\n{user_prompt}"
    elif task == "Refactor":
        final_prompt = f"Refactor this code and improve readability:\n{user_prompt}"
    else:
        final_prompt = user_prompt

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

ask_btn = ttk.Button(app, text="Ask", command=generate_response)
ask_btn.pack(pady=(0, 10))

copy_btn = ttk.Button(app, text="📋 Copy", command=copy_response_to_clipboard)
copy_btn.pack(pady=(0, 10))

# --- Output Response ---
output_label = ttk.Label(app, text="Response:")
output_label.pack()

output_text = tk.Text(app, height=15, wrap="word")
output_text.pack(padx=10, pady=(0, 10), fill="both", expand=True)

scrollbar = ttk.Scrollbar(app, command=output_text.yview)
scrollbar.pack(side="right", fill="y")
output_text.config(yscrollcommand=scrollbar.set)

# --- Run the App ---
app.mainloop()
