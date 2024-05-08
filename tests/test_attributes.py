from uprobe.attributes._attributes import cal_temp, cal_fold, cal_gc_content, cal_target_fold_score
from uprobe.attributes._attributes import cal_target_blocks, cal_self_match, count_n_bowtie2_aligned_genes

def test_cal_temp(seq="ATGC"):
    s = cal_temp(seq)
    assert s == cal_temp(seq)

def test_cal_fold(seq="ATGC"):
    score = cal_fold(seq)
    assert score == cal_fold(seq)

def test_cal_gc_content(seq="ATGC"):
    score = cal_gc_content(seq)
    assert score == cal_gc_content(seq)

def test_cal_target_fold_score(seq="ATGC"):
    score = cal_target_fold_score(seq)
    assert score == cal_target_fold_score(seq)

def test_cal_target_blocks(seq="ATGC", offset=0, whole_fold=("ATGC", 0, 0)):
    score = cal_target_blocks(seq, offset, whole_fold)
    assert score == cal_target_blocks(seq, offset, whole_fold)

def test_cal_self_match(seq="ATGC"):
    score = cal_self_match(seq)
    assert score == cal_self_match(seq)

def test_cal_n_mapped_genes():
    recname2seq = {
        "1": "ATGCAGGGTTAAC",
        "2": "ATGCAGCTACGTT",
        "3": "ATGCAAGGTTAAC",
        "4": "ATGCAGGGTTAAC",
        "5": "ATGCAAGGTTAAC",
    }
    name = "test"
    index_prefix = "test"
    threads = 1
    n_mapped_genes = count_n_bowtie2_aligned_genes(".", recname2seq, name, index_prefix, threads)
    print(n_mapped_genes)
    assert n_mapped_genes == count_n_bowtie2_aligned_genes(".", recname2seq, name, index_prefix, threads)
 
