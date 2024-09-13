from uprobe.process.sorts import sort_n_trans
import pandas as pd


def test_sort_n_trans():
    data = {
        'n_mapped_genes': [100, 200, 150], 
        'circle_fold_score': [0.8, 0.7, 0.9],
        'self_match_circle': [0.6, 0.7, 0.5],
        'amp_fold_score': [1.2, 1.1, 1.3],
        'self_match_amp': [0.4, 0.5, 0.3],
        'target_blocks': [10, 5, 15],
        'target_fold_score': [0.6, 0.8, 0.7],
        'tm_region': [60, 70, 65],
        'n_trans': [500, 400, 600]
    }
    df = pd.DataFrame(data)
    res_df = sort_n_trans(df, is_ascending=False)
    assert res_df['n_trans'].to_list() == [600, 500, 400]
