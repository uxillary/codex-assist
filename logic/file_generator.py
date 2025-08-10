import json
import os
import re
import time
from typing import List, Dict

from services.openai_helper import HISTORY_FILE


def parse_generated_files(text: str) -> List[Dict[str, str]]:
    pattern = re.compile(
        r"(?:^|\n)(?:[#>]*\s*(?:file(?:name)?\s*:)?\s*)?([\w./-]+\.[\w\d]+)\s*\n```(?:\w+)?\n(.*?)```",
        re.DOTALL,
    )
    files = []
    for idx, (fname, code) in enumerate(pattern.findall(text), 1):
        base, ext = os.path.splitext(os.path.basename(fname.strip()))
        numbered = f"{base}_{idx:03}{ext}"
        files.append(
            {
                "filename": numbered,
                "original": fname.strip(),
                "code": code.strip(),
                "mode": "append",
            }
        )
    return files


def log_file_action(filename: str, mode: str, code: str) -> None:
    try:
        path = HISTORY_FILE
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                hist = json.load(f)
        else:
            hist = []
        hist.append(
            {
                "ts": time.time(),
                "action": "save_file",
                "file": filename,
                "mode": mode,
                "code": code,
            }
        )
        with open(path, "w", encoding="utf-8") as f:
            json.dump(hist, f, indent=2)
    except Exception:
        pass


def save_generated_file(ctx, item: Dict[str, str], mode: str) -> str:
    """Write the generated file to disk relative to project folder."""
    if not ctx.active_project:
        raise ValueError("No project folder selected")
    path = os.path.join(ctx.active_project, item["filename"])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path) and mode == "append":
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n" + item["code"])
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(item["code"])
    log_file_action(item["filename"], mode, item["code"])
    return path


__all__ = ["parse_generated_files", "save_generated_file", "log_file_action"]
