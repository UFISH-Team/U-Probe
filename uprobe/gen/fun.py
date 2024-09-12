import pandas as pd
import os
import typing as t
from pyfaidx import Fasta
from typing import List

from ..utils import get_logger, reverse_complement

log = get_logger(__name__)

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

def extract_exons_rca(df_gtf: pd.DataFrame, fa: Fasta,
                  genelist: pd.DataFrame, min_length: int=40
                  ) :
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
        df_exons['transcript_name'] = df_exons['info'].str.extract(r'transcript_name\s+"([^"]+)"')[0]
        exon_cnts = df_exons.groupby(by=['chr', 'start', 'end', 'length', 'strand', 'transcript_name'], as_index=False).count()
        gene2exons[gene] = []
        for idx, row in exon_cnts.iterrows():
            chr_, start, end, strand, trans_name = str(row['chr']), row['start'], row['end'], row['strand'], row['transcript_name']
            name = '_'.join([chr_, str(start), str(end), strand])
            n_trans = row['type']
            chr_ = chr_.replace('chr', '')
            seq = fa[chr_][start:end].seq.upper()
            if strand == '-':
                seq = reverse_complement(seq)
            exon = (name, trans_name, seq, n_trans)
            gene2exons[gene].append(exon)
    return gene2exons

def get_exon_seq(genes, fa, gtf):
    fa = Fasta(fa)
    genelist = pd.DataFrame(genes, columns=['geneID'])
    df_gtf = read_gtf(gtf, extract_fields=['gene_name', "transcript_name"], get_length=True)
    gene2exons = extract_exons_rca(df_gtf, fa, genelist)
    return gene2exons

def change_chrom_name(chrom):
    if chrom.startswith('chr'):
        return chrom[3:]
    else:
        return 'chr'+chrom
        #return chrom
    
# 假设 Exon 和 Utr 定义如下
Exon = t.Tuple[str, str, str, int]  # (type, name, seq, n_trans)
Utr = t.Tuple[str, str, str, int]  # (type, name, seq, n_trans)

def extract_gene_features(df_gtf: pd.DataFrame, fa: Fasta,
                          genelist: pd.DataFrame, min_length: int=40
                          ) -> t.Mapping[str, t.List[t.Tuple[str, str]]]:
    """Extract all exons and UTRs of each gene"""
    gene_features = {}

    for item in genelist.iterrows():
        gene = item[1]['geneID']
        df_gene = df_gtf[df_gtf.gene_name == gene]
        
        if df_gene.shape[0] <= 0:
            raise ValueError(f"Gene {gene} not exists in GTF file.")

        # 提取外显子（CDS和exon）
        df_exons = df_gene[df_gene.type.isin(['CDS', 'exon'])].copy()
        df_exons = df_exons[df_exons.length > min_length]
        
        if df_exons.shape[0] == 0:
            raise ValueError(f"Gene {gene} can't find any exon records.")

        gene_features[gene] = []
        
        for idx, row in df_exons.iterrows():
            chr_, start, end, strand = str(row['chr']), row['start'], row['end'], row['strand']
            name = f"{gene}_{start}_{end}"
            n_trans = row['type']
            seq = fa[chr_][start:end].seq.upper()
            if strand == '-':
                seq = reverse_complement(seq)
            gene_features[gene].append(("exon", name, seq, n_trans))

        # 提取UTR
        df_utrs = df_gene[df_gene.type == 'UTR'].copy()
        df_utrs = df_utrs[df_utrs.length > min_length]

        if df_utrs.shape[0] > 0:
            for idx, row in df_utrs.iterrows():
                chr_, start, end, strand = str(row['chr']), row['start'], row['end'], row['strand']
                name = f"{gene}_{start}_{end}"
                n_trans = 1
                seq = fa[chr_][start:end].seq.upper()
                if strand == '-':
                    seq = reverse_complement(seq)
                
                if idx == 0:
                    utr_type = "5'UTR" if strand == '+' else "3'UTR"
                elif idx == df_utrs.shape[0] - 1:
                    utr_type = "3'UTR" if strand == '+' else "5'UTR"
                else:
                    utr_type = "unknown_UTR"
                
                gene_features[gene].append((utr_type, name, seq, n_trans))

    return gene_features


def extract_trans_seqs(gtf_path, fa_path, output_fa_path):
    """Extract transcript's sequences.
    """
    #import pdb; pdb.set_trace()
    log.info(f"Extract transcript sequences from: {gtf_path}, {fa_path}")

    fa = Fasta(str(fa_path))
    exons_df = read_gtf(gtf_path, filter_by_type='exon', extract_fields=["gene_id", "transcript_id"])
    #exons_df = remove_small_chromosomes_df(exons_df)
    exons_df = exons_df[exons_df.start < exons_df.end]
    exons_df = exons_df[['chr','start','end','strand','gene_id','transcript_id']].dropna(axis=0, how="any", subset=['transcript_id'])
    trans = {}  # (gene_id, trans_id) -> [chr, strand, exons],  exons: (start, end)
    for (_, row) in exons_df.iterrows():
        key_ = (row['gene_id'], row['transcript_id'])
        chrom, strand, left, right = str(row['chr']), row['strand'], row['start'], row['end']
        if key_ not in trans:
            trans[key_] = [chrom, strand, [[left, right]]]
        else:
            trans[key_][2].append([left, right])
    adjacent_thresh = 5
    for key_, [chrom, strand, exons] in list(trans.items()):  # merge adjacent exons
        exons.sort()
        tmp_exons = [exons[0]]
        for i in range(1, len(exons)):
            if exons[i][0] - tmp_exons[-1][1] <= adjacent_thresh:
                tmp_exons[-1][1] = exons[i][1]
            else:
                tmp_exons.append(exons[i])
        trans[key_] = [chrom, strand, tmp_exons]
    seq_dict = {}
    for key_, [chrom, strand, exons] in list(trans.items()):
        seq_lst = []
        for i in range(len(exons)):
            try:
                seq = fa[chrom][exons[i][0]:exons[i][1]].seq
            except KeyError:
                #import ipdb; ipdb.set_trace()
                chrom = change_chrom_name(chrom)
                seq = fa[chrom][exons[i][0]:exons[i][1]].seq
            if strand == '-':
                seq = reverse_complement(seq)
                seq_lst.append(seq)
            else:
                seq_lst.append(seq)
        seq = "".join(seq_lst)
        seq_dict[key_] = seq

    log.info(f"Save results to {output_fa_path}")
    with open(output_fa_path, 'w') as f:
        for (gene_id, tran_id), seq in seq_dict.items():
            f.write(f">{gene_id}_{tran_id}\n")
            f.write(f"{seq}\n")


def generate_target_seqs(target_genes, fasta_path, gtf_path, min_length=40, overlap=1):
    exon_info = get_exon_seq(target_genes, fasta_path, gtf_path)
    data_list = []  # 收集数据的列表

    for gene_name, exon_list in exon_info.items():
        for i, exon_data in enumerate(exon_list, start=1):
            name, trans_name, seq, n_trans = exon_data
            chr_name = name.split('_')[0]  # 解析染色体名称

            # 生成子序列
            for i in range(0, len(seq), min_length-overlap):
                tem = seq[i:min_length+i]
                tem = seq[i:i + min_length]
                if len(tem) == min_length:  # 确保片段长度符合要求
                    start = i + 1  # 人类可读的位置应该从1开始
                    end = i + min_length
                    gene_id = f"{gene_name}.{i}"
                    
                    # 将数据添加到列表中
                    data_list.append([gene_id, chr_name, trans_name, start, end, tem, n_trans])

    # 创建 DataFrame
    data = pd.DataFrame(data_list, columns=['gene_id', 'chr_name', 'transcript_name','start', 'end', 'target_region', 'n_trans'])
    return data



