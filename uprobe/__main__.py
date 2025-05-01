import argparse
from pathlib import Path
from .workflow import construct_workflow
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
    parser.add_argument("--output_csv", type=Path, required=True,
                        help="Path to the output CSV file.")
    parser.add_argument("--raw_results_csv", type=Path, default=None,
                        help="Path to the raw results CSV file.")
    parser.add_argument("--workdir", type=Path, default=Path("."),
                        help="Working directory (default: current directory).")

    args = parser.parse_args()

    workflow = construct_workflow(
        args.protocol_yaml,
        args.genomes_yaml,
        args.output_csv,
        args.workdir,
        args.raw_results_csv
    )

    workflow()



if __name__ == "__main__":
    main()