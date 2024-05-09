from uprobe.gen.fun import exon_cut

def test_exon_cut():
    targetseqs = ['SRY', 'RPS4Y1']
    data = exon_cut(targetseqs, './Y.fasta', './Y.gtf')
    data.to_csv('exon_cut.csv', index=False)
    assert data.shape[0] == 41