from pathlib import Path
from fastapi import HTTPException
from .utils import run_cmd
import typing as t

SYSTEM_PATH = Path('/home/qzhang/fisheye')

def rca(genelist: str, gtf: str, fasta: str, 
            threads: int = 16, index_prefix: str = "bowtie2-index",
            tm_range: tuple = (36, 44), target_fold_thresh: int = 12,
            output_dir: str = "rca", best_num: int = 50, 
            blast_target: int = 0, location_interval: int = 2,
            output_raw: bool = False):

    genelist_path = Path(genelist)
    gtf_path = Path(gtf)
    fasta_path = Path(fasta)
    if not genelist_path.exists() or not gtf_path.exists() or not fasta_path.exists():
        raise HTTPException(status_code=404, detail="One or more input files not found")
    cmd = [
        "python", f"{SYSTEM_PATH}/fisheye/primer_design/tools/double_hybirdize.py", str(genelist_path), str(gtf_path), str(fasta_path),
        f"--threads={threads}",
        f"--index_prefix={index_prefix}",
    f"--tm_range={tm_range[0]},{tm_range[1]}",
    f"--target_fold_thresh={target_fold_thresh}",
    f"--output_dir={output_dir}",
    f"--best_num={best_num}",
    f"--output_raw={output_raw}",
    f"--blast_target={blast_target}",
        f"--location_interval={location_interval}"
    ]
    run_cmd(cmd)
    

def dnafish(ini_path: str, eq_space: bool = False):
    """
    Function to execute DNA pipeline commands.
    If eq_space is True, additional commands (-BA and -DQ) will be executed.
    """
    # Base pipeline command
    base_cmd = ["python", f"{SYSTEM_PATH}/fisheye/pool_design/run.py", "--config-file", ini_path, "--all"]
    run_cmd(base_cmd)  

    if eq_space:
        # Command -BA
        cmd_ba = ["python", f"{SYSTEM_PATH}/fisheye/pool_design/run.py", "--config-file", ini_path, "--bacterial"]
        run_cmd(cmd_ba) 

        # Command -DQ
        cmd_dq = ["python", f"{SYSTEM_PATH}/fisheye/pool_design/run.py", "--config-file", ini_path, "--del-qc"]
        run_cmd(cmd_dq) 
    
def uprobe(protocol_yaml: t.Union[str, Path, dict], genomes_yaml: t.Union[str, Path, dict], output_csv: str, 
           raw_results_csv: t.Optional[str] = None, workdir: str = "./"):
    """
    Function to execute uprobe commands with the provided parameters.
    If raw_results_csv is not provided, the function will not generate the raw results CSV file.
    Args:
        protocol_yaml: Path to the protocol YAML file
        genomes_yaml: Path to the genomes YAML file
        output_csv: Path for the output CSV file
        raw_results_csv: Path for the raw results CSV file
        workdir: Working directory, defaults to current directory
    """
    cmd = [
        "uprobe",
        f"--protocol_yaml", protocol_yaml,
        f"--genomes_yaml", genomes_yaml,
        f"--output_csv", output_csv,
        f"--raw_results_csv", raw_results_csv,
        f"--workdir", workdir
    ]
    run_cmd(cmd)
    
