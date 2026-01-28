import time
import typing as T
from pathlib import Path

import pandas as pd
import yaml

from .attributes import add_attributes
from .gen.barcodes import quick_generate
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
        require_genome: bool = True
    ):

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.protocol = self._load_config(protocol_config)
        self.genomes = self._load_config(genomes_config)
        if require_genome:
            self.genome = self._validate_and_get_genome()
        else:
            self.genome = None
        self._generate_html = True 
        self._include_plots = True 
        self._embed_plots = True  
        self._csv_filename = None

    def _parse_targets(self) -> T.Tuple[T.List[str], T.Dict[str, str]]:
        """
        Parse targets into genome targets (names only) and direct targets (name: sequence).
        """
        targets = self.protocol.get("targets", [])
        genome_targets = []
        direct_targets = {}

        if isinstance(targets, dict):
            for name, seq in targets.items():
                if seq and isinstance(seq, str):
                    direct_targets[name] = seq
                else:
                    genome_targets.append(name)
        elif isinstance(targets, list):
            for item in targets:
                if isinstance(item, str):
                    genome_targets.append(item)
                elif isinstance(item, dict):
                    for name, seq in item.items():
                        if seq and isinstance(seq, str):
                            direct_targets[name] = seq
                        else:
                            genome_targets.append(name)
        genome_targets = list(dict.fromkeys(genome_targets))
        return genome_targets, direct_targets

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

    def quick_generate_barcodes(self, num_barcodes: int, length: int, **kwargs) -> T.List[str]:
        log.info(f"Quick generating {num_barcodes} barcodes of length {length}...")
        barcodes = quick_generate(num_barcodes, length, **kwargs)
        log.info(f"Generated {len(barcodes)} barcodes.")
        return barcodes

    def validate_targets(self, continue_on_invalid: bool = True) -> bool:
        genome_targets, direct_targets = self._parse_targets()
        
        if not genome_targets and not direct_targets:
            raise ValueError("No targets specified in the protocol.")
            
        log.info("Validating targets...")
        
        valid_genome_targets = []
        if genome_targets:
            gtf_path = Path(self.genome['gtf'])
            _, valid_list, invalid_list = validate_targets(genome_targets, gtf_path, DTF_NAME_FIX=True)
            
            if invalid_list:
                log.warning(f"Invalid targets found (not in genome): {invalid_list}")
                
            valid_genome_targets = valid_list
        
        # Reconstruct targets for protocol
        new_targets = []
        new_targets.extend(valid_genome_targets)
        for name, seq in direct_targets.items():
            new_targets.append({name: seq})
        self.protocol["targets"] = new_targets
        if not new_targets:
            log.error("No valid targets remaining after validation.")
            if not continue_on_invalid:
                raise ValueError("No valid targets remaining.")
            return False
        log.info(f"Target validation successful. Valid: {len(valid_genome_targets)} genome targets, {len(direct_targets)} custom sequences.")
        return True

    def generate_target_seqs(self) -> pd.DataFrame:
        log.info("Generating target region sequences...")
        extract_params = self.protocol['extracts']['target_region']
        genome_targets, direct_targets = self._parse_targets()
        dfs = []
        # 1. Process Genome Targets
        if genome_targets:
            log.info(f"Extracting {len(genome_targets)} targets from genome using source '{extract_params['source']}'...")
            try:
                df_genome = generate_target_seqs(
                    source=extract_params['source'],
                    targets=genome_targets,
                    fasta_path=self.genome['fasta'],
                    gtf_path=self.genome['gtf'],
                    min_length=extract_params['length'],
                    overlap=extract_params['overlap']
                )
                if not df_genome.empty:
                    dfs.append(df_genome)
                else:
                    log.warning("No sequences generated for genome targets.")
            except Exception as e:
                log.error(f"Failed to generate sequences for genome targets: {e}")  
        # 2. Process Direct Targets
        if direct_targets:
            log.info(f"Processing {len(direct_targets)} custom sequence targets...")
            min_length = extract_params['length']
            overlap = extract_params['overlap']
            data_list = []
            for target_name, seq in direct_targets.items():
                n = 1
                for i in range(0, len(seq) - min_length + 1, min_length - overlap):
                    tem = seq[i:i + min_length]
                    if len(tem) == min_length:
                        start = i + 1
                        end = i + min_length
                        probe_id = f"{target_name}_{n}"
                        n += 1
                        sub_region = f"{start}-{end}"
                        data_list.append([probe_id, target_name, sub_region, tem])
            
            df_direct = pd.DataFrame(data_list, columns=['probe_id', 'target', 'sub_region','target_region'])
            if not df_direct.empty:
                 df_direct['start'] = df_direct['sub_region'].apply(lambda x: int(x.split('-')[0]))
                 df_direct['end'] = df_direct['sub_region'].apply(lambda x: int(x.split('-')[1]))
                 # Add placeholders for genome-specific columns
                 df_direct['transcript_names'] = 'custom'
                 df_direct['n_trans'] = 1
                 df_direct['exon_name'] = '.' 
            if not df_direct.empty:
                dfs.append(df_direct)
            else:
                log.warning("No sequences generated from provided custom sequences (check length vs min_length).")

        if not dfs:
            log.error("No target sequences generated from any source.")
            return pd.DataFrame()
            
        df_final = pd.concat(dfs, ignore_index=True)
        if 'sub_region' not in df_final.columns or df_final['sub_region'].isnull().any():
            if 'start' in df_final.columns and 'end' in df_final.columns:
                mask = df_final['sub_region'].isna()
                df_final.loc[mask, 'sub_region'] = df_final.loc[mask].apply(
                    lambda row: f"{int(row['start'])}-{int(row['end'])}" if pd.notnull(row['start']) else None, 
                    axis=1
                )
        log.info(f"Total generated target sequences: {len(df_final)}")
        return df_final

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
        self._csv_filename = f"{name}_{time_str}.csv"
        if raw_csv:
            raw_path = self.output_dir / f"{name}_{time_str}_raw.csv"
            log.info(f"Saving raw results to {raw_path}")
            df_final.to_csv(raw_path, index=False)

        post_process_config = self.protocol.get('post_process', {})
        has_post_processing = any(post_process_config.get(key) for key in 
                                ['filters', 'sorts', 'remove_overlap', 'equal_space', 'avoid_otp'])
        
        if has_post_processing:
            log.info("Post-processing probes...")
            df_processed = post_process(df_final, self.protocol)
            
            if df_processed.empty:
                log.warning("No probes remaining after post-processing filters. Using raw data for final result.")
                output_path = self.output_dir / f"{name}_{time_str}.csv"
                log.info(f"Saving {df_final.shape[0]} raw probes to {output_path} (post-processing resulted in empty dataset)")
                df_final.to_csv(output_path, index=False)
                return df_final
            else:
                output_path = self.output_dir / f"{name}_{time_str}.csv"
                log.info(f"Saving {df_processed.shape[0]} processed probes to {output_path}")
                df_processed.to_csv(output_path, index=False)
                return df_processed
        else:
            log.info("No post-processing steps configured, using raw data as final result")
            output_path = self.output_dir / f"{name}_{time_str}.csv"
            log.info(f"Saving {df_final.shape[0]} probes to {output_path}")
            df_final.to_csv(output_path, index=False)
            return df_final

    def run_workflow(self, raw_csv: bool = False, continue_on_invalid_targets: bool = False, threads: int = 10) -> pd.DataFrame:      
        log.info("--- Starting U-Probe Workflow ---")
        
        # Check and install tools if needed
        from .utils import check_and_install_tools
        tools_to_check = set()
        
        # From genome config
        if self.genome:
            aligners = self.genome.get('align_index', [])
            for aligner in aligners:
                tools_to_check.add(aligner)
            if self.genome.get('jellyfish', False):
                tools_to_check.add('jellyfish')
                
        # From attributes
        if 'attributes' in self.protocol:
            for attr_name, attr_config in self.protocol['attributes'].items():
                if 'aligner' in attr_config:
                    tools_to_check.add(attr_config['aligner'])
        
        if tools_to_check:
            check_and_install_tools(list(tools_to_check))
            
        # 1. Build Genome Index (if needed)
        self.build_genome_index(threads=threads)
        # 2. Validate Targets(RNA)
        source = self.protocol['extracts']['target_region']['source']
        if source != 'genome':
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
        summary_config = self.protocol.get('summary', {})
        if summary_config.get('report_name') and not df_processed.empty:
            log.info("Generating final report with summary statistics...")
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
        
        try:
            from .process.summary import generate_summary_data
            summary_config = self.protocol.get('summary', {})
            if summary_config:
                log.info("Generating summary statistics for report...")
                summary_data = generate_summary_data(df_processed, summary_config)
                if hasattr(df_processed, 'attrs'):
                    df_processed.attrs['summary_data'] = summary_data
                else:
                    import tempfile
                    import pickle
                    import os
                    temp_dir = tempfile.gettempdir()
                    summary_file = os.path.join(temp_dir, 'uprobe_summary_data.pkl')
                    with open(summary_file, 'wb') as f:
                        pickle.dump(summary_data, f)
                    log.info(f"Summary data saved to temporary file: {summary_file}")
            plot_data = {}
            if include_plots:
                try:
                    plot_result = generate_plot_report(
                        df_processed, 
                        self.protocol, 
                        self.output_dir, 
                        report_suffix,
                        save_files=False, 
                        return_base64=True 
                    )
                    
                    plot_data = plot_result.get("plot_data", {}) 
                except Exception as e:
                    log.error(f"Failed to generate plots: {e}")
            protocol_name = self.protocol.get('name', 'probes')
            time_str = time.strftime("%Y%m%d_%H%M%S")
            html_output_path = self.output_dir / f"{protocol_name}_report{report_suffix}_{time_str}.html"
            summary_config = self.protocol.get('summary', {})
            template_type = summary_config.get('report_name', 'scientific_report')
            
            html_path = save_html_report(
                df_processed, 
                self.protocol, 
                html_output_path,
                template_type=template_type,
                plot_data=plot_data,
                csv_filename=self._csv_filename
            )
            
            if html_path:
                html_paths.append(html_path)
                log.info(f"HTML report generated: {html_path}")
                    
        except Exception as e:
            log.error(f"Failed to generate HTML report: {e}")
        
        log.info(f"Report generation completed: {len(html_paths)} HTML reports")
        return {"html_reports": html_paths}
