import pandas as pd
from uprobe.gen import construct_probes
from uprobe.workflow import parse_yaml, check_protocol_yaml
from pathlib import Path


HERE = Path(__file__).parent


def fake_target_seqs():
    return [
        "ATGAAGGCCTGCCGGTTATGAAGGCCTGCCGGTTATGAA",
        "ATGAAGGCCTGTTGGACGGGGGCCCAAATTTTTTATGAA"
    ]

def fake_barcodes():
    return [
        ("ATGAAG", "ATGAAG"),
        ("ATGAAG", "ATGAAG")
    ]


def test_constrct_probes():
    config = parse_yaml(HERE / "data" / "double_hyb_rca.yaml")
    check_protocol_yaml(config)
    target_seqs = fake_target_seqs()
    barcodes = fake_barcodes()
    probes = construct_probes(config, target_seqs, barcodes)
    assert isinstance(probes, pd.DataFrame)
    circle_probe = 'GGCAGGCCTTCATATGAAGAATGAAGGGCCTTCATAACC'
    assert probes['circle_probe'][0] == circle_probe
    amp_probe = 'TTCATAACCGGCATCTTCATT'
    assert probes['amp_probe'][0] == amp_probe

