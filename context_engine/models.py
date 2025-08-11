from __future__ import annotations
from typing import List, Literal, Optional, Dict
from datetime import datetime
import numpy as np
from pydantic import BaseModel, Field, ConfigDict

class Turn(BaseModel):
    role: Literal["user", "assistant"]
    text: str
    ts: datetime = Field(default_factory=datetime.utcnow)

class DecisionLedger(BaseModel):
    decisions: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    todos: List[str] = Field(default_factory=list)
    prefs: List[str] = Field(default_factory=list)
    ids: Dict[str, str] = Field(default_factory=dict)

class FSChunk(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str
    type: Literal["extractive", "abstractive"]
    tags: List[str] = Field(default_factory=list)
    text: str
    src_turn: int
    vec: Optional[np.ndarray] = None

class Memory(BaseModel):
    AC: List[Turn] = Field(default_factory=list)
    DL: DecisionLedger = Field(default_factory=DecisionLedger)
    CA_ptr: int = 0
