# src/cli_web_flow/auth.py
import json
import fcntl
import os
from pathlib import Path
from typing import Optional

def get_config_paths():
    config_dir = Path.home() / ".cli-web-flow"
    config_file = config_dir / "config.json"
    return config_dir, config_file

def _update_config(key: str, value: str) -> None:
    config_dir, config_file = get_config_paths()
    config_dir.mkdir(parents=True, exist_ok=True)
    data = {}
    try:
        with open(config_file, "a+") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                f.seek(0)
                content = f.read()
                data = json.loads(content) if content else {}
                data[key] = value
                f.seek(0)
                f.truncate()
                json.dump(data, f)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except OSError as e:
        raise RuntimeError(f"Failed to save config: {e}")

def save_cookie_path(cookie_path: str) -> None:
    _update_config("cookie_path", cookie_path)

def get_cookie_path() -> Optional[str]:
    _, config_file = get_config_paths()
    if not config_file.exists():
        return None
    try:
        with open(config_file, "r") as f:
            data = json.load(f)
            return data.get("cookie_path")
    except (json.JSONDecodeError, OSError):
        return None

def save_project_id(project_id: str) -> None:
    _update_config("project_id", project_id)

def get_project_id() -> Optional[str]:
    _, config_file = get_config_paths()
    if not config_file.exists():
        return None
    try:
        with open(config_file, "r") as f:
            data = json.load(f)
            return data.get("project_id")
    except (json.JSONDecodeError, OSError):
        return None