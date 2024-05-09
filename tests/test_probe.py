import pandas as pd
from uprobe.gen.probe import construct_probes
from uprobe.workflow import parse_yaml, check_protocol_yaml
from pathlib import Path


HERE = Path(__file__).parent


def fake_target_seqs():
    return [
        "ATGAAGGCCTGCCGGTTATGAAGGCCTGCCGGTTATGAAGGCCTGCCGGTT",
        "GTGAGGGCCTGCCGGTTGTGAGGGCCTGCCGGTTGTGAGGGCCTGCCGGTT",
        "CTGAAGGCCGGCCGGTTCTGAAGGCCGGCCGGTTCTGAAGGCCGGCCGGTT",
    ]


def test_constrct_probes():
    config = parse_yaml(HERE / "double_hyb_rca.yaml")
    check_protocol_yaml(config)
    target_seqs = fake_target_seqs()
    probes = construct_probes(config, target_seqs)
    assert isinstance(probes, pd.DataFrame)
    assert probes.shape[0] == 3
    assert "circle_probe:part1" in probes.columns
    # ensure part1 length is 13
    assert all(probes["circle_probe:part1"].apply(len) == 13)
    assert "circle_probe:part2" in probes.columns
    assert "circle_probe:part3" in probes.columns
    # ensure part1 length is 13
    assert all(probes["circle_probe:part3"].apply(len) == 13)
    assert "amp_probe:part1" in probes.columns
    assert "amp_probe:part2" in probes.columns
