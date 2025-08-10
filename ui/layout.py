import tkinter as tk
from tkinter import ttk
from ttkbootstrap import Style

from ui.status_bar import StatusBar
from ui.settings_panel import create_settings_panel
from ui.tabs.response_tab import create_tab as create_response_tab
from ui.tabs.history_tab import create_tab as create_history_tab
from ui.tabs.files_tab import create_tab as create_files_tab
from ui.events import UIEvents


def launch_ui(ctx):
    app = tk.Tk()
    app.title('Codex Desktop Assistant')
    app.geometry('900x600')
    style = Style(ctx.settings.get('theme', 'darkly'))

    # Project controls
    project_frame = ttk.LabelFrame(app, text='Project Controls', padding=10)
    project_frame.pack(fill='x', padx=10, pady=10)
    # Buttons
    new_btn = ttk.Button(project_frame, text='🆕 New Project')
    load_btn = ttk.Button(project_frame, text='📂 Load Project')
    save_btn = ttk.Button(project_frame, text='💾 Save Project As')
    folder_btn = ttk.Button(project_frame, text='🗂️ Load Folder')
    for b in (new_btn, load_btn, save_btn, folder_btn):
        b.pack(side='left', padx=2)
    settings_btn = create_settings_panel(ctx, project_frame, style)
    settings_btn.pack(side='right')

    # Main layout
    main_frame = ttk.Frame(app)
    main_frame.pack(fill='both', expand=True, padx=10, pady=10)
    content_pane = ttk.Panedwindow(main_frame, orient='horizontal')
    content_pane.pack(fill='both', expand=True)
    left_panel = ttk.Frame(content_pane)
    content_pane.add(left_panel, weight=3)
    right_tabs = ttk.Notebook(content_pane)
    content_pane.add(right_tabs, weight=1)

    # Tabs
    resp_widgets = create_response_tab(ctx, left_panel)
    resp_widgets['frame'].pack(fill='both', expand=True)
    events = None
    files_tab, files_update = create_files_tab(right_tabs, lambda item, mode: events.save_generated_file(item, mode))
    right_tabs.add(files_tab, text='Generated Files')
    hist_tab, refresh_history = create_history_tab(ctx, right_tabs)
    right_tabs.add(hist_tab, text='History')

    status_bar = StatusBar(app)

    events = UIEvents(ctx, resp_widgets, lambda files: files_update(files), status_bar, refresh_history)
    new_btn.config(command=events.new_project)
    load_btn.config(command=events.load_project)
    save_btn.config(command=events.save_project_as)
    folder_btn.config(command=events.choose_folder)

    status_bar.update_usage(ctx.settings.get('show_prompt_cost', True))
    refresh_history()
    app.mainloop()


__all__ = ['launch_ui']
