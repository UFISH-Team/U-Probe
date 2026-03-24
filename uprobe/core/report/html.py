"""
HTML report generation for U-Probe analysis.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

from uprobe.core.utils import get_logger

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
    <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.css">
    <script type="text/javascript" charset="utf8" src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
    <script type="text/javascript" charset="utf8" src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.js"></script>
    <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
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
    
    summary_config = protocol.get('summary', {})
    attributes = summary_config.get('attributes', [])
    if isinstance(attributes, dict):
        attributes = list(attributes.keys())
        
    # Create a consolidated summary table
    content.append('<h3>Attribute Distribution Summary</h3>')
    content.append('<p>Overview of probe counts and key thermodynamic properties across all targets.</p>')
    
    if target_col:
        # Group by target and calculate stats for all attributes in one go
        agg_dict = {target_col: 'count'} # Start with count
        
        # Add min/max/mean for each attribute
        valid_attrs = [attr for attr in attributes if attr in df.columns]
        
        if valid_attrs:
            # First, get the counts
            stats_df = df.groupby(target_col).size().reset_index(name='Probe Count')
            
            # Then calculate stats for each attribute and merge
            for attr in valid_attrs:
                attr_stats = df.groupby(target_col)[attr].agg(['min', 'max', 'mean']).reset_index()
                
                # Format the Min-Max column
                attr_stats[f'{attr} (Min-Max)'] = attr_stats.apply(
                    lambda row: f"{row['min']:.0f} - {row['max']:.0f}", axis=1
                )
                
                # Format the Mean column
                attr_stats[f'{attr} (Mean)'] = attr_stats['mean'].round(2)
                
                # Merge back to main stats_df
                stats_df = pd.merge(stats_df, attr_stats[[target_col, f'{attr} (Min-Max)', f'{attr} (Mean)']], on=target_col)
            
            # Rename target column for display
            stats_df.rename(columns={target_col: 'Target'}, inplace=True)
            
            content.append('<div class="table-container">')
            content.append(stats_df.to_html(index=False, classes='table table-striped', border=0))
            content.append('</div>')
            
            # Add plots in a grid if available
            if plot_data:
                content.append('<h3>Attribute Distributions</h3>')
                content.append('<div class="plot-grid">')
                for attr_name in valid_attrs:
                    # Find all plots related to this attribute
                    attr_plots = {k: v for k, v in plot_data.items() if k.startswith(attr_name)}
                    for plot_id, plot_div in sorted(attr_plots.items()):
                        content.append(f'''
                        <div class="plot-container">
                            {plot_div}
                        </div>
                        ''')
                content.append('</div>')
        else:
            # Fallback if no attributes match
            target_counts = df[target_col].value_counts().reset_index()
            target_counts.columns = ['Target', 'Probe Count']
            content.append('<div class="table-container" style="max-width: 500px;">')
            content.append(target_counts.to_html(index=False, classes='table table-striped', border=0))
            content.append('</div>')
    else:
        content.append("<p>Target column not found for summary.</p>")

    content.append('</div>')
    return '\n'.join(content)

def _get_quality_assessment_section(df: pd.DataFrame, protocol: Dict[str, Any]) -> str:
    """Generate quality assessment section with visualizations."""
    protocol_name = protocol.get("name", "").lower()
    content = ['<div class="section">', '<h2>Results visualization</h2>']
    
    script_lines = []

    # Determine the source type from protocol or columns
    source_type = str(protocol.get('extracts', {}).get('target_region', {}).get('source', '')).lower()
    
    # Check if we have region/feature columns (exon, utr, cds)
    has_exon_col = 'exon_name' in df.columns
    has_utr_col = 'utr_name' in df.columns
    has_cds_col = 'cds_name' in df.columns
    
    feature_col = None
    feature_label = "Feature"
    if has_exon_col:
        feature_col = 'exon_name'
        feature_label = "Exon"
    elif has_utr_col:
        feature_col = 'utr_name'
        feature_label = "UTR"
    elif has_cds_col:
        feature_col = 'cds_name'
        feature_label = "CDS"

    # For RNA/transcript-based probes (exon, UTR, CDS), visualize transcript & feature coverage
    if feature_col and all(col in df.columns for col in ['target', 'transcript_names', 'probe_id', 'start', 'end']):
        content.append(f"<h3>Transcript & {feature_label} Genomic Coverage</h3>")
        content.append(f"<p>The chart below displays the distribution of probes across different transcripts mapped to their <b>actual genomic coordinates</b>. The Y-axis represents individual transcripts, and the X-axis represents the genomic position. Introns appear as large gaps between probe clusters. You can zoom in to see specific probes.</p>")
        
        content.append('<div class="plot-grid">')
        
        for target in df['target'].unique():
            target_df = df[df['target'] == target].copy()
            target_df['start'] = pd.to_numeric(target_df['start'], errors='coerce')
            target_df['end'] = pd.to_numeric(target_df['end'], errors='coerce')
            target_df = target_df.dropna(subset=['start', 'end']).sort_values('start')
            
            if not target_df.empty:
                transcript_probe_map = []
                unique_transcripts = set()
                
                color_palette = [
                    '#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', 
                    '#1abc9c', '#d35400', '#34495e', '#c0392b', '#8e44ad',
                    '#27ae60', '#2980b9', '#f1c40f', '#e67e22', '#16a085'
                ]
                
                import re
                
                for idx, (_, row) in enumerate(target_df.iterrows()):
                    feat_val = str(row[feature_col])
                    rel_start = row['start']
                    rel_end = row['end']
                    
                    # Try to parse genomic coordinates from feature name (e.g., chr1_1000_2000_+)
                    match = re.search(r'_(\d+)_(\d+)_([+-])$', feat_val)
                    
                    abs_start = rel_start
                    abs_end = rel_end
                    is_genomic = False
                    
                    if match:
                        g_start = int(match.group(1))
                        g_end = int(match.group(2))
                        strand = match.group(3)
                        is_genomic = True
                        
                        if strand == '+':
                            abs_start = g_start + rel_start - 1
                            abs_end = g_start + rel_end - 1
                        else:
                            # For minus strand, relative start 1 is at g_end
                            abs_start = g_end - rel_end + 1
                            abs_end = g_end - rel_start + 1
                            
                    # Parse transcripts for hover text
                    t_names = row['transcript_names']
                    probe_transcripts = []
                    if isinstance(t_names, str):
                        try:
                            import ast
                            names = ast.literal_eval(t_names)
                            if isinstance(names, list):
                                probe_transcripts = names
                            else:
                                probe_transcripts = [n.strip(" '\"[]") for n in t_names.split(',')]
                        except:
                            probe_transcripts = [n.strip(" '\"[]") for n in t_names.split(',')]
                    elif isinstance(t_names, list):
                        probe_transcripts = t_names
                    else:
                        probe_transcripts = [str(t_names)]
                    
                    clean_transcripts = [t.strip(" '\"[]") for t in probe_transcripts if t and str(t).strip(" '\"[]")]
                    n_trans = len(clean_transcripts)
                    
                    probe_color = color_palette[idx % len(color_palette)]
                    
                    for trans in clean_transcripts:
                        unique_transcripts.add(trans)
                        transcript_probe_map.append({
                            'transcript': trans,
                            'probe_id': row['probe_id'],
                            'abs_start': abs_start,
                            'abs_end': abs_end,
                            'rel_start': rel_start,
                            'rel_end': rel_end,
                            'feat_val': feat_val,
                            'is_genomic': is_genomic,
                            'color': probe_color,
                            'n_trans': n_trans
                        })
                
                if not unique_transcripts:
                    continue
                    
                # Compress X-axis to hide large introns
                intervals = []
                for item in transcript_probe_map:
                    s, e = min(item['abs_start'], item['abs_end']), max(item['abs_start'], item['abs_end'])
                    intervals.append([s - 50, e + 50]) # Add 50bp margin
                
                intervals.sort(key=lambda x: x[0])
                merged_blocks = []
                if intervals:
                    merged_blocks = [intervals[0]]
                    for current in intervals[1:]:
                        previous = merged_blocks[-1]
                        if current[0] <= previous[1] + 100: # Merge if gap is <= 100bp
                            previous[1] = max(previous[1], current[1])
                        else:
                            merged_blocks.append(current)
                
                GAP_SIZE = 100 # Fixed size for introns/gaps in the plot
                
                def compress_x(real_x):
                    if not merged_blocks: return real_x
                    compressed = 0
                    for i, block in enumerate(merged_blocks):
                        if real_x < block[0]:
                            if i == 0: return real_x - block[0]
                            prev_block = merged_blocks[i-1]
                            fraction = (real_x - prev_block[1]) / (block[0] - prev_block[1])
                            return compressed + fraction * GAP_SIZE
                        elif real_x <= block[1]:
                            return compressed + (real_x - block[0])
                        else:
                            compressed += (block[1] - block[0])
                            if i < len(merged_blocks) - 1:
                                compressed += GAP_SIZE
                    last_block = merged_blocks[-1]
                    return compressed + (real_x - last_block[1])

                tickvals = []
                ticktext = []
                for block in merged_blocks:
                    tickvals.append(compress_x(block[0] + 50))
                    ticktext.append(str(int(block[0] + 50)))
                    tickvals.append(compress_x(block[1] - 50))
                    ticktext.append(str(int(block[1] - 50)))
                    
                sorted_transcripts = sorted(list(unique_transcripts))
                
                import re as regex
                safe_target = regex.sub(r'\W+', '_', str(target))
                div_id = f"rna_plot_{safe_target}"
                
                plot_height = max(300, len(sorted_transcripts) * 40 + 100)
                
                content.append(f'<div class="plot-container" style="grid-column: 1 / -1;">')
                content.append(f'<div id="{div_id}" style="width:100%;height:{plot_height}px;"></div>')
                
                traces_js = []
                probes_in_map = {}
                for item in transcript_probe_map:
                    pid = item['probe_id']
                    if pid not in probes_in_map:
                        probes_in_map[pid] = {'x': [], 'y': [], 'text': [], 'color': item['color']}
                    
                    cx_start = compress_x(item['abs_start'])
                    cx_end = compress_x(item['abs_end'])
                    
                    probes_in_map[pid]['x'].extend([cx_start, cx_end, None])
                    probes_in_map[pid]['y'].extend([item['transcript'], item['transcript'], None])
                    
                    pos_str = f"{item['abs_start']}-{item['abs_end']}" if item['is_genomic'] else f"{item['rel_start']}-{item['rel_end']} (Relative)"
                    hover_text = f"<b>Probe:</b> {pid}<br><b>Genomic Pos:</b> {pos_str}<br><b>{feature_label}:</b> {item['feat_val']}<br><b>Total Transcripts:</b> {item['n_trans']}<br><b>Current Track:</b> {item['transcript']}"
                    
                    probes_in_map[pid]['text'].extend([hover_text, hover_text, None])
                    
                for pid, pdata in probes_in_map.items():
                    trace_js = f"""{{
                        x: {json.dumps(pdata['x'])},
                        y: {json.dumps(pdata['y'])},
                        mode: 'lines',
                        type: 'scatter',
                        text: {json.dumps(pdata['text'])},
                        hoverinfo: 'text',
                        line: {{ width: 8, color: '{pdata['color']}' }},
                        name: '{pid}',
                        showlegend: false
                    }}"""
                    traces_js.append(trace_js)
                
                xaxis_title = 'Genomic Position (Introns Compressed)' if any(item['is_genomic'] for item in transcript_probe_map) else f'Relative Position within {feature_label}'
                
                script_lines.append(f"""
                var traces_{div_id} = [{','.join(traces_js)}];
                
                var layout_{div_id} = {{
                    title: '{target} - Probe Genomic Distribution Across Transcripts',
                    xaxis: {{ 
                        title: '{xaxis_title}',
                        tickvals: {json.dumps(tickvals)},
                        ticktext: {json.dumps(ticktext)},
                        tickangle: 45
                    }},
                    yaxis: {{ 
                        title: 'Transcript',
                        categoryorder: 'category ascending',
                        type: 'category'
                    }},
                    hovermode: 'closest',
                    margin: {{ t: 40, l: 150, b: 80 }}
                }};
                Plotly.newPlot('{div_id}', traces_{div_id}, layout_{div_id});
                """)
                
                # Add Recommendations
                probe_n_trans = {}
                probe_details = {}
                for item in transcript_probe_map:
                    pid = item['probe_id']
                    probe_n_trans[pid] = item['n_trans']
                    if pid not in probe_details:
                        probe_details[pid] = item
                
                sorted_probes = sorted(probe_n_trans.items(), key=lambda x: x[1], reverse=True)
                top_probes = sorted_probes[:3]
                
                if top_probes:
                    content.append(f'<div class="recommendation-box" style="margin-top: 15px; padding: 15px; background-color: #f8f9fa; border-left: 4px solid #2ecc71; border-radius: 4px;">')
                    content.append(f'<h4 style="margin-top: 0; color: #2c3e50;">💡 Top Recommended Probes</h4>')
                    content.append(f'<p style="font-size: 0.9em; color: #7f8c8d; margin-bottom: 10px;">These probes satisfy all design attributes and target the maximum number of transcripts:</p>')
                    content.append('<ul style="margin-bottom: 0; padding-left: 20px;">')
                    for pid, n_trans in top_probes:
                        p_detail = probe_details[pid]
                        pos_str = f"{p_detail['abs_start']}-{p_detail['abs_end']}" if p_detail['is_genomic'] else f"{p_detail['rel_start']}-{p_detail['rel_end']} (Relative)"
                        content.append(f"<li style='margin-bottom: 5px;'><b>{pid}</b>: Targets <span style='color: #e74c3c; font-weight: bold;'>{n_trans}</span> transcripts (Region: {p_detail['feat_val']}, Pos: {pos_str})</li>")
                    content.append('</ul>')
                    content.append('</div>')
                    
                content.append('</div>')
            
    # For DNA/genome probes, visualize regional coverage
    elif 'genome' in source_type or 'dna' in protocol_name:
        content.append("<h3>Regional Coverage Map</h3>")
        content.append("<p>The chart below displays the distribution of probes across the target genomic region. Overlapping probes are stacked vertically.</p>")
        
        # Check if we have sub_region column to extract start/end
        if 'sub_region' in df.columns and ('start' not in df.columns or 'end' not in df.columns):
            try:
                # Extract start and end from sub_region (format: "start_end")
                df[['start', 'end']] = df['sub_region'].str.split('_', expand=True)
                df['start'] = pd.to_numeric(df['start'], errors='coerce')
                df['end'] = pd.to_numeric(df['end'], errors='coerce')
            except Exception as e:
                logger.warning(f"Could not parse start/end from sub_region: {e}")
                
        if all(col in df.columns for col in ['target', 'start', 'end', 'probe_id']):
            content.append('<div class="plot-grid">')
            
            for target in df['target'].unique():
                target_df = df[df['target'] == target].copy()
                target_df['start'] = pd.to_numeric(target_df['start'], errors='coerce')
                target_df['end'] = pd.to_numeric(target_df['end'], errors='coerce')
                target_df = target_df.dropna(subset=['start', 'end']).sort_values('start')
                
                if not target_df.empty:
                    # Pileup logic for overlapping probes
                    tracks = []
                    y_vals = []
                    for _, row in target_df.iterrows():
                        placed = False
                        for i, end_pos in enumerate(tracks):
                            if row['start'] > end_pos:
                                tracks[i] = row['end']
                                y_vals.append(i)
                                placed = True
                                break
                        if not placed:
                            tracks.append(row['end'])
                            y_vals.append(len(tracks) - 1)
                    
                    target_df['track'] = y_vals
                    
                    import re
                    safe_target = re.sub(r'\W+', '_', str(target))
                    div_id = f"dna_plot_{safe_target}"
                    plot_height = max(250, len(tracks) * 20 + 150)
                    
                    content.append(f'<div class="plot-container" style="grid-column: 1 / -1;">')
                    content.append(f'<div id="{div_id}" style="width:100%;height:{plot_height}px;"></div>')
                    content.append('</div>')
                    
                    x_lines = []
                    y_lines = []
                    texts = []
                    
                    # A list of distinct colors for probes
                    color_palette = [
                        '#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', 
                        '#1abc9c', '#d35400', '#34495e', '#c0392b', '#8e44ad',
                        '#27ae60', '#2980b9', '#f1c40f', '#e67e22', '#16a085'
                    ]
                    
                    for idx, (_, row) in enumerate(target_df.iterrows()):
                        x_lines.extend([row['start'], row['end'], None])
                        y_lines.extend([row['track'], row['track'], None])
                        texts.extend([f"Probe: {row['probe_id']}<br>Pos: {row['start']}-{row['end']}", f"Probe: {row['probe_id']}<br>Pos: {row['start']}-{row['end']}", None])
                    
                    # Try to get the total length of the target region if available
                    max_x = target_df['end'].max()
                    
                    # Check if we can infer the total region length from target_region column
                    if 'target_region' in target_df.columns:
                        try:
                            # Assuming target_region contains the full sequence for that target
                            # We take the length of the longest string in target_region for this target
                            region_lengths = target_df['target_region'].dropna().apply(len)
                            if not region_lengths.empty:
                                max_region_len = region_lengths.max()
                                if max_region_len > max_x:
                                    max_x = max_region_len
                        except Exception as e:
                            logger.warning(f"Could not calculate target_region length: {e}")
                            
                    # Add a 5% margin to the right
                    xaxis_range = [0, max_x * 1.05]
                    
                    # Add a background shape to represent the full target region
                    shapes = []
                    if 'target_region' in target_df.columns:
                        shapes.append(f"{{type: 'rect', xref: 'x', x0: 0, x1: {max_x}, yref: 'paper', y0: 0, y1: 1, fillcolor: '#f1f2f6', opacity: 0.5, line: {{width: 1, color: '#bdc3c7'}}}}")
                    
                    # Create multiple traces, one for each probe to color them differently
                    traces_js = []
                    for idx, (_, row) in enumerate(target_df.iterrows()):
                        probe_color = color_palette[idx % len(color_palette)]
                        start_idx = idx * 3
                        end_idx = start_idx + 3
                        
                        trace_js = f"""{{
                            x: {json.dumps(x_lines[start_idx:end_idx])},
                            y: {json.dumps(y_lines[start_idx:end_idx])},
                            mode: 'lines',
                            type: 'scatter',
                            text: {json.dumps(texts[start_idx:end_idx])},
                            hoverinfo: 'text',
                            line: {{ width: 10, color: '{probe_color}' }},
                            showlegend: false
                        }}"""
                        traces_js.append(trace_js)
                    
                    script_lines.append(f"""
                    var traces_{div_id} = [{','.join(traces_js)}];
                    
                    var layout_{div_id} = {{
                        title: '{target} - Probe Coverage Map',
                        xaxis: {{ 
                            title: 'Genomic Position',
                            range: {json.dumps(xaxis_range)}
                        }},
                        yaxis: {{ title: 'Track', showticklabels: false, rangemode: 'tozero', autorange: 'reversed' }},
                        hovermode: 'closest',
                        margin: {{ t: 40 }},
                        shapes: [{','.join(shapes)}]
                    }};
                    Plotly.newPlot('{div_id}', traces_{div_id}, layout_{div_id});
                    """)
                    
                    # Add Recommendations for DNA
                    content.append(f'<div class="recommendation-box" style="margin-top: 15px; padding: 15px; background-color: #f8f9fa; border-left: 4px solid #3498db; border-radius: 4px;">')
                    content.append(f'<h4 style="margin-top: 0; color: #2c3e50;">💡 Coverage Analysis</h4>')
                    
                    total_probes = len(target_df)
                    coverage_span = target_df['end'].max() - target_df['start'].min() if not target_df.empty else 0
                    
                    content.append(f'<ul style="margin-bottom: 0; padding-left: 20px;">')
                    content.append(f"<li style='margin-bottom: 5px;'>Total Probes: <b>{total_probes}</b></li>")
                    content.append(f"<li style='margin-bottom: 5px;'>Effective Coverage Span: <b>{coverage_span} bp</b></li>")
                    
                    if total_probes < 5:
                        content.append(f"<li style='margin-bottom: 5px; color: #e74c3c;'><b>Warning:</b> Low probe count. Consider relaxing design constraints.</li>")
                    else:
                        content.append(f"<li style='margin-bottom: 5px; color: #27ae60;'><b>Status:</b> Sufficient probe density for this target region.</li>")
                        
                    content.append('</ul>')
                    content.append('</div>')
            
            content.append('</div>')
        else:
            content.append("<p>Required columns for regional coverage analysis are missing.</p>")
    else:
        content.append("<p>Results visualization features will be added based on protocol requirements.</p>")
    
    content.append('</div>')
    
    if script_lines:
        content.append('<script>')
        content.append('\n'.join(script_lines))
        content.append('</script>')
        
    return '\n'.join(content)

def _get_recommendations_section(df: pd.DataFrame, protocol: Dict[str, Any]) -> str:
    """Old recommendations section - now integrated into other sections."""
    return ""

def _get_details_section(df: pd.DataFrame) -> str:
    """Generate the detailed probe data table section."""
    content = ['<div class="section">', '<h2>Probe information table</h2>']
    
    total_rows = len(df)
    content.append(f'<p>Total {total_rows} probes. Use the search and pagination features below to explore the data.</p>')
    
    # Add download button
    content.append('''
    <div style="margin: 20px 0; text-align: right;">
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
    df_display = _prepare_df_for_display(df)
    content.append(df_display.to_html(index=False, table_id="probeDataTable", classes='display table table-striped', border=0))
    content.append('</div>')
    content.append('</div>')
    
    # Add DataTables initialization script
    content.append('''
    <script>
        $(document).ready( function () {
            $('#probeDataTable').DataTable({
                pageLength: 15,
                scrollX: true,
                order: [] // Disable initial sorting to keep original order
            });
        });
    </script>
    ''')
    
    return '\n'.join(content)


def _build_scientific_report_content(df: pd.DataFrame, protocol: Dict[str, Any], plot_data: Dict[str, str]) -> str:
    """Builds the full HTML content for the scientific report."""
    # Remove the old Analysis & Recommendations section call
    content = [
        _get_summary_section(df, protocol, plot_data),
        _get_quality_assessment_section(df, protocol),
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
