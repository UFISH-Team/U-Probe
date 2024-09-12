from uprobe.gen.fun import get_exon_seq
from pathlib import Path

HERE = Path(__file__).parent

fa = HERE / "data" / "hg38" / "hg38.fa"
gtf = HERE / "data" / "hg38" / "hg38.gtf"
genes = ['HSFY3P', 'ZFY']

def test_get_exon_seq():

    get_exon_seq(genes, fa, gtf)
    
    