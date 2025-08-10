import json
import tkinter as tk
from tkinter import ttk


def create_tab(ctx, parent):
    frame = ttk.Frame(parent, padding=10)
    history_text = tk.Text(frame, wrap='word', state='disabled')
    history_text.pack(side='left', fill='both', expand=True)

    def refresh():
        try:
            with open(ctx.history_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            data = []
        history_text.configure(state='normal')
        history_text.delete('1.0', tk.END)
        for item in data[-50:]:
            line = f"[{item.get('ts', 0):.0f}] {item.get('task', '')} -> {item.get('model', '')}\n{item.get('response', '')}\n\n"
            history_text.insert(tk.END, line)
        history_text.configure(state='disabled')

    return frame, refresh


__all__ = ['create_tab']
