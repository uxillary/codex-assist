from context import AppContext
from ui.layout import launch_ui
from logging_bus import start_dispatcher


def main():
    start_dispatcher()
    ctx = AppContext()
    launch_ui(ctx)


if __name__ == '__main__':
    main()
