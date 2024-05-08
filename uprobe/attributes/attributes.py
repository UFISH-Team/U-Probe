import sys
import logging
import os
import pandas as pd
import typing as t
import primer3
import RNA
import subprocess as subp
import pysam
from pathos.pools import ProcessPool

from ..utils import get_logger, reverse_complement

log = get_logger(__name__)

Aln = t.Tuple[str, int, int]  # chr, start, end
Block = t.Tuple[str, str, t.List[Aln]]  # query_name, query_seq, alignments

def read_sam_align_blocks(
        sam_path: str
        ) -> t.Iterable[Block]:
    def yield_cond(old, rec, block, end=False):
        res = (old is not None)
        if res and not end:
            res &= rec.query_name != old.query_name
        return res
    with pysam.AlignmentFile(sam_path, mode='r') as sam:
        alns = []
        old = None
        rec = None
        for rec in sam.fetch():
            aln = rec.reference_name, rec.reference_start, rec.reference_end
            if yield_cond(old, rec, alns):
                yield old.query_name, old.query_sequence, alns
                alns = []
            if aln[0] is not None:
                alns.append(aln)
            old = rec
        if (rec is not None) and yield_cond(old, rec, alns, end=True):
            yield old.query_name, old.query_sequence, alns

def bowtie2_align_se_sen(
        fq_path: str,
        index: str,
        sam_path: str,
        threads: int = 10,
        log_file: t.Optional[str] = 'bowtie2.log',
        header: bool = True,
        ) -> str:
    cmd = ["bowtie2", "-x", index, "-U", fq_path]
    if not header:
        cmd.append("--no-hd")
    cmd += ["-t", "-k", "100", "--very-sensitive-local"]
    cmd += ["-p", str(threads)]
    cmd += ["-S", sam_path]
    cmd = " ".join(cmd)
    if log_file:
        cmd += f" > {log_file} 2>&1"
    log.info(f"Call cmd: {cmd}")
    subp.check_call(cmd, shell=True)
    return sam_path

def write_fastq(outdir, gene, recname2seq: t.Mapping[str, str]):
    fq = f'{outdir}/{gene}.fq'
    with open(fq, 'w') as f:
        for recname, seq in recname2seq.items():
            f.write(f"@{recname}\n")
            f.write(seq+"\n")
            f.write("+\n")
            f.write("~"*len(seq)+"\n")
    return fq

def count_n_bowtie2_aligned_genes(
        outdir: str,
        recname2seq: t.Mapping[str, str],
        name: str,
        index_prefix: str,
        threads: int):
    fq_path = write_fastq(outdir, name, recname2seq)
    sam_path = f"{outdir}/{name}.sam"
    if not os.path.exists(sam_path):
        bowtie2_align_se_sen(
            fq_path, index_prefix,
            sam_path, threads=threads,
            log_file=f"{outdir}/{name}.bowtie2.log")
    else:
        log.info("{} exists".format(sam_path))
    n_mapped_genes = {}
    for rec_name, seq, alns in read_sam_align_blocks(sam_path):
        n_genes = len(set([chr_.split("_")[0] for chr_, s, e in alns]))
        n_mapped_genes[rec_name] = n_genes
    return n_mapped_genes

def self_match(probe: str, min_match = 4):
    length = len(probe)
    probe_re = reverse_complement(probe)
    match_pairs = 0
    for i in range(0,length-min_match+1):
        tem = probe[i:min_match+i]
        for j in range(0,length-min_match+1):
            tem_re = probe_re[j:min_match+j]
            if tem == tem_re and i + j + min_match - 2 != length:
                match_pairs = match_pairs + 1
    return match_pairs


def get_sub_seq_params(tem, anchor1, anchor2, offset, whole_fold):
    # small is better, means RNA more unlikely to fold
    target_fold_score = -RNA.fold_compound(tem).mfe()[1]
    tem1 = tem[0:13]
    tem2 = tem[13:26]
    tem3 = tem[27:40]
    tem4 = tem[26]
    tm1 = primer3.calcTm(tem1)
    tm2 = primer3.calcTm(tem2)
    tm3 = primer3.calcTm(tem3)
    region = max(tm1,tm2,tm3) - min(tm1,tm2,tm3)
    tem1_re = reverse_complement(tem1)
    tem2_re = reverse_complement(tem2)
    tem3_re = reverse_complement(tem3)
    pad_probe = tem1_re+anchor1+"A"+anchor2+tem2_re
    amp_probe = tem3_re+tem4+reverse_complement(anchor2)[:-2]
    match_pairs_pad = self_match(pad_probe)
    match_pairs_amp = self_match(amp_probe)
    pad_fold_score = -RNA.fold_compound(pad_probe).mfe()[1]
    amp_fold_score = -RNA.fold_compound(amp_probe).mfe()[1]
    target_fold = whole_fold[0][offset:offset+len(tem)]
    target_blocks = len(target_fold) - target_fold.count('.')  # smaller is better
    return [
        offset, pad_fold_score, amp_fold_score,
        match_pairs_pad, match_pairs_amp,
        region, tm1, tm2, tm3,
        target_fold_score, target_blocks,
        pad_probe, amp_probe
    ]


def primer_design(
        tmp_dir,
        name, anchor1, anchor2, exons,
        index_prefix, threads=10,
        min_length=40):
    """Design primers for one gene"""
    df_rows = []
    sub_seqs = []
    pool = ProcessPool(ncpus=threads)
    map_ = map if threads <= 1 else pool.map

    def process_(exon):
        exon_name, seq, n_trans = exon
        seq_len = len(seq)
        whole_fold = RNA.fold_compound(seq).mfe()
        seqs = []; rows = []
        for i in range(0,len(seq)-min_length+1):
            tem = seq[i:min_length+i]
            params = get_sub_seq_params(tem, anchor1, anchor2, i, whole_fold)
            row = [exon_name, n_trans] + params + [tem]
            seqs.append(tem)
            rows.append(row)
        return seqs, rows

    for seqs, rows in map_(process_, exons):
        sub_seqs.extend(seqs)
        df_rows.extend(rows)

    df = pd.DataFrame(df_rows)
    df.columns = ['exon_name', 'n_trans', 'offset',
                  'pad_fold_score', 'amp_fold_score',
                  'self_match_pad', 'self_match_amp', 
                  'tm_region', 'tm1', 'tm2', 'tm3',
                  'target_fold_score', 'target_blocks',
                  'primer_pad', 'primer_amp',
                  'target_seq']
    
    recname2seq = {f"{row['exon_name']}_{row['offset']}": row['target_seq'] for (_, row) in df.iterrows()}
    n_mapped_genes = count_n_bowtie2_aligned_genes(tmp_dir, recname2seq, name, index_prefix, threads)
    n_mapped_genes = [n_mapped_genes[f"{row['exon_name']}_{row['offset']}"] for _, row in df.iterrows()]
    df['n_mapped_genes'] = n_mapped_genes

    return df