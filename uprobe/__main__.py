
"""
Main entry point for U-Probe CLI.
"""
import sys
import os
from pathlib import Path

# Add project root to sys.path for development
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from .cli import main


if __name__ == '__main__':
    main()
