
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from uprobe.cli import cli

if __name__ == "__main__":
    cli()
