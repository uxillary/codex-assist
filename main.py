"""Entry point wiring the PySimpleGUI application."""
import PySimpleGUI as sg

from state import AppState
from ui import create_main_window
from events import handle_event, update_status
from tokens import recalc_and_update


def main() -> None:
    state = AppState()
    window = create_main_window(state)
    update_status(window, state)
    recalc_and_update(window, state)
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        handle_event(window, state, event, values)
    window.close()


if __name__ == '__main__':
    main()
