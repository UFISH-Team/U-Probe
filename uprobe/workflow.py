import os
import typing as T
from pathlib import Path
import yaml

import pandas as pd

from .utils import get_logger
from .attributes import add_attributes
from .tools import  build_genome
from .gen.fun import generate_target_seqs
from .gen.probe import construct_probes
from .post_process import process


def parse_yaml(path: Path) -> dict:
    content = path.read_text(encoding="utf-8")
    res = yaml.load(content, Loader=yaml.FullLoader)
    return res


def check_protocol_yaml(res: dict):
    assert "genome" in res, "genome key not found"
    assert "name" in res, "name key not found"


def check_genome_yaml(res: dict):
    pass

def construct_workflow(
        protocol_yaml: Path,
        genomes_yaml: Path,
        output_csv: Path,
        workdir: Path = Path("."),
        ) -> T.Callable:
    log = get_logger("workflow")
    protocol = parse_yaml(protocol_yaml)
    check_protocol_yaml(protocol)
    genomes = parse_yaml(genomes_yaml)
    check_genome_yaml(genomes)
    genome_name = protocol['genome']
    genome = genomes[genome_name]
    fasta_path = Path(genome['fasta'])
    assert fasta_path.exists(), f"Genome fasta file not found: {fasta_path}"
    gtf_path = Path(genome['gtf'])
    assert gtf_path.exists(), f"Genome gtf file not found: {gtf_path}"
    genome = build_genome(genome)

    def workflow():
        os.chdir(workdir)
        log.info(protocol['name'])
        df_targets = generate_target_seqs(
            protocol["targets"],
            genome['fasta'],
            genome['gtf'],
            overlap=10,
            min_length=40,
            )
        seqs = df_targets["target_region"].to_list()
        probe_df = construct_probes(protocol, seqs)
        assert probe_df.shape[0] == df_targets.shape[0]
        df = pd.concat([df_targets, probe_df], axis=1)
        df = add_attributes(df, protocol, genome, workdir)
        df = process(df, protocol)
        print(df)
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