import pytest
from pathlib import Path

# 假设 construct_probes 已从你实际的代码模块中导入
from uprobe.gen.probe import construct_probes  # 请替换成实际模块路径
from uprobe.workflow import parse_yaml, check_protocol_yaml
from uprobe.gen.probe import DAG

HERE = Path(__file__).parent

def fake_target_seqs():
    return [
        "ATGAAGGCCTGCCGGTTATGAAGGCCTGCCGGTTATGAAG",
        "ATGAAGGCCTGTTGGACGGGGGCCCAAATTTTTTATGAAG"
    ]
"""import pandas as pd
def test_constrct_probes():
    config = parse_yaml(HERE / "data" / "double_hyb_rca.yaml")
    check_protocol_yaml(config)
    target_seqs = fake_target_seqs()
    workdir = HERE / "data" / "workdir"
    workdir.mkdir(parents=True, exist_ok=True)
    probes = construct_probes(workdir, config, target_seqs)
    assert isinstance(probes, pd.DataFrame)
    circle_probe = 'GGCAGGCCTTCATAAACCCTTGGCCAGGGGAAAATTTCGGCCTTCATAACC'
    print(probes['circle_probe'][0])
    assert probes['circle_probe'][0] == circle_probe
    print(probes['amp_probe'][0])
    assert probes['amp_probe'][0] == 'CTTCATAACCGGCTGAAATTTTCCCCT'"""


def test_probe_dependencies():
    config = parse_yaml(HERE / "data" / "double_hyb_rca.yaml")
    check_protocol_yaml(config)
    workdir = HERE / "data" / "workdir"
    workdir.mkdir(parents=True, exist_ok=True)
    
    dag = DAG()
    dag.from_config(config, workdir)
    
    # Test circle_probe dependencies
    circle_probe = dag.get_node_by_name("circle_probe")
    assert circle_probe is not None
    assert len(circle_probe.deps) == 3 
    print("circle_probe.deps:",circle_probe.deps)      # part1, part2, part3
    assert any(dep.name == "circle_probe.part1" for dep in circle_probe.deps)
    assert any(dep.name == "circle_probe.part2" for dep in circle_probe.deps)
    assert any(dep.name == "circle_probe.part3" for dep in circle_probe.deps)
    
    # Test part2 dependencies
    part2 = dag.get_node_by_name("circle_probe.part2")
    assert part2 is not None
    assert len(part2.deps) == 2 
    print("part2.deps:",part2.deps)      # barcode1, barcode2
    assert any(dep.name == "circle_probe.part2.barcode1" for dep in part2.deps)
    assert any(dep.name == "circle_probe.part2.barcode2" for dep in part2.deps)
    
    # Test amp_probe dependencies
    amp_probe = dag.get_node_by_name("amp_probe")
    assert amp_probe is not None
    assert len(amp_probe.deps) == 2 
    print("amp_probe.deps:",amp_probe.deps)      # part1, part2
    assert any(dep.name == "amp_probe.part1" for dep in amp_probe.deps)
    assert any(dep.name == "amp_probe.part2" for dep in amp_probe.deps)
    
    # Test external dependencies
    barcode1 = dag.get_node_by_name("circle_probe.part2.barcode1")
    assert barcode1 is not None
    assert len(barcode1.deps) == 0
    assert len(barcode1.external_deps) == 2
    print("barcode1.external_deps:",barcode1.external_deps)  # target_region.gene_id and encoding
    assert "target_region.gene_id" in barcode1.external_deps
    assert "encoding" in barcode1.external_deps
    
    barcode2 = dag.get_node_by_name("circle_probe.part2.barcode2")
    assert barcode2 is not None
    assert len(barcode2.deps) == 0
    assert len(barcode2.external_deps) == 2
    print("barcode2.external_deps:",barcode2.external_deps)  # target_region.gene_id and encoding
    assert "target_region.gene_id" in barcode2.external_deps
    assert "encoding" in barcode2.external_deps
    
    # Test part1 external dependencies
    part1 = dag.get_node_by_name("circle_probe.part1")
    assert part1 is not None
    assert len(part1.deps) == 0
    print("part1.external_deps:",part1.external_deps)
    assert len(part1.external_deps) == 2  # target_region
    assert "target_region" in part1.external_deps
    
    # Test part3 external dependencies
    part3 = dag.get_node_by_name("circle_probe.part3")
    assert part3 is not None
    assert len(part3.deps) == 0
    print("part3.external_deps:",part3.external_deps)
    assert len(part3.external_deps) == 3  # target_region
    assert "target_region" in part3.external_deps

