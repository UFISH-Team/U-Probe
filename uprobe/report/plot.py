"""
Plot generation for probe analysis reports.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

try:
    import plotly.express as px
    import plotly.graph_objects as go
    import plotly.io as pio
    pio.templates.default = "plotly_white"
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False

from uprobe.utils import get_logger

logger = get_logger(__name__)

def _get_color_scheme(targets: List[str]) -> Dict[str, str]:
    """Generate a consistent color scheme for targets."""
    # Use a professional color palette
    colors = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
        '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5',
        '#c49c94', '#f7b6d3', '#c7c7c7', '#dbdb8d', '#9edae5'
    ]
    
    color_map = {}
    for i, target in enumerate(sorted(targets)):
        color_map[target] = colors[i % len(colors)]
    
    return color_map

def create_histogram(
    data: pd.DataFrame,
    title: str,
    xlabel: str,
    ylabel: str = "Frequency",
    bins: int = 30,
    figsize: Tuple[int, int] = (600, 400),
    color_map: Optional[Dict[str, str]] = None,
    single_color: Optional[str] = None
) -> str:
    """Create histogram plot and return as HTML string."""
    if not PLOTTING_AVAILABLE:
        logger.warning("Plotly not available, skipping histogram generation")
        return ""
    
    try:
        use_group_color = 'group' in data.columns and data['group'].nunique() > 1
        
        if use_group_color:
            fig = px.histogram(
                data,
                x='value',
                color='group',
                color_discrete_map=color_map,
                barmode='overlay',
                nbins=bins,
                labels={'value': xlabel, 'group': 'Target'},
                title=title,
                template="plotly_white",
                opacity=0.7
            )
        else:
            fig = px.histogram(
                data,
                x='value',
                nbins=bins,
                labels={'value': xlabel},
                title=title,
                template="plotly_white",
                opacity=0.7
            )
            if single_color:
                fig.update_traces(marker_color=single_color)

        right_margin = 120 if use_group_color else 60
        
        fig.update_layout(
            width=figsize[0],
            height=figsize[1],
            title_font_size=16,
            xaxis_title_font_size=14,
            yaxis_title_font_size=14,
            margin=dict(l=60, r=right_margin, t=60, b=60),
            showlegend=use_group_color
        )
        
        if use_group_color:
            fig.update_layout(
                legend_title_text='Target',
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=1,
                    xanchor="left",
                    x=1.02
                )
            )
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    except Exception as e:
        logger.error(f"Error creating histogram: {e}")
        return ""


def create_boxplot(
    data_dict: Dict[str, List[float]],
    title: str,
    xlabel: str,
    ylabel: str,
    figsize: Tuple[int, int] = (600, 400), # Increased default height
    color_map: Optional[Dict[str, str]] = None
) -> str:
    """Create boxplot and return as HTML string."""
    if not PLOTTING_AVAILABLE:
        logger.warning("Plotly not available, skipping boxplot generation")
        return ""
    
    try:
        df_list = []
        for group, values in data_dict.items():
            if values:
                df_list.append(pd.DataFrame({'group': group, 'value': values}))
        
        if not df_list:
            logger.warning("No data for boxplot")
            return ""
            
        df = pd.concat(df_list)
        
        fig = px.box(
            df,
            x='group',
            y='value',
            color='group',
            color_discrete_map=color_map,
            title=title,
            labels={'group': xlabel, 'value': ylabel},
            template="plotly_white"
        )
        
        # Rotate x-axis labels if there are many targets
        num_targets = len(data_dict)
        if num_targets > 10:
            fig.update_xaxes(tickangle=45)

        fig.update_layout(
            width=figsize[0],
            height=figsize[1],
            title_font_size=16,
            xaxis_title_font_size=14,
            yaxis_title_font_size=14,
            margin=dict(l=60, r=60, t=60, b=100), # Increased margins for rotated labels
            showlegend=False
        )
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    except Exception as e:
        logger.error(f"Error creating boxplot: {e}")
        return ""

def create_scatter_plot(
    data: pd.DataFrame,
    title: str,
    xlabel: str,
    ylabel: str,
    figsize: Tuple[int, int] = (600, 400),
    color_map: Optional[Dict[str, str]] = None,
    single_color: Optional[str] = None
) -> str:
    """Create scatter plot and return as HTML string."""
    if not PLOTTING_AVAILABLE:
        logger.warning("Plotly not available, skipping scatter plot generation")
        return ""
    
    try:
        use_group_color = 'group' in data.columns and data['group'].nunique() > 1
        
        if use_group_color:
            fig = px.scatter(
                data,
                x='x',
                y='y',
                color='group',
                color_discrete_map=color_map,
                hover_data=['probe_id'],
                title=title,
                labels={'x': xlabel, 'y': ylabel, 'group': 'Target'},
                template="plotly_white"
            )
        else:
            fig = px.scatter(
                data,
                x='x',
                y='y',
                hover_data=['probe_id'],
                title=title,
                labels={'x': xlabel, 'y': ylabel},
                template="plotly_white"
            )
            if single_color:
                fig.update_traces(marker_color=single_color)
        
        right_margin = 120 if use_group_color else 60
        
        fig.update_layout(
            width=figsize[0],
            height=figsize[1],
            title_font_size=16,
            xaxis_title_font_size=14,
            yaxis_title_font_size=14,
            margin=dict(l=60, r=right_margin, t=60, b=60),
            showlegend=use_group_color
        )
        
        if use_group_color:
            fig.update_layout(
                legend_title_text='Target',
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=1,
                    xanchor="left",
                    x=1.02
                )
            )
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    except Exception as e:
        logger.error(f"Error creating scatter plot: {e}")
        return ""


def create_bar_chart(
    data: pd.DataFrame,
    title: str,
    xlabel: str,
    ylabel: str,
    figsize: Tuple[int, int] = (600, 400), # Increased default height
    color_map: Optional[Dict[str, str]] = None,
    single_color: Optional[str] = None
) -> str:
    """Create bar chart and return as HTML string."""
    if not PLOTTING_AVAILABLE:
        logger.warning("Plotly not available, skipping bar chart generation")
        return ""
    
    try:
        # Determine if we should use group coloring or single color
        use_group_color = 'group' in data.columns and data['group'].nunique() > 1
        
        if use_group_color:
            fig = px.bar(
                data,
                x='category',
                y='value',
                color='group',
                color_discrete_map=color_map,
                barmode='group',
                title=title,
                labels={'category': xlabel, 'value': ylabel, 'group': 'Target'},
                template="plotly_white"
            )
        else:
            # Single color bar chart
            fig = px.bar(
                data,
                x='category',
                y='value',
                title=title,
                labels={'category': xlabel, 'value': ylabel},
                template="plotly_white"
            )
            # Apply single color if provided
            if single_color:
                fig.update_traces(marker_color=single_color)
        
        # Rotate x-axis labels if there are many categories
        num_categories = data['category'].nunique()
        bottom_margin = 100
        if num_categories > 10:
            fig.update_xaxes(tickangle=45)
            bottom_margin = 120  # More space for rotated labels
        elif num_categories > 5:
            bottom_margin = 110

        # Adjust right margin based on whether we have a legend
        right_margin = 120 if use_group_color else 60

        fig.update_layout(
            width=figsize[0],
            height=figsize[1],
            title_font_size=16,
            xaxis_title_font_size=14,
            yaxis_title_font_size=14,
            margin=dict(l=60, r=right_margin, t=60, b=bottom_margin),
            showlegend=use_group_color
        )
        
        if use_group_color:
            fig.update_layout(
                legend_title_text='Target',
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=1,
                    xanchor="left",
                    x=1.02
                )
            )
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    except Exception as e:
        logger.error(f"Error creating bar chart: {e}")
        return ""

def _get_plot_config_for_attribute(attribute_name: str) -> Optional[Dict]:
    """Get plot type and parameters based on attribute name."""
    name_lower = attribute_name.lower()
    
    if 'tm' in name_lower or 'temperature' in name_lower:
        return {
            "plot_type": "boxplot",
            "title": f"{attribute_name}",
            "ylabel": "Tm (°C)"
        }
    if 'gc' in name_lower or 'gc_content' in name_lower:
        return {
            "plot_type": "histogram",
            "title": f"{attribute_name}",
            "xlabel": "GC Content (%)"
        }
    if 'kmer' in name_lower:
        return {
            "plot_type": "boxplot",
            "title": f"{attribute_name}",
            "xlabel": "K-mer Count"
        }
    if 'fold' in name_lower:
        return {
            "plot_type": "histogram",
            "title": f"{attribute_name}",
            "xlabel": "Folding Score"
        }
    if 'selfmatch' in name_lower:
        return {
            "plot_type": "bar",
            "title": f"{attribute_name}",
            "xlabel": "Self Match Score"
        }
    if 'mappedsites' in name_lower:
        return {
            "plot_type": "scatter",
            "title": f"{attribute_name}",
            "xlabel": "Mapped Sites"
        }
    if 'mappedgenes' in name_lower:
        return {
            "plot_type": "scatter",
            "title": f"{attribute_name}",
            "xlabel": "Mapped genes"
        }
    
    return None


def generate_plot_report(
    df: pd.DataFrame,
    protocol: Dict[str, Any],
    output_dir: Path,
    report_suffix: str = "",
    save_files: bool = False,
    return_base64: bool = True # This parameter is kept for compatibility but output is HTML string
) -> Dict[str, Any]:
    if not PLOTTING_AVAILABLE:
        logger.warning("Plotly not available, skipping plot generation")
        return {"plot_data": {}, "plot_files": []}
    
    logger.info("Generating plot report...")
    
    summary_config = protocol.get('summary', {})
    attributes_to_plot = summary_config.get('attributes', [])

    if isinstance(attributes_to_plot, dict):
        attributes_to_plot = list(attributes_to_plot.keys())

    plot_data = {}
    plot_files = []
    
    target_col = 'target' if 'target' in df.columns else ('gene' if 'gene' in df.columns else None)
    
    # Create a consistent color map for targets
    color_map = None
    if target_col:
        unique_targets = sorted(df[target_col].unique())
        color_map = _get_color_scheme(unique_targets)

    for attr_name in attributes_to_plot:
        if attr_name not in df.columns:
            logger.warning(f"Attribute '{attr_name}' for plotting not found in data.")
            continue
        
        plot_config = _get_plot_config_for_attribute(attr_name)
        if not plot_config:
            logger.info(f"No standard plot configuration for attribute '{attr_name}', skipping.")
            continue

        plot_html = ""
        plot_type = plot_config['plot_type']
        
        try:
            # For histograms, bar charts, and scatter plots, create a separate plot for each target if multiple targets exist.
            # For boxplots, group them together for comparison.
            
            is_multi_target_individual_plot = plot_type in ['histogram', 'bar', 'scatter']
            
            if is_multi_target_individual_plot and target_col and df[target_col].nunique() > 1:
                # --- INDIVIDUAL PLOTS FOR MULTIPLE TARGETS ---
                for target in df[target_col].unique():
                    target_df = df[df[target_col] == target]
                    plot_title = f"{plot_config['title']} ({target})"
                    plot_name_suffix = ""

                    if plot_type == 'histogram':
                        data = target_df[attr_name].dropna()
                        if not data.empty:
                            target_color = color_map.get(target) if color_map else None
                            plot_html = create_histogram(
                                data=data.to_frame(name='value'),
                                title=plot_title,
                                xlabel=plot_config['xlabel'],
                                color_map=None,
                                single_color=target_color
                            )
                            plot_name_suffix = "histogram"
                    
                    elif plot_type == 'bar':
                        data = target_df[attr_name].dropna()
                        if not data.empty:
                            data_dict = data.value_counts().to_dict()
                            # For single target plots, use the target's color
                            bar_data = pd.DataFrame(list(data_dict.items()), columns=['category', 'value'])
                            target_color = color_map.get(target) if color_map else None
                            plot_html = create_bar_chart(
                                data=bar_data,
                                title=plot_title,
                                xlabel=plot_config.get('xlabel', attr_name),
                                ylabel="Count",
                                color_map=None,
                                single_color=target_color
                            )
                            plot_name_suffix = "barchart"

                    elif plot_type == 'scatter':
                        if 'probe_id' in target_df.columns:
                            y_data = target_df[attr_name].dropna()
                            if not y_data.empty:
                                target_color = color_map.get(target) if color_map else None
                                plot_html = create_scatter_plot(
                                    data=pd.DataFrame({
                                        'x': y_data.index,
                                        'y': y_data,
                                        'probe_id': target_df.loc[y_data.index, 'probe_id']
                                    }),
                                    title=plot_title,
                                    xlabel="Probe Index",
                                    ylabel=plot_config.get('xlabel', attr_name),
                                    color_map=None,
                                    single_color=target_color
                                )
                                plot_name_suffix = "scatter"
                    
                    if plot_html:
                        plot_name = f'{attr_name}_{target}_{plot_name_suffix}'
                        plot_data[plot_name] = plot_html
                        plot_html = "" # Reset for next loop iteration
            
            else:
                # --- GROUPED PLOTS OR SINGLE TARGET PLOTS ---
                if plot_type == 'histogram':
                    data = df[attr_name].dropna()
                    if not data.empty:
                        plot_html = create_histogram(
                            data=data.to_frame(name='value'),
                            title=plot_config['title'],
                            xlabel=plot_config['xlabel'],
                            color_map=color_map
                        )
                        if plot_html:
                            plot_data[f'{attr_name}_histogram'] = plot_html
                
                elif plot_type == 'boxplot':
                    if target_col:
                        grouped_data = {
                            str(target): df[df[target_col] == target][attr_name].dropna().tolist()
                            for target in df[target_col].unique()
                        }
                        grouped_data = {k: v for k, v in grouped_data.items() if v}
                        
                        if grouped_data:
                            plot_html = create_boxplot(
                                data_dict=grouped_data,
                                title=plot_config['title'],
                                xlabel='Target',
                                ylabel=plot_config.get('ylabel', attr_name),
                                color_map=color_map
                            )
                            if plot_html:
                                plot_data[f'{attr_name}_boxplot'] = plot_html
                
                elif plot_type == 'bar':
                    data = df[attr_name].dropna()
                    if not data.empty:
                        data_dict = data.value_counts().to_dict()
                        plot_html = create_bar_chart(
                            data=pd.DataFrame(list(data_dict.items()), columns=['category', 'value']),
                            title=plot_config['title'],
                            xlabel=plot_config.get('xlabel', attr_name),
                            ylabel="Count",
                            color_map=color_map
                        )
                        if plot_html:
                            plot_data[f'{attr_name}_barchart'] = plot_html
                
                elif plot_type == 'scatter':
                    if 'probe_id' in df.columns:
                        y_data = df[attr_name].dropna()
                        if not y_data.empty:
                            plot_html = create_scatter_plot(
                                data=pd.DataFrame({
                                    'x': y_data.index,
                                    'y': y_data,
                                    'probe_id': df.loc[y_data.index, 'probe_id']
                                }),
                                title=plot_config['title'],
                                xlabel="Probe Index",
                                ylabel=plot_config.get('xlabel', attr_name),
                                color_map=color_map
                            )
                            if plot_html:
                                plot_data[f'{attr_name}_scatter'] = plot_html

            if plot_html and save_files:
                plot_name = f'{attr_name}_{plot_type}' # Generic name
                plot_file = output_dir / f"{plot_name}{report_suffix}.html"
                try:
                    with open(plot_file, 'w', encoding='utf-8') as f:
                        f.write(plot_html)
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
