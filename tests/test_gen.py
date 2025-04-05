from uprobe.gen.genebars import generate_gene_dict
from pathlib import Path
from uprobe.workflow import parse_yaml

HERE = Path(__file__).parent


def test_generate_gene_dict():
    path = HERE / "data" / "double_hyb_rca.yaml"
    res = parse_yaml(path)

    gene_dict = generate_gene_dict(res)
    assert gene_dict['ZFY'] == ['AAACCCTTGGCC', 'GGGGAAAATTTC']