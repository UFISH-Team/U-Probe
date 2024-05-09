import os
import typing as t
import primer3
import RNA
import subprocess as subp
import pysam
import pandas as pd
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


def cal_temp(seq: str): # Tm
    return primer3.calcTm(seq)

def cal_fold(seq: str): # MFE
    return -RNA.fold_compound(seq).mfe()[1]

def cal_gc_content(seq: str):
    return (seq.count('G') + seq.count('C')) / len(seq)

def cal_target_fold_score(seq: str):
    return -RNA.fold_compound(seq).mfe()[1]

def cal_target_blocks(seq: str, offset: int, whole_fold: t.Tuple[str, int, int]):
    target_fold = whole_fold[0][offset:offset+len(seq)]
    target_blocks = len(target_fold) - target_fold.count('.')  # smaller is better
    return target_blocks

def cal_self_match(seq: str):
    return self_match(seq)
