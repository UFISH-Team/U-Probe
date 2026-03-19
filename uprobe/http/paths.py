"""
Path utilities for the U-Probe HTTP server.

We intentionally compute runtime directories (like `outputs/`) relative to the
server process working directory by default, because the code may live in a
different location than where the HTTP service is launched.
"""

from __future__ import annotations

import os
from pathlib import Path
import configparser

def get_server_root() -> Path:
    """Return the server root directory used for resolving runtime paths."""
    root = os.environ.get("UPROBE_SERVER_ROOT")
    if root:
        return Path(root).expanduser().resolve()
    
    this_file = Path(__file__).resolve()
    project_root = this_file.parent.parent.parent
    return project_root

def get_config() -> configparser.ConfigParser:
    """Helper to load the config.ini file."""
    config = configparser.ConfigParser()
    config_path = get_server_root() / "config.ini"
    if config_path.exists():
        try:
            config.read(config_path, encoding="utf-8")
        except Exception as e:
            print(f"Warning: Failed to load config from {config_path}: {e}")
    return config

def get_data_dir() -> Path:
    """Return the base directory for all application data."""
    config = get_config()
    if config.has_section("Paths") and config.has_option("Paths", "data_dir"):
        path = Path(config.get("Paths", "data_dir")).expanduser().resolve()
    else:
        path = (get_server_root() / "data").resolve()
    
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_genomes_dir() -> Path:
    """Return the base directory for storing genome files."""
    config = get_config()
    if config.has_section("Paths") and config.has_option("Paths", "genomes_dir"):
        path = Path(config.get("Paths", "genomes_dir")).expanduser().resolve()
    else:
        path = (get_data_dir() / "genomes").resolve()
        
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_results_dir() -> Path:
    """Return the directory for storing task results."""
    config = get_config()
    if config.has_section("Paths") and config.has_option("Paths", "results_dir"):
        path = Path(config.get("Paths", "results_dir")).expanduser().resolve()
    else:
        path = (get_data_dir() / "results").resolve()
        
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_fisheye_dir() -> Path:
    """Return the path to the fisheye directory."""
    config = get_config()
    if config.has_section("Paths") and config.has_option("Paths", "fisheye_dir"):
        return Path(config.get("Paths", "fisheye_dir")).expanduser().resolve()
    return Path("/home/qzhang/fisheye")

# --- Derived Paths ---

def get_public_genomes_dir() -> Path:
    """Return the directory for storing public genome files."""
    public_dir = get_genomes_dir() / "public"
    public_dir.mkdir(parents=True, exist_ok=True)
    return public_dir

def get_user_genomes_dir(username: str) -> Path:
    """Return the directory for storing user-specific genome files."""
    user_dir = get_genomes_dir() / "users" / username
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir

def get_genomes_yaml() -> Path:
    """Return the path to the main genomes.yaml file (now used as public)."""
    return (get_data_dir() / "genomes.yaml").resolve()

def get_user_genomes_yaml(username: str) -> Path:
    """Return the path to the user-specific genomes.yaml file."""
    user_dir = get_user_genomes_dir(username)
    return (user_dir / "genomes.yaml").resolve()

def get_barcodes_csv() -> Path:
    """Return the path to the barcodes CSV file."""
    return (get_data_dir() / "barcodes" / "KYRCA 2-2-12.csv").resolve()

def get_probe_json() -> Path:
    """Return the path to the probe.json file."""
    return (get_data_dir() / "probe.json").resolve()

def get_tasks_dir() -> Path:
    """Return the directory for storing user tasks."""
    tasks_dir = get_data_dir() / "user_tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    return tasks_dir

def get_output_dir() -> Path:
    """Return the output directory for uploads and generated files."""
    return get_results_dir()
