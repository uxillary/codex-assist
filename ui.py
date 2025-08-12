"""PySimpleGUI layouts and helpers."""
import PySimpleGUI as sg
from state import AppState


def create_main_window(state: AppState) -> sg.Window:
    sg.theme('DarkGrey9')  # use existing dark theme

    project_row = [
        sg.Input(state.project.name, key='-PROJECT_NAME-', size=(25, 1)),
        sg.Button('✨', key='-BTN_NEW-', tooltip='New Project'),
        sg.Button('🗂️', key='-BTN_OPEN-', tooltip='Open Project'),
        sg.Button('✓', key='-BTN_SAVE_NAME-', tooltip='Save Project Name'),
        sg.Button('📁', key='-BTN_LOAD_FOLDER-', tooltip='Add/Load Folder'),
        sg.Button('🧹', key='-BTN_CLEAR_CHAT-', tooltip='Clear Chat History'),
        sg.Button('🔥', key='-BTN_WIPE_CONTEXT-', tooltip='Wipe Context', button_color=('white', 'firebrick4')),
    ]

    prompt_row = [
        sg.Input(key='-PROMPT-', expand_x=True, do_not_clear=False),
        sg.Button('Ask', key='-ASK-', tooltip='Send prompt'),
        sg.Text('Ready', key='-STATUS-', size=(16, 1), justification='right')
    ]

    response = sg.Multiline('', key='-RESPONSE-', expand_x=True, expand_y=True, disabled=True, autoscroll=True)
    console = sg.Multiline('', key='-CONSOLE-', size=(None, 5), disabled=True, autoscroll=True)

    bottom_row = [
        sg.Text('Estimated prompt tokens: 0', key='-EST_TOKENS-'),
        sg.Push(),
        sg.Text('Prompt £0.0000 | Session £0.0000', key='-EST_COST-')
    ]

    layout = [
        project_row,
        prompt_row,
        [response],
        [console],
        bottom_row,
    ]

    window = sg.Window('Codex Assist', layout, return_keyboard_events=True, finalize=True)
    return window
