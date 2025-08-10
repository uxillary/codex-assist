import json
from typing import Tuple

from utils import approx_tokens
from context import AppContext
from logging_bus import emit


def build_prompt(ctx: AppContext, user_prompt: str) -> Tuple[str, bool]:
    """Construct the final prompt using settings and context."""
    parts = []
    token_total = 0
    char_total = 0
    trimmed = False
    if ctx.settings.get('use_project_context') and ctx.context_summary:
        for rel, summary in ctx.context_summary.items():
            entry = f"{rel}: {summary}"
            tokens = approx_tokens(entry)
            if token_total + tokens > 3000 or char_total + len(entry) > 10_000:
                trimmed = True
                break
            token_total += tokens
            char_total += len(entry)
            parts.append(entry)
        if parts:
            parts = ['context'] + parts
        if trimmed:
            parts.append('Context trimmed to fit within limits.')
            emit('WARN', 'BUILD', 'Context truncated', max_tokens=3000, tokens=token_total)
        emit('INFO', 'BUILD', 'Collected project context', files=len(ctx.context_summary), tokens=token_total)
    if ctx.settings.get('include_history'):
        try:
            with open(ctx.history_path, 'r', encoding='utf-8') as f:
                hist = json.load(f)
        except Exception:
            hist = []
        for item in hist[-5:]:
            text = f"User: {item['prompt']}\nAssistant: {item['response']}"
            parts.append(text)
    parts.append(user_prompt)
    return '\n\n'.join(parts), trimmed


__all__ = ['build_prompt']
