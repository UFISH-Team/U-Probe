import pandas as pd
import numpy as np
from typing import Dict, Any
from uprobe.utils import get_logger

log = get_logger(__name__)

def equal_space(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    select probes from each target to ensure the number of probes is equal to the desired number
    
    Args:
        df: DataFrame with probe data
        config: equal_space configuration, format:
               {
                   "target1": {"number_desired": 1000},
                   "target2": {"number_desired": 2000}
               }
               or global configuration:
               {"number_desired": 1000}
    """
    if df.empty:
        return df
    if 'target' not in df.columns:
        log.warning("DataFrame does not have 'target' column, skip equal_space processing")
        return df
    result_dfs = []
    targets = df['target'].unique()
    log.info(f"equal_space processing started, there are {len(targets)} targets")
    for target in targets:
        target_df = df[df['target'] == target].copy()
        current_count = len(target_df)
        if target in config and 'number_desired' in config[target]:
            number_desired = config[target]['number_desired']
        elif 'number_desired' in config:
            number_desired = config['number_desired']
        else:
            log.warning(f"target {target} does not have number_desired, skip processing")
            result_dfs.append(target_df)
            continue
        
        if current_count <= number_desired:
            log.info(f"target {target}: keeping all {current_count} probes (desired: {number_desired})")
            result_dfs.append(target_df)
        else:
            # if there is a sub_region column, sort by location and select evenly
            if 'sub_region' in target_df.columns:
                # extract the start position of sub_region and sort
                target_df['_start_pos'] = target_df['sub_region'].str.split('-').str[0].astype(int)
                target_df = target_df.sort_values('_start_pos')
                target_df = target_df.drop('_start_pos', axis=1)
            indices = np.linspace(0, current_count - 1, number_desired, dtype=int)
            selected_df = target_df.iloc[indices].copy()
            log.info(f"target {target}: selected {len(selected_df)} probes from {current_count} (desired: {number_desired})")
            result_dfs.append(selected_df)
    if result_dfs:
        final_df = pd.concat(result_dfs, ignore_index=True)
        log.info(f"equal_space processing completed, final number of probes: {len(final_df)}")
        return final_df
    else:
        return df
