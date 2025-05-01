import pytest
from pathlib import Path
from uprobe.utils import reverse_complement


from uprobe.gen.probe import construct_probes 
from uprobe.workflow import parse_yaml, check_protocol_yaml
from uprobe.gen.probe import DAG
from uprobe.gen.probe import ExprProbe, TemplateProbe

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
    workdir = HERE / "data" / "probe_rca"
    import shutil
    if workdir.exists():
        shutil.rmtree(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    
    dag = DAG()
    dag.from_config(config, workdir) 
    
    print("dag.nodes names:",[node.name for node in dag.nodes])
    circle_probe = dag.get_node_by_name("circle_probe")
    assert isinstance(circle_probe, TemplateProbe) 
    assert circle_probe.template == "{part1}{part2}{part3}"
    assert len(circle_probe.deps) == 3 
    print("circle_probe.deps names:",[dep.name for dep in circle_probe.deps])     
    
    part1 = dag.get_node_by_name("circle_probe.part1")
    assert isinstance(part1, ExprProbe)
    print("part1.expr:",part1.expr)
    assert part1.expr == "rc(target_region[0:13])"
    assert len(part1.deps) == 0 
    
    part2 = dag.get_node_by_name("circle_probe.part2")
    assert isinstance(part2, TemplateProbe)
    assert part2.template == "{barcode1}N{barcode2}"
    assert len(part2.deps) == 2
    print("part2.deps names:",[dep.name for dep in part2.deps])   

    part3 = dag.get_node_by_name("circle_probe.part3")
    assert isinstance(part3, ExprProbe) 
    assert part3.expr == "rc(target_region[13:26])" 
    assert len(part3.deps) == 0

    barcode1 = dag.get_node_by_name("circle_probe.part2.barcode1")
    assert isinstance(barcode1, ExprProbe)
    assert barcode1.expr == "encoding[gene_id]['barcode1']"
    assert len(barcode1.deps) == 0

    assert "encoding" in barcode1.external_deps
    assert "gene_id" in barcode1.external_deps

    barcode2 = dag.get_node_by_name("circle_probe.part2.barcode2")
    assert isinstance(barcode2, ExprProbe)
    assert barcode2.expr == "encoding[gene_id]['barcode2']"
    assert len(barcode2.deps) == 0
    assert "encoding" in barcode2.external_deps
    assert "gene_id" in barcode2.external_deps

    amp_probe = dag.get_node_by_name("amp_probe")
    assert isinstance(amp_probe, TemplateProbe)
    assert amp_probe.template == "{part1}N{part2}"
    assert len(amp_probe.deps) == 2 

    amp_part1 = dag.get_node_by_name("amp_probe.part1")
    assert isinstance(amp_part1, ExprProbe)
    assert amp_part1.expr == "rc(circle_probe.part2.barcode2)" 
    assert len(amp_part1.deps) == 1
    assert amp_part1.deps[0].name == "circle_probe.part2.barcode2"

    amp_part2 = dag.get_node_by_name("amp_probe.part2")
    assert isinstance(amp_part2, ExprProbe)
    assert amp_part2.expr == "rc(target_region[-13:])" 
    assert len(amp_part2.deps) == 0 

    target_region="ATGAAGGCCTGCCGGTTATGAAGGCCTGCCGGTTATGAAG"
    gene_id="gene1" 
    encoding_dict = {
        "gene1": {
            "barcode1": "AAAATTTTTTTTAAGCA",
            "barcode2": "ATTTATTGCGATTTGGC"
        },
        "g42115": {
             "barcode1": "AAAATTTTTTTTAAGCA",
             "barcode2": "GGTTTTTTTTTTTTTTT"
        }
    }
    context = {
        "target_region": target_region,
        "gene_id": gene_id,
        "encoding": encoding_dict,
    }

    dag.run(context=context)

    assert circle_probe.done
    assert amp_probe.done
    assert part1.done
    assert part2.done
    assert part3.done
    assert barcode1.done
    assert barcode2.done
