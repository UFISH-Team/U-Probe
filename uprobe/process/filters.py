import pandas as pd
import typing as t

def filter_n_mapped_genes(df: pd.DataFrame, threshold: int) -> pd.DataFrame:
    df['n_mapped_genes'] = df['n_mapped_genes'].apply(lambda x: list(x.values())[0])
    print(df['n_mapped_genes'])
    return df[df["n_mapped_genes"].values <= threshold]

def filter_tm(df: pd.DataFrame,
                       tm_columns: t.List[str], 
                       min_tm: int = 35, 
                       max_tm: int = 45
                       ) -> pd.DataFrame:
    return df[
        df[tm_columns].apply(lambda x: x.between(min_tm, max_tm)).all(axis=1)
    ]

def filter_target_fold_score(df: pd.DataFrame, 
                             threshold: int = 50
                             ) -> pd.DataFrame:
    return df[df["target_fold_score"] <= threshold]

def filter_gc_content(df: pd.DataFrame, 
                      ratio: float = 0.3
                      ) -> pd.DataFrame:
    return df[df["target_gc_content"] >= ratio]

def filter_circle_fold_score(res_df: pd.DataFrame,
                            circle_fold_thresh: int = 80
                            ) -> pd.DataFrame:
    return res_df[res_df['circle_fold_score'] <= circle_fold_thresh]

def filter_circle_AT(res_df: pd.DataFrame
                     ) -> pd.DataFrame:
    return res_df[res_df['circle_probe'].str.match("^[AT].*[AT]$")]

