"""
API for U-Probe.
"""
import time
import typing as T
from pathlib import Path

import pandas as pd
import yaml

from .attributes import add_attributes
from .gen.barcodes import generate_barcodes_from_config
from .gen.fun import generate_target_seqs, validate_targets
from .gen.probe import construct_probes
from .process import post_process
from .report import generate_plot_report
from .report.html import save_html_report

from .tools import build_genome
from .utils import get_logger

log = get_logger(__name__)


class UProbeAPI:
    def __init__(
        self,
        protocol_config: T.Union[Path, dict],
        genomes_config: T.Union[Path, dict],
        output_dir: Path,
    ):

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.protocol = self._load_config(protocol_config)
        self.genomes = self._load_config(genomes_config)
        self.genome = self._validate_and_get_genome()
        # Report generation preferences (根据用户要求默认改为HTML)
        self._generate_pdf = False  # 默认不生成PDF
        self._generate_html = True  # 默认生成HTML 
        self._include_plots = True  # 默认包含图表
        self._embed_plots = True  # 默认将图表嵌入HTML而不单独保存

    def _load_config(self, config: T.Union[Path, dict]) -> dict:
        if isinstance(config, Path):
            return yaml.safe_load(config.read_text(encoding="utf-8"))
        return config

    def _validate_and_get_genome(self) -> dict:
        genome_name = self.protocol.get('genome')
        if not genome_name or genome_name not in self.genomes:
            raise ValueError(f"Genome '{genome_name}' not found in genomes configuration.")
        genome = self.genomes[genome_name]
        for key in ['fasta', 'gtf']:
            if key not in genome:
                raise ValueError(f"'{key}' not specified for genome '{genome_name}'.")
            path = Path(genome[key])
            if not path.exists():
                raise IOError(f"Genome file not found: {path}")
        log.info(f"Using FASTA: {genome['fasta']} and GTF: {genome['gtf']}")
        return genome

    def build_genome_index(self, threads: int = 10):
        log.info("Building genome index...")
        build_genome(self.genome, threads=threads)
        log.info("Genome index building completed.")

    def generate_barcodes(self) -> T.Dict[str, T.List[str]]:
        log.info("Generating barcodes...")
        barcode_sets = generate_barcodes_from_config(self.protocol, self.output_dir)
        log.info(f"Generated {len(barcode_sets)} barcode set(s).")
        return barcode_sets
    
    def validate_targets(self, continue_on_invalid: bool = False) -> bool:
        targets = self.protocol.get("targets", [])
        if not targets:
            raise ValueError("No targets specified in the protocol.")
        log.info("Validating targets...")
        gtf_path = Path(self.genome['gtf'])
        valid, valid_targets, invalid_targets = validate_targets(targets, gtf_path, DTF_NAME_FIX=True)
        if not valid:
            error_msg = f"Invalid targets found: {invalid_targets}"
            if not continue_on_invalid:
                raise ValueError(error_msg)
            log.warning(f"{error_msg}. Continuing with valid targets as requested.")
            self.protocol["targets"] = valid_targets
            if not valid_targets:
                log.error("No valid targets remaining after validation.")
                return False
        log.info("Target validation successful.")
        return True

    def generate_target_seqs(self) -> pd.DataFrame:
        log.info("Generating target region sequences...")
        extract_params = self.protocol['extracts']['target_region']      
        df_targets = generate_target_seqs(
            source=extract_params['source'],
            targets=self.protocol["targets"],
            fasta_path=self.genome['fasta'],
            gtf_path=self.genome['gtf'],
            min_length=extract_params['length'],
            overlap=extract_params['overlap']
        )
        if df_targets.empty:
            log.error("No target sequences generated. Check target definitions and extraction parameters.")
        return df_targets

    def construct_probes(self, df_targets: pd.DataFrame) -> pd.DataFrame:
        log.info("Constructing probes...")
        contexts = [
            {
                "target_region": row['target_region'],
                "target": row.get('target') or row.get('gene'),
                "encoding": self.protocol['encoding'],
            }
            for _, row in df_targets.iterrows()
        ]
        probe_df = construct_probes(self.protocol, contexts)
        if probe_df.empty:
            log.error("No probes were constructed. Check probe construction parameters.")
        else:
            log.info(f"Successfully generated {probe_df.shape[0]} initial probes.")
        return probe_df

    def post_process_probes(self, df_probes: pd.DataFrame, raw_csv: bool = False) -> pd.DataFrame:
        log.info("Adding attributes to probes...")
        df_final = add_attributes(df_probes, self.protocol, self.genome)
        time_str = time.strftime("%Y%m%d_%H%M%S")
        name = self.protocol.get("name", "probes")
        if raw_csv:
            raw_path = self.output_dir / f"{name}_{time_str}_raw.csv"
            log.info(f"Saving raw results to {raw_path}")
            df_final.to_csv(raw_path, index=False)
            # Generate report for raw data if configured
            if self.protocol.get('report') and not df_final.empty:
                log.info("Generating report for raw data...")
                self.generate_report(df_final, 
                                   include_plots=self._include_plots,
                                   report_suffix="_raw", 
                                   generate_html=self._generate_html,
                                   embed_plots=self._embed_plots)
        log.info("Post-processing probes...")
        df_processed = post_process(df_final, self.protocol)       
        if df_processed.empty:
            log.warning("No probes remaining after post-processing filters.")
        else:
            output_path = self.output_dir / f"{name}_{time_str}.csv"
            log.info(f"Saving {df_processed.shape[0]} processed probes to {output_path}")
            df_processed.to_csv(output_path, index=False)        
        return df_processed

    def run_workflow(self, raw_csv: bool = False, continue_on_invalid_targets: bool = False, threads: int = 10) -> pd.DataFrame:      
        log.info("--- Starting U-Probe Workflow ---")
        # 1. Build Genome Index (if needed)
        self.build_genome_index(threads=threads)
        # 2. Validate Targets(RNA)
        if self.protocol['extracts']['target_region']['source'] == 'genome':
            pass
        else:
            if not self.validate_targets(continue_on_invalid=continue_on_invalid_targets):
                log.error("Workflow halted due to target validation failure.")
                return pd.DataFrame()        
        # 3. Generate Target Region Sequences
        df_targets = self.generate_target_seqs()
        if df_targets.empty:
            return pd.DataFrame()
        # 4. Construct Probes
        df_probes = self.construct_probes(df_targets)
        if df_probes.empty:
            return pd.DataFrame()
        # 5. Post-process
        df_combined = pd.concat([df_targets.reset_index(drop=True), df_probes.reset_index(drop=True)], axis=1)
        df_processed = self.post_process_probes(df_combined, raw_csv=raw_csv)
        # 6. Generate Report (if configured)
        if self.protocol.get('report') and not df_processed.empty:
            self.generate_report(df_processed, 
                               include_plots=self._include_plots,
                               generate_html=self._generate_html,
                               embed_plots=self._embed_plots)
        log.info("--- U-Probe Workflow Completed ---")
        return df_processed

    def generate_report(self, df_processed: pd.DataFrame, include_plots: bool = True, report_suffix: str = "", generate_html: bool = True, embed_plots: bool = True) -> T.Dict[str, T.List[Path]]:
        """
        Args:
            df_processed: DataFrame with probe data
            include_plots: Whether to include visualization plots
            report_suffix: Suffix to add to report filenames (e.g. "_raw")
            generate_html: Whether to generate HTML reports (always True now)
            embed_plots: If True, embed plots in HTML (not save separately)
        """
        if df_processed.empty:
            log.warning("No probe data available for report generation")
            return {"html_reports": []}
        
        html_paths = []
        
        # Get report configuration
        report_config = self.protocol.get('report', [])
        
        if 'base_info' in report_config:
            try:
                # Handle plots first
                plot_data = {}
                if 'plot' in report_config and include_plots:
                    try:
                        # Generate plots as base64 data for embedding
                        plot_result = generate_plot_report(
                            df_processed, 
                            self.protocol, 
                            self.output_dir, 
                            report_suffix,
                            save_files=False,  # Don't save plot files
                            return_base64=True # Return base64 data for embedding
                        )
                        
                        plot_data = plot_result.get("plot_data", {}) 
                    except Exception as e:
                        log.error(f"Failed to generate plots: {e}")
                
                # Generate HTML report with embedded plots
                protocol_name = self.protocol.get('name', 'probes')
                time_str = time.strftime("%Y%m%d_%H%M%S")
                html_output_path = self.output_dir / f"{protocol_name}_report{report_suffix}_{time_str}.html"
                
                html_path = save_html_report(
                    df_processed, 
                    self.protocol, 
                    html_output_path,
                    plot_data=plot_data
                )
                
                if html_path:
                    html_paths.append(html_path)
                    log.info(f"HTML report generated: {html_path}")
                        
            except Exception as e:
                log.error(f"Failed to generate HTML report: {e}")
        
        log.info(f"Report generation completed: {len(html_paths)} HTML reports")
        return {"html_reports": html_paths}
