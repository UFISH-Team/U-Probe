import pandas as pd
import typing as t

def filter_n_mapped_genes(df: pd.DataFrame, n_mapped_genes: int) -> pd.DataFrame:
    """
    Filter out rows where the number of mapped genes is greater than the specified threshold.

    Parameters:
    - df: Input DataFrame.
    - n_mapped_genes: Maximum allowed number of mapped genes.

    Returns:
    - Filtered DataFrame.
    """
    return df[df["n_mapped_genes"] <= n_mapped_genes]

def filter_tm(df: pd.DataFrame, min_tm: int = 35, max_tm: int = 45) -> pd.DataFrame:
    """
    Filter rows based on melting temperature (tm) values.

    Parameters:
    - df: Input DataFrame.
    - min_tm: Minimum melting temperature.
    - max_tm: Maximum melting temperature.

    Returns:
    - Filtered DataFrame.
    """
    return df[
        (df["tm"].between(min_tm, max_tm)) 
    ]

def filter_target_fold_score(df: pd.DataFrame, threshold: int = 50) -> pd.DataFrame:
    """
    Filter out rows where the target fold score is greater than the specified threshold.

    Parameters:
    - df: Input DataFrame.
    - threshold: Maximum allowed target fold score.

    Returns:
    - Filtered DataFrame.
    """
    return df[df["target_fold_score"] <= threshold]

def filter_gc_content(df: pd.DataFrame, ratio: float = 0.3) -> pd.DataFrame:
    """
    Filter rows based on GC content ratio.

    Parameters:
    - df: Input DataFrame.
    - ratio: Minimum allowed GC content ratio.

    Returns:
    - Filtered DataFrame.
    """
    return df[df["gc_content"] >= ratio]

def filter_circle_fold_score(res_df: pd.DataFrame, circle_fold_thresh: int = 80) -> pd.DataFrame:
    """
    Filter rows based on circle fold score.

    Parameters:
    - res_df: Input DataFrame.
    - circle_fold_thresh: Maximum allowed circle fold score.

    Returns:
    - Filtered DataFrame.
    """
    return res_df[res_df['circle_fold_score'] <= circle_fold_thresh]

def filter_circle_AT(res_df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter rows based on the 'circle_probe' sequence starting and ending with A or T.

    Parameters:
    - res_df: Input DataFrame.

    Returns:
    - Filtered DataFrame.
    """
    return res_df[res_df['circle_probe'].str.match("^[AT].*[AT]$")]

