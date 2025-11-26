from pathlib import Path
import subprocess as subp

from uprobe.utils import get_logger

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
        "-logfile", f"{str(Path(db_prefix).parent)}/make_nt.log",
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

def build_jf_index(fasta, k, out_jf, threads=10, size='64G'):
    """
    Build Jellyfish index.

    Args:
        fasta (str): input FASTA
        k (int): k-mer length
        out_jf (str): output .jf
        threads (int): threads
        size (str): hash size

    Returns:
        str: output .jf
    """
    cmd = [
        'jellyfish', 'count',
        '-m', str(k),
        '-s', size,
        '-t', str(threads),
        '-C',
        '-o', out_jf,
        fasta
    ]
    cmd = " ".join(cmd)
    log.info(f"Call cmd: {cmd}")
    subp.check_call(cmd, shell=True)
    return out_jf


def merge_jf_indices(jf_list, out_jf):
    """
    Merge Jellyfish indices.

    Args:
        jf_list (list[str]): list of .jf files
        out_jf (str): merged .jf

    Returns:
        str: merged .jf
    """
    cmd = ['jellyfish', 'merge', '-o', out_jf] + jf_list
    cmd = " ".join(cmd)
    log.info(f"Call cmd: {cmd}")
    subp.check_call(cmd, shell=True)
    return out_jf
