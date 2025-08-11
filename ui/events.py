import threading
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox

from services.openai_helper import send_prompt, estimate_cost
from logic import prompt_builder, file_generator, context_manager, project_manager
from utils import approx_tokens
from logging_bus import emit


class UIEvents:
    def __init__(self, ctx, widgets, files_update, status_bar, refresh_history):
        self.ctx = ctx
        self.widgets = widgets
        self.files_update = files_update
        self.status_bar = status_bar
        self.refresh_history = refresh_history
        widgets['ask_btn'].config(command=self.generate_response)
        widgets['prompt_entry'].bind('<KeyRelease>', self.update_token_estimate)
        self.update_token_estimate()

    # --- Prompt handling ---
    def generate_response(self):
        prompt_widget = self.widgets['prompt_entry']
        response_widget = self.widgets['response_text']
        user_prompt = prompt_widget.get('1.0', tk.END).strip()
        if not user_prompt:
            self.status_bar.set_status('⚠️ Please enter a prompt.')
            return
        task = self.widgets['task_var'].get()
        if task == 'Explain Code':
            base_prompt = f"Explain what this code does:\n{user_prompt}"
        elif task == 'Generate Commit Message':
            base_prompt = f"Write a git commit message for the following change:\n{user_prompt}"
        elif task == 'Refactor':
            base_prompt = f"Refactor this code and improve readability:\n{user_prompt}"
        else:
            base_prompt = user_prompt
        final_prompt, trimmed = prompt_builder.build_prompt(self.ctx, base_prompt)
        response_widget.delete('1.0', tk.END)
        tok_count = approx_tokens(final_prompt)
        self.widgets['token_var'].set(f"Estimated prompt tokens: {tok_count}")
        emit('INFO', 'BUILD', 'Token count', tokens=tok_count)
        if trimmed:
            self.status_bar.set_status('⚠️ Context trimmed to fit within limits.')
        else:
            self.status_bar.set_status('💬 Thinking... please wait.')
        model = self.widgets['model_var'].get()
        result, usage = send_prompt(final_prompt, model=model, task=task)
        self.last_prompt_cost = estimate_cost(usage, model) if usage else 0.0
        response_widget.insert(tk.END, result)
        self.ctx.generated_files = file_generator.parse_generated_files(result)
        self.files_update(self.ctx.generated_files)
        self.status_bar.set_status('✅ Done.')
        self.status_bar.update_usage(self.ctx.settings.get('show_prompt_cost', True), self.last_prompt_cost)
        self.refresh_history()

    def update_token_estimate(self, _event=None):
        prompt = self.widgets['prompt_entry'].get('1.0', tk.END).strip()
        est_prompt, _ = prompt_builder.build_prompt(self.ctx, prompt)
        tokens = approx_tokens(est_prompt)
        self.widgets['token_var'].set(f"Estimated prompt tokens: {tokens}")

    # --- File saving ---
    def save_generated_file(self, item, mode):
        try:
            path = file_generator.save_generated_file(self.ctx, item, mode)
            self.status_bar.set_status(f"✅ Saved {path}")
        except Exception as e:
            messagebox.showerror('Save Error', str(e))
            self.status_bar.set_status(f"⚠️ Error: {e}")

    # --- Project management ---
    def choose_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.status_bar.set_status('🔍 Scanning project...')
            threading.Thread(target=self._scan_thread, args=(folder,)).start()

    def _scan_thread(self, folder):
        def progress(count, done):
            if done:
                self.status_bar.set_status('✅ Project loaded')
            else:
                self.status_bar.set_status(f"Summarized {count} files")
            self.status_bar.update_usage()
        context_manager.scan_folder(folder, self.ctx, progress)
        self.ctx.project_root = folder

    def new_project(self):
        name = simpledialog.askstring('New Project', 'Project name:')
        if name:
            folder = project_manager.new_project(self.ctx, name)
            self.status_bar.set_status('🆕 Project created')

    def load_project(self):
        file_path = filedialog.askopenfilename(initialdir=project_manager.PROJECTS_DIR, filetypes=[('Codex Project', '*.codexproj')])
        if file_path:
            project_manager.load_project(self.ctx, file_path)
            self.status_bar.set_status('📁 Project loaded')
            self.refresh_history()

    def save_project_as(self):
        name = simpledialog.askstring('Save Project As', 'Project name:')
        if name:
            project_manager.save_project_as(self.ctx, name)
            self.status_bar.set_status('💾 Project saved')


__all__ = ['UIEvents']
