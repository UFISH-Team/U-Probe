"""
U-Probe package.
"""

from __future__ import annotations

from typing import Any

__version__ = "0.1.0"

__all__ = ["UProbeAPI", "__version__"]

def __getattr__(name: str) -> Any:
    """Lazy attribute access for optional heavy imports."""
    if name == "UProbeAPI":
        from uprobe.core.api import UProbeAPI
        return UProbeAPI
    raise AttributeError(f"module 'uprobe' has no attribute {name!r}")
