import os
import typing as T
from pathlib import Path
import pandas as pd

import yaml

from uprobe.utils import get_logger, gene_barcode
from uprobe.attributes import add_attributes
from uprobe.tools import  build_genome
from uprobe.gen.fun import generate_target_seqs
from uprobe.gen.probe_rca import construct_probes
from uprobe.process import post_process

log = get_logger(__name__)

def parse_yaml(path: Path) -> dict:
    content = path.read_text(encoding="utf-8")
    res = yaml.load(content, Loader=yaml.FullLoader)
    return res

def check_protocol_yaml(res: dict):
    print(res)
    assert "genome" in res, "genome key not found"
    assert "name" in res, "name key not found"

def construct_workflow(
        protocol_yaml: T.Union[Path, dict],
        genomes_yaml: T.Union[Path, dict],
        output_csv: Path,
        workdir: Path = Path("."),
        raw_results_csv: T.Optional[Path] = None,
        ) -> T.Callable:
    if isinstance(protocol_yaml, dict):
        protocol = protocol_yaml
    else:
        log.info("parsing protocol yaml.")
        protocol = parse_yaml(protocol_yaml)
        check_protocol_yaml(protocol)
    
    if isinstance(genomes_yaml, dict):
        genomes = genomes_yaml
    else:
        log.info("parsing genomes yaml.")
        genomes = parse_yaml(genomes_yaml)

    genome_name = protocol['genome']
    genome = genomes[genome_name]

    fasta_path = Path(genome['fasta'])
    assert fasta_path.exists(), f"genome fasta file not found: {fasta_path}"
    log.info(f"found genome fasta file: {fasta_path}")

    gtf_path = Path(genome['gtf'])
    assert gtf_path.exists(), f"Genome gtf file not found: {gtf_path}"
    log.info(f"found genome gtf file: {gtf_path}")

    log.info("building genome.")
    genome = build_genome(genome)

    def workflow():
        os.chdir(workdir)
        log.info(f"changed working directory to: {workdir}")
        log.info(f"running workflow: {protocol['name']}")
        
        log.info("generating target sequences.")
        df_targets = generate_target_seqs(
            protocol["targets"],
            genome['fasta'],
            genome['gtf'],
            overlap = protocol['extracts']['target_region']['overlap'],
            min_length=protocol['extracts']['target_region']['length'],
        )
        
        log.info("generating gene barcode dictionary.")
        barcode_dict = gene_barcode(protocol)
        df_targets['barcodes'] = df_targets['gene'].map(barcode_dict)

        seqs = df_targets['target_region'].to_list()
        barcodes = df_targets['barcodes'].tolist()

        log.info("constructing probes.")
        probe_df = construct_probes(protocol, seqs, barcodes)

        assert probe_df.shape[0] == df_targets.shape[0], "mismatch in number of targets and probes."
        
        #print(f"probe columns: {probe_df.columns}")
        #print(f"df columns: {df_targets.columns}")

        df = pd.merge(df_targets, probe_df, on='target_region', how='inner')
        df = add_attributes(df, protocol, genome, workdir)

        if raw_results_csv:
            log.info(f"saving raw results to csv: {workdir}/{raw_results_csv}")
            df.to_csv(workdir / raw_results_csv, index=False)
        
        log.info("post-processing the results.")
        df = post_process(df, protocol)

        if df.shape[0] == 0:
            log.warning("df is empty, no results.")
        else:
            # Drop all columns containing 'part' in their names
            part_columns = [col for col in df.columns if 'part' in col]
            df = df.drop(columns=part_columns)

            log.info(f"saving post-processed results to csv: {workdir}/{output_csv}")
            df.to_csv(workdir / output_csv, index=False)

    return workflow


if __name__ == "__main__":
    import fire
    def main(
            protocol_yaml: T.Union[Path, str, dict],
            genomes_yaml: T.Union[Path, str, dict],
            output_csv: str,
            workdir: str = "tests",
            raw_results_csv: T.Optional[str] = None): 
        workflow = construct_workflow(
            Path(protocol_yaml),
            Path(genomes_yaml),
            Path(output_csv),
            Path(workdir),
            Path(raw_results_csv) if raw_results_csv else None
        )
        workflow()
    fire.Fire(main)