import os
from pathlib import Path
import subprocess as subp

import fire

from ..utils import get_logger


log = get_logger(__name__)

def build_bowtie2_index(fasta_path, index_prefix, threads=10):
    cmd = ["bowtie2-build", "--threads", str(threads), str(fasta_path), str(index_prefix)]
    cmd = " ".join(cmd)
    log.info(f"Call cmd: {cmd}")
    subp.check_call(cmd, shell=True)


def build_blast_db(fasta_path: Path, db_prefix: Path, title: str = "blast_db") -> None:
    """Build a BLAST database from a FASTA file."""
    cmd = [
        "makeblastdb",
        "-in", str(fasta_path),
        "-dbtype", "nucl",
        "-title", title,
        "-parse_seqids",
        "-out", str(db_prefix),
        "-logfile", "make_nt.log",
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


if __name__ == "__main__":
    fire.Fire({
        "build_bowtie2_index": build_bowtie2_index,
        "build_blast_index": build_blast_db,
        "build_mmseqs_index": build_mmseqs_index,
    })