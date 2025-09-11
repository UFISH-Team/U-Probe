"""
HTML report generation for U-Probe analysis.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

from uprobe.utils import get_logger

logger = get_logger(__name__)


def _get_base_template() -> str:
    """Get base HTML template for all reports."""
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>U-Probe Scientific Analysis Report - {protocol_name}</title>
    <style>
        body {{
            font-family: 'Times New Roman', serif;
            line-height: 1.8;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 30px;
            background-color: #fafafa;
        }}
        .container {{
            background-color: white;
            padding: 50px;
            border-radius: 5px;
            box-shadow: 0 2px 15px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 2px solid #2c3e50;
            padding-bottom: 30px;
            margin-bottom: 40px;
        }}
        .header h1 {{
            color: #2c3e50;
            margin: 0;
            font-size: 2.8em;
            font-weight: normal;
        }}
        .header .subtitle {{
            color: #7f8c8d;
            font-size: 1.1em;
            margin-top: 15px;
            font-style: italic;
        }}
        .abstract {{
            background: #ecf0f1;
            padding: 25px;
            border-radius: 5px;
            margin: 30px 0;
            border-left: 5px solid #3498db;
        }}
        .abstract h3 {{
            color: #2c3e50;
            margin-top: 0;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .section h2 {{
            color: #2c3e50;
            border-bottom: 1px solid #bdc3c7;
            padding-bottom: 10px;
            font-size: 1.8em;
            font-weight: normal;
        }}
        .section h3 {{
            color: #34495e;
            font-size: 1.3em;
            margin-top: 25px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 15px;
            border: 1px solid #dee2e6;
            text-align: center;
        }}
        .stat-value {{
            font-size: 1.6em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 4px;
        }}
        .stat-label {{
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        .table-container {{
            overflow-x: auto;
            margin: 25px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border: 1px solid #dee2e6;
        }}
        th, td {{
            padding: 8px 12px;
            text-align: left;
            border: 1px solid #dee2e6;
            font-size: 0.9em;
        }}
        th {{
            background-color: #2c3e50;
            color: white;
            font-weight: bold;
        }}
        .plot-container {{
            text-align: center;
            margin: 20px 0;
            page-break-inside: avoid;
            padding: 10px;
        }}
        .plot-container img {{
            max-width: 80%;
            max-height: 400px;
            height: auto;
            border: 1px solid #dee2e6;
        }}
        .plot-caption {{
            font-size: 0.9em;
            color: #7f8c8d;
            margin-top: 10px;
            font-style: italic;
        }}
        .method-section {{
            background: #f8f9fa;
            padding: 25px;
            border: 1px solid #dee2e6;
            margin: 25px 0;
        }}
        .method-section h3 {{
            color: #2c3e50;
            margin-top: 0;
        }}
        .citation {{
            font-size: 0.9em;
            color: #7f8c8d;
            font-style: italic;
        }}
        .footer {{
            text-align: center;
            margin-top: 50px;
            padding-top: 25px;
            border-top: 1px solid #dee2e6;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        .reference {{
            font-size: 0.9em;
            margin: 5px 0;
        }}
        .equation {{
            text-align: center;
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border: 1px solid #dee2e6;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>U-Probe Scientific Analysis Report</h1>
            <div class="subtitle">Comprehensive Probe Design and Quality Assessment</div>
            <div class="subtitle">Protocol: {protocol_name}</div>
            <div class="subtitle">Generated: {timestamp}</div>
        </div>
        
        {content}
        
        <div class="footer">
            <p><strong>U-Probe Analysis Pipeline</strong></p>
            <p>Scientific Report Template | Computational Biology Analysis</p>
            <p class="citation">For research use. Please cite appropriate references when publishing.</p>
        </div>
    </div>
</body>
</html>
'''


def _get_summary_section(df: pd.DataFrame, protocol: Dict[str, Any], plot_data: Dict[str, str]) -> str:
    """Generate dynamic summary section based on protocol."""
    content = ['<div class="section">', '<h2>📊 Summary Statistics & Visualizations</h2>']

    # Add overall probe count summary
    target_col = 'target' if 'target' in df.columns else ('gene' if 'gene' in df.columns else None)
    if target_col:
        target_counts = df[target_col].value_counts()
        if not target_counts.empty:
            content.append('<h3>Overall Probe Counts by Target</h3>')
            content.append('<div class="table-container" style="max-width: 500px; margin-left: 0;">')
            count_df = target_counts.reset_index()
            count_df.columns = ['Target', 'Probe Count']
            content.append(count_df.to_html(index=False, classes='table table-striped', border=0))
            content.append('</div>')
    
    summary_config = protocol.get('summary', {})
    attributes = summary_config.get('attributes', [])
    if isinstance(attributes, dict):
        attributes = list(attributes.keys())
    
    if not attributes:
        content.append("<p>No summary attributes specified in the protocol.</p>")
    
    for attr_name in attributes:
        if attr_name not in df.columns:
            continue
        
        content.append(f'<h3>{attr_name.replace("_", " ").title()}</h3>')
        
        # Stats
        if target_col and df[target_col].nunique() > 1:
            # Per-target stats
            stats_df = df.groupby(target_col)[attr_name].agg(['mean', 'min', 'max', 'median']).reset_index()
            stats_df = stats_df.round(2)
            content.append('<div class="table-container">')
            content.append(stats_df.to_html(index=False, classes='table table-striped', border=0))
            content.append('</div>')
        else:
            # Overall stats
            stats = df[attr_name].agg(['mean', 'min', 'max', 'median']).to_dict()
            stats_html = '<div class="stats-grid">'
            for stat_name, value in stats.items():
                stats_html += f'''
                    <div class="stat-card">
                        <div class="stat-value">{value:.2f}</div>
                        <div class="stat-label">{stat_name.capitalize()}</div>
                    </div>
                '''
            stats_html += '</div>'
            content.append(stats_html)

        # Plots
        attr_plots = {k: v for k, v in plot_data.items() if k.startswith(attr_name)}
        
        if attr_plots:
            plot_html = '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; margin-top: 20px;">'
            for plot_name, b64_data in sorted(attr_plots.items()):
                title_suffix = plot_name.replace(attr_name, '').replace('_', ' ').strip().title()
                plot_title = f'{attr_name.replace("_", " ").title()}'
                if title_suffix:
                    plot_title += f' - {title_suffix}'
                
                plot_html += f'''
                    <div class="plot-container">
                        <img src="data:image/png;base64,{b64_data}" alt="{plot_title}">
                        <div class="plot-caption">{plot_title}</div>
                    </div>
                '''
            plot_html += '</div>'
            content.append(plot_html)

    content.append('</div>')
    return '\n'.join(content)

def _get_quality_assessment_section(protocol: Dict[str, Any]) -> str:
    """Generate quality assessment section with placeholders."""
    protocol_name = protocol.get("name", "").lower()
    content = ['<div class="section">', '<h2>🔍 Quality Assessment</h2>']

    if 'dna' in protocol_name:
        content.append("<h3>Probe Coverage Analysis</h3>")
        content.append("<p><i>[Placeholder for DNA probe coverage plot and analysis. Logic to be implemented.]</i></p>")
        content.append('<div class="plot-container" style="border: 2px dashed #ccc; padding: 20px; background: #f9f9f9;"><p>Coverage Plot Area</p></div>')
    elif 'rna' in protocol_name:
        content.append("<h3>Optimal Probe Recommendation</h3>")
        content.append("<p><i>[Placeholder for RNA optimal probe selection plot (e.g., by transcript position). Logic to be implemented.]</i></p>")
        content.append('<div class="plot-container" style="border: 2px dashed #ccc; padding: 20px; background: #f9f9f9;"><p>Transcript Position Plot Area</p></div>')
    else:
        content.append("<p>No specific quality assessment configured for this protocol type.</p>")
    
    content.append('</div>')
    return '\n'.join(content)

def _get_recommendations_section(protocol: Dict[str, Any]) -> str:
    """Generate recommendations section with placeholders."""
    protocol_name = protocol.get("name", "").lower()
    content = ['<div class="section">', '<h2>💡 Analysis & Recommendations</h2>']

    if 'dna' in protocol_name:
        content.append("<h3>Probe Pool Reliability Analysis</h3>")
        content.append("<p><i>[Placeholder for DNA probe pool confidence analysis. This section will discuss the overall quality and expected performance of the generated probe set based on the QC metrics.]</i></p>")
    elif 'rna' in protocol_name:
        content.append("<h3>Guidelines for Optimal Probe Selection</h3>")
        content.append("<p><i>[Placeholder for RNA probe selection guidelines. This section will provide recommendations on how to choose the best probes from the generated set for experimental validation, considering factors like melting temperature, GC content, and specificity.]</i></p>")
    else:
        content.append("<p>No specific recommendations available for this protocol type.</p>")
        
    content.append('</div>')
    return '\n'.join(content)

def _get_details_section(df: pd.DataFrame) -> str:
    """Generate the detailed probe data table section."""
    content = ['<div class="section">', '<h2>📄 Probe Details</h2>']
    content.append('<p>The table below contains the full dataset of all generated probes and their calculated attributes.</p>')
    content.append('<div class="table-container">')
    content.append(df.to_html(index=False, classes='table table-striped', border=0))
    content.append('</div>')
    content.append('</div>')
    return '\n'.join(content)


def _build_scientific_report_content(df: pd.DataFrame, protocol: Dict[str, Any], plot_data: Dict[str, str]) -> str:
    """Builds the full HTML content for the scientific report."""
    content = [
        _get_summary_section(df, protocol, plot_data),
        _get_quality_assessment_section(protocol),
        _get_recommendations_section(protocol),
        _get_details_section(df)
    ]
    return "\n".join(content)


def save_html_report(
    df: pd.DataFrame,
    protocol: Dict[str, Any],
    output_path: Path,
    template_type: str = "scientific_report",
    plot_data: Optional[Dict[str, str]] = None
) -> Optional[Path]:
    """Save HTML report to file."""
    try:
        logger.info(f"Generating {template_type} HTML report...")
        
        if not plot_data:
            plot_data = {}
        
        # Define content builders for different templates
        content_builders = {
            'dna_report': _build_scientific_report_content, # Using scientific as base for now
            'rna_report': _build_scientific_report_content, # Using scientific as base for now
            'scientific_report': _build_scientific_report_content,
        }

        # Get the appropriate content builder, defaulting to the scientific one
        builder = content_builders.get(template_type, _build_scientific_report_content)
        
        # Generate the HTML content using the selected builder
        content = builder(df, protocol, plot_data)
        
        # Get the base HTML template
        template = _get_base_template()
        
        # Fill template
        protocol_name = protocol.get('name', 'Unknown Protocol')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        html_content = template.format(
            protocol_name=protocol_name,
            timestamp=timestamp,
            content=content
        )
        
        # Save to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML report saved to: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error generating HTML report: {e}")
        return None
