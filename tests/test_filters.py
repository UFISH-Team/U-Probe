from uprobe.filters._filters import filter_tm, filter_circle_fold_score,  filter_primer_circle, filter_n_mapped_genes
import pandas as pd

def test_filter_tm():
    # case: tm1, tm2, tm3 partially in range
    df = pd.DataFrame({
        'tm1': [30, 40, 50],
        'tm2': [30, 40, 50],
        'tm3': [30, 40, 50],
    })
    assert filter_tm(df, tm_range=(35, 45)).shape[0] == 1

def test_filter_circle_fold_score():
    # case: partially rows are less than threshold
    df = pd.DataFrame({
        'circle_fold_score': [70, 80, 90],
    })
    assert filter_circle_fold_score(df, circle_fold_thresh=80).shape[0] == 2

def test_filter_primer_circle():
    # case: partially rows are matched
    df = pd.DataFrame({
        'primer_circle': ['ACCGTA', 'CCCATGG', 'TAAAGC', 'ATGCGT'],
    })
    assert filter_primer_circle(df).shape[0] == 2

def test_filter_n_mapped_genes():
    # case: partially rows are less than threshold
    df = pd.DataFrame({
        'n_mapped_genes': [5, 10, 15],
    })
    assert filter_n_mapped_genes(df, n_mapped_genes_thresh=10).shape[0] == 2