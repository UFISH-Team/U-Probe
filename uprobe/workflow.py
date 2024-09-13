import os
import typing as T
from pathlib import Path
import yaml

import pandas as pd

from uprobe.utils import get_logger
from uprobe.gen.geneldict import generate_gene_dict
from uprobe.attributes import add_attributes
from uprobe.tools import  build_genome
from uprobe.gen.fun import generate_target_seqs
from uprobe.gen.probe import construct_probes
from uprobe.process import post_process
from uprobe.utils import get_logger

log = get_logger(__name__)

def parse_yaml(path: Path) -> dict:
    content = path.read_text(encoding="utf-8")
    res = yaml.load(content, Loader=yaml.FullLoader)
    return res


def check_protocol_yaml(res: dict):
    assert "genome" in res, "genome key not found"
    assert "name" in res, "name key not found"


def construct_workflow(
        protocol_yaml: Path,
        genomes_yaml: Path,
        output_csv: Path,
        workdir: Path = Path("."),
        ) -> T.Callable:
    
    log.info("parsing protocol yaml.")
    protocol = parse_yaml(protocol_yaml)
    check_protocol_yaml(protocol)
    
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
            overlap=10,
            min_length=40,
        )
        
        log.info("generating gene barcode dictionary.")
        barcode_dict = generate_gene_dict(protocol)
        df_targets['barcodes'] = df_targets['gene'].map(barcode_dict)

        seqs = df_targets['target_region'].to_list()
        barcodes = df_targets['barcodes'].tolist()

        log.info("constructing probes.")
        probe_df = construct_probes(protocol, seqs, barcodes)

        assert probe_df.shape[0] == df_targets.shape[0], "mismatch in number of targets and probes."
        
        print(f"probe: {probe_df.columns}")
        print(f"df: {df_targets.columns}")
        log.info("merging target sequences with probe data.")
        df = pd.merge(df_targets, probe_df, on='target_region', how='inner')
        
        log.info("adding attributes to the DataFrame.")
        df = add_attributes(df, protocol, genome, workdir)
        
        log.info("post-processing the DataFrame.")
        df = post_process(df, protocol)

        if df.shape[0] == 0:
            log.warning("dataFrame is empty, no results.")
        else:
            log.info("dropping unnecessary columns from the dataFrame.")
            df = df.drop(columns=['circle_probe:part1', 'circle_probe:part2', 'circle_probe:part3',
                                  'amp_probe:part1', 'amp_probe:part2'])

            log.info(f"saving results to csv: {output_csv}")
            df.to_csv(output_csv, index=False)

    return workflow


if __name__ == "__main__":
    import fire
    def main(
            protocol_yaml: str,
            genomes_yaml: str,
            output_csv: str,
            workdir: str = "/home/qzhang/U-Probe/tests"):
        workflow = construct_workflow(
            Path(protocol_yaml),
            Path(genomes_yaml),
            Path(output_csv),
            Path(workdir)
        )
        workflow()
    fire.Fire(main)