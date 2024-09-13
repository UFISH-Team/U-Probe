import argparse
from pathlib import Path
from .workflow import construct_workflow

def main():
    # 定义命令行参数
    parser = argparse.ArgumentParser(description="Run the workflow for double hybrid RCA.")
    parser.add_argument("--genomes_yaml", type=Path, required=True,
                        help="Path to the genomes YAML file.")
    parser.add_argument("--protocol_yaml", type=Path, required=True,
                        help="Path to the protocol YAML file.")
    parser.add_argument("--output_csv", type=Path, required=True,
                        help="Path to the output CSV file.")
    parser.add_argument("--workdir", type=Path, default=Path("."),
                        help="Working directory (default: current directory).")

    # 解析命令行参数
    args = parser.parse_args()

    # 构造工作流
    workflow = construct_workflow(
        args.protocol_yaml,
        args.genomes_yaml,
        args.output_csv,
        args.workdir
    )
    
        # 运行工作流
    workflow.run()

if __name__ == "__main__":
    main()