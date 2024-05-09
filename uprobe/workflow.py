import os
import typing as T
from pathlib import Path
import yaml
from .utils import get_logger
from .attributes import add_attributes
from .tools.aligner import build_genome


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
        workdir: Path,
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
    log.log(f"Building genome {genome_name}")
    genome = build_genome(genome)

    def workflow():
        os.chdir(workdir)
        log.log(protocol['name'])

    return workflow
