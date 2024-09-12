from .filters import (
    filter_gc_content,
    filter_n_mapped_genes,
    filter_target_fold_score,
    filter_tm,
    filter_circle_AT
)

import pandas as pd 

def filter_table(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """
    Filter the table by the specified columns in the protocol.
    """
    if 'n_mapped_genes' in filters:
        df = filter_n_mapped_genes(df, filters['n_mapped_genes'])
    
    if 'tm' in filters:
        min_tm = filters['tm'].get('min', 35)
        max_tm = filters['tm'].get('max', 45)
        df = filter_tm(df, min_tm, max_tm)

    if 'target_fold_score' in filters:
        df = filter_target_fold_score(df, filters['target_fold_score'])

    if 'gc_content' in filters:
        df = filter_gc_content(df, filters['gc_content'])

    if 'circle_AT' in filters:
        df = filter_circle_AT(df)

    return df

def sort_table(df: pd.DataFrame, keys: list, ascending: list) -> pd.DataFrame:
    """
    Sort the table by the specified columns in the protocol.
    """
    return df.sort_values(by=keys, ascending=ascending)

def remove_overlap(df: pd.DataFrame, location_interval: int) -> pd.DataFrame:
    """
    Remove overlapping entries based on a specified location interval,
    considering each transcript separately.
    """
    # 确保输入 DataFrame 按照 'transcript_name' 和 'start' 列排序
    df = df.sort_values(by=['transcript_name', 'start'])
    non_overlapping = []

    # 遍历每个唯一的转录本
    for transcript, group in df.groupby('transcript_name'):
        current_end = None
        for index, row in group.iterrows():
            if current_end is None or row['start'] > current_end + location_interval:
                non_overlapping.append(row)
                current_end = row['end']

    return pd.DataFrame(non_overlapping)

def process(df: pd.DataFrame, processes: dict) -> pd.DataFrame:
    """
    Post-process the data frame according to the protocol.
    """

    if 'filters' in processes:
        filters = processes['filters']
        df = filter_table(df, filters)

    if 'sorts' in processes:
        sorts = processes['sorts']
        pos_fields = sorts.get('is_ascending', [])
        neg_fields = sorts.get('is_descending', [])

        # Combine positive and negative fields for sorting
        sort_keys = pos_fields + neg_fields
        is_ascending = [True] * len(pos_fields) + [False] * len(neg_fields)

        # Sort by the combined fields
        df = sort_table(df, sort_keys, is_ascending)

    if process == "remove_overlap":
        location_interval = processes['remove_overlap'].get('location_interval', 0)
        df = remove_overlap(df, location_interval)

    return df