"""
Report generation module for U-Probe.
"""
from .plot import generate_plot_report
from .html import save_html_report

__all__ = [
    'generate_plot_report', 
    'save_html_report'
]
