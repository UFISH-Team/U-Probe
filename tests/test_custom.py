import pytest
from pathlib import Path

from uprobe.gen.probe import construct_probes 
from uprobe.workflow import parse_yaml, check_protocol_yaml
from uprobe.gen.probe import DAG

HERE = Path(__file__).parent

target_region="ATGAAGGCCTGCCGGTTATGAAGGCCTGCCGGTTATGAAG"
gene_id="gene1" 
encoding_dict = {
    "gene1": {
        "BC2": "AAAATTTTTTTTAAGCA",
        "BC3": "ATTTATTGCGATTTGGC"
    },
    "g42115": {
            "BC2": "AAAATTTTTTTTAAGCA",
            "BC3": "GGTTTTTTTTTTTTTTT"
    }
}
context = {
    "target_region": target_region,
    "gene_id": gene_id,
    "encoding": encoding_dict,
}

'''
def test_probe_dependencies():
    config = parse_yaml(HERE / "data" / "probes.yaml")
    #check_protocol_yaml(config)
    workdir = HERE / "data" / "probe_custom_test"
    workdir.mkdir(parents=True, exist_ok=True)
    
    dag = DAG()
    dag.from_config(config, workdir)
    print("dag.nodes:",[node.name for node in dag.nodes])
    probe_1 = dag.get_node_by_name("probe_1")
    assert len(probe_1.deps) == 2
    print("probe_1.deps names:",[dep.name for dep in probe_1.deps])
    probe_1_part1 = dag.get_node_by_name("probe_1.part1")
    print("probe_1.part1.deps names:", [dep.name for dep in probe_1_part1.deps] if probe_1_part1 else "Node not found")
    print("probe_1.part1.external_deps:", probe_1_part1.external_deps if probe_1_part1 else "Node not found")
    dag.run(context=context)
'''

def test_construct_probes():
    config = parse_yaml(HERE / "data" / "probes.yaml")
    workdir = HERE / "data" / "probe_custom_test"
    workdir.mkdir(parents=True, exist_ok=True)
    construct_probes(workdir, config, context)


