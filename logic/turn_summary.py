from services.openai_helper import send_prompt, save_turn_summary


def summarize_turn(prompt: str, response: str) -> str:
    """Create a 1–2 sentence summary for a prompt/response pair."""
    combo = (
        "Summarize the following user/assistant exchange in 1-2 sentences.\n"
        f"User: {prompt}\nAssistant: {response}"
    )
    summary, _ = send_prompt(combo)
    summary = summary.strip()
    save_turn_summary(summary)
    return summary


__all__ = ["summarize_turn"]
