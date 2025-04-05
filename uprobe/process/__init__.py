import pandas as pd 
import re
from .filters import (
    filter_gc_content,
    filter_n_mapped_genes,
    filter_target_fold_score,
    filter_tm,
    filter_circle_AT
)

def parse_condition(condition: str) -> list:
    """Parse a condition string into list of (column, operator, value) tuples
    """
    # Split by & if present
    conditions = [c.strip() for c in condition.split('&')]
    
    result = []
    # Match patterns like "column <= 80" or "column >= 35"
    pattern = r'(\w+)\s*([<>=]+)\s*(\d+)'
    
    for cond in conditions:
        match = re.match(pattern, cond)
        if not match:
            raise ValueError(f"Invalid condition format: {cond}")
        column, operator, value = match.groups()
        result.append((column, operator, float(value)))
    
    return result

def apply_condition(df: pd.DataFrame,
                    conditions: list
                    ) -> pd.DataFrame:
    """Apply multiple conditions to a DataFrame
    """
    for column, operator, value in conditions:
        if column == 'n_mapped_genes':
            # Special handling for n_mapped_genes which contains dictionaries
            if operator == '<=':
                df = df[df[column].apply(lambda x: max(x.values()) <= value)]
            elif operator == '>=':
                df = df[df[column].apply(lambda x: min(x.values()) >= value)]
            elif operator == '<':
                df = df[df[column].apply(lambda x: max(x.values()) < value)]
            elif operator == '>':
                df = df[df[column].apply(lambda x: min(x.values()) > value)]
            elif operator == '==':
                df = df[df[column].apply(lambda x: any(v == value for v in x.values()))]
            else:
                raise ValueError(f"Unsupported operator: {operator}")
        else:
            # Normal numeric comparison for other columns
            if operator == '<=':
                df = df[df[column] <= value]
            elif operator == '>=':
                df = df[df[column] >= value]
            elif operator == '<':
                df = df[df[column] < value]
            elif operator == '>':
                df = df[df[column] > value]
            elif operator == '==':
                df = df[df[column] == value]
            else:
                raise ValueError(f"Unsupported operator: {operator}")
    return df

def filter_table(df: pd.DataFrame,
                  filters: dict
                  ) -> pd.DataFrame:
    """Filter the table by the specified columns in the protocol.
    """
    for filter_name, filter_config in filters.items():
        if isinstance(filter_config, dict) and 'condition' in filter_config:
            condition = filter_config['condition']
            if isinstance(condition, str):
                conditions = parse_condition(condition)
                df = apply_condition(df, conditions)
            elif isinstance(condition, list):
                # Handle multiple conditions
                for cond in condition:
                    conditions = parse_condition(cond)
                    df = apply_condition(df, conditions)
        elif filter_name == 'n_mapped_genes':
            df = filter_n_mapped_genes(df, filter_config)
        elif filter_name == 'tm':
            min_tm = filter_config.get('min', 35)
            max_tm = filter_config.get('max', 45)
            df = filter_tm(df, min_tm, max_tm)
        elif filter_name == 'target_fold_score':
            df = filter_target_fold_score(df, filter_config)
        elif filter_name == 'gc_content':
            df = filter_gc_content(df, filter_config)
        elif filter_name == 'circle_AT':
            df = filter_circle_AT(df)
    return df

def sort_table(df: pd.DataFrame, 
               keys: list, 
               ascending: list
               ) -> pd.DataFrame:
    """
    Sort the table by the specified columns in the protocol.
    
    """
    return df.sort_values(by=keys, ascending=ascending)

def remove_overlap(df: pd.DataFrame, 
                   location_interval: int
                   ) -> pd.DataFrame:
    """
    Remove overlapping entries based on a specified location interval, considering each transcript separately.
    """
    df['transcript_name'] = df['transcript_name'].apply(lambda x: 
                                                        ', '.join(x) if isinstance(x, list) else x)

    df = df.sort_values(by=['transcript_name', 'start'])
    non_overlapping = []
    for _, group in df.groupby('transcript_name'):
        current_end = None
        for _, row in group.iterrows():
            if current_end is None or row['start'] > current_end + location_interval:
                non_overlapping.append(row)
                current_end = row['end']
    return pd.DataFrame(non_overlapping).reset_index(drop=True)

def post_process(df: pd.DataFrame, 
                 config: dict
                 ) -> pd.DataFrame:
    """
    Post-process the data frame according to the protocol.
    """
    processes = config.get('post_process', {})
    if 'filters' in processes:
        filters = processes['filters']
        df = filter_table(df, filters)
    if 'sorts' in processes:
        sorts = processes['sorts']
        pos_fields = sorts.get('is_ascending', [])
        neg_fields = sorts.get('is_descending', [])
        sort_keys = pos_fields + neg_fields
        is_ascending = [True] * len(pos_fields) + [False] * len(neg_fields)
        df = sort_table(df, sort_keys, is_ascending)
    if "remove_overlap" in processes:
        location_interval = processes['remove_overlap'].get('location_interval', 0)
        df = remove_overlap(df, location_interval)
    return df