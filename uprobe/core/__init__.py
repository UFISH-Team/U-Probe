"""
U-Probe package.

Note:
This package exposes `UProbeAPI`, but we avoid importing it eagerly to keep
lightweight entry points (e.g. `python -m uprobe.core.agent.repl_bootstrap`) working
even in environments where optional runtime dependencies are not installed yet.
"""

from __future__ import annotations

from typing import Any

from uprobe import __version__

__all__ = ["UProbeAPI"]


def __getattr__(name: str) -> Any:
    """Lazy attribute access for optional heavy imports."""
    if name == "UProbeAPI":
        from .api import UProbeAPI  # Local import to avoid import-time deps

        return UProbeAPI
    raise AttributeError(f"module 'uprobe.core' has no attribute {name!r}")

