"""Reducers and condensers."""
from __future__ import annotations
from typing import List
from .tokens import len_tokens, cap_to_tokens


def _split_lines(text: str) -> List[str]:
    return [l.strip() for l in text.splitlines() if l.strip()]

def densify(existing: str, incoming: str, max_tokens: int = 160) -> str:
    merged = list(dict.fromkeys(_split_lines(existing) + _split_lines(incoming)))
    text = "\n".join(merged)
    return cap_to_tokens(text, max_tokens)

def condenser(chunks: List[str], target_tokens: int) -> str:
    text = "\n".join(chunks)
    if len_tokens(text) <= target_tokens:
        return text
    return cap_to_tokens(text, target_tokens)

def final_budget_cut(context: str, target_tokens: int) -> str:
    if len_tokens(context) <= target_tokens:
        return context
    return cap_to_tokens(context, target_tokens)
