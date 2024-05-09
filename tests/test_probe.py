import pandas as pd
from uprobe.gen.probe import construct_probes
from uprobe.workflow import parse_yaml, check_probe_yaml
from pathlib import Path


HERE = Path(__file__).parent


def fake_target_seqs():
    return [
        "ATGAAGGCCTGCCGGTTATGAAGGCCTGCCGGTTATGAAG",
        "ATGAAGGCCTGTTGGACGGGGGCCCAAATTTTTTATGAAG"
    ]


def test_constrct_probes():
    config = parse_yaml(HERE / "double_hyb_rca.yaml")
    check_probe_yaml(config)
    target_seqs = fake_target_seqs()
    probes = construct_probes(config, target_seqs)
    assert isinstance(probes, pd.DataFrame)
    circle_probe = 'GGCAGGCCTTCATAAACCCTTGGCCAGGGGAAAATTTCGGCCTTCATAACC'
    print(probes['circle_probe'][0])
    assert probes['circle_probe'][0] == circle_probe
    print(probes['amp_probe'][0])
    assert probes['amp_probe'][0] == 'CTTCATAACCGGCTGAAATTTTCCCC'

