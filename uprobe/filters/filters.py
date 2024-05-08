import pandas as pd
import typing as t

# Path: uprobe/filters/tm.py

def filter_tm(res_df: pd.DataFrame,
              tm_range=(35, 45)  # default range
              ) -> pd.DataFrame:
    for i in range(1, 4):  # tm1 tm2 tm3
        res_df = res_df[(tm_range[0] <= res_df[f"tm{i}"]) & (res_df[f"tm{i}"] <= tm_range[1])]
    return res_df


def filter_circle_fold_score(res_df: pd.DataFrame,
                             circle_fold_thresh=80  # default threshold
                             ) -> pd.DataFrame:
    res_df = res_df[res_df['circle_fold_score'] <= circle_fold_thresh]
    return res_df