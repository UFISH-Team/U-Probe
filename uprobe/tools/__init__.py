from pathlib import Path
from .aligner import (
    build_bowtie2_index, build_blast_db, build_mmseqs_index
)
from uprobe.gen.fun import extract_trans_seqs
from uprobe.utils import get_logger

log = get_logger(__name__)

def build_transcripts_index(gtf: Path,
                             fasta: Path, 
                             outdir: Path, 
                             threads: int = 10
                            ) -> str:
    trans_fasta_path = outdir.parent / "transcript.fa"
    index_prefix = outdir / fasta.stem
    if trans_fasta_path.exists():
        log.info("transcript.fa found in output dir")
    else:
        log.info("transcript.fa not found, extracting sequences from gtf")
        extract_trans_seqs(gtf, fasta, trans_fasta_path)
    index_flag = outdir.with_suffix(".bt2")
    if index_flag.exists():
        log.info("bowtie2 index found in the output dir")
    else:
        log.info("no bowtie2 index found, building it now")
        build_bowtie2_index(trans_fasta_path, index_prefix, threads)
    return str(index_prefix)

def build_genome(genome: dict,
                 threads: int = 10
                 ) -> dict:
    """Build the genome index using the provided fasta file."""
    fasta_path = Path(genome['fasta'])
    prefix = fasta_path.stem

    bowtie2_index_files = [
                    f"{prefix}.1.bt2",
                    f"{prefix}.2.bt2",
                    f"{prefix}.3.bt2",
                    f"{prefix}.4.bt2",
                    f"{prefix}.rev.1.bt2",
                    f"{prefix}.rev.2.bt2"
                    ]
    blast_index_files = [ 
                    f"{prefix}.ndb",
                    f"{prefix}.nin",
                    f"{prefix}.nhr",
                    f"{prefix}.nsq"
                    ]
    mmseqs_index_files = [
                    f"{prefix}.db",
                    f"{prefix}.dbtype",
                    f"{prefix}.dbstat",
                    f"{prefix}.dbmeta"
                    ]
    aligner_index: list = genome['align_index']
    for aligner in aligner_index:
        log.info(f"building {aligner} index for {prefix}")
        index_dir = fasta_path.parent / f"{aligner}_genome"/ prefix
        if index_dir.parent.exists():
            log.info(f"index already exists: {index_dir.parent}")
        else:
            log.info(f"index does not exist, building it now: {index_dir.parent}")
            index_dir.parent.mkdir(parents=True, exist_ok=True)
            if aligner == "bowtie2":
                if all((index_dir.parent / file_name).exists() for file_name in bowtie2_index_files):
                    log.info(f"index already exists: {index_dir.parent}")
                else:
                    build_bowtie2_index(fasta_path, index_dir)
            elif aligner == "blast":
                if all((index_dir.parent / file_name).exists() for file_name in blast_index_files):
                    log.info(f"index already exists: {index_dir.parent}")
                else:          
                    build_blast_db(fasta_path, index_dir, title=prefix)
            elif aligner == "mmseqs":
                if all((index_dir.parent / file_name).exists() for file_name in mmseqs_index_files):
                    log.info(f"index already exists: {index_dir.parent}")
                else:
                    build_mmseqs_index(fasta_path, str(index_dir))
            else:
                raise NotImplementedError(f"aligner {aligner} is not implemented")
    log.info(f"building {aligner} index for {prefix} transcript")
    tran_index_dir = fasta_path.parent / f"blast_transcript"
    if all((tran_index_dir / file_name).exists() for file_name in bowtie2_index_files):
        log.info(f"transcript index already exists: {tran_index_dir}")
    else:
        log.info(f"transcript index does not exist, building it now: {tran_index_dir}")
        tran_index_dir.mkdir(parents=True, exist_ok=True)
        build_transcripts_index(gtf=Path(genome['gtf']), 
                                fasta=fasta_path, 
                                outdir=tran_index_dir, 
                                threads=threads)
    return genome
