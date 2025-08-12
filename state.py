from dataclasses import dataclass, field
from typing import List, Dict, Optional
import time


@dataclass
class Project:
    """Represents a persisted project and its context."""
    name: str = ""
    folder: Optional[str] = None
    context_chunks: List[str] = field(default_factory=list)
    chat_history: List[Dict] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


@dataclass
class AppState:
    """Holds in-memory application state."""
    project: Project = field(default_factory=Project)
    model_name: str = "gpt-3.5-turbo"
    is_building_context: bool = False
    last_token_estimate: int = 0
    last_cost_estimate: float = 0.0
    session_cost_estimate: float = 0.0


__all__ = ["Project", "AppState"]
