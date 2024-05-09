from pathlib import Path
import typing as T
from pyfaidx import Fasta
from fun import read_gtf,extract_exons_rca

def extract_target_seqs(
        target_genes: T.List[str],
        genome_fa: Path,
        genome_gtf: Path,
        length: int,
        overlap: int,
        output_csv: Path
        ):
    
    fa = Fasta(genome_fa)
    df_gtf = read_gtf(genome_gtf, extract_fields=['gene_name'], get_length=True)
    gene2exons = extract_exons_rca(df_gtf, fa, target_genes, min_length=40)

    pass
