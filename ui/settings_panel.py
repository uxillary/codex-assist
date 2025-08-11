import tkinter as tk
from tkinter import filedialog
from ttkbootstrap import Style
import os


def create_settings_panel(ctx, root, style: Style):
    settings_btn = tk.Button(root, text='⚙️')
    settings_menu = tk.Menu(root, tearoff=False)

    use_ctx = tk.BooleanVar(value=ctx.settings.get('use_project_context', True))
    include_hist = tk.BooleanVar(value=ctx.settings.get('include_history', False))
    show_cost = tk.BooleanVar(value=ctx.settings.get('show_prompt_cost', True))
    use_turn_summaries = tk.BooleanVar(value=ctx.settings.get('use_turn_summaries', True))
    context_tier = tk.StringVar(value=ctx.settings.get('context_tier', 'Standard'))

    def _apply_settings():
        ctx.settings['use_project_context'] = use_ctx.get()
        ctx.settings['include_history'] = include_hist.get()
        ctx.settings['show_prompt_cost'] = show_cost.get()
        ctx.settings['use_turn_summaries'] = use_turn_summaries.get()
        ctx.settings['context_tier'] = context_tier.get()

    settings_menu.add_checkbutton(label='Use project context', variable=use_ctx, command=_apply_settings)
    settings_menu.add_checkbutton(label='Include chat history', variable=include_hist, command=_apply_settings)
    settings_menu.add_checkbutton(label='Use turn summaries', variable=use_turn_summaries, command=_apply_settings)
    settings_menu.add_checkbutton(label='Show prompt cost', variable=show_cost, command=_apply_settings)

    tier_menu = tk.Menu(settings_menu, tearoff=False)
    for tier in ['Basic', 'Standard', 'Detailed']:
        tier_menu.add_radiobutton(label=tier, value=tier, variable=context_tier, command=_apply_settings)
    settings_menu.add_cascade(label='Context tier', menu=tier_menu)

    def _select_detailed():
        initial = getattr(ctx, 'project_root', '') or '.'
        files = filedialog.askopenfilenames(initialdir=initial)
        if files:
            root = getattr(ctx, 'project_root', '')
            ctx.settings['detailed_files'] = [os.path.relpath(f, root) if root and f.startswith(root) else f for f in files]
            ctx.save_settings()
    settings_menu.add_command(label='Select detailed files', command=_select_detailed)

    theme_choice = tk.StringVar(value=ctx.settings.get('theme', 'darkly'))
    theme_menu = tk.Menu(settings_menu, tearoff=False)
    for theme in ['darkly', 'flatly']:
        theme_menu.add_radiobutton(label=theme, value=theme, variable=theme_choice)
    settings_menu.add_cascade(label='Theme', menu=theme_menu)

    def change_theme(*_):
        style.theme_use(theme_choice.get())
        ctx.settings['theme'] = theme_choice.get()
    theme_choice.trace_add('write', change_theme)

    def show_menu(event=None):
        settings_menu.tk_popup(settings_btn.winfo_rootx(), settings_btn.winfo_rooty()+settings_btn.winfo_height())

    settings_btn.config(command=show_menu)
    return settings_btn


__all__ = ['create_settings_panel']
