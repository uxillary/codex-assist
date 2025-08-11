"""Heuristic extractors for DL signals and summaries."""
from __future__ import annotations
import re
from typing import List
from .models import DecisionLedger
from .tokens import cap_to_tokens

_signal_re = re.compile(r"^(decide|constraint|todo|pref|id):\s*(.*)", re.I)

def extract_dl_signals(text: str) -> DecisionLedger:
    dl = DecisionLedger()
    for line in text.splitlines():
        m = _signal_re.match(line.strip())
        if not m:
            continue
        key, val = m.group(1).lower(), m.group(2).strip()
        if key == "decide":
            dl.decisions.append(val)
        elif key == "constraint":
            dl.constraints.append(val)
        elif key == "todo":
            dl.todos.append(val)
        elif key == "pref":
            dl.prefs.append(val)
        elif key == "id":
            parts = val.split("=", 1)
            if len(parts) == 2:
                dl.ids[parts[0].strip()] = parts[1].strip()
    return dl

# Optional stub for LLM extraction
def llm_extract_signals(text: str) -> DecisionLedger:  # pragma: no cover - placeholder
    return extract_dl_signals(text)

def make_extractive(u: str, a: str, max_tokens: int = 120) -> str:
    lines: List[str] = []
    for part in [u, a]:
        for sent in re.split(r"[\n\.]+", part):
            sent = sent.strip()
            if not sent:
                continue
            lines.append(f"- {sent}")
    text = "\n".join(lines)
    return cap_to_tokens(text, max_tokens)

def make_abstractive(u: str, a: str, max_tokens: int = 120) -> str:
    combined = u.strip() + " " + a.strip()
    sentences = re.split(r"[\n\.]+", combined)
    sentences = [s.strip() for s in sentences if s.strip()]
    summary = ". ".join(sentences[:4])
    return cap_to_tokens(summary, max_tokens)
