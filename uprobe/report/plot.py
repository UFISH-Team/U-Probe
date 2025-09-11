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


def _get_plot_config_for_attribute(attribute_name: str) -> Optional[Dict]:
    """Get plot type and parameters based on attribute name."""
    name_lower = attribute_name.lower()
    
    if 'tm' in name_lower or 'temperature' in name_lower:
        return {
            "plot_type": "boxplot",
            "title": f"Distribution of {attribute_name}",
            "ylabel": "Temperature (°C)"
        }
    if 'gc' in name_lower or 'gc_content' in name_lower:
        return {
            "plot_type": "histogram",
            "title": f"Distribution of {attribute_name}",
            "xlabel": "GC Content (%)"
        }
    if 'kmer' in name_lower:
        return {
            "plot_type": "boxplot",
            "title": f"Distribution of {attribute_name}",
            "xlabel": "K-mer Count"
        }
    if 'fold' in name_lower:
        return {
            "plot_type": "histogram",
            "title": f"Distribution of {attribute_name}",
            "xlabel": "Folding Score"
        }
    if 'selfmatch' in name_lower:
        return {
            "plot_type": "bar",
            "title": f"Distribution of {attribute_name}",
            "xlabel": "Self Match Score"
        }
    if 'mappedsites' in name_lower:
        return {
            "plot_type": "scatter",
            "title": f"Distribution of {attribute_name}",
            "xlabel": "Mapped Sites"
        }
    if 'mappedgenes' in name_lower:
        return {
            "plot_type": "scatter",
            "title": f"Distribution of {attribute_name}",
            "xlabel": "Mapped Genes"
        }
    
    return None


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
    
    summary_config = protocol.get('summary', {})
    attributes_to_plot = summary_config.get('attributes', [])

    if isinstance(attributes_to_plot, dict):
        attributes_to_plot = list(attributes_to_plot.keys())

    plot_data = {}
    plot_files = []
    
    target_col = 'target' if 'target' in df.columns else ('gene' if 'gene' in df.columns else None)
    
    for attr_name in attributes_to_plot:
        if attr_name not in df.columns:
            logger.warning(f"Attribute '{attr_name}' for plotting not found in data.")
            continue
        
        plot_config = _get_plot_config_for_attribute(attr_name)
        if not plot_config:
            logger.info(f"No standard plot configuration for attribute '{attr_name}', skipping.")
            continue

        plot_base64 = ""
        plot_type = plot_config['plot_type']
        
        try:
            if plot_type == 'histogram':
                if target_col and df[target_col].nunique() > 1:
                    for target in df[target_col].unique():
                        target_data = df[df[target_col] == target][attr_name].dropna()
                        if target_data.empty:
                            continue
                        plot_base64 = create_histogram(
                            data=target_data.tolist(),
                            title=f"{plot_config['title']} ({target})",
                            xlabel=plot_config['xlabel']
                        )
                        if plot_base64:
                            plot_name = f'{attr_name}_{target}_histogram'
                            if return_base64:
                                plot_data[plot_name] = plot_base64
                            # File saving logic can be added here if needed
                else:
                    plot_base64 = create_histogram(
                        data=df[attr_name].dropna().tolist(),
                        title=plot_config['title'],
                        xlabel=plot_config['xlabel']
                    )
                    if plot_base64:
                        plot_name = f'{attr_name}_histogram'
                        if return_base64:
                            plot_data[plot_name] = plot_base64
                        # File saving logic can be added here if needed
            elif plot_type == 'boxplot':
                if target_col:
                    grouped_data = {
                        str(target): df[df[target_col] == target][attr_name].dropna().tolist()
                        for target in df[target_col].unique()
                    }
                    grouped_data = {k: v for k, v in grouped_data.items() if v}
                    
                    if grouped_data:
                        plot_base64 = create_boxplot(
                            data_dict=grouped_data,
                            title=plot_config['title'],
                            xlabel='Target',
                            ylabel=plot_config['ylabel']
                        )
                    if plot_base64:
                        plot_name = f'{attr_name}_boxplot'
                        if return_base64:
                            plot_data[plot_name] = plot_base64
            
            elif plot_type == 'bar':
                data = df[attr_name].dropna()
                if not data.empty:
                    data_dict = data.value_counts().to_dict()
                    plot_base64 = create_bar_chart(
                        data_dict=data_dict,
                        title=plot_config['title'],
                        xlabel=plot_config.get('xlabel', attr_name),
                        ylabel="Count"
                    )
                    if plot_base64:
                        plot_name = f'{attr_name}_barchart'
                        if return_base64:
                            plot_data[plot_name] = plot_base64

            elif plot_type == 'scatter':
                y_data = df[attr_name].dropna()
                if not y_data.empty:
                    x_data = y_data.index.tolist()
                    plot_base64 = create_scatter_plot(
                        x_data=x_data,
                        y_data=y_data.tolist(),
                        title=plot_config['title'],
                        xlabel="Probe Index",
                        ylabel=plot_config.get('xlabel', attr_name)
                    )
                    if plot_base64:
                        plot_name = f'{attr_name}_scatter'
                        if return_base64:
                            plot_data[plot_name] = plot_base64
            
            # This part for saving files is now mostly handled inside the loops for histograms
            # Boxplot saving can be done here.
            if plot_base64 and save_files:
                plot_name = f'{attr_name}_{plot_type}' # Generic name, might need adjustment
                plot_file = output_dir / f"{plot_name}{report_suffix}.png"
                try:
                    plot_binary = base64.b64decode(plot_base64)
                    with open(plot_file, 'wb') as f:
                        f.write(plot_binary)
                    plot_files.append(plot_file)
                    logger.info(f"Saved plot: {plot_file}")
                except Exception as e:
                    logger.error(f"Error saving plot {plot_name}: {e}")

        except Exception as e:
            logger.error(f"Failed to generate plot for '{attr_name}': {e}")
            
    return {
        "plot_data": plot_data,
        "plot_files": plot_files
    }
