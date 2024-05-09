import fire
import subprocess as subp
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


if __name__ == "__main__":
    fire.Fire({
        "build_bowtie2_index": build_bowtie2_index,
        "build_blast_index": build_blast_index,
        "build_mmseqs_index": build_mmseqs_index,
    })