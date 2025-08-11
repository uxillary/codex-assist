import json
from typing import Tuple
import os

from utils import approx_tokens
from context import AppContext
from logging_bus import emit


def build_prompt(ctx: AppContext, user_prompt: str) -> Tuple[str, bool]:
    """Construct the final prompt using settings and context."""
    parts = []
    token_total = 0
    char_total = 0
    trimmed = False
    tier = ctx.settings.get('context_tier', 'Standard')
    if ctx.settings.get('use_project_context') and ctx.context_summary:
        if tier == 'Basic':
            overview = getattr(ctx, 'project_overview', '')
            if not overview:
                overview = ' '.join(ctx.context_summary.values())
            entry = f"Project Overview: {overview}"
            parts.append(entry)
            token_total += approx_tokens(entry)
        else:
            for rel, summary in ctx.context_summary.items():
                entry = f"{rel}: {summary}"
                tokens = approx_tokens(entry)
                if token_total + tokens > 3000 or char_total + len(entry) > 10_000:
                    trimmed = True
                    break
                token_total += tokens
                char_total += len(entry)
                parts.append(entry)
            if tier == 'Detailed':
                for rel in ctx.settings.get('detailed_files', []):
                    path = os.path.join(getattr(ctx, 'project_root', ''), rel)
                    try:
                        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                            code = f.read()
                    except Exception:
                        continue
                    tokens = approx_tokens(code)
                    if token_total + tokens > 3000 or char_total + len(code) > 10_000:
                        trimmed = True
                        break
                    token_total += tokens
                    char_total += len(code)
                    parts.append(f"{rel} code:\n{code}")
            if trimmed:
                parts.append('Context trimmed to fit within limits.')
                emit('WARN', 'BUILD', 'Context truncated', max_tokens=3000, tokens=token_total)
            emit('INFO', 'BUILD', 'Collected project context', files=len(ctx.context_summary), tokens=token_total)
    if ctx.settings.get('use_turn_summaries'):
        try:
            with open(ctx.turn_summaries_path, 'r', encoding='utf-8') as f:
                summaries = json.load(f)
        except Exception:
            summaries = []
        for s in summaries[-5:]:
            parts.append(f"Summary: {s}")
    elif ctx.settings.get('include_history'):
        try:
            with open(ctx.history_path, 'r', encoding='utf-8') as f:
                hist = json.load(f)
        except Exception:
            hist = []
        for item in hist[-5:]:
            text = f"User: {item['prompt']}\nAssistant: {item['response']}"
            parts.append(text)
    parts.append(user_prompt)
    final = '\n\n'.join(parts)
    tokens = approx_tokens(final)
    if tokens > 4000 or len(final) > 10_000:
        final = final[:10_000] + "\n\n(Context trimmed to fit)"
        trimmed = True
        emit('WARN', 'BUILD', 'Prompt trimmed', tokens=tokens)
    return final, trimmed


__all__ = ['build_prompt']
