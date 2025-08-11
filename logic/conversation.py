import json
import os
from typing import Tuple


def build_conversation_context(project_dir: str, recent_turns_count: int) -> Tuple[str, str]:
    """Load running summary and recent turns from project history.

    Args:
        project_dir: Project directory containing history and summary files.
        recent_turns_count: Number of recent turns to include.

    Returns:
        running_summary: Text from running_summary.txt or empty string.
        recent_turns_text: Formatted recent dialogue turns or empty string.
    """
    summary_path = os.path.join(project_dir, "running_summary.txt")
    history_path = os.path.join(project_dir, "history.json")

    try:
        with open(summary_path, "r", encoding="utf-8") as f:
            running_summary = f.read().strip()
    except Exception:
        running_summary = ""

    try:
        with open(history_path, "r", encoding="utf-8") as f:
            history = json.load(f)
    except Exception:
        history = []

    recent_text = ""
    if recent_turns_count > 0 and history:
        recent_items = list(reversed(history[-recent_turns_count:]))
        formatted = []
        for item in recent_items:
            prompt = item.get("prompt", "").strip()
            response = item.get("response", "").strip()
            formatted.append(f"User: {prompt}\nAssistant: {response}")
        recent_text = "\n\n".join(formatted)

    return running_summary, recent_text


__all__ = ["build_conversation_context"]
