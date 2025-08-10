import tkinter as tk
from ttkbootstrap import Style


def create_settings_panel(ctx, root, style: Style):
    settings_btn = tk.Button(root, text='⚙️')
    settings_menu = tk.Menu(root, tearoff=False)

    use_ctx = tk.BooleanVar(value=ctx.settings.get('use_project_context', True))
    include_hist = tk.BooleanVar(value=ctx.settings.get('include_history', False))
    show_cost = tk.BooleanVar(value=ctx.settings.get('show_prompt_cost', True))

    def _apply_settings():
        ctx.settings['use_project_context'] = use_ctx.get()
        ctx.settings['include_history'] = include_hist.get()
        ctx.settings['show_prompt_cost'] = show_cost.get()

    settings_menu.add_checkbutton(label='Use project context', variable=use_ctx, command=_apply_settings)
    settings_menu.add_checkbutton(label='Include chat history', variable=include_hist, command=_apply_settings)
    settings_menu.add_checkbutton(label='Show prompt cost', variable=show_cost, command=_apply_settings)

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
