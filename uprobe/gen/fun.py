import pandas as pd
import os
import typing as t

from pyfaidx import Fasta
from typing import List

os.listdir(os.getcwd())

# 读取gtf
GTF_FIELDS = [
    'chr', 'source', 'type', 'start', 'end', 'score', 'strand', 'score', 'info'
]

def read_gtf(
        gtf: str,
        filter_by_type: t.Optional[str]=None,
        extract_fields: t.List[str]=["gene_name"],
        get_length=True,
        basic_fields=GTF_FIELDS,
        ) -> pd.DataFrame:
    df = pd.read_csv(gtf, sep='\t', header=None, comment='#')
    df.columns = basic_fields
    if filter_by_type:
        df = df[df[basic_fields[2]] == filter_by_type]
    if get_length:
        df['length'] = df['end'] - df['start']
    for f in extract_fields:
        df[f] = df[basic_fields[-1]].str.extract(f"{f} \"(.*?)\"")

    #Determine whether the chromosome name in the gtf file starts with chr, if not, add it(2021.07.15)
    chr_new = []
    for chr_ in df.chr:
        if str(chr_).startswith('chr'):
            chr_new.append(chr_)
        else:
            chr_new.append(f'chr{chr_}')
            #chr_new.append(f'{chr_}')
    df.chr = chr_new
    return df


Exon = t.Tuple[str, str, str, int]  # (tyep, name, seq, n_trans)
def extract_exons_rca(df_gtf: pd.DataFrame, fa: Fasta,
                  genelist: pd.DataFrame, min_length: int=40
                  ) -> t.Mapping[str, t.List[Exon]]:
    """Extract all exons of each gene"""
    #import ipdb; ipdb.set_trace()
    gene2exons = {}
    for item in genelist.iterrows():
        gene = item[1]['geneID']
        df_gene = df_gtf[df_gtf.gene_name == gene]
        if df_gene.shape[0] <= 0:
            raise ValueError(f"Gene {gene} not exists in GTF file.")

        df_exons = df_gene[df_gene.type == 'CDS'].copy()
        if df_exons.shape[0] == 0:
            df_exons = df_gene[df_gene.type == 'exon'].copy()
        df_exons = df_exons[df_exons.length > min_length]
        if df_exons.shape[0] == 0:
            raise ValueError(f"Gene {gene} can't found any exon records.")
        exon_cnts = df_exons.groupby(by=['chr', 'start', 'end', "length", "strand"], as_index=False).count()
        gene2exons[gene] = []
        for idx, row in exon_cnts.iterrows():
            chr_, start, end, strand = str(row['chr']), row['start'], row['end'], row['strand']
            name = '_'.join([chr_, str(start), str(end), strand])
            n_trans = row['type']
            seq = fa[chr_][start:end].seq.upper()
            if strand == '-':
                seq = reverse_complement(seq)
            exon = (name, seq, n_trans)
            gene2exons[gene].append(exon)
    return gene2exons





