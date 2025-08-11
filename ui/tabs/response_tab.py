import tkinter as tk
from tkinter import ttk


def create_tab(ctx, parent):
    frame = ttk.Frame(parent)

    prompt_frame = ttk.LabelFrame(frame, text='Prompt', padding=10)
    prompt_frame.pack(fill='x')
    prompt_entry = tk.Text(prompt_frame, height=6, wrap='word')
    prompt_entry.pack(fill='both', expand=True)

    option_frame = ttk.Frame(prompt_frame, padding=5)
    option_frame.pack(fill='x')
    task_var = tk.StringVar(value='Custom')
    task_dropdown = ttk.Combobox(option_frame, textvariable=task_var, state='readonly')
    task_dropdown['values'] = ['Custom', 'Explain Code', 'Generate Commit Message', 'Refactor']
    task_dropdown.current(0)
    task_dropdown.pack(side='left')

    model_var = tk.StringVar(value=ctx.model)
    model_dropdown = ttk.Combobox(option_frame, textvariable=model_var, state='readonly')
    model_dropdown['values'] = ['gpt-3.5-turbo', 'gpt-4']
    model_dropdown.current(0)
    model_dropdown.pack(side='left', padx=10)

    ask_btn = ttk.Button(option_frame, text='🤖 Ask')
    ask_btn.pack(side='left', padx=10)

    token_var = tk.StringVar(value='Estimated prompt tokens: 0')
    token_label = ttk.Label(option_frame, textvariable=token_var)
    token_label.pack(side='right')

    response_frame = ttk.LabelFrame(frame, text='Response', padding=10)
    response_frame.pack(fill='both', expand=True, pady=(10, 0))
    text_container = ttk.Frame(response_frame)
    text_container.pack(fill='both', expand=True)
    response_text = tk.Text(text_container, wrap='word', height=10)
    scroll = ttk.Scrollbar(text_container, orient='vertical', command=response_text.yview)
    response_text.configure(yscrollcommand=scroll.set)
    response_text.pack(side='left', fill='both', expand=True)
    scroll.pack(side='right', fill='y')
    btn_bar = ttk.Frame(response_frame)
    btn_bar.pack(fill='x', pady=5)
    copy_btn = ttk.Button(btn_bar, text='Copy', command=lambda: frame.clipboard_append(response_text.get('1.0', tk.END)))
    copy_btn.pack(side='left', padx=2)
    clear_btn = ttk.Button(btn_bar, text='Clear', command=lambda: response_text.delete('1.0', tk.END))
    clear_btn.pack(side='left', padx=2)
    cancel_btn = ttk.Button(btn_bar, text='Cancel')
    cancel_btn.pack(side='left', padx=2)
    cancel_btn.pack_forget()

    return {
        'frame': frame,
        'prompt_entry': prompt_entry,
        'response_text': response_text,
        'ask_btn': ask_btn,
        'token_var': token_var,
        'model_var': model_var,
        'task_var': task_var,
        'cancel_btn': cancel_btn,
    }


__all__ = ['create_tab']
