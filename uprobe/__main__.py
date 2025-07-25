import argparse
from pathlib import Path
from .api import run_workflow
import sys
import os
import typing as T

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

def main():
    parser = argparse.ArgumentParser(description="Run the workflow for double hybrid RCA.")
    parser.add_argument("--genomes_yaml", type=Path, required=True,
                        help="Path to the genomes YAML file.")
    parser.add_argument("--protocol_yaml", type=Path, required=True,
                        help="Path to the protocol YAML file.")
    parser.add_argument("--output_dir", type=Path, required=True,
                        help="Path to the output directory.")
    parser.add_argument("--raw_csv", type=bool, default=False,
                        help="Path to the raw results CSV file.")
    parser.add_argument("--continue_on_invalid", action='store_true',
                        help="Continue with valid targets if some are invalid.")

    args = parser.parse_args()

    try:
        run_workflow(
            protocol_config=args.protocol_yaml,
            genomes_config=args.genomes_yaml,
            output_dir=args.output_dir,
            raw_csv=args.raw_csv,
            continue_on_invalid_targets=args.continue_on_invalid
        )
    except (ValueError, IOError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
