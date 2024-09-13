from pathlib import Path
import subprocess as subp

from ..utils import get_logger

log = get_logger(__name__)

def build_bowtie2_index(fasta_path: Path, 
                        index_prefix: Path, 
                        threads: int=10
                        ) -> None:
    cmd = ["bowtie2-build", "--threads", 
           str(threads), 
           str(fasta_path), 
           str(index_prefix)]
    cmd = " ".join(cmd)
    log.info(f"Call cmd: {cmd}")
    subp.check_call(cmd, shell=True)

def build_blast_db(fasta_path: Path, 
                   db_prefix: Path, 
                   title: str = "blast_db"
                   ) -> None:
    cmd = [
        "makeblastdb",
        "-in", str(fasta_path),
        "-dbtype", "nucl",
        "-title", title,
        "-parse_seqids",
        "-out", str(db_prefix),
        "-logfile", f"{str(db_prefix.parent)}/make_nt.log",
    ]
    cmd = " ".join(cmd)
    log.info(f"Call cmd: {cmd}")
    subp.check_call(cmd, shell=True)

def build_mmseqs_db(fa_path, output_path):
    cmd = f"mmseqs createdb {fa_path} {output_path}"
    log.info(f"Call cmd: {cmd}")
    subp.check_call(cmd, shell=True)
    return output_path

def build_mmseqs_index(fa_path, output_path):
    db_path = build_mmseqs_db(fa_path, f"{output_path}")
    cmd = f"mmseqs createindex {db_path} {output_path}"
    log.info(f"Call cmd: {cmd}")
    subp.check_call(cmd, shell=True)
    return output_path