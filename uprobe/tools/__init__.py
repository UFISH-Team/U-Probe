from pathlib import Path
from .aligner import (
    build_bowtie2_index, build_blast_db, build_mmseqs_index
)
from ..gen.fun import extract_trans_seqs
from ..utils import get_logger

log = get_logger(__name__)

def build_transcripts_index(gtf: Path, fasta: Path, outdir: Path, threads: int) -> str:
    """Build the transcripts index using the provided GTF and FASTA files."""
    

    trans_fasta_path = outdir.parent / "transcript.fa"
    index_prefix = outdir / fasta.stem
    
    # 检查转录本 FASTA 文件是否存在
    if trans_fasta_path.exists():
        log.info("transcript.fa found in output directory.")
    else:
        log.info("transcript.fa not found, extracting sequences from GTF.")
        extract_trans_seqs(gtf, fasta, trans_fasta_path)
    
    index_flag = outdir.with_suffix(".1.bt2")
    
    # 检查 Bowtie2 索引是否存在
    if index_flag.exists():
        log.info("bowtie2 index found in the output directory.")
    else:
        log.info("no bowtie2 index found, building it now.")
        build_bowtie2_index(trans_fasta_path, str(index_prefix), threads)
    
    return str(index_prefix)


def build_genome(genome: dict) -> dict:
    aligner_index: list = genome['align_index']
    fasta_path = Path(genome['fasta'])
    prefix = fasta_path.stem

    for aligner in aligner_index:
        log.info(f"building {aligner} index for {prefix}")
        # 创建新的文件夹用于存放索引
        index_dir = fasta_path.parent / f"genome_{aligner}_index"/ prefix
        index_dir.parent.mkdir(parents=True, exist_ok=True)
        
        if aligner == "bowtie2":
            if (index_dir.parent / f"{prefix}.1.bt2").exists():
                log.info(f"index {index_dir.parent} already exists.")
                continue
            build_bowtie2_index(fasta_path, str(index_dir))
        
        elif aligner == "blast":
            if (index_dir.parent / f"{prefix}.ndb").exists():
                log.info(f"Index {index_dir.parent} already exists.")
                continue
            build_blast_db(fasta_path, str(index_dir), title=prefix)
        
        elif aligner == "mmseqs":
            if (index_dir.parent / f"{prefix}.mmseqs").exists():
                log.info(f"index {index_dir.parent} already exists.")
                continue
            build_mmseqs_index(fasta_path, str(index_dir))

        else:
            raise NotImplementedError(f"aligner {aligner} is not implemented.")

        log.info(f"building {aligner} index for {prefix} transcript")

        # 创建新的文件夹用于存放索引
        tran_index_dir = fasta_path.parent / f"transcript-index"
        tran_index_dir.mkdir(parents=True, exist_ok=True)

        build_transcripts_index(genome['gtf'], fasta_path, tran_index_dir, 10)

    return genome