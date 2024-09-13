import pytest
import pandas as pd
from uprobe.process.filters import (
    filter_gc_content,
    filter_n_mapped_genes,
    filter_target_fold_score,
    filter_tm,
    filter_circle_AT
)

# 使用 pytest.fixture 定义样本数据
@pytest.fixture
def sample_df():
    data = {
        'n_mapped_genes': [2, 5, 3, 1],
        'tm1': [36, 44, 50, 30],
        'tm2': [37, 42, 33, 40],
        'tm3': [39, 46, 32, 38],
        'target_fold_score': [70, 20, 75, 60],
        'gc_content': [0.4, 0.2, 0.5, 0.3],
        'circle_fold_score': [90, 75, 85, 70],
        'circle_probe': ['ATCGTA', 'GCTA', 'CGTA', 'AGTC']
    }
    return pd.DataFrame(data)

def test_filter_n_mapped_genes(sample_df):
    result = filter_n_mapped_genes(sample_df, 3)
    assert result.shape[0] == 3

def test_filter_tm(sample_df):
    result = filter_tm(sample_df, 35, 45)
    assert result.shape[0] == 1

def test_filter_gc_content(sample_df):
    result = filter_gc_content(sample_df, 0.3)
    assert result.shape[0] == 3

def test_filter_target_fold_score(sample_df):
    result = filter_target_fold_score(sample_df, 60)
    assert result.shape[0] == 2  # 只有两行满足条件

def test_filter_circle_AT(sample_df):
    result = filter_circle_AT(sample_df)
    assert result.shape[0] == 1 