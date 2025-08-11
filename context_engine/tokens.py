"""Token utilities using tiktoken when available."""
from __future__ import annotations
from typing import List

try:
    import tiktoken
except Exception:  # pragma: no cover - fallback
    tiktoken = None

def _simple_tokenize(text: str) -> List[str]:
    return text.split()

def len_tokens(text: str, model_hint: str = "gpt-4o-mini") -> int:
    if tiktoken is not None:
        try:
            enc = tiktoken.encoding_for_model(model_hint)
            return len(enc.encode(text))
        except Exception:
            pass
    return len(_simple_tokenize(text))

def cap_to_tokens(text: str, target: int, model_hint: str = "gpt-4o-mini") -> str:
    tokens = _simple_tokenize(text)
    if len(tokens) <= target:
        return text
    return " ".join(tokens[:target])
