"""
HTML report generation utilities for U-Probe.
直接生成美观简洁的HTML报告，不依赖markdown转换。
"""
import base64
import io
from pathlib import Path
from typing import Dict, List
import pandas as pd
from datetime import datetime
from ..utils import get_logger

logger = get_logger(__name__)

def generate_modern_css() -> str:
    """Generate modern CSS styles for the HTML report."""
    return """
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }
        
        .report-container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
            position: relative;
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse"><path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="1"/></pattern></defs><rect width="100" height="100" fill="url(%23grid)"/></svg>') repeat;
            z-index: 1;
        }
        
        .header-content {
            position: relative;
            z-index: 2;
        }
        
        .header h1 {
            font-size: 2.5em;
            font-weight: 700;
            margin-bottom: 10px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        
        .header .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
            font-weight: 300;
        }
        
        .content {
            padding: 40px;
        }
        
        .overview-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        
        .overview-card {
            background: linear-gradient(135deg, #f8f9ff 0%, #e8f4f8 100%);
            border-radius: 15px;
            padding: 30px 25px;
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            border: 1px solid rgba(102, 126, 234, 0.1);
        }
        
        .overview-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .overview-card .icon {
            width: 60px;
            height: 60px;
            margin: 0 auto 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 24px;
            font-weight: bold;
        }
        
        .overview-card h3 {
            color: #2c3e50;
            font-size: 1.1em;
            margin-bottom: 10px;
            font-weight: 600;
        }
        
        .overview-card .value {
            font-size: 2.2em;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 5px;
        }
        
        .overview-card .label {
            color: #7f8c8d;
            font-size: 0.9em;
        }
        
        .section {
            margin: 40px 0;
            background: #fff;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.05);
        }
        
        .section-title {
            font-size: 1.8em;
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 3px solid #667eea;
            display: flex;
            align-items: center;
            font-weight: 600;
        }
        
        .section-title::before {
            content: '';
            width: 8px;
            height: 8px;
            background: #667eea;
            border-radius: 50%;
            margin-right: 15px;
        }
        
        .guide-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        
        .guide-item {
            background: linear-gradient(135deg, #f8f9ff 0%, #e8f4f8 100%);
            border-radius: 12px;
            padding: 25px;
            border-left: 5px solid #667eea;
        }
        
        .guide-item h4 {
            color: #2c3e50;
            font-size: 1.2em;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
        }
        
        .guide-item h4::before {
            content: '✓';
            color: #27ae60;
            font-weight: bold;
            margin-right: 10px;
            background: rgba(39, 174, 96, 0.1);
            padding: 5px;
            border-radius: 50%;
            width: 25px;
            height: 25px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8em;
        }
        
        .guide-item p {
            color: #555;
            line-height: 1.6;
        }
        
        .parameters-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.05);
        }
        
        .parameters-table th {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 15px;
            text-align: left;
            font-weight: 600;
        }
        
        .parameters-table td {
            padding: 15px;
            border-bottom: 1px solid #f1f3f4;
        }
        
        .parameters-table tr:hover {
            background: #f8f9ff;
        }
        
        .parameter-name {
            font-family: 'Monaco', 'Consolas', monospace;
            font-weight: 600;
            color: #2c3e50;
        }
        
        .parameter-range {
            color: #27ae60;
            font-weight: 600;
        }
        
        .plot-container {
            background: #fff;
            border-radius: 15px;
            padding: 30px;
            margin: 20px 0;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.05);
        }
        
        .plot-title {
            font-size: 1.3em;
            color: #2c3e50;
            margin-bottom: 20px;
            font-weight: 600;
        }
        
        .plot-image {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .action-buttons {
            display: flex;
            gap: 20px;
            margin: 30px 0;
            flex-wrap: wrap;
            justify-content: center;
        }
        
        .action-button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 30px;
            border-radius: 25px;
            text-decoration: none;
            font-weight: 600;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            display: flex;
            align-items: center;
            gap: 10px;
            cursor: pointer;
        }
        
        .action-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
            color: white;
            text-decoration: none;
        }
        
        .footer {
            background: #f8f9fa;
            padding: 30px;
            text-align: center;
            color: #7f8c8d;
            border-top: 1px solid #e9ecef;
        }
        
        .alert {
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            border-left: 5px solid;
        }
        
        .alert-info {
            background: #e8f4f8;
            border-left-color: #17a2b8;
            color: #0c5460;
        }
        
        .alert-warning {
            background: #fff3cd;
            border-left-color: #ffc107;
            color: #856404;
        }
        
        .alert-success {
            background: #d4edda;
            border-left-color: #28a745;
            color: #155724;
        }
        
        @media (max-width: 768px) {
            .overview-grid {
                grid-template-columns: 1fr;
            }
            
            .guide-grid {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .content {
                padding: 20px;
            }
            
            .action-buttons {
                flex-direction: column;
                align-items: center;
            }
        }
    </style>
    """

def generate_html_report(title: str, content: str, custom_css: str = "") -> str:
    """Generate a complete HTML document with modern styling."""
    css = generate_modern_css() + custom_css
    
    html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {css}
</head>
<body>
    {content}
</body>
</html>"""
    return html_template

def get_protocol_type(df: pd.DataFrame, protocol: Dict) -> str:
    """Detect protocol type based on data columns and configuration."""
    extract_source = protocol.get('extracts', {}).get('target_region', {}).get('source', '')
    if extract_source == 'exon':
        return 'RNA'
    elif extract_source == 'genome':
        return 'DNA'
    
    rna_indicators = ['transcript', 'exon_rank', 'transcript_name']
    dna_indicators = ['kmerCount', 'NC_']
    columns = df.columns.tolist()
    
    if any(indicator in ' '.join(columns) for indicator in rna_indicators):
        return 'RNA'
    elif any(indicator in ' '.join(columns) for indicator in dna_indicators):
        return 'DNA'
    
    return 'Unknown'

def generate_overview_section(df: pd.DataFrame, protocol: Dict) -> str:
    """Generate overview statistics section."""
    protocol_type = get_protocol_type(df, protocol)
    
    total_probes = len(df)
    
    # Calculate key metrics
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
    gc_cols = [col for col in numeric_cols if 'gcContent' in col]
    tm_cols = [col for col in numeric_cols if 'tm' in col]
    
    avg_gc = df[gc_cols[0]].mean() if gc_cols else 0
    avg_tm = df[tm_cols[0]].mean() if tm_cols else 0
    
    # Count unique targets
    target_cols = ['gene', 'target', 'transcript']
    unique_targets = 0
    for col in target_cols:
        if col in df.columns:
            unique_targets = df[col].nunique()
            break
    
    return f"""
    <div class="overview-grid">
        <div class="overview-card">
            <div class="icon">🧬</div>
            <h3>总探针数量</h3>
            <div class="value">{total_probes:,}</div>
            <div class="label">个探针序列</div>
        </div>
        <div class="overview-card">
            <div class="icon">🎯</div>
            <h3>靶标数量</h3>
            <div class="value">{unique_targets}</div>
            <div class="label">个独特靶标</div>
        </div>
        <div class="overview-card">
            <div class="icon">⚗️</div>
            <h3>协议类型</h3>
            <div class="value">{protocol_type}</div>
            <div class="label">探针设计</div>
        </div>
        <div class="overview-card">
            <div class="icon">🌡️</div>
            <h3>平均Tm值</h3>
            <div class="value">{avg_tm:.1f}°C</div>
            <div class="label">退火温度</div>
        </div>
    </div>
    """

def generate_selection_guide_section(protocol_type: str) -> str:
    """Generate probe selection guide section."""
    common_guides = [
        {
            "title": "GC含量筛选",
            "content": "选择GC含量在40-80%之间的探针，确保最佳的杂交效率和稳定性。过低或过高的GC含量都会影响探针性能。"
        },
        {
            "title": "退火温度优化", 
            "content": "根据实验条件选择合适的Tm值范围（通常35-44°C）。相近的Tm值有助于实现一致的杂交条件。"
        },
        {
            "title": "特异性评估",
            "content": "优先选择映射基因数量较少的探针（≤5个），降低非特异性结合的风险，提高检测准确性。"
        },
        {
            "title": "二级结构检查",
            "content": "选择折叠得分较低的探针，避免自身互补配对形成二级结构，影响杂交效率。"
        }
    ]
    
    if protocol_type == 'RNA':
        specific_guides = [
            {
                "title": "转录本覆盖",
                "content": "对于多异构体基因，建议选择覆盖组成型外显子的探针，确保检测的一致性和可靠性。"
            },
            {
                "title": "外显子选择",
                "content": "优先选择位于功能重要外显子的探针，避开剪接变异频繁的区域。"
            }
        ]
        common_guides.extend(specific_guides)
    
    elif protocol_type == 'DNA':
        specific_guides = [
            {
                "title": "基因组覆盖",
                "content": "确保探针在目标区域内均匀分布，获得完整的基因组覆盖信息。"
            },
            {
                "title": "k-mer唯一性",
                "content": "选择k-mer计数较低的探针，提高基因组特异性，减少交叉反应。"
            }
        ]
        common_guides.extend(specific_guides)
    
    guide_html = ""
    for guide in common_guides:
        guide_html += f"""
        <div class="guide-item">
            <h4>{guide['title']}</h4>
            <p>{guide['content']}</p>
        </div>
        """
    
    return f"""
    <div class="section">
        <h2 class="section-title">探针筛选指南</h2>
        <div class="guide-grid">
            {guide_html}
        </div>
    </div>
    """

def generate_parameters_section() -> str:
    """Generate recommended parameters section."""
    parameters = [
        {"name": "GC含量", "range": "40% - 80%", "description": "最佳杂交稳定性"},
        {"name": "退火温度", "range": "35°C - 44°C", "description": "实验条件兼容性"},
        {"name": "映射基因数", "range": "≤ 5", "description": "特异性保证"},
        {"name": "自匹配得分", "range": "越低越好", "description": "避免自互补"},
        {"name": "折叠得分", "range": "越低越好", "description": "减少二级结构"},
        {"name": "k-mer计数", "range": "越低越好", "description": "基因组唯一性"}
    ]
    
    table_rows = ""
    for param in parameters:
        table_rows += f"""
        <tr>
            <td class="parameter-name">{param['name']}</td>
            <td class="parameter-range">{param['range']}</td>
            <td>{param['description']}</td>
        </tr>
        """
    
    return f"""
    <div class="section">
        <h2 class="section-title">推荐参数范围</h2>
        <table class="parameters-table">
            <thead>
                <tr>
                    <th>参数</th>
                    <th>推荐范围</th>
                    <th>说明</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
    </div>
    """

def generate_plots_section(plot_data: Dict[str, str]) -> str:
    """Generate plots section with embedded images."""
    if not plot_data:
        return ""
    
    plot_descriptions = {
        "quality_metrics": {
            "title": "质量指标分布",
            "description": "显示探针各项质量指标的统计分布，帮助识别数据范围和异常值"
        },
        "correlation_matrix": {
            "title": "参数相关性矩阵", 
            "description": "展示不同参数之间的相关关系，指导探针筛选策略"
        },
        "genomic_coverage": {
            "title": "基因组覆盖分布",
            "description": "DNA探针在目标基因组区域的空间分布情况"
        },
        "transcript_coverage": {
            "title": "转录本覆盖分析",
            "description": "RNA探针在不同转录本和外显子上的分布模式"
        }
    }
    
    plots_html = ""
    for plot_name, base64_data in plot_data.items():
        plot_info = plot_descriptions.get(plot_name, {"title": plot_name, "description": ""})
        plots_html += f"""
        <div class="plot-container">
            <div class="plot-title">{plot_info['title']}</div>
            <p style="color: #7f8c8d; margin-bottom: 20px;">{plot_info['description']}</p>
            <img src="{base64_data}" alt="{plot_info['title']}" class="plot-image" />
        </div>
        """
    
    return f"""
    <div class="section">
        <h2 class="section-title">数据可视化分析</h2>
        {plots_html}
    </div>
    """

def generate_action_buttons_section() -> str:
    """Generate action buttons section."""
    return """
    <div class="section">
        <h2 class="section-title">下一步操作</h2>
        <div class="alert alert-info">
            <strong>💡 使用建议：</strong> 根据上述指南筛选高质量探针，建议优先考虑特异性和温度一致性。
        </div>
        <div class="action-buttons">
            <div class="action-button" onclick="window.print()">
                🖨️ 打印报告
            </div>
            <div class="action-button" onclick="alert('请在数据表格中应用筛选条件')">
                🔍 开始筛选
            </div>
            <div class="action-button" onclick="alert('请参考参数范围进行排序')">
                📊 排序优化
            </div>
        </div>
        <div class="alert alert-warning">
            <strong>⚠️ 重要提醒：</strong> 所有计算结果仅供参考，实际使用前请进行实验验证。
        </div>
    </div>
    """

def generate_complete_html_report(df: pd.DataFrame, protocol: Dict, plot_data: Dict[str, str] = None) -> str:
    """Generate a complete, modern HTML report directly without markdown."""
    protocol_name = protocol.get('name', '探针设计')
    current_time = datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')
    
    # Generate content sections
    overview_section = generate_overview_section(df, protocol)
    protocol_type = get_protocol_type(df, protocol)
    guide_section = generate_selection_guide_section(protocol_type)
    parameters_section = generate_parameters_section()
    plots_section = generate_plots_section(plot_data or {})
    actions_section = generate_action_buttons_section()
    
    content = f"""
    <div class="report-container">
        <div class="header">
            <div class="header-content">
                <h1>U-Probe 探针分析报告</h1>
                <div class="subtitle">{protocol_name} • {current_time}</div>
            </div>
        </div>
        
        <div class="content">
            {overview_section}
            {guide_section}
            {parameters_section}
            {plots_section}
            {actions_section}
        </div>
        
        <div class="footer">
            <p>报告由 U-Probe v1.0 自动生成 • 数据仅供研究使用</p>
        </div>
    </div>
    """
    
    return generate_html_report(f"U-Probe 报告 - {protocol_name}", content)

def save_html_report(df: pd.DataFrame, protocol: Dict, output_path: Path, plot_data: Dict[str, str] = None) -> Path:
    """Generate and save HTML report to file."""
    
    try:
        html_content = generate_complete_html_report(df, protocol, plot_data)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to generate HTML report: {e}")
        return None
