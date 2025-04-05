from uprobe.utils import gene_barcode
from pathlib import Path
from uprobe.workflow import parse_yaml

HERE = Path(__file__).parent


def test_gene_barcode():
    path = HERE / "data" / "double_hyb_rca.yaml"
    res = parse_yaml(path)

    gene_dict = gene_barcode(res)
    print(gene_dict)
    assert gene_dict['g42179'] == ('AAAATTTTTTTTAAGCA', 'GGTTTTTTTTTTTTTTT')