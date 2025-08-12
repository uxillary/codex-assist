"""Application entry point launching the Tkinter UI."""

from context import AppContext
from ui.layout import launch_ui


def main() -> None:
    """Start the desktop assistant."""
    ctx = AppContext()
    launch_ui(ctx)


if __name__ == "__main__":
    main()
