"""Event handlers for the PySimpleGUI application."""
from pathlib import Path
import PySimpleGUI as sg

from state import AppState, Project
import tokens
import persistence


def append_console(window, text: str) -> None:
    if "-CONSOLE-" in window.AllKeysDict:
        current = window["-CONSOLE-"].get() or ""
        window["-CONSOLE-"].update(current + text + "\n")


def update_status(window, state: AppState, text: str = None) -> None:
    if text is not None:
        window["-STATUS-"].update(text)
        return
    if state.is_building_context:
        window["-STATUS-"].update("Building context…")
        window["-ASK-"].update(disabled=True)
    else:
        window["-STATUS-"].update("Ready")
        window["-ASK-"].update(disabled=False)


def handle_new_project(window, state: AppState, values):
    if sg.popup_yes_no("Start a new project? This clears chat history but keeps current context unless you also wipe it.") != "Yes":
        return
    state.project.chat_history.clear()
    window["-RESPONSE-"].update("")
    state.project.name = ""
    window["-PROJECT_NAME-"].update("")
    append_console(window, "Started new project")
    update_status(window, state)
    tokens.recalc_and_update(window, state)


def handle_open_project(window, state: AppState, values):
    path = sg.popup_get_file("Open Project", initial_folder=persistence.PROJECT_ROOT, file_types=(("Project", "*.json"),))
    if not path:
        return
    name = Path(path).stem
    proj = persistence.load_project(name)
    if proj:
        state.project = proj
        window["-PROJECT_NAME-"].update(proj.name)
        window["-RESPONSE-"].update("")
        append_console(window, f"Opened project: {proj.name}")
        update_status(window, state)
        tokens.recalc_and_update(window, state)


def handle_save_name(window, state: AppState, values):
    name = values.get("-PROJECT_NAME-", "").strip()
    if not name:
        return
    state.project.name = name
    persistence.save_project(state.project)
    append_console(window, f"Saved project: {name}")
    update_status(window, state, "Saved")
    tokens.recalc_and_update(window, state)


def handle_load_folder(window, state: AppState, values):
    folder = sg.popup_get_folder("Select folder")
    if not folder:
        return
    state.is_building_context = True
    update_status(window, state)
    try:
        for path in Path(folder).rglob('*'):
            if path.is_file():
                try:
                    content = path.read_text(encoding='utf-8')
                except Exception:
                    continue
                state.project.context_chunks.append(content[:500])
        state.project.folder = folder
        append_console(window, f"Loaded folder: {folder}")
    finally:
        state.is_building_context = False
        update_status(window, state)
        tokens.recalc_and_update(window, state)


def handle_clear_chat(window, state: AppState, values):
    state.project.chat_history.clear()
    window["-RESPONSE-"].update("")
    append_console(window, "Chat history cleared")
    update_status(window, state)
    tokens.recalc_and_update(window, state)


def handle_wipe_context(window, state: AppState, values):
    if sg.popup_yes_no("Wipe project context? This removes all loaded files/summaries. Chat history remains unless also cleared.") != "Yes":
        return
    state.project.context_chunks.clear()
    append_console(window, "Context wiped")
    update_status(window, state)
    tokens.recalc_and_update(window, state)


def handle_ask(window, state: AppState, values):
    prompt = values.get("-PROMPT-", "").strip()
    if not prompt:
        return
    state.project.chat_history.append({"role": "user", "content": prompt})
    state.is_building_context = True
    update_status(window, state)
    append_console(window, f"User: {prompt}")
    # Simulate assistant response
    reply = f"Echo: {prompt}"
    state.project.chat_history.append({"role": "assistant", "content": reply})
    window["-RESPONSE-"].update(reply)
    state.is_building_context = False
    update_status(window, state)
    append_console(window, f"Assistant: {reply}")
    tokens.recalc_and_update(window, state, prompt, add_cost=True)


def handle_event(window, state: AppState, event, values):
    if event in ("-BTN_NEW-", "Ctrl+N"):
        handle_new_project(window, state, values)
    elif event in ("-BTN_OPEN-", "Ctrl+O"):
        handle_open_project(window, state, values)
    elif event in ("-BTN_SAVE_NAME-", "Ctrl+S"):
        handle_save_name(window, state, values)
    elif event in ("-BTN_LOAD_FOLDER-", "Ctrl+Shift+F"):
        handle_load_folder(window, state, values)
    elif event in ("-BTN_CLEAR_CHAT-", "Ctrl+L"):
        handle_clear_chat(window, state, values)
    elif event in ("-BTN_WIPE_CONTEXT-", "Ctrl+Shift+Delete"):
        handle_wipe_context(window, state, values)
    elif event == "-ASK-":
        handle_ask(window, state, values)

