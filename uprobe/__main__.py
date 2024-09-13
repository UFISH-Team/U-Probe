import argparse
from pathlib import Path
from .workflow import construct_workflow

def main():
    parser = argparse.ArgumentParser(description="Run the workflow for double hybrid RCA.")
    parser.add_argument("--genomes_yaml", type=Path, required=True,
                        help="Path to the genomes YAML file.")
    parser.add_argument("--protocol_yaml", type=Path, required=True,
                        help="Path to the protocol YAML file.")
    parser.add_argument("--output_csv", type=Path, required=True,
                        help="Path to the output CSV file.")
    parser.add_argument("--workdir", type=Path, default=Path("."),
                        help="Working directory (default: current directory).")

    args = parser.parse_args()

    workflow = construct_workflow(
        args.protocol_yaml,
        args.genomes_yaml,
        args.output_csv,
        args.workdir
    )

    workflow.run()

if __name__ == "__main__":
    main()