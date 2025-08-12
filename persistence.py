"""Project persistence helpers."""
import json
import os
from pathlib import Path
import time
from typing import Optional

from state import Project

PROJECT_ROOT = Path.home() / ".codex-assist" / "projects"


def _path_for(name: str) -> Path:
    return PROJECT_ROOT / f"{name}.json"


def save_project(project: Project) -> None:
    """Persist project metadata to disk."""
    if not project.name:
        return
    PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
    project.updated_at = time.time()
    data = {
        "name": project.name,
        "folder": project.folder,
        "context_chunks": project.context_chunks,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }
    with _path_for(project.name).open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_project(name: str) -> Optional[Project]:
    path = _path_for(name)
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return Project(**data)
