"""
Summary statistics generation for probe data.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from uprobe.utils import get_logger

logger = get_logger(__name__)


def calculate_summary_stats(
    df: pd.DataFrame,
    column: str,
    stats_types: List[str]
) -> Dict[str, Any]:
    if column not in df.columns:
        logger.warning(f"Column '{column}' not found in DataFrame")
        return {}
    series = df[column].dropna()
    if len(series) == 0:
        logger.warning(f"No valid data found in column '{column}'")
        return {}
    stats = {}
    for stat_type in stats_types:
        try:
            if stat_type == 'count':
                stats['count'] = len(series)
            elif stat_type == 'mean':
                stats['mean'] = float(series.mean())
            elif stat_type == 'std':
                stats['std'] = float(series.std())
            elif stat_type == 'min':
                stats['min'] = float(series.min())
            elif stat_type == 'max':
                stats['max'] = float(series.max())
            elif stat_type == 'median':
                stats['median'] = float(series.median())
            elif stat_type == 'q25':
                stats['q25'] = float(series.quantile(0.25))
            elif stat_type == 'q75':
                stats['q75'] = float(series.quantile(0.75))
            elif stat_type == 'range':
                stats['range'] = float(series.max() - series.min())
            else:
                logger.warning(f"Unknown statistic type: {stat_type}")
        except Exception as e:
            logger.error(f"Error calculating {stat_type} for column {column}: {e}")
    
    return stats


def calculate_grouped_stats(
    df: pd.DataFrame,
    column: str,
    group_by: str,
    stats_types: List[str]
) -> Dict[str, Dict[str, Any]]:
    if column not in df.columns:
        logger.warning(f"Column '{column}' not found in DataFrame")
        return {}
    if group_by not in df.columns:
        logger.warning(f"Group by column '{group_by}' not found in DataFrame")
        return {}
    grouped_stats = {}
    for group_name, group_df in df.groupby(group_by):
        group_stats = calculate_summary_stats(group_df, column, stats_types)
        if group_stats:
            grouped_stats[str(group_name)] = group_stats
    return grouped_stats


def generate_summary_data(
    df: pd.DataFrame,
    summary_config: Dict[str, Any]
) -> Dict[str, Any]:
    logger.info(f"Generating summary statistics for DataFrame with shape: {df.shape}")
    target_col = None
    if 'target' in df.columns:
        target_col = 'target'
    elif 'gene' in df.columns:
        target_col = 'gene'
    summary_data = {
        'overall_stats': {},
        'attribute_stats': {},
        'grouped_stats': {},
        'probe_counts': {},
        'data_info': {
            'total_probes': len(df),
            'columns': list(df.columns),
            'targets': list(df[target_col].unique()) if target_col else []
        }
    }
    if target_col:
        target_counts = df[target_col].value_counts().to_dict()
        summary_data['probe_counts'] = {str(k): int(v) for k, v in target_counts.items()}
    attributes = summary_config.get('attributes', {})
    if isinstance(attributes, list):
        attributes = {attr: {} for attr in attributes}
    logger.info(f"Processing {len(attributes)} attributes: {list(attributes.keys())}")
    for attr_name, attr_config in attributes.items():
        if attr_name not in df.columns:
            logger.warning(f"Attribute '{attr_name}' not found in data columns: {list(df.columns)}")
            continue
        stats_types = attr_config.get('stats', ['count', 'mean', 'std', 'min', 'max'])     
        attr_stats = calculate_summary_stats(df, attr_name, stats_types)
        if attr_stats:
            summary_data['attribute_stats'][attr_name] = attr_stats
        if attr_config.get('group_by_target', True) and target_col:
            grouped_stats = calculate_grouped_stats(df, attr_name, target_col, stats_types)
            if grouped_stats:
                summary_data['grouped_stats'][attr_name] = grouped_stats
    visualization_data = {}
    for attr_name, attr_config in attributes.items():
        if attr_name not in df.columns:
            continue
        vis_types = attr_config.get('visualizations', [])
        if vis_types:
            attr_data = df[attr_name].dropna()
            if len(attr_data) > 0:
                visualization_data[attr_name] = {
                    'data': attr_data.tolist(),
                    'vis_types': vis_types
                }
    summary_data['visualization_data'] = visualization_data
    logger.info(f"Summary generated for {len(summary_data['attribute_stats'])} attributes")
    return summary_data


def process_summary(
    df: pd.DataFrame,
    summary_config: Dict[str, Any]
) -> pd.DataFrame:
    try:
        summary_data = generate_summary_data(df, summary_config)
        if hasattr(df, 'attrs'):
            df.attrs['summary_data'] = summary_data
        else:
            import tempfile
            import pickle
            import os
            temp_dir = tempfile.gettempdir()
            summary_file = os.path.join(temp_dir, 'uprobe_summary_data.pkl')
            with open(summary_file, 'wb') as f:
                pickle.dump(summary_data, f)
        logger.info("Summary processing completed")
    except Exception as e:
        logger.error(f"Error in summary processing: {e}")
    
    return df
