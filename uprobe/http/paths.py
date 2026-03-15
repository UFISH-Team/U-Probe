"""
Path utilities for the U-Probe HTTP server.

We intentionally compute runtime directories (like `outputs/`) relative to the
server process working directory by default, because the code may live in a
different location than where the HTTP service is launched.
"""

from __future__ import annotations

import os
from pathlib import Path


def get_server_root() -> Path:
    """Return the server root directory used for resolving runtime paths.

    Priority:
    - `UPROBE_SERVER_ROOT` env var (explicit override)
    - Project root directory (where uprobe.http package is installed)
    """

    root = os.environ.get("UPROBE_SERVER_ROOT")
    if root:
        return Path(root).expanduser().resolve()
    
    # Calculate based on this file's location: uprobe/http/paths.py
    # Project root is 3 levels up from this file
    this_file = Path(__file__).resolve()
    project_root = this_file.parent.parent.parent  # uprobe/http/paths.py -> project_root/
    return project_root


def get_data_dir() -> Path:
    """Return the data directory for persistent application data (e.g. database, avatars).

    Priority:
    - `server_config.json` in the server root (field: "data_dir")
    - `<server_root>/data` (default)
    """
    server_root = get_server_root()
    config_path = server_root / "server_config.json"
    
    if config_path.exists():
        try:
            import json
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                custom_path = config.get("data_dir")
                if custom_path:
                    final_path = Path(custom_path).expanduser().resolve()
                    final_path.mkdir(parents=True, exist_ok=True)
                    return final_path
        except Exception as e:
            print(f"Warning: Failed to load config from {config_path}: {e}")

    final_path = (server_root / "data").resolve()
    final_path.mkdir(parents=True, exist_ok=True)
    return final_path


def get_output_dir() -> Path:
    """Return the output directory for uploads and generated files.

    Priority:
    - `server_config.json` in the server root (field: "output_dir")
    - `<server_root>/outputs` (default)
    """
    server_root = get_server_root()
    config_path = server_root / "server_config.json"
    
    if config_path.exists():
        try:
            import json
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                custom_path = config.get("output_dir")
                if custom_path:
                    # Resolve relative paths against server_root, absolute paths as is
                    final_path = Path(custom_path).expanduser().resolve()
                    return final_path
        except Exception as e:
            print(f"Warning: Failed to load config from {config_path}: {e}")

    final_path = (server_root / "outputs").resolve()
    return final_path

