import os
import json
import time
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DEFAULT_MODEL = "gpt-3.5-turbo"
MAX_TOKENS = 300

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR
USAGE_FILE = PROJECT_DIR / "usage.json"
HISTORY_FILE = PROJECT_DIR / "history.json"


def set_project_dir(path: str) -> None:
    """Set file paths for usage and history under a project directory."""
    global PROJECT_DIR, USAGE_FILE, HISTORY_FILE, usage_data
    PROJECT_DIR = Path(path)
    PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    USAGE_FILE = PROJECT_DIR / "usage.json"
    HISTORY_FILE = PROJECT_DIR / "history.json"
    usage_data = _load_json(
        USAGE_FILE,
        {
            "session_tokens": 0,
            "session_cost": 0.0,
            "total_tokens": 0,
            "total_cost": 0.0,
        },
    )
    usage_data["session_tokens"] = 0
    usage_data["session_cost"] = 0.0
    _save_usage()


def _load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


usage_data = _load_json(USAGE_FILE, {
    "session_tokens": 0,
    "session_cost": 0.0,
    "total_tokens": 0,
    "total_cost": 0.0,
})


def _save_usage() -> None:
    PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(USAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(usage_data, f, indent=2)
    except Exception:
        pass

# reset session on startup after helper is defined
usage_data["session_tokens"] = 0
usage_data["session_cost"] = 0.0
_save_usage()


def _record_history(entry: dict) -> None:
    PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    data = _load_json(HISTORY_FILE, [])
    data.append(entry)
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def get_usage() -> dict:
    """Return current usage stats."""
    return usage_data

def send_prompt(prompt_text: str, model: str = DEFAULT_MODEL, task: str = ""):
    """Send a prompt to OpenAI and record history and usage."""
    if len(prompt_text) > 10_000:
        return "[ERROR] Prompt too long. Try disabling project context.", None
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful coding assistant."},
                {"role": "user", "content": prompt_text},
            ],
            temperature=0.7,
            max_tokens=500,
        )
        message = response.choices[0].message.content.strip()
        usage = response.usage
        cost = estimate_cost(usage, model)
        usage_data["session_tokens"] += usage.total_tokens
        usage_data["session_cost"] += cost
        usage_data["total_tokens"] += usage.total_tokens
        usage_data["total_cost"] += cost
        _save_usage()
        _record_history({
            "ts": time.time(),
            "model": model,
            "task": task,
            "prompt": prompt_text,
            "response": message,
            "tokens": usage.total_tokens,
            "cost": cost,
        })
        return message, usage
    except Exception as e:
        _record_history({
            "ts": time.time(),
            "model": model,
            "task": task,
            "prompt": prompt_text,
            "response": f"[ERROR] {str(e)}",
            "tokens": 0,
            "cost": 0,
        })
        return f"[ERROR] {str(e)}", None

def estimate_cost(usage, model):
    input_tokens = usage.prompt_tokens
    output_tokens = usage.completion_tokens
    total_tokens = usage.total_tokens

    if model == "gpt-3.5-turbo":
        return total_tokens / 1000 * 0.0015
    elif model == "gpt-4":
        # Based on typical 2025 pricing
        return (input_tokens / 1000 * 0.01) + (output_tokens / 1000 * 0.03)
    return 0.0

__all__ = [
    "send_prompt",
    "get_usage",
    "estimate_cost",
    "set_project_dir",
]

