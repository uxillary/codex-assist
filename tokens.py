"""Utility functions for token and cost estimation."""
from typing import List, Dict

# Rough per-1k token cost estimates (GBP)
COST_PER_K = {
    "gpt-3.5-turbo": 0.0015,
    "gpt-4": 0.03,
}


def estimate_tokens(prompt: str, context_chunks: List[str], history: List[Dict], model: str) -> int:
    """Very rough token estimate using whitespace splitting."""
    tokens = len(prompt.split())
    tokens += sum(len(chunk.split()) for chunk in context_chunks)
    tokens += sum(len(m.get("content", "").split()) for m in history)
    return tokens


def estimate_cost(tokens: int, model: str) -> float:
    rate = COST_PER_K.get(model, 0.002)
    return (tokens / 1000.0) * rate


def recalc_and_update(window, state, prompt: str = "", add_cost: bool = False) -> None:
    """Recalculate token/cost estimates and update UI labels."""
    tokens = estimate_tokens(prompt, state.project.context_chunks, state.project.chat_history, state.model_name)
    cost = estimate_cost(tokens, state.model_name)
    state.last_token_estimate = tokens
    state.last_cost_estimate = cost
    if add_cost:
        state.session_cost_estimate += cost
    if window is not None:
        if "-EST_TOKENS-" in window.AllKeysDict:
            window["-EST_TOKENS-"].update(f"Estimated prompt tokens: {tokens}")
        if "-EST_COST-" in window.AllKeysDict:
            window["-EST_COST-"].update(
                f"Prompt £{cost:.4f} | Session £{state.session_cost_estimate:.4f}"
            )
