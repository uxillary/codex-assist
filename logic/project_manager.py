import json
import os
from pathlib import Path
from typing import Optional

from services.openai_helper import set_project_dir
from .context_manager import scan_folder

PROJECTS_DIR = Path('codex_projects')
PROJECTS_DIR.mkdir(exist_ok=True)


def _write_proj_meta(name: str, root_path: str, folder: Path) -> None:
    meta_path = folder / f"{name}.codexproj"
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump({'name': name, 'root': root_path}, f, indent=2)


def new_project(ctx, name: str) -> Path:
    folder = PROJECTS_DIR / name
    folder.mkdir(parents=True, exist_ok=True)
    _write_proj_meta(name, '', folder)
    ctx.active_project = str(folder)
    ctx.settings['last_project'] = str(folder)
    set_project_dir(str(folder))
    return folder


def load_project(ctx, file_path: str) -> None:
    folder = Path(file_path).parent
    ctx.active_project = str(folder)
    ctx.settings['last_project'] = str(folder)
    set_project_dir(str(folder))
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        root = meta.get('root', '')
    except Exception:
        root = ''
    ctx.project_root = root
    try:
        with open(folder / 'context_summary.json', 'r', encoding='utf-8') as f:
            ctx.context_summary = json.load(f)
    except Exception:
        ctx.context_summary = {}


def save_project(ctx) -> None:
    if not ctx.active_project:
        return
    folder = Path(ctx.active_project)
    with open(folder / 'context_summary.json', 'w', encoding='utf-8') as f:
        json.dump(ctx.context_summary, f, indent=2)
    with open(folder / 'settings.json', 'w', encoding='utf-8') as f:
        json.dump(ctx.settings, f, indent=2)


def save_project_as(ctx, name: str) -> Path:
    folder = PROJECTS_DIR / name
    folder.mkdir(parents=True, exist_ok=True)
    ctx.active_project = str(folder)
    _write_proj_meta(name, getattr(ctx, 'project_root', ''), folder)
    save_project(ctx)
    set_project_dir(str(folder))
    ctx.settings['last_project'] = str(folder)
    return folder


def open_last_project(ctx) -> Optional[Path]:
    last = ctx.settings.get('last_project')
    if last and os.path.isdir(last):
        for name in os.listdir(last):
            if name.endswith('.codexproj'):
                load_project(ctx, os.path.join(last, name))
                return Path(last)
    return None


__all__ = ['new_project', 'load_project', 'save_project', 'save_project_as', 'open_last_project', 'scan_folder']
