"""
Plot generation for probe analysis reports.
"""
import base64
import io
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False

from uprobe.utils import get_logger

logger = get_logger(__name__)

# Set plotting style
if PLOTTING_AVAILABLE:
    plt.style.use('default')
    sns.set_palette("husl")


def create_histogram(
    data: List[float],
    title: str,
    xlabel: str,
    ylabel: str = "Frequency",
    bins = 30,  # Can be int or 'auto'
    figsize: Tuple[int, int] = (6, 4),
    bar_width_ratio: float = 0.8
) -> str:
    """Create histogram plot and return as base64 string.
    
    Args:
        data: List of numeric values
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
        bins: Number of bins (int) or 'auto' for automatic calculation
        figsize: Figure size tuple
        bar_width_ratio: Width ratio of bars (0.0-1.0), controls bar spacing
        
    Returns:
        Base64 encoded plot image
    """
    if not PLOTTING_AVAILABLE:
        logger.warning("Matplotlib not available, skipping histogram generation")
        return ""
    
    fig, ax = plt.subplots(figsize=figsize)
    
    try:
        # Auto-adjust bins based on data size and range
        data_array = np.array(data)
        n_data = len(data_array)
        
        if bins == 'auto' or (isinstance(bins, int) and bins <= 0):
            # Use Sturges' rule combined with square root choice for optimal binning
            sturges_bins = int(np.log2(n_data)) + 1
            sqrt_bins = int(np.sqrt(n_data))
            
            # Choose the more conservative (smaller) value but ensure reasonable range
            suggested_bins = min(sturges_bins, sqrt_bins)
            bins = max(min(suggested_bins, 50), 10)  # Between 10 and 50 bins
        elif isinstance(bins, int):
            # Use provided bins but cap at reasonable limits
            bins = max(min(bins, 50), 5)  # Between 5 and 50 bins
        
        # Create histogram with controlled bar width
        n, bins_edges, patches = ax.hist(
            data, 
            bins=bins, 
            alpha=0.7, 
            color='skyblue', 
            edgecolor='black', 
            rwidth=bar_width_ratio,  # Use the configurable width ratio
            linewidth=0.5
        )
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.grid(True, alpha=0.3, axis='y')  # Only show horizontal grid lines
        
        # Add statistics text and lines
        mean_val = np.mean(data)
        median_val = np.median(data)
        std_val = np.std(data)
        
        # Add mean and median lines
        ax.axvline(mean_val, color='red', linestyle='--', alpha=0.8, 
                  linewidth=2, label=f'Mean: {mean_val:.2f}')
        ax.axvline(median_val, color='orange', linestyle=':', alpha=0.8, 
                  linewidth=2, label=f'Median: {median_val:.2f}')
        
        # Add statistics text box
        stats_text = f'N = {n_data}\nStd = {std_val:.2f}'
        ax.text(0.98, 0.98, stats_text, transform=ax.transAxes,
                verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8),
                fontsize=9)
        
        ax.legend(loc='upper right', bbox_to_anchor=(0.98, 0.85))
        
        plt.tight_layout()
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        plot_data = base64.b64encode(buffer.read()).decode()
        plt.close(fig)
        
        return plot_data
        
    except Exception as e:
        logger.error(f"Error creating histogram: {e}")
        plt.close(fig)
        return ""


def create_boxplot(
    data_dict: Dict[str, List[float]],
    title: str,
    xlabel: str,
    ylabel: str,
    figsize: Tuple[int, int] = (8, 4)
) -> str:
    """Create boxplot and return as base64 string.
    
    Args:
        data_dict: Dictionary with group names as keys and data lists as values
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
        figsize: Figure size tuple
        
    Returns:
        Base64 encoded plot image
    """
    if not PLOTTING_AVAILABLE:
        logger.warning("Matplotlib not available, skipping boxplot generation")
        return ""
    
    fig, ax = plt.subplots(figsize=figsize)
    
    try:
        # Prepare data for boxplot
        data_list = []
        labels = []
        for group_name, values in data_dict.items():
            if values:  # Only add non-empty groups
                data_list.append(values)
                labels.append(group_name)
        
        if not data_list:
            logger.warning("No data available for boxplot")
            plt.close(fig)
            return ""
        
        bp = ax.boxplot(data_list, labels=labels, patch_artist=True)
        
        # Customize colors
        colors = plt.cm.Set3(np.linspace(0, 1, len(data_list)))
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Rotate labels if too many
        if len(labels) > 5:
            plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        plot_data = base64.b64encode(buffer.read()).decode()
        plt.close(fig)
        
        return plot_data
        
    except Exception as e:
        logger.error(f"Error creating boxplot: {e}")
        plt.close(fig)
        return ""


def create_scatter_plot(
    x_data: List[float],
    y_data: List[float],
    title: str,
    xlabel: str,
    ylabel: str,
    figsize: Tuple[int, int] = (6, 4)
) -> str:
    """Create scatter plot and return as base64 string.
    
    Args:
        x_data: X-axis data
        y_data: Y-axis data
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
        figsize: Figure size tuple
        
    Returns:
        Base64 encoded plot image
    """
    if not PLOTTING_AVAILABLE:
        logger.warning("Matplotlib not available, skipping scatter plot generation")
        return ""
    
    fig, ax = plt.subplots(figsize=figsize)
    
    try:
        ax.scatter(x_data, y_data, alpha=0.6, c='steelblue', s=50)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Add correlation coefficient if both datasets have enough points
        if len(x_data) > 1 and len(y_data) > 1:
            corr = np.corrcoef(x_data, y_data)[0, 1]
            if not np.isnan(corr):
                ax.text(0.05, 0.95, f'Correlation: {corr:.3f}', 
                       transform=ax.transAxes, fontsize=10,
                       bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        plot_data = base64.b64encode(buffer.read()).decode()
        plt.close(fig)
        
        return plot_data
        
    except Exception as e:
        logger.error(f"Error creating scatter plot: {e}")
        plt.close(fig)
        return ""


def create_bar_chart(
    data_dict: Dict[str, float],
    title: str,
    xlabel: str,
    ylabel: str,
    figsize: Tuple[int, int] = (8, 4)
) -> str:
    """Create bar chart and return as base64 string.
    
    Args:
        data_dict: Dictionary with categories as keys and values as values
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
        figsize: Figure size tuple
        
    Returns:
        Base64 encoded plot image
    """
    if not PLOTTING_AVAILABLE:
        logger.warning("Matplotlib not available, skipping bar chart generation")
        return ""
    
    fig, ax = plt.subplots(figsize=figsize)
    
    try:
        categories = list(data_dict.keys())
        values = list(data_dict.values())
        
        bars = ax.bar(categories, values, alpha=0.7, color='lightcoral')
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{value:.0f}' if isinstance(value, (int, float)) else str(value),
                   ha='center', va='bottom', fontsize=10)
        
        # Rotate labels if too many
        if len(categories) > 5:
            plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        plot_data = base64.b64encode(buffer.read()).decode()
        plt.close(fig)
        
        return plot_data
        
    except Exception as e:
        logger.error(f"Error creating bar chart: {e}")
        plt.close(fig)
        return ""


def generate_summary_plots(
    df: pd.DataFrame,
    summary_data: Dict[str, Any],
    visualization_config: Dict[str, Any]
) -> Dict[str, str]:
    """Generate all summary plots based on configuration.
    
    Args:
        df: DataFrame containing probe data
        summary_data: Summary statistics data
        visualization_config: Visualization configuration
        
    Returns:
        Dictionary with plot names as keys and base64 plot data as values
    """
    if not PLOTTING_AVAILABLE:
        logger.warning("Matplotlib not available, skipping plot generation")
        return {}
    
    plots = {}
    
    try:
        # Probe count bar chart
        if summary_data.get('probe_counts'):
            probe_count_plot = create_bar_chart(
                summary_data['probe_counts'],
                "Probe Count by Target",
                "Target",
                "Number of Probes"
            )
            if probe_count_plot:
                plots['probe_counts'] = probe_count_plot
        
        # Attribute distribution plots
        visualization_data = summary_data.get('visualization_data', {})
        for attr_name, attr_data in visualization_data.items():
            vis_types = attr_data.get('vis_types', [])
            data = attr_data.get('data', [])
            
            if not data:
                continue
            
            # Histogram
            if 'histogram' in vis_types:
                hist_plot = create_histogram(
                    data,
                    f"{attr_name} Distribution",
                    attr_name.replace('_', ' ').title(),
                    "Frequency",
                    bins='auto',  # Let the function auto-calculate bins
                    bar_width_ratio=0.8  # Controlled bar width for better appearance
                )
                if hist_plot:
                    plots[f'{attr_name}_histogram'] = hist_plot
            
            # Boxplot by target
            target_col = 'target' if 'target' in df.columns else ('gene' if 'gene' in df.columns else None)
            if 'boxplot' in vis_types and target_col:
                grouped_data = {}
                for target in df[target_col].unique():
                    target_data = df[df[target_col] == target][attr_name].dropna().tolist()
                    if target_data:
                        grouped_data[str(target)] = target_data
                
                if grouped_data:
                    box_plot = create_boxplot(
                        grouped_data,
                        f"{attr_name} by Target",
                        "Target",
                        attr_name.replace('_', ' ').title()
                    )
                    if box_plot:
                        plots[f'{attr_name}_boxplot'] = box_plot
        
        # Correlation scatter plots
        numeric_attrs = []
        for attr_name in summary_data.get('attribute_stats', {}):
            if attr_name in df.columns and df[attr_name].dtype in ['float64', 'int64']:
                numeric_attrs.append(attr_name)
        
        # Create scatter plots for interesting attribute pairs
        correlation_pairs = visualization_config.get('correlations', [])
        for pair in correlation_pairs:
            if len(pair) == 2 and pair[0] in df.columns and pair[1] in df.columns:
                x_data = df[pair[0]].dropna().tolist()
                y_data = df[pair[1]].dropna().tolist()
                
                # Ensure same length
                min_len = min(len(x_data), len(y_data))
                if min_len > 0:
                    scatter_plot = create_scatter_plot(
                        x_data[:min_len],
                        y_data[:min_len],
                        f"{pair[0]} vs {pair[1]}",
                        pair[0].replace('_', ' ').title(),
                        pair[1].replace('_', ' ').title()
                    )
                    if scatter_plot:
                        plots[f'{pair[0]}_vs_{pair[1]}_scatter'] = scatter_plot
        
        logger.info(f"Generated {len(plots)} summary plots")
        
    except Exception as e:
        logger.error(f"Error generating summary plots: {e}")
    
    return plots


def generate_plot_report(
    df: pd.DataFrame,
    protocol: Dict[str, Any],
    output_dir: Path,
    report_suffix: str = "",
    save_files: bool = False,
    return_base64: bool = True
) -> Dict[str, Any]:
    if not PLOTTING_AVAILABLE:
        logger.warning("Matplotlib not available, skipping plot generation")
        return {"plot_data": {}, "plot_files": []}
    
    logger.info("Generating plot report...")
    
    # Get summary data
    summary_data = getattr(df, 'attrs', {}).get('summary_data', {})
    if not summary_data:
        # Try to load from temporary file (fallback)
        try:
            import tempfile
            import pickle
            import os
            
            temp_dir = tempfile.gettempdir()
            summary_file = os.path.join(temp_dir, 'uprobe_summary_data.pkl')
            if os.path.exists(summary_file):
                with open(summary_file, 'rb') as f:
                    summary_data = pickle.load(f)
                logger.info("Loaded summary data from temporary file")
        except Exception as e:
            logger.warning(f"Could not load summary data: {e}")
            summary_data = {}
    
    # Get visualization configuration
    visualization_config = protocol.get('post_process', {}).get('summary', {}).get('visualizations', {})
    
    plot_data = {}
    plot_files = []
    
    if summary_data:
        plots = generate_summary_plots(df, summary_data, visualization_config)
        
        for plot_name, plot_base64 in plots.items():
            if return_base64:
                plot_data[plot_name] = plot_base64
            
            if save_files and plot_base64:
                # Save plot to file
                plot_file = output_dir / f"{plot_name}{report_suffix}.png"
                try:
                    plot_binary = base64.b64decode(plot_base64)
                    with open(plot_file, 'wb') as f:
                        f.write(plot_binary)
                    plot_files.append(plot_file)
                    logger.info(f"Saved plot: {plot_file}")
                except Exception as e:
                    logger.error(f"Error saving plot {plot_name}: {e}")
    
    return {
        "plot_data": plot_data,
        "plot_files": plot_files,
        "summary_data": summary_data
    }
