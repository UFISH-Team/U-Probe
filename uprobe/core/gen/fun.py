import pandas as pd
import os
import typing as t
from pyfaidx import Fasta

from uprobe.core.utils import *

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
    chr_new = []
    for chr_ in df.chr:
        if str(chr_).startswith('chr'):
            chr_new.append(chr_)
        else:
            chr_new.append(f'chr{chr_}')
    df.chr = chr_new
    return df

def process_gtf_inplace(filepath):
    """
    If gene_name does not exist, replace gene with gene_name.
    """
    with open(filepath, 'r') as file:
        lines = file.readlines()
    updated_lines = []
    for line in lines:
        if line.startswith('#') or not line.strip():
            updated_lines.append(line)
            continue
        fields = line.strip().split('\t')
        if len(fields) < 9:
            log.warning(f"not a valid GTF line: {line.strip()}")
            updated_lines.append(line)
            continue
        attributes = fields[8]
        if "gene_name" in attributes:
            updated_lines.append(line)
        else:
            updated_attributes = []
            for attr in attributes.split(';'):
                attr = attr.strip()
                if not attr:
                    continue
                if attr.startswith("gene "):
                    updated_attributes.append(attr.replace("gene ", "gene_name ")) 
                else:
                    updated_attributes.append(attr)
            fields[8] = '; '.join(updated_attributes)
            updated_lines.append('\t'.join(fields) + '\n')
    with open(filepath, 'w') as file:
        file.writelines(updated_lines)

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
        df_exons['transcript_name'] = df_exons['info'].str.extract(r'transcript_id\s+"([^"]+)"')[0]
        exon_cnts = df_exons.groupby(
            by=['chr', 'start', 'end', 'length', 'strand'],
            as_index=False
        ).agg(
            count=('transcript_name', 'count'),  
            transcript_name=('transcript_name', lambda x: list(set(x))) 
        )
        gene2exons[gene] = []
        for idx, row in exon_cnts.iterrows():
            chr_, start, end, strand, trans_name = str(row['chr']), row['start'], row['end'], row['strand'], row['transcript_name']
            exon_name = '_'.join([chr_, str(start), str(end), strand])
            n_trans = row['count']
            #chr_ = chr_.replace('chr', '')
            seq = fa[chr_][start:end].seq.upper()
            if strand == '-':
                seq = reverse_complement(seq)
            exon = (exon_name, trans_name, seq, n_trans)
            gene2exons[gene].append(exon)
    return gene2exons

def get_exon_seq(genes, fa, gtf):
    fa = Fasta(fa)
    genelist = pd.DataFrame(genes, columns=['geneID'])
    df_gtf = read_gtf(gtf, extract_fields=['gene_name', "transcript_id"], get_length=True)
    gene2exons = extract_exons_rca(df_gtf, fa, genelist)
    return gene2exons

def change_chrom_name(chrom):
    if chrom.startswith('chr'):
        return chrom[3:]
    else:
        return 'chr'+chrom
    
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
        # extract CDS/exon
        df_exons = df_gene[df_gene.type.isin(['CDS', 'exon'])].copy()
        df_exons = df_exons[df_exons.length > min_length]
        if df_exons.shape[0] == 0:
            raise ValueError(f"Gene {gene} can't find any exon records.")
        gene_features[gene] = []
        df_exons['transcript_name'] = df_exons['info'].str.extract(r'transcript_id\s+"([^"]+)"')[0]
        df_exons = df_exons.groupby(
            by=['chr', 'start', 'end', 'length', 'strand'],
            as_index=False
        ).agg(
            count=('transcript_name', 'count'),  
            transcript_name=('transcript_name', lambda x: list(set(x))) 
        )
        for idx, row in df_exons.iterrows():
            chr_, start, end, strand = str(row['chr']), row['start'], row['end'], row['strand']
            name = f"{gene}_{start}_{end}"
            n_trans = row['count']
            seq = fa[chr_][start:end].seq.upper()
            if strand == '-':
                seq = reverse_complement(seq)
            gene_features[gene].append(("exon", name, seq, n_trans))
        # extract utr
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
    """
    Extract transcript's sequences.
    """
    log.info(f"extract transcript sequences from: {gtf_path}, {fa_path}")
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
                log.warning(f"Sequence {chrom} not found in FASTA index, rebuilding index...")
                fa.close()
                import os
                fai_file = str(fa_path) + '.fai'
                if os.path.exists(fai_file):
                    os.remove(fai_file)
                    log.info(f"Removed corrupted index file: {fai_file}")
                fa = Fasta(str(fa_path)) 
                seq = fa[chrom][exons[i][0]:exons[i][1]].seq
            if strand == '-':
                seq = reverse_complement(seq)
                seq_lst.append(seq)
            else:
                seq_lst.append(seq)
        seq = "".join(seq_lst)
        seq_dict[key_] = seq
    log.info(f"save results to {output_fa_path}")
    with open(output_fa_path, 'w') as f:
        for (gene_id, tran_id), seq in seq_dict.items():
            f.write(f">{gene_id}_{tran_id}\n")
            f.write(f"{seq}\n")

def generate_target_seqs(
                        source,
                        targets, 
                        fasta_path, 
                        gtf_path, 
                        min_length: int = 40, 
                        overlap: int = 20
                         ):
    if source == 'exon' or source == 'CDS':
        exon_info = get_exon_seq(targets, fasta_path, gtf_path)
        data_list = [] 
        for gene_name, exon_list in exon_info.items():
            n = 1
            for j, exon_data in enumerate(exon_list, start=1):
                exon_name, trans_name, seq, n_trans = exon_data
                for i in range(0, len(seq) - min_length + 1,  min_length - overlap):
                    tem = seq[i:i + min_length]
                    if len(tem) == min_length: 
                        start = i + 1  
                        end = i + min_length
                        gene_id = f"{gene_name}_{n}"
                        sub_region = f"{start}_{end}"
                        n += 1
                        data_list.append([gene_id, gene_name, sub_region, exon_name, trans_name, start, end, tem, n_trans])
        data = pd.DataFrame(data_list, columns=['probe_id', 'target', 'sub_region','exon_name', 'transcript_names','start', 
                                                'end', 'target_region', 'n_trans'])
        return data
    elif source == 'UTR':
        utr_info = extract_gene_features(targets, fasta_path, gtf_path)
        data_list = []
        for gene_name, utr_list in utr_info.items():
            n = 1
            for j, utr_data in enumerate(utr_list, start=1):
                utr_name, trans_name, seq, n_trans = utr_data
                # extract target region seqs
                for i in range(0, len(seq) - min_length + 1,  min_length - overlap):
                    tem = seq[i:i + min_length]
                    if len(tem) == min_length: 
                        start = i + 1  
                        end = i + min_length
                        gene_id = f"{gene_name}_{n}"
                        sub_region = f"{start}_{end}"
                        n += 1
                        data_list.append([gene_id, gene_name, sub_region, utr_name, trans_name, start, end, tem, n_trans])
        data = pd.DataFrame(data_list, columns=['probe_id', 'target', 'sub_region', 'utr_name', 'transcript_names','start', 
                                                'end', 'target_region', 'n_trans'])
        return data
    elif source == 'genome':
        data_list = []
        for target in targets:
            seq_list = extract_fasta(fasta_path, target, min_length, overlap)
            data_list.extend(seq_list)
        data = pd.DataFrame(data_list, columns=['probe_id', 'target', 'sub_region', 'target_region'])
        return data

def validate_targets(targets, gtf_path, DTF_NAME_FIX=False):
    log.info(f"validating targets in gtf file: {targets}")
    df_gtf = read_gtf(gtf_path)
    if DTF_NAME_FIX:
        process_gtf_inplace(gtf_path)
        df_gtf = read_gtf(gtf_path)
    genome_genes = set(df_gtf['gene_name'].unique())
    valid_targets = []
    invalid_targets = []
    for target in targets:
        if target in genome_genes:
            valid_targets.append(target)
        else:
            invalid_targets.append(target)
    if invalid_targets:
        log.warning(f"invalid targets: {invalid_targets}")
        return False, valid_targets, invalid_targets
    else:
        return True, valid_targets, invalid_targets

