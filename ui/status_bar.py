import tkinter as tk
from services.openai_helper import get_usage


class StatusBar:
    def __init__(self, root):
        self.status_var = tk.StringVar()
        self.usage_var = tk.StringVar()
        frame = tk.Frame(root)
        frame.pack(side='bottom', fill='x')
        tk.Label(frame, textvariable=self.status_var).pack(side='left', padx=10)
        tk.Label(frame, textvariable=self.usage_var).pack(side='right', padx=10)

    def set_status(self, text: str):
        self.status_var.set(text)

    def update_usage(self, show_cost: bool = True, last_prompt_cost: float = 0.0):
        u = get_usage()
        if show_cost:
            prompt_cost_txt = f"Prompt: ${last_prompt_cost:.4f} | "
        else:
            prompt_cost_txt = ''
        self.usage_var.set(
            f"{prompt_cost_txt}Session: {u['session_tokens']}t (${u['session_cost']:.4f}) | "
            f"Total: {u['total_tokens']}t (${u['total_cost']:.4f})"
        )


__all__ = ['StatusBar']
