import os
from pathlib import Path
import subprocess as subp

import fire

from ..utils import get_logger


log = get_logger(__name__)


def build_bowtie2_index(fa_path, output_path):
    cmd = f"bowtie2-build {fa_path} {output_path}"
    log.info(f"Call cmd: {cmd}")
    subp.check_call(cmd, shell=True)
    return output_path


def build_blast_index(fa_path, output_path):
    cmd = f"makeblastdb -in {fa_path} -dbtype nucl -out {output_path}"
    log.info(f"Call cmd: {cmd}")
    subp.check_call(cmd, shell=True)
    return output_path


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


def build_genome(genome: dict) -> dict:
    aligner_index: list = genome['genome_index']
    fasta_path = Path(genome['fasta'])
    prefix = fasta_path.stem
    index = str(fasta_path.parent / prefix)
    for aligner in aligner_index:
        log.info("Building index for %s" % aligner)
        genome[f"{aligner}_index"] = index
        if aligner == "bowtie2":
            if (fasta_path.parent / f"{prefix}.1.bt2").exists():
                log.info(f"Index {index} already exists.")
                continue
            build_bowtie2_index(fasta_path, index)
        elif aligner == "blast":
            # TODO: check index exist or not
            build_blast_index(fasta_path, index)
        elif aligner == "mmseqs":
            # TODO: check index exist or not
            build_mmseqs_index(fasta_path, index)
        else:
            raise NotImplementedError(f"Aligner {aligner} is not implemented.")
    trans_index = genome.get("transcripts_index")
    if trans_index:
        log.info("Building index for transcripts")
    return genome


if __name__ == "__main__":
    fire.Fire({
        "build_bowtie2_index": build_bowtie2_index,
        "build_blast_index": build_blast_index,
        "build_mmseqs_index": build_mmseqs_index,
    })