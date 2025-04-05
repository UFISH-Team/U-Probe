from uprobe.attributes._attributes import cal_temp, cal_fold, cal_gc_content, cal_target_fold_score
from uprobe.attributes._attributes import cal_target_blocks, cal_self_match, count_n_bowtie2_aligned_genes
from uprobe.tools.aligner import build_bowtie2_index

def test_cal_temp(seq="ATGC"):
    s = cal_temp(seq)
    assert isinstance(s, float), "Expected float, got {}".format(type(s))

def test_cal_fold(seq="ATGC"):
    score = cal_fold(seq)
    assert isinstance(score, float), "Expected float, got {}".format(type(score))

def test_cal_gc_content(seq="ATGC"):
    score = cal_gc_content(seq)
    assert score == 0.5, "Expected 0.5, got {}".format(score)

def test_cal_target_fold_score(seq="ATGC"):
    score = cal_target_fold_score(seq)
    assert isinstance(score, float), "Expected float, got {}".format(type(score))

def test_cal_target_blocks(seq="ATGC", offset=0):
    score = cal_target_blocks(seq, offset)
    assert isinstance(score, int), "Expected int, got {}".format(type(score))

def test_cal_self_match(seq="ATGC"):
    score = cal_self_match(seq)
    assert isinstance(score, int), "Expected int, got {}".format(type(score))

def test_cal_n_mapped_genes():
    recname2seq = {
        "1": "ATGCAGGGTTAAC",
        "2": "ATGCAGCTACGTT",
        "3": "ATGCAAGGTTAAC",
        "4": "ATGCAGGGTTAAC",
        "5": "ATGCAAGGTTAAC",
    }
    name = "test"
    index_prefix = "./tests/data/test/genome-bowtie2_index/test"
    threads = 10
    #build_bowtie2_index("./tests/data/test/test.fa", index_prefix)
    n_mapped_genes = count_n_bowtie2_aligned_genes(".", recname2seq, name, index_prefix, threads)
    print(n_mapped_genes)
    assert isinstance(n_mapped_genes, dict), "Expected dict, got {}".format(type(n_mapped_genes))
 
