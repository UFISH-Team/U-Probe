from pathlib import Path
from uprobe.workflow import parse_yaml, check_probe_yaml, check_genome_yaml

HERE = Path(__file__).parent


def test_parse_yaml():
    path = HERE / "double_hyb_rca.yaml"
    res = parse_yaml(path)
    check_probe_yaml(res)
    assert res["name"] == "RCA Double Hybridization"
    assert res['genome'] == "hg38"
    path = HERE / "genomes.yaml"
    res = parse_yaml(path)
    check_genome_yaml(res)
