import os
import json
import time
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from logging_bus import emit

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DEFAULT_MODEL = "gpt-3.5-turbo"
MAX_TOKENS = 300

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR
USAGE_FILE = PROJECT_DIR / "usage.json"
HISTORY_FILE = PROJECT_DIR / "history.json"
TURN_SUMMARIES_FILE = PROJECT_DIR / "turn_summaries.json"


def set_project_dir(path: str) -> None:
    """Set file paths for usage, history and summaries under a project directory."""
    global PROJECT_DIR, USAGE_FILE, HISTORY_FILE, TURN_SUMMARIES_FILE, usage_data
    PROJECT_DIR = Path(path)
    PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    USAGE_FILE = PROJECT_DIR / "usage.json"
    HISTORY_FILE = PROJECT_DIR / "history.json"
    TURN_SUMMARIES_FILE = PROJECT_DIR / "turn_summaries.json"
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


def save_turn_summary(text: str) -> None:
    """Append a turn summary string to the project file."""
    data = _load_json(TURN_SUMMARIES_FILE, [])
    data.append(text)
    try:
        with open(TURN_SUMMARIES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def get_usage() -> dict:
    """Return current usage stats."""
    return usage_data


def stream_chat(
    prompt_text: str,
    model: str,
    task: str,
    on_chunk,
    on_done,
    on_error,
    should_cancel,
):
    """Stream a chat completion and emit progress events."""
    emit("INFO", "STREAM", "Queued request", model=model, task=task)
    if len(prompt_text) > 10_000:
        on_error("Prompt too long. Try disabling project context.")
        return
    try:
        stream = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful coding assistant."},
                {"role": "user", "content": prompt_text},
            ],
            temperature=0.7,
            max_tokens=500,
            stream=True,
        )
        emit("INFO", "STREAM", "Sending request")
        full_text = ""
        usage = None
        for part in stream:
            if should_cancel():
                emit("WARN", "STREAM", "Stream cancelled")
                break
            delta = part.choices[0].delta
            if delta and delta.content:
                full_text += delta.content
                on_chunk(delta.content)
                emit("INFO", "STREAM", "Chunk", size=len(delta.content))
            if getattr(part.choices[0], "finish_reason", None) is not None:
                usage = getattr(part, "usage", None)
        if usage:
            cost = estimate_cost(usage, model)
            usage_data["session_tokens"] += usage.total_tokens
            usage_data["session_cost"] += cost
            usage_data["total_tokens"] += usage.total_tokens
            usage_data["total_cost"] += cost
            _save_usage()
            _record_history(
                {
                    "ts": time.time(),
                    "model": model,
                    "task": task,
                    "prompt": prompt_text,
                    "response": full_text,
                    "tokens": usage.total_tokens,
                    "cost": cost,
                }
            )
        emit("INFO", "STREAM", "Done")
        on_done(full_text, usage)
    except Exception as e:
        emit("ERROR", "STREAM", "HTTP error", error=str(e))
        on_error(str(e))

def send_prompt(prompt_text: str, model: str = DEFAULT_MODEL, task: str = ""):
    """Send a prompt to OpenAI and record history and usage."""
    if len(prompt_text) > 10_000:
        return "[ERROR] Prompt too long. Try disabling project context.", None
    emit("INFO", "NETWORK", "Sending request", model=model, task=task)
    start = time.time()
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
        latency_ms = int((time.time() - start) * 1000)
        message = response.choices[0].message.content.strip()
        usage = response.usage
        cost = estimate_cost(usage, model)
        emit(
            "INFO",
            "COST",
            "Estimated cost",
            input_tokens=usage.prompt_tokens,
            output_tokens=usage.completion_tokens,
            usd=round(cost, 4),
        )
        emit("INFO", "SYSTEM", "Request complete", latency_ms=latency_ms)
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
        emit("ERROR", "NETWORK", "HTTP error", error=str(e))
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
    "stream_chat",
    "save_turn_summary",
]

