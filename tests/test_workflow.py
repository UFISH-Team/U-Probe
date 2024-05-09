from pathlib import Path
from uprobe.workflow import (
    parse_yaml, check_protocol_yaml, check_genome_yaml,
    construct_workflow
)

HERE = Path(__file__).parent


def test_parse_yaml():
    path = HERE / "data" / "double_hyb_rca.yaml"
    res = parse_yaml(path)
    check_protocol_yaml(res)
    assert res["name"] == "RCA Double Hybridization"
    assert res['genome'] == "hg38"
    path = HERE / "data" / "genomes.yaml"
    res = parse_yaml(path)
    check_genome_yaml(res)


def test_construct_workflow():
    genomes_yaml = HERE / "data" / "genomes.yaml"
    protocol_yaml = HERE / "data" / "double_hyb_rca.yaml"
    construct_workflow(protocol_yaml, genomes_yaml, HERE)


def test_workflow():
    genomes_yaml = HERE / "data" / "genomes.yaml"
    protocol_yaml = HERE / "data" / "double_hyb_rca.yaml"
    workflow = construct_workflow(
        protocol_yaml, genomes_yaml,
        HERE / "output.probe.csv",
        ".")
    workflow()
