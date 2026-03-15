import pandas as pd 
import re
from .otp import avoid_otp
from .equal_space import equal_space
from .summary import process_summary
from uprobe.core.utils import get_logger

logger = get_logger(__name__)


def parse_condition(condition: str) -> list:
    """Parse a condition string into list of (column, operator, value) tuples
    """
    conditions = [c.strip() for c in condition.split('&')]
    result = []
    # Match patterns like "column <= 80" or "column >= 35"
    pattern = r'(\w+)\s*([<>=]+)\s*(\d+(?:\.\d+)?)'
    for cond in conditions:
        match = re.match(pattern, cond)
        if not match:
            raise ValueError(f"Invalid condition format: {cond}")
        column, operator, value = match.groups()
        try:
            value = int(value)
        except ValueError:
            value = float(value)
        result.append((column, operator, value))
    return result

def apply_condition(df: pd.DataFrame,
                    conditions: list
                    ) -> pd.DataFrame:
    for column, operator, value in conditions:
        if column not in df.columns:
            continue
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
    for filter_name, filter_config in filters.items():
        if isinstance(filter_config, dict) and 'condition' in filter_config:
            condition = filter_config['condition']
            if isinstance(condition, str):
                conditions = parse_condition(condition)
                df = apply_condition(df, conditions)
            elif isinstance(condition, list):
                for cond in condition:
                    conditions = parse_condition(cond)
                    df = apply_condition(df, conditions)
    return df

def sort_table(df: pd.DataFrame, 
               keys: list, 
               ascending: list
               ) -> pd.DataFrame:
    valid_keys = [key for key in keys if key in df.columns]
    valid_ascending = ascending[:len(valid_keys)]
    if not valid_keys:
        return df  
    return df.sort_values(by=valid_keys, ascending=valid_ascending)

def remove_overlap(df: pd.DataFrame, 
                   config: dict,
                   location_interval: int
                   ) -> pd.DataFrame:
    transcript_col = None
    if 'transcript_name' in df.columns:
        transcript_col = 'transcript_name'
    elif 'transcript_names' in df.columns:
        transcript_col = 'transcript_names'
    if transcript_col:
        df[transcript_col] = df[transcript_col].apply(lambda x: 
                                                     ', '.join(x) if isinstance(x, list) else x)
        df = df.sort_values(by=[transcript_col, 'start'])
        non_overlapping = []
        for _, group in df.groupby(transcript_col):
            current_end = None
            for _, row in group.iterrows():
                if current_end is None or row['start'] > current_end + location_interval:
                    non_overlapping.append(row)
                    current_end = row['end']
        return pd.DataFrame(non_overlapping).reset_index(drop=True)
    elif 'target' in df.columns:
        df = df.sort_values(by=['target', 'sub_region'])
        non_overlapping = []
        for target_name, group in df.groupby('target'):
            group = group.sort_values('sub_region')
            current_end = None
            for _, row in group.iterrows():
                s, e = row['sub_region'].split('-')
                start = int(s)
                end = int(e)
                if current_end is None or start > current_end + location_interval:
                    non_overlapping.append(row)
                    current_end = end
        return pd.DataFrame(non_overlapping).reset_index(drop=True)
    else:
        return df

def post_process(df: pd.DataFrame, 
                 config: dict
                 ) -> pd.DataFrame:
    processes = config.get('post_process', {})
    if 'filters' in processes and processes['filters']:
        logger.info("Filtering the table")
        filters = processes['filters']
        df = filter_table(df, filters)
    if "avoid_otp" in processes and processes['avoid_otp']:
        logger.info("Avoiding OTP")
        config = processes['avoid_otp']
        mapped_sites_cols = []
        for col in df.columns:
            if not col.endswith('_num') and f"{col}_num" in df.columns:
                sample_val = None
                non_na_series = df[col].dropna()
                for val in non_na_series:
                    try:
                        if isinstance(val, str):
                            import ast
                            parsed_val = ast.literal_eval(val)
                            if isinstance(parsed_val, list) and len(parsed_val) > 0:
                                sample_val = parsed_val
                                break
                        elif isinstance(val, list) and len(val) > 0:
                            sample_val = val
                            break
                    except Exception:
                        continue
                if sample_val is not None:
                    if isinstance(sample_val[0], (tuple, list)) and len(sample_val[0]) == 3:
                        mapped_sites_cols.append(col)
        if mapped_sites_cols:
            for target, target_config in config.items():
                target_regions = target_config.get('target_regions', [])
                density_thresh = float(target_config.get('density_thresh', 1e-4))
                search_range = tuple(map(float, target_config.get('search_range', [-1000000, 1000000])))
                avoid_target_overlap = target_config.get('avoid_target_overlap', True)
                target_df = df[df['target'] == target] if 'target' in df.columns else df
                if target_df.empty:
                    logger.warning(f"No probes found for target {target}, skipping OTP filtering")
                    continue
                blocks = []
                for _, row in target_df.iterrows():
                    probe_id = row.get('probe_id', f"probe_{row.name}")
                    seq = row.get('target_region', '')
                    all_alns = []
                    for col in mapped_sites_cols:
                        mapped_sites = row[col]
                        try:
                            if isinstance(mapped_sites, str):
                                import ast
                                mapped_sites = ast.literal_eval(mapped_sites)
                            if isinstance(mapped_sites, list) and len(mapped_sites) > 0:
                                alns = [(ref_name, start_pos-1, end_pos) for ref_name, start_pos, end_pos in mapped_sites]
                                all_alns.extend(alns)
                        except Exception:
                            pass
                    if all_alns:
                        blocks.append((probe_id, seq, all_alns))
                if not blocks:
                    logger.warning(f"No alignment data found for target {target}, skipping OTP filtering")
                    continue
                counted = avoid_otp(blocks, target_regions, density_thresh, avoid_target_overlap, search_range)
                if counted:
                    filtered_probe_ids = []
                    on_target_counts = {}
                    off_target_counts = {}
                    on_target_rates = {}
                    for b, c in counted:
                        name, seq, alns = b
                        on_target = c[0]
                        off_target = c[1]
                        total = on_target + off_target
                        on_target_rate = on_target / total if total > 0 else 0
                        filtered_probe_ids.append(name)
                        on_target_counts[name] = on_target
                        off_target_counts[name] = off_target
                        on_target_rates[name] = on_target_rate
                    if 'probe_id' in df.columns:
                        target_mask = df['target'] == target if 'target' in df.columns else pd.Series([True] * len(df))
                        probe_mask = df['probe_id'].isin(filtered_probe_ids)
                        keep_mask = (~target_mask) | probe_mask
                        df = df[keep_mask].reset_index(drop=True)
                        for probe_id in filtered_probe_ids:
                            mask = df['probe_id'] == probe_id
                            df.loc[mask, 'on_target'] = on_target_counts[probe_id]
                            df.loc[mask, 'off_target'] = off_target_counts[probe_id]
                            df.loc[mask, 'target_ratio'] = on_target_rates[probe_id]
                else:
                    if 'target' in df.columns:
                        df = df[df['target'] != target].reset_index(drop=True)
        else:
            logger.error("No mapped_sites columns found in DataFrame, please check the input data")
    if "remove_overlap" in processes and processes['remove_overlap']:
        logger.info("Removing overlap")
        location_interval = processes['remove_overlap'].get('location_interval', 0)
        df = remove_overlap(df, config, location_interval)
    if "equal_space" in processes and processes['equal_space']:
        logger.info("Equalizing space")
        df = equal_space(df, processes['equal_space'])
    if 'sorts' in processes and processes['sorts']:
        logger.info("Sorting the table")
        sorts = processes['sorts']
        pos_fields = sorts.get('is_ascending', [])
        neg_fields = sorts.get('is_descending', [])
        sort_keys = pos_fields + neg_fields
        is_ascending = [True] * len(pos_fields) + [False] * len(neg_fields)
        df = sort_table(df, sort_keys, is_ascending)
    if 'summary' in processes and processes['summary']:
        logger.info("Summary configuration found - will be processed during report generation")
    return df
