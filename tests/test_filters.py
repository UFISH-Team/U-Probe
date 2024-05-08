from uprobe.filters._filters import filter_tm, filter_circle_fold_score
import pandas as pd

def test_filter_tm():
    # case1: tm1, tm2, tm3 all in range
    df = pd.DataFrame({
        'tm1': [40, 40, 50],
        'tm2': [40, 40, 50],
        'tm3': [40, 40, 50],
    })
    assert filter_tm(df, tm_range=(35, 45)).shape[0] == 2

    # case2: tm1, tm2, tm3 all out of range
    df = pd.DataFrame({
        'tm1': [30, 30, 30],
        'tm2': [30, 30, 30],
        'tm3': [30, 30, 30],
    })
    assert filter_tm(df, tm_range=(35, 45)).shape[0] == 0

    # case3: tm1, tm2, tm3 partially in range
    df = pd.DataFrame({
        'tm1': [30, 40, 50],
        'tm2': [30, 40, 50],
        'tm3': [30, 40, 50],
    })
    assert filter_tm(df, tm_range=(35, 45)).shape[0] == 1

def test_filter_circle_fold_score():
    # case1: all rows are less than threshold
    df = pd.DataFrame({
        'circle_fold_score': [70, 80, 80],
    })
    assert filter_circle_fold_score(df, circle_fold_thresh=80).shape[0] == 3

    # case2: all rows are greater than threshold
    df = pd.DataFrame({
        'circle_fold_score': [90, 90, 90],
    })
    assert filter_circle_fold_score(df, circle_fold_thresh=80).shape[0] == 0

    # case3: partially rows are less than threshold
    df = pd.DataFrame({
        'circle_fold_score': [70, 80, 90],
    })
    assert filter_circle_fold_score(df, circle_fold_thresh=80).shape[0] == 2