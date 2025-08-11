import os
import json
from typing import Callable, Dict

from services.openai_helper import send_prompt
from utils import file_hash
from logging_bus import emit


def load_summary_cache(folder: str) -> Dict[str, dict]:
    path = os.path.join(folder, 'summaries.json')
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_summary_cache(folder: str, data: Dict[str, dict]) -> None:
    path = os.path.join(folder, 'summaries.json')
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def summarize_file(path: str) -> str:
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        return f"[Error reading file] {e}"
    if len(content) > 15000:
        content = content[:15000]
    prompt = f"Summarize the purpose of this file in 1–2 sentences:\n\n{content}"
    summary, _ = send_prompt(prompt)
    return summary.strip()


def scan_folder(folder: str, context, progress: Callable[[int, bool], None] | None = None) -> None:
    summary_cache = load_summary_cache(folder)
    context.context_summary = {}
    summaries = []
    for root, _, files in os.walk(folder):
        for name in files:
            if not name.lower().endswith(('.py', '.md', '.txt', '.json')):
                continue
            path = os.path.join(root, name)
            try:
                if os.path.getsize(path) > 100 * 1024:
                    continue
            except OSError:
                continue
            rel = os.path.relpath(path, folder)
            h = file_hash(path)
            cached = summary_cache.get(rel)
            if cached and cached.get('hash') == h:
                summary = cached['summary']
            else:
                emit('INFO', 'SYSTEM', f'Scanning {rel}')
                summary = summarize_file(path)
                summary_cache[rel] = {'hash': h, 'summary': summary}
            context.context_summary[rel] = summary
            summaries.append(summary)
            if progress:
                progress(len(context.context_summary), False)
            emit('INFO', 'SYSTEM', f'Summarized {len(context.context_summary)} files')
    save_summary_cache(folder, summary_cache)
    if summaries:
        prompt = 'Create a short project overview from these file summaries:\n' + '\n'.join(summaries)
        overview, _ = send_prompt(prompt)
        context.project_overview = overview.strip()
    if progress:
        progress(len(context.context_summary), True)


__all__ = ['scan_folder', 'summarize_file', 'load_summary_cache', 'save_summary_cache']
