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


def _prepare_df_for_display(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare DataFrame for display by capitalizing the first letter of each word in column names."""
    df_display = df.copy()
    df_display.columns = [col.replace('_', ' ').title() for col in df_display.columns]
    return df_display


def _get_base_template() -> str:
    """Get base HTML template for all reports."""
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>U-Probe Design Results Analysis Report - {protocol_name}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
        
        :root {{
            --primary-color: #2c3e50;
            --secondary-color: #3498db;
            --text-color: #34495e;
            --light-gray-color: #ecf0f1;
            --background-color: #f7f9fa;
            --border-color: #dfe6e9;
            --white-color: #ffffff;
        }}

        body {{
            font-family: 'Roboto', sans-serif;
            line-height: 1.7;
            color: var(--text-color);
            background-color: var(--background-color);
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 1600px;
            margin: 20px auto;
            background-color: var(--white-color);
            padding: 50px;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.07);
        }}
        .header {{
            text-align: center;
            padding-bottom: 30px;
            margin-bottom: 50px;
            border-bottom: 1px solid var(--border-color);
        }}
        .header h1 {{
            color: var(--primary-color);
            margin: 0;
            font-size: 2.8em;
            font-weight: 700;
            letter-spacing: -1px;
        }}
        .header .subtitle {{
            color: #7f8c8d;
            font-size: 1.1em;
            margin-top: 15px;
        }}
        .section {{
            margin-bottom: 60px;
        }}
        .section h2 {{
            color: var(--primary-color);
            font-size: 2.2em;
            font-weight: 700;
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 3px solid var(--secondary-color);
            display: inline-block;
        }}
        .section h3 {{
            color: var(--primary-color);
            font-size: 1.6em;
            margin-top: 40px;
            margin-bottom: 20px;
            border-left: 4px solid var(--secondary-color);
            padding-left: 15px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .stat-item {{
            text-align: center;
            padding: 15px 10px;
            border-bottom: 2px solid var(--border-color);
        }}
        .stat-value {{
            font-size: 1.8em;
            font-weight: 600;
            color: var(--primary-color);
            margin-bottom: 5px;
        }}
        .stat-label {{
            color: #6c757d;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .table-container {{
            overflow-x: auto;
            margin-top: 30px;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: var(--white-color);
        }}
        th, td {{
            padding: 15px 20px;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }}
        th {{
            background-color: var(--light-gray-color);
            color: var(--primary-color);
            font-weight: 700;
            font-size: 0.85em;
            letter-spacing: 0.5px;
        }}
        tbody tr:last-child th,
        tbody tr:last-child td {{
            border-bottom: none;
        }}
        tbody tr:hover {{
            background-color: #f2f5f7;
        }}
        .plot-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(45%, 1fr));
            gap: 30px;
            margin-top: 25px;
        }}
        .plot-container {{
            border: 1px solid var(--border-color);
            padding: 15px;
            background: var(--white-color);
        }}
        .plot-caption {{
            font-size: 0.9em;
            color: #6c757d;
            margin-top: 10px;
            text-align: center;
            font-weight: 500;
        }}
        .footer {{
            text-align: center;
            margin-top: 60px;
            padding-top: 30px;
            border-top: 1px solid var(--border-color);
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        .download-btn {{
            background: var(--secondary-color);
            color: white;
            border: none;
            padding: 10px 20px;
            font-size: 0.9em;
            font-weight: 500;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            text-decoration: none;
        }}
        .download-btn:hover {{
            background: var(--primary-color);
        }}
    </style>
    <script>
        // Store complete data for download
        let completeData = {complete_data_json};
        let downloadFileName = '{download_filename}';
        
        function downloadTableData() {{
            if (!completeData || completeData.length === 0) {{
                alert('No data available for download');
                return;
            }}
            
            // Convert JSON data to CSV
            const headers = Object.keys(completeData[0]);
            let csv = headers.join(',') + '\\n';
            
            completeData.forEach(row => {{
                const values = headers.map(header => {{
                    let value = row[header] || '';
                    value = String(value);
                    // Escape quotes and wrap in quotes if contains comma, quote, or newline
                    if (value.includes(',') || value.includes('"') || value.includes('\\n')) {{
                        value = '"' + value.replace(/"/g, '""') + '"';
                    }}
                    return value;
                }});
                csv += values.join(',') + '\\n';
            }});
            
            // Create download link
            const blob = new Blob([csv], {{ type: 'text/csv;charset=utf-8;' }});
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', downloadFileName);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }}
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>U-Probe Analysis Report</h1>
            <div class="subtitle">Protocol: {protocol_name}</div>
            <div class="subtitle">Generated: {timestamp}</div>
        </div>
        
        {content}
        
        <div class="footer">
            <p>U-Probe Analysis Pipeline</p>
        </div>
    </div>
</body>
</html>
'''


def _get_summary_section(df: pd.DataFrame, protocol: Dict[str, Any], plot_data: Dict[str, str]) -> str:
    """Generate dynamic summary section based on protocol."""
    content = ['<div class="section">', '<h2>Statistics</h2>']

    # Add overall probe count summary
    target_col = 'target' if 'target' in df.columns else ('gene' if 'gene' in df.columns else None)
    if target_col:
        target_counts = df[target_col].value_counts()
        if not target_counts.empty:
            content.append('<h3>Probe number</h3>')
            content.append('<div class="table-container" style="max-width: 500px; margin-left: 0;">')
            count_df = target_counts.reset_index()
            count_df.columns = ['Target', 'Probe Number']
            content.append(count_df.to_html(index=True, classes='table table-striped', border=0))
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
        
        content.append(f'<h3>{attr_name.title()}</h3>')
        
        # Stats
        if target_col and df[target_col].nunique() > 1:
            # Per-target stats
            stats_df = df.groupby(target_col)[attr_name].agg(['mean', 'min', 'max', 'median']).reset_index()
            stats_df = stats_df.round(2)
            # Convert column names to lowercase
            stats_df_display = _prepare_df_for_display(stats_df)
            content.append('<div class="table-container">')
            content.append(stats_df_display.to_html(index=True, classes='table table-striped', border=0))
            content.append('</div>')
        else:
            # Overall stats
            stats = df[attr_name].agg(['mean', 'min', 'max', 'median']).to_dict()
            stats_html = '<div class="stats-grid">'
            for stat_name, value in stats.items():
                stats_html += f'''
                    <div class="stat-item">
                        <div class="stat-value">{value:.2f}</div>
                        <div class="stat-label">{stat_name.title()}</div>
                    </div>
                '''
            stats_html += '</div>'
            content.append(stats_html)

        # Plots
        attr_plots = {k: v for k, v in plot_data.items() if k.startswith(attr_name)}
        
        if attr_plots:
            plot_html = '<div class="plot-grid">'
            for _, plot_div in sorted(attr_plots.items()):
                plot_html += f'''
                    <div class="plot-container">
                        {plot_div}
                        <div class="plot-caption"></div>
                    </div>
                '''
            plot_html += '</div>'
            content.append(plot_html)

    content.append('</div>')
    return '\n'.join(content)

def _get_quality_assessment_section(protocol: Dict[str, Any]) -> str:
    """Generate quality assessment section with placeholders."""
    protocol_name = protocol.get("name", "").lower()
    content = ['<div class="section">', '<h2>Results visualization</h2>']

    if 'dna' in protocol_name:
        content.append("<h3>Coverage</h3>")
        content.append("<p>Coverage analysis will be available in future versions.</p>")
    elif 'rna' in protocol_name:
        content.append("<h3>Probe optimization</h3>")
        content.append("<p>Probe optimization analysis will be available in future versions.</p>")
    else:
        content.append("<p>Results visualization features will be added based on protocol requirements.</p>")
    
    content.append('</div>')
    return '\n'.join(content)

def _get_recommendations_section(protocol: Dict[str, Any]) -> str:
    """Generate recommendations section with placeholders."""
    protocol_name = protocol.get("name", "").lower()
    content = ['<div class="section">', '<h2>Analysis & recommendations</h2>']

    if 'dna' in protocol_name:
        content.append("<h3>Reliability</h3>")
        content.append("<p>Probe reliability analysis will be provided based on quality metrics and experimental validation.</p>")
    elif 'rna' in protocol_name:
        content.append("<h3>Selection</h3>")
        content.append("<p>Probe selection recommendations will be provided based on melting temperature, GC content, and specificity analysis.</p>")
    else:
        content.append("<p>Analysis & recommendations will be customized based on protocol specifications.</p>")
        
    content.append('</div>')
    return '\n'.join(content)

def _get_details_section(df: pd.DataFrame) -> str:
    """Generate the detailed probe data table section."""
    content = ['<div class="section">', '<h2>Probe information table</h2>']
    
    # Show preview of first 5 rows
    preview_df = df.head(5)
    total_rows = len(df)
    
    content.append(f'<p>Showing {min(5, total_rows)} of {total_rows} probes. Download complete data using the button below.</p>')
    
    # Add download button
    content.append('''
    <div style="margin: 20px 0; text-align: center;">
        <button onclick="downloadTableData()" class="download-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 8px;">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="7,10 12,15 17,10"></polyline>
                <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
            Download (.csv)
        </button>
    </div>
    ''')
    
    content.append('<div class="table-container">')
    preview_df_display = _prepare_df_for_display(preview_df)
    content.append(preview_df_display.to_html(index=True, classes='table table-striped', border=0))
    content.append('</div>')
    if total_rows > 5:
        content.append(f'<p style="text-align: center; color: #7f8c8d; font-style: italic;">... and {total_rows - 5} more rows</p>')
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
    plot_data: Optional[Dict[str, str]] = None,
    csv_filename: Optional[str] = None
) -> Optional[Path]:
    """Save HTML report to file."""
    try:
        logger.info(f"Generating {template_type} HTML report...")
        if not plot_data:
            plot_data = {}
        content_builders = {
            'dna_report': _build_scientific_report_content, 
            'rna_report': _build_scientific_report_content,
            'scientific_report': _build_scientific_report_content,
        }
        builder = content_builders.get(template_type, _build_scientific_report_content)
        content = builder(df, protocol, plot_data)
        template = _get_base_template()
        protocol_name = protocol.get('name', 'Unknown Protocol')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if csv_filename:
            download_filename = csv_filename
        else:
            # {Protocol}_{YYYYMMDD}_{HHMMSS}.csv
            import time
            time_str = time.strftime("%Y%m%d_%H%M%S")
            download_filename = f"{protocol_name}_{time_str}.csv"
        complete_data_json = df.to_json(orient='records')
        html_content = template.format(
            protocol_name=protocol_name,
            timestamp=timestamp,
            content=content,
            complete_data_json=complete_data_json,
            download_filename=download_filename
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return output_path
    except Exception as e:
        logger.error(f"Error generating HTML report: {e}")
        return None
