import tkinter as tk
from tkinter import ttk
from ttkbootstrap import Style
from openai_helper import send_prompt
from dotenv import load_dotenv
import os

load_dotenv()

# Set up the main app window
app = tk.Tk()
app.title("Codex Desktop Assistant")
app.geometry("700x500")

# Apply modern theme
style = Style("darkly")

# Prompt frame
prompt_label = ttk.Label(app, text="Your Prompt:")
prompt_label.pack(pady=(10, 0))

prompt_entry = tk.Text(app, height=6, wrap="word")
prompt_entry.pack(padx=10, pady=(0, 10), fill="x")

# Task selector
task_frame = ttk.Frame(app)
task_frame.pack(padx=10, pady=(0, 10), fill="x")

task_label = ttk.Label(task_frame, text="Task:")
task_label.pack(side="left")

task_var = tk.StringVar()
task_dropdown = ttk.Combobox(task_frame, textvariable=task_var, state="readonly")
task_dropdown["values"] = ["Custom", "Explain Code", "Generate Commit Message", "Refactor"]
task_dropdown.current(0)
task_dropdown.pack(side="left", padx=(10, 0))

# Output frame
output_label = ttk.Label(app, text="Response:")
output_label.pack()

output_text = tk.Text(app, height=15, wrap="word")
output_text.pack(padx=10, pady=(0, 10), fill="both", expand=True)

# Scrollbar for output
scrollbar = ttk.Scrollbar(app, command=output_text.yview)
scrollbar.pack(side="right", fill="y")
output_text.config(yscrollcommand=scrollbar.set)

# Button callback
def generate_response():
    task = task_var.get()
    user_prompt = prompt_entry.get("1.0", tk.END).strip()

    if task == "Explain Code":
        final_prompt = f"Explain what this code does:\n{user_prompt}"
    elif task == "Generate Commit Message":
        final_prompt = f"Write a git commit message for the following change:\n{user_prompt}"
    elif task == "Refactor":
        final_prompt = f"Refactor this code and improve readability:\n{user_prompt}"
    else:
        final_prompt = user_prompt

    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, "Thinking...\n")
    app.update()

    result = send_prompt(final_prompt)
    output_text.delete("1.0", tk.END)
    output_text.insert(tk.END, result)

# Generate button
submit_btn = ttk.Button(app, text="Generate", command=generate_response)
submit_btn.pack(pady=10)

# Run the app
app.mainloop()
