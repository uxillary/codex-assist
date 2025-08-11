import json
from typing import Tuple
import os

from utils import approx_tokens
from context import AppContext
from logging_bus import emit
from .conversation import build_conversation_context
from services.openai_helper import PROJECT_DIR


def build_prompt(ctx: AppContext, user_prompt: str) -> Tuple[str, bool]:
    """Construct the final prompt using settings, repo and conversation context."""
    parts = []
    token_total = 0
    char_total = 0
    trimmed = False
    recent_idx = None
    summary_idx = None

    # --- Conversation memory ---
    if ctx.settings.get('use_conversation_memory', True):
        running_summary, recent_turns = build_conversation_context(
            str(PROJECT_DIR), ctx.settings.get('recent_turns_count', 2)
        )
        if running_summary:
            entry = f"Conversation summary:\n{running_summary}"
            parts.append(entry)
            summary_idx = len(parts) - 1
            token_total += approx_tokens(entry)
            char_total += len(entry)
        if ctx.settings.get('recent_turns_count', 2) > 0 and recent_turns:
            entry = f"Recent dialogue:\n{recent_turns}"
            parts.append(entry)
            recent_idx = len(parts) - 1
            token_total += approx_tokens(entry)
            char_total += len(entry)

    # --- Project context ---
    tier = ctx.settings.get('context_tier', 'Standard')
    if ctx.settings.get('use_project_context') and ctx.context_summary:
        if tier == 'Basic':
            overview = getattr(ctx, 'project_overview', '')
            if not overview:
                overview = ' '.join(ctx.context_summary.values())
            entry = f"Project Overview: {overview}"
            tokens = approx_tokens(entry)
            if token_total + tokens <= 3000 and char_total + len(entry) <= 10_000:
                parts.append(entry)
                token_total += tokens
                char_total += len(entry)
            else:
                trimmed = True
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
            if tier == 'Detailed' and not trimmed:
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
            emit('WARN', 'BUILD', 'Context truncated', max_tokens=3000, tokens=token_total)
        emit('INFO', 'BUILD', 'Collected project context', files=len(ctx.context_summary), tokens=token_total)

    parts.append(user_prompt)
    final = '\n\n'.join(parts)
    tokens = approx_tokens(final)

    if tokens > 3000 or len(final) > 10_000:
        if recent_idx is not None:
            parts.pop(recent_idx)
            trimmed = True
            emit('WARN', 'BUILD', 'Context trimmed by dropping recent turns')
            final = '\n\n'.join(parts)
            tokens = approx_tokens(final)
        if (tokens > 3000 or len(final) > 10_000) and summary_idx is not None:
            part = parts[summary_idx]
            summary_body = part.split('\n', 1)[1] if '\n' in part else part
            if len(summary_body) > 800:
                parts[summary_idx] = f"Conversation summary:\n{summary_body[-800:]}"
                trimmed = True
                emit('WARN', 'BUILD', 'Context trimmed by shrinking summary')
                final = '\n\n'.join(parts)
                tokens = approx_tokens(final)
        if tokens > 3000 or len(final) > 10_000:
            final = final[:10_000]
            trimmed = True
            emit('WARN', 'BUILD', 'Prompt trimmed', tokens=tokens)

    return final, trimmed


__all__ = ['build_prompt']
