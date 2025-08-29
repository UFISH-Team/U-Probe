"""
Generate visualization plots for probe results.
"""
import pandas as pd
import base64
import io
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from ..utils import get_logger

logger = get_logger(__name__)

# Try to import plotting libraries
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    import numpy as np
    # Set default matplotlib and seaborn style
    plt.style.use('default')
    sns.set_palette("husl")
    PLOTTING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Plotting libraries not available: {e}")
    logger.warning("Install matplotlib and seaborn for plot generation: pip install matplotlib seaborn")
    PLOTTING_AVAILABLE = False

def plot_to_base64() -> str:
    """Convert current matplotlib plot to base64 string for HTML embedding."""
    try:
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        img_data = buffer.getvalue()
        buffer.close()
        b64_string = base64.b64encode(img_data).decode('utf-8')
        return f"data:image/png;base64,{b64_string}"
    except Exception as e:
        logger.error(f"Failed to convert plot to base64: {e}")
        return ""

def save_plot_conditionally(output_path: Optional[Path] = None, return_base64: bool = False) -> Optional[str]:
    """Save plot to file and/or return as base64 string."""
    base64_data = None
    if return_base64:
        base64_data = plot_to_base64()
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        logger.info(f"Plot saved to {output_path}")
    plt.close()
    return base64_data

def detect_protocol_type(df: pd.DataFrame, protocol: Dict) -> str:
    """Detect protocol type based on data columns and configuration."""
    extract_source = protocol.get('extracts', {}).get('target_region', {}).get('source', '')
    if extract_source == 'exon':
        return 'RNA'
    elif extract_source == 'genome':
        return 'DNA'
    
    # Check column names  
    rna_indicators = ['transcript', 'exon_rank', 'transcript_name', 'transcript_names']
    dna_indicators = ['kmerCount', 'NC_']
    
    columns = df.columns.tolist()
    
    if any(indicator in ' '.join(columns) for indicator in rna_indicators):
        return 'RNA'
    elif any(indicator in ' '.join(columns) for indicator in dna_indicators):
        return 'DNA'
    
    return 'Unknown'

def plot_genomic_coverage(df: pd.DataFrame, target_regions: List[str], output_path: Optional[Path] = None, return_base64: bool = False) -> Optional[str]:
    """Plot genomic coverage for DNA probes."""
    
    fig, axes = plt.subplots(len(target_regions), 1, figsize=(12, 4 * len(target_regions)))
    if len(target_regions) == 1:
        axes = [axes]
    
    for idx, target_region in enumerate(target_regions):
        target_df = df[df.get('target', df.get('gene', '')) == target_region].copy()
        
        if target_df.empty:
            continue
            
        # Extract chromosomal positions
        if 'start' in target_df.columns and 'end' in target_df.columns:
            positions = target_df[['start', 'end']].copy()
            positions['center'] = (positions['start'] + positions['end']) / 2
            positions['length'] = positions['end'] - positions['start']
            
            # Create coverage histogram
            if not positions.empty:
                axes[idx].hist(positions['center'], bins=50, alpha=0.7, color='steelblue')
                axes[idx].set_xlabel('Genomic Position')
                axes[idx].set_ylabel('Probe Density')
                axes[idx].set_title(f'Probe Coverage Distribution - {target_region}')
                axes[idx].grid(True, alpha=0.3)
                
                # Add statistics
                mean_pos = positions['center'].mean()
                axes[idx].axvline(mean_pos, color='red', linestyle='--', 
                                label=f'Mean Position: {mean_pos:.0f}')
                axes[idx].legend()
    
    plt.tight_layout()
    return save_plot_conditionally(output_path, return_base64)

def plot_transcript_coverage(df: pd.DataFrame, output_path: Optional[Path] = None, return_base64: bool = False) -> Optional[str]:
    """Plot transcript coverage and probe distribution for RNA probes."""
    
    # Prepare transcript data
    if 'transcript_name' in df.columns:
        transcript_col = 'transcript_name'
    elif 'transcript_names' in df.columns:
        transcript_col = 'transcript_names'
    elif 'transcript' in df.columns:
        transcript_col = 'transcript'
    else:
        transcript_col = None
    
    if not transcript_col:
        logger.warning("No transcript information found for RNA probe visualization")
        return None
    
    # Handle list-type transcript names
    df_plot = df.copy()
    df_plot[transcript_col] = df_plot[transcript_col].apply(
        lambda x: ', '.join(x) if isinstance(x, list) else str(x)
    )
    
    # Count probes per transcript
    transcript_counts = df_plot[transcript_col].value_counts()
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. Transcript probe count distribution
    axes[0, 0].bar(range(len(transcript_counts)), transcript_counts.values, 
                   color='lightcoral', alpha=0.7)
    axes[0, 0].set_xlabel('Transcript Index')
    axes[0, 0].set_ylabel('Number of Probes')
    axes[0, 0].set_title('Probes per Transcript')
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. Probe positions along transcripts (if position data available)
    if 'start' in df.columns and 'end' in df.columns:
        for transcript in transcript_counts.head(5).index:  # Top 5 transcripts
            transcript_df = df_plot[df_plot[transcript_col] == transcript]
            positions = (transcript_df['start'] + transcript_df['end']) / 2
            axes[0, 1].scatter(positions, [transcript] * len(positions), 
                             alpha=0.6, s=20)
        
        axes[0, 1].set_xlabel('Position')
        axes[0, 1].set_ylabel('Transcript')
        axes[0, 1].set_title('Probe Positions along Transcripts (Top 5)')
        axes[0, 1].grid(True, alpha=0.3)
    else:
        # If no position data, show probe count histogram
        axes[0, 1].hist(transcript_counts.values, bins=20, alpha=0.7, color='lightgreen')
        axes[0, 1].set_xlabel('Probes per Transcript')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].set_title('Distribution of Probes per Transcript')
        axes[0, 1].grid(True, alpha=0.3)
    
    # 3. Gene-level coverage (if gene info available)
    gene_col = 'gene' if 'gene' in df.columns else 'target'
    if gene_col in df.columns:
        gene_counts = df[gene_col].value_counts()
        axes[1, 0].bar(range(len(gene_counts)), gene_counts.values, 
                       color='gold', alpha=0.7)
        axes[1, 0].set_xlabel('Gene Index')
        axes[1, 0].set_ylabel('Number of Probes')
        axes[1, 0].set_title('Probes per Gene')
        axes[1, 0].grid(True, alpha=0.3)
    
    # 4. Exon distribution (if available)
    if 'exon_rank' in df.columns:
        exon_counts = df['exon_rank'].value_counts().sort_index()
        axes[1, 1].bar(exon_counts.index, exon_counts.values, 
                       color='mediumpurple', alpha=0.7)
        axes[1, 1].set_xlabel('Exon Number')
        axes[1, 1].set_ylabel('Number of Probes')
        axes[1, 1].set_title('Probe Distribution by Exon')
        axes[1, 1].grid(True, alpha=0.3)
    else:
        # Show transcript length distribution if available
        if len(transcript_counts) > 0:
            axes[1, 1].pie(transcript_counts.head(10).values, 
                          labels=transcript_counts.head(10).index,
                          autopct='%1.1f%%', startangle=90)
            axes[1, 1].set_title('Top 10 Transcripts by Probe Count')
    
    plt.tight_layout()
    return save_plot_conditionally(output_path, return_base64)

def plot_quality_metrics(df: pd.DataFrame, output_path: Optional[Path] = None, return_base64: bool = False) -> Optional[str]:
    """Plot quality metrics distribution for all probe types."""
    
    # Identify quality metric columns
    quality_metrics = []
    metric_patterns = ['gcContent', 'tm', 'foldScore', 'selfMatch', 'mappedGenes', 'mappedSites', 'kmerCount']
    
    for col in df.columns:
        if any(pattern in col for pattern in metric_patterns):
            if df[col].dtype in ['float64', 'int64'] and not df[col].isna().all():
                quality_metrics.append(col)
    
    if not quality_metrics:
        logger.warning("No quality metrics found for visualization")
        return None
    
    # Create subplots
    n_metrics = len(quality_metrics)
    n_cols = 3
    n_rows = (n_metrics + n_cols - 1) // n_cols
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 4 * n_rows))
    if n_rows == 1:
        axes = axes.reshape(1, -1)
    elif n_cols == 1:
        axes = axes.reshape(-1, 1)
    
    for idx, metric in enumerate(quality_metrics):
        row = idx // n_cols
        col = idx % n_cols
        
        # Skip if data is all NaN
        if df[metric].isna().all():
            continue
            
        # Plot histogram
        axes[row, col].hist(df[metric].dropna(), bins=30, alpha=0.7, color='skyblue')
        axes[row, col].set_xlabel(metric)
        axes[row, col].set_ylabel('Frequency')
        axes[row, col].set_title(f'Distribution of {metric}')
        axes[row, col].grid(True, alpha=0.3)
        
        # Add statistics
        mean_val = df[metric].mean()
        median_val = df[metric].median()
        axes[row, col].axvline(mean_val, color='red', linestyle='--', alpha=0.8, label=f'Mean: {mean_val:.2f}')
        axes[row, col].axvline(median_val, color='orange', linestyle='--', alpha=0.8, label=f'Median: {median_val:.2f}')
        axes[row, col].legend(fontsize=8)
    
    # Hide empty subplots
    for idx in range(n_metrics, n_rows * n_cols):
        row = idx // n_cols
        col = idx % n_cols
        axes[row, col].set_visible(False)
    
    plt.tight_layout()
    return save_plot_conditionally(output_path, return_base64)

def plot_correlation_matrix(df: pd.DataFrame, output_path: Optional[Path] = None, return_base64: bool = False) -> Optional[str]:
    """Plot correlation matrix for numeric attributes."""
    
    # Get numeric columns
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    
    # Filter out columns with too many NaN values
    numeric_cols = [col for col in numeric_cols if df[col].notna().sum() > len(df) * 0.1]
    
    if len(numeric_cols) < 2:
        logger.warning("Not enough numeric columns for correlation matrix")
        return None
    
    # Calculate correlation matrix
    correlation_matrix = df[numeric_cols].corr()
    
    # Plot heatmap
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(correlation_matrix, annot=True, cmap='RdBu_r', center=0,
                square=True, linewidths=0.5, cbar_kws={"shrink": .8}, ax=ax)
    ax.set_title('Correlation Matrix of Probe Attributes')
    
    plt.tight_layout()
    return save_plot_conditionally(output_path, return_base64)

def generate_plot_report(df: pd.DataFrame, protocol: Dict, output_dir: Path, report_suffix: str = "", save_files: bool = True, return_base64: bool = False) -> Dict:
    """Generate visualization plots for probe results."""
    if df.empty:
        logger.warning("Empty dataframe, cannot generate plots")
        return {"plot_paths": [], "plot_data": {}}
    
    # Detect protocol type
    protocol_type = detect_protocol_type(df, protocol)
    protocol_name = protocol.get('name', 'probes')
    
    # Create output directory if saving files
    if save_files:
        output_dir.mkdir(parents=True, exist_ok=True)
    
    plot_paths = []
    plot_data = {}
    
    try:
        # 1. Quality metrics distribution
        quality_plot_name = "quality_metrics"
        quality_plot_path = output_dir / f"{protocol_name}_quality_metrics{report_suffix}.png" if save_files else None
        quality_base64 = plot_quality_metrics(df, quality_plot_path, return_base64)
        if quality_plot_path:
            plot_paths.append(quality_plot_path)
        if quality_base64:
            plot_data[quality_plot_name] = quality_base64
        
        # 2. Correlation matrix
        corr_plot_name = "correlation_matrix"
        corr_plot_path = output_dir / f"{protocol_name}_correlation_matrix{report_suffix}.png" if save_files else None
        corr_base64 = plot_correlation_matrix(df, corr_plot_path, return_base64)
        if corr_plot_path:
            plot_paths.append(corr_plot_path)
        if corr_base64:
            plot_data[corr_plot_name] = corr_base64
        
        # 3. Protocol-specific plots
        if protocol_type == 'DNA':
            # DNA: Genomic coverage plots
            target_regions = protocol.get('targets', [])
            if target_regions:
                coverage_plot_name = "genomic_coverage"
                coverage_plot_path = output_dir / f"{protocol_name}_genomic_coverage{report_suffix}.png" if save_files else None
                coverage_base64 = plot_genomic_coverage(df, target_regions, coverage_plot_path, return_base64)
                if coverage_plot_path:
                    plot_paths.append(coverage_plot_path)
                if coverage_base64:
                    plot_data[coverage_plot_name] = coverage_base64
        
        elif protocol_type == 'RNA':
            # RNA: Transcript coverage plots
            transcript_plot_name = "transcript_coverage"
            transcript_plot_path = output_dir / f"{protocol_name}_transcript_coverage{report_suffix}.png" if save_files else None
            transcript_base64 = plot_transcript_coverage(df, transcript_plot_path, return_base64)
            if transcript_plot_path:
                plot_paths.append(transcript_plot_path)
            if transcript_base64:
                plot_data[transcript_plot_name] = transcript_base64
    except Exception as e:
        logger.error(f"Error generating plots: {e}")
        # Continue with available plots
    
    return {"plot_paths": plot_paths, "plot_data": plot_data}
