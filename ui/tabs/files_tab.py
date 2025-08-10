import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Callable


def create_tab(parent, save_callback: Callable[[Dict[str, str], str], None]):
    frame = ttk.Frame(parent, padding=10)
    canvas = tk.Canvas(frame)
    scroll = ttk.Scrollbar(frame, orient='vertical', command=canvas.yview)
    canvas.configure(yscrollcommand=scroll.set)
    scroll.pack(side='right', fill='y')
    canvas.pack(side='left', fill='both', expand=True)
    inner = ttk.Frame(canvas)
    canvas.create_window((0, 0), window=inner, anchor='nw')

    def update(files: List[Dict[str, str]]):
        for widget in inner.winfo_children():
            widget.destroy()
        for item in files:
            f = ttk.Frame(inner, padding=5)
            f.pack(fill='x', pady=5)
            ttk.Label(f, text=item['filename']).pack(anchor='w')
            text = tk.Text(f, height=min(10, len(item['code'].splitlines())), wrap='none')
            text.insert('1.0', item['code'])
            text.configure(state='disabled')
            text.pack(fill='both', expand=True, pady=2)
            opt_var = tk.StringVar(value=item.get('mode', 'append'))
            mode_dd = ttk.Combobox(f, textvariable=opt_var, state='readonly', width=10)
            mode_dd['values'] = ['append', 'overwrite']
            mode_dd.pack(side='left', pady=2)
            ttk.Button(f, text='💾 Save File', command=lambda it=item, var=opt_var: save_callback(it, var.get())).pack(side='right', padx=5, pady=2)
        canvas.configure(scrollregion=canvas.bbox('all'))

    inner.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
    return frame, update


__all__ = ['create_tab']
