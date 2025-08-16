import os
import typing as t
import primer3
import RNA
import subprocess as subp
from uprobe.utils import get_logger, reverse_complement, write_fastq

log = get_logger(__name__)

Aln = t.Tuple[str, int, int]  # chr, start, end
Block = t.Tuple[str, str, t.List[Aln]]  # query_name, query_seq, alignments

def read_sam_align_blocks(
        sam_path: str,
        min_mapq: int = 30  # MAPQ 是通过比对得分和输入序列的错配情况计算的，值越高表示比对质量越好
                            # MAPQ > 30: 比对质量相对可靠（唯一比对或高匹配度）。
                            # MAPQ > 20: 允许某些中质量比对。
                            # MAPQ = 0: 通常会被完全过滤掉，因为这些序列可能无法唯一比对
        ) -> t.Iterable[Block]:
    import pysam
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
            if rec.mapping_quality < min_mapq:
                continue
            aln = rec.reference_name, rec.reference_start, rec.reference_end
            if yield_cond(old, rec, alns):
                yield old.query_name, old.query_sequence, alns
                alns = []
            if aln[0] is not None:
                alns.append(aln)
            #print(aln)
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
    cmd = ["bowtie2", "-x", str(index), "-U", str(fq_path)]
    if not header:
        cmd.append("--no-hd")
    cmd += ["-t", "-k", "100", "--very-sensitive-local"]
    cmd += ["-p", str(threads)]
    cmd += ["-S", str(sam_path)]
    cmd_str = " ".join(cmd)
    if log_file:
        cmd_str += f" > {log_file} 2>&1"
    log.info(f"Call cmd: {cmd_str}")
    try:
        subp.check_call(cmd_str, shell=True)
    except subp.CalledProcessError as e:
        log.error(f"Error: {e}")
        if log_file:
            # print log file
            with open(log_file) as f:
                log.error(f.read())
    return sam_path

def static_otp(outdir: str, 
                pool_name: str, 
                region: str, 
                target_seq: str,
                index_prefix: str, 
                threads: int = 10,
                target_regions: str = None,
                density_thresh: float = 1e-5,
                avoid_target_overlap: bool = True,
                search_range: t.Tuple[int, int] = (-1e5, 1e5)
                ):
    recname2seq = {region: target_seq}
    fq_path = write_fastq(outdir, pool_name, recname2seq)
    sam_path = f"{outdir}/{pool_name}.sam"
    if not os.path.exists(sam_path):
        bowtie2_align_se_sen(
            fq_path, index_prefix,
            sam_path, threads=threads,
            log_file=f"{outdir}/{pool_name}.bowtie2.log")
    out_path = f"{outdir}/{pool_name}.otp.csv"
    counted = cal_otp(sam_path, out_path, target_regions, density_thresh, 
            avoid_target_overlap, search_range)
    return counted

def count_n_bowtie2_aligned_genes(
        outdir: str,
        recname2seq: t.Mapping[str, str],
        name: str,
        index_prefix: str,
        min_mapq: int = 30,
        threads: int = 10):
    fq_path = write_fastq(outdir, name, recname2seq)
    sam_path = f"{outdir}/{name}.sam"
    if not os.path.exists(sam_path):
        bowtie2_align_se_sen(
            fq_path, index_prefix,
            sam_path, threads=threads,
            log_file=f"{outdir}/{name}.bowtie2.log")
    n_mapped_genes = {}
    for rec_name, seq, alns in read_sam_align_blocks(sam_path, min_mapq=min_mapq):

        n_genes = len(set(["_".join(chr_.split("_")[-4:]) for chr_, s, e in alns]))
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

def preprocess_seq(seq):
    return seq.replace('N', 'A')

def cal_temp(seq: str): # Tm
    seq = preprocess_seq(seq)
    return primer3.calc_tm(seq)

def cal_fold(seq: str): # RNA fold
    return -RNA.fold_compound(seq).mfe()[1]

def cal_gc_content(seq: str): #target gc content
    return (seq.count('G') + seq.count('C')) / len(seq)

def cal_target_fold_score(seq: str):
    if not seq or seq is None:
        return float('nan')
    
    # Replace any invalid characters with A (ViennaRNA only accepts AUGC)
    # Convert T to U for RNA folding
    clean_seq = seq.upper().replace('T', 'U')
    # Replace any other invalid characters with A
    valid_chars = set('AUGC')
    clean_seq = ''.join(c if c in valid_chars else 'A' for c in clean_seq)
    
    if not clean_seq:
        return float('nan')
    
    try:
        return -RNA.fold_compound(clean_seq).mfe()[1]
    except Exception as e:
        print(f"Warning: RNA folding failed for sequence '{seq[:20]}...': {e}")
        return float('nan')

def cal_target_blocks(seq: str, offset: float):
    whole_fold = RNA.fold_compound(seq).mfe()
    target_fold = whole_fold[0][offset:offset+len(seq)]
    target_blocks = len(target_fold) - target_fold.count('.')  # smaller is better
    return target_blocks

def cal_self_match(seq: str):
    return self_match(seq)

def cal_otp(sam_path: str, 
            out_path: str,
            target_regions: t.List[str], 
            density_thresh: float = 1e-5, 
            avoid_target_overlap: bool = True, 
            search_range: t.Tuple[int, int] = (-1e5, 1e5)):
    from uprobe.attributes.otp import avoid_otp
    counted = avoid_otp(sam_path, out_path, target_regions, density_thresh, avoid_target_overlap, search_range)
    return counted
