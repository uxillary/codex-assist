import threading
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox

from services.openai_helper import stream_chat, estimate_cost
from logic import prompt_builder, file_generator, context_manager, project_manager
from logic.turn_summary import summarize_turn
from utils import approx_tokens
from logging_bus import emit


class UIEvents:
    def __init__(self, ctx, widgets, files_update, status_bar, refresh_history, app, folder_btn, progress):
        self.ctx = ctx
        self.widgets = widgets
        self.files_update = files_update
        self.status_bar = status_bar
        self.refresh_history = refresh_history
        self.app = app
        self.folder_btn = folder_btn
        self.progress = progress
        self.cancel_stream = False
        widgets['ask_btn'].config(command=self.generate_response)
        widgets['prompt_entry'].bind('<KeyRelease>', self.update_token_estimate)
        widgets['cancel_btn'].config(command=self.cancel_streaming)
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
        self.widgets['context_var'].set(
            f"Context: {self.ctx.settings.get('context_tier', 'Standard')} + "
            f"{'memory' if self.ctx.settings.get('use_conversation_memory', True) else 'no memory'} + "
            f"{self.ctx.settings.get('recent_turns_count', 2)} turns (~{tok_count} tokens)"
        )
        emit('INFO', 'BUILD', 'Context',
             repo=self.ctx.settings.get('use_project_context'),
             memory=self.ctx.settings.get('use_conversation_memory', True),
             turns=self.ctx.settings.get('recent_turns_count', 2),
             est_in_tokens=tok_count)
        status_txt = 'Thinking…'
        if trimmed:
            status_txt += ' (Context trimmed)'
        self.status_bar.set_status(status_txt)
        model = self.widgets['model_var'].get()
        buffer = []
        self.cancel_stream = False
        self.widgets['cancel_btn'].pack(side='left', padx=2)
        self.widgets['ask_btn'].config(state='disabled')

        def flush_buffer():
            if buffer:
                response_widget.insert(tk.END, ''.join(buffer))
                buffer.clear()
            if not getattr(self, 'stream_done', False):
                response_widget.after(50, flush_buffer)

        def on_chunk(text):
            buffer.append(text)

        def on_done(full_text, usage):
            self.stream_done = True
            self.last_prompt_cost = estimate_cost(usage, model) if usage else 0.0
            self.ctx.generated_files = file_generator.parse_generated_files(full_text)
            self.files_update(self.ctx.generated_files)
            self.status_bar.set_status('✅ Done.' if not self.cancel_stream else '⛔ Cancelled')
            self.status_bar.update_usage(self.ctx.settings.get('show_prompt_cost', True), self.last_prompt_cost)
            self.widgets['cancel_btn'].pack_forget()
            self.widgets['ask_btn'].config(state='normal')
            if not self.cancel_stream:
                summarize_turn(user_prompt, full_text)
            self.refresh_history()

        def on_error(msg):
            self.stream_done = True
            response_widget.insert(tk.END, f"[ERROR] {msg}")
            self.status_bar.set_status(f"⚠️ {msg}")
            self.widgets['cancel_btn'].pack_forget()
            self.widgets['ask_btn'].config(state='normal')
            self.refresh_history()

        def worker():
            stream_chat(final_prompt, model, task, on_chunk, on_done, on_error, lambda: self.cancel_stream)

        self.stream_done = False
        threading.Thread(target=worker, daemon=True).start()
        flush_buffer()

    def update_token_estimate(self, _event=None):
        prompt = self.widgets['prompt_entry'].get('1.0', tk.END).strip()
        est_prompt, _ = prompt_builder.build_prompt(self.ctx, prompt)
        tokens = approx_tokens(est_prompt)
        self.widgets['token_var'].set(f"Estimated prompt tokens: {tokens}")
        self.widgets['context_var'].set(
            f"Context: {self.ctx.settings.get('context_tier', 'Standard')} + "
            f"{'memory' if self.ctx.settings.get('use_conversation_memory', True) else 'no memory'} + "
            f"{self.ctx.settings.get('recent_turns_count', 2)} turns (~{tokens} tokens)"
        )

    def cancel_streaming(self):
        self.cancel_stream = True
        self.widgets['cancel_btn'].pack_forget()

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
            self.start_busy_ui()
            threading.Thread(target=self._scan_thread, args=(folder,)).start()

    def _scan_thread(self, folder):
        def progress(count, done):
            if done:
                self.app.after(0, self.stop_busy_ui)
                self.app.after(0, lambda: self.status_bar.set_status('✅ Project loaded'))
            else:
                self.app.after(0, lambda: self.status_bar.set_status(f"Summarized {count} files"))
            self.app.after(0, self.status_bar.update_usage)
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

    # --- Busy UI helpers ---
    def start_busy_ui(self):
        self.app.config(cursor='wait')
        self.folder_btn.config(state='disabled')
        self.widgets['ask_btn'].config(state='disabled')
        self.progress.pack(side='left', padx=5)
        self.progress.start()

    def stop_busy_ui(self):
        self.app.config(cursor='arrow')
        self.folder_btn.config(state='normal')
        self.widgets['ask_btn'].config(state='normal')
        self.progress.stop()
        self.progress.pack_forget()


__all__ = ['UIEvents']
