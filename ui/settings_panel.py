import tkinter as tk
from tkinter import filedialog, messagebox
from ttkbootstrap import Style
import os
from pathlib import Path


class MenuToolTip:
    """Simple tooltip for Tkinter Menu items."""

    def __init__(self, menu: tk.Menu, descriptions: dict[int, str]):
        self.menu = menu
        self.descriptions = descriptions
        self.tip = None
        menu.bind("<Motion>", self._on_motion)
        menu.bind("<Leave>", lambda _e: self._hide())

    def _on_motion(self, event: tk.Event) -> None:
        index = self.menu.index(f"@{event.y}")
        if index is None:
            self._hide()
            return
        text = self.descriptions.get(index)
        if text:
            self._show(text, event.x_root + 10, event.y_root + 10)
        else:
            self._hide()

    def _show(self, text: str, x: int, y: int) -> None:
        self._hide()
        self.tip = tw = tk.Toplevel(self.menu)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tk.Label(tw, text=text, background="#ffffe0", relief="solid", borderwidth=1).pack()

    def _hide(self) -> None:
        if self.tip is not None:
            self.tip.destroy()
            self.tip = None


def create_settings_panel(ctx, root, style: Style, refresh_history=None):
    settings_btn = tk.Button(root, text='⚙️')
    settings_menu = tk.Menu(root, tearoff=False)
    tooltips: dict[int, str] = {}

    use_ctx = tk.BooleanVar(value=ctx.settings.get('use_project_context', True))
    include_hist = tk.BooleanVar(value=ctx.settings.get('include_history', False))
    show_cost = tk.BooleanVar(value=ctx.settings.get('show_prompt_cost', True))
    use_turn_summaries = tk.BooleanVar(value=ctx.settings.get('use_turn_summaries', True))
    use_memory = tk.BooleanVar(value=ctx.settings.get('use_conversation_memory', True))
    recent_turns = tk.IntVar(value=ctx.settings.get('recent_turns_count', 2))
    context_tier = tk.StringVar(value=ctx.settings.get('context_tier', 'Standard'))

    def _apply_settings():
        ctx.settings['use_project_context'] = use_ctx.get()
        ctx.settings['include_history'] = include_hist.get()
        ctx.settings['show_prompt_cost'] = show_cost.get()
        ctx.settings['use_turn_summaries'] = use_turn_summaries.get()
        ctx.settings['context_tier'] = context_tier.get()
        ctx.settings['use_conversation_memory'] = use_memory.get()
        ctx.settings['recent_turns_count'] = int(recent_turns.get())

    settings_menu.add_checkbutton(label='Use project context', variable=use_ctx, command=_apply_settings)
    tooltips[settings_menu.index('end')] = 'Include summaries of project files when prompting.'
    settings_menu.add_checkbutton(label='Include chat history', variable=include_hist, command=_apply_settings)
    tooltips[settings_menu.index('end')] = 'Send previous conversation turns in prompts.'
    settings_menu.add_checkbutton(label='Use turn summaries', variable=use_turn_summaries, command=_apply_settings)
    tooltips[settings_menu.index('end')] = 'Summarize earlier turns to save tokens.'
    settings_menu.add_checkbutton(label='Use conversation memory', variable=use_memory, command=_apply_settings)
    tooltips[settings_menu.index('end')] = 'Keep long-term memory of the conversation.'
    settings_menu.add_checkbutton(label='Show prompt cost', variable=show_cost, command=_apply_settings)
    tooltips[settings_menu.index('end')] = 'Display estimated token usage and cost.'

    def _recent_turns_dialog():
        win = tk.Toplevel(root)
        win.title('Recent full turns')
        tk.Label(win, text='Recent full turns:').pack(padx=10, pady=5)
        spin = tk.Spinbox(win, from_=0, to=5, textvariable=recent_turns, width=5)
        spin.pack(padx=10, pady=5)
        tk.Button(win, text='OK', command=lambda: [ _apply_settings(), win.destroy() ]).pack(pady=5)

    settings_menu.add_command(label='Recent full turns', command=_recent_turns_dialog)
    tooltips[settings_menu.index('end')] = 'Number of most recent turns to include fully.'

    tier_menu = tk.Menu(settings_menu, tearoff=False)
    for tier in ['Basic', 'Standard', 'Detailed']:
        tier_menu.add_radiobutton(label=tier, value=tier, variable=context_tier, command=_apply_settings)
    settings_menu.add_cascade(label='Context tier', menu=tier_menu)
    tooltips[settings_menu.index('end')] = 'Choose how detailed the project context should be.'

    def _select_detailed():
        initial = getattr(ctx, 'project_root', '') or '.'
        files = filedialog.askopenfilenames(initialdir=initial)
        if files:
            root = getattr(ctx, 'project_root', '')
            ctx.settings['detailed_files'] = [os.path.relpath(f, root) if root and f.startswith(root) else f for f in files]
            ctx.save_settings()
    settings_menu.add_command(label='Select detailed files', command=_select_detailed)
    tooltips[settings_menu.index('end')] = 'Pick files that always use detailed summaries.'

    theme_choice = tk.StringVar(value=ctx.settings.get('theme', 'darkly'))
    theme_menu = tk.Menu(settings_menu, tearoff=False)
    for theme in ['darkly', 'flatly']:
        theme_menu.add_radiobutton(label=theme, value=theme, variable=theme_choice)
    settings_menu.add_cascade(label='Theme', menu=theme_menu)
    tooltips[settings_menu.index('end')] = 'Switch the application theme.'

    def _clear_context():
        if not messagebox.askyesno('Clear context', 'Remove all saved project context summaries?'):
            return
        ctx.context_summary = {}
        ctx.project_overview = ''
        if getattr(ctx, 'active_project', ''):
            path = Path(ctx.active_project) / 'context_summary.json'
            try:
                path.unlink()
            except Exception:
                pass

    settings_menu.add_command(label='Clear project context', command=_clear_context)
    tooltips[settings_menu.index('end')] = 'Delete cached summaries for project files.'

    def _clear_history():
        if not messagebox.askyesno('Clear chat history', 'Delete all stored chat history?'):
            return
        for p in [ctx.history_path, ctx.turn_summaries_path]:
            try:
                os.remove(p)
            except Exception:
                pass
        try:
            summary_file = Path(ctx.history_path).parent / 'running_summary.txt'
            summary_file.unlink()
        except Exception:
            pass
        if refresh_history:
            refresh_history()

    settings_menu.add_command(label='Clear chat history', command=_clear_history)
    tooltips[settings_menu.index('end')] = 'Erase saved chat exchanges.'

    def change_theme(*_):
        style.theme_use(theme_choice.get())
        ctx.settings['theme'] = theme_choice.get()
    theme_choice.trace_add('write', change_theme)

    def show_menu(event=None):
        settings_menu.tk_popup(settings_btn.winfo_rootx(), settings_btn.winfo_rooty()+settings_btn.winfo_height())

    settings_btn.config(command=show_menu)
    MenuToolTip(settings_menu, tooltips)
    return settings_btn


__all__ = ['create_settings_panel']
