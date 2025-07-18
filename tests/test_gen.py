import pytest
from pathlib import Path
import yaml  # 需要导入 yaml
from uprobe.gen.probe import construct_probes
from uprobe.utils import gene_barcode
from uprobe.workflow import parse_yaml

HERE = Path(__file__).parent


def test_gene_barcode():
    path = HERE / "data" / "double_hyb_rca.yaml"
    res = parse_yaml(path)

    gene_dict = gene_barcode(res)
    print(gene_dict)
    assert gene_dict['g42179'] == ('AAAATTTTTTTTAAGCA', 'GGTTTTTTTTTTTTTTT')


@pytest.fixture
def sample_config():
    """加载示例配置文件"""
    path = HERE / "data" / "double_hyb_rca.yaml"
    return parse_yaml(path)

@pytest.fixture
def sample_target_fasta(tmp_path):
    """创建一个临时的目标序列FASTA文件"""
    fasta_content = """>target1|gene1|info=abc
AGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCTAGCT
>target2|gene2|info=xyz
CGTACGTACGTACGTACGTACGTACGTACGTACGTACGTA
"""
    fasta_path = tmp_path / "target_seqs.fa"
    fasta_path.write_text(fasta_content)
    return fasta_path

def test_construct_probes(tmp_path, sample_config, sample_target_fasta):
    """测试 construct_probes 函数"""
    workdir = tmp_path / "probes_output"
    workdir.mkdir()

    # 为了简化测试，我们可以修改配置，只处理一个 target
    sample_config['targets'] = ['target1']
    # 确保 encoding 和 barcode_set 存在于配置中 (double_hyb_rca.yaml 应该有)
    assert 'encoding' in sample_config
    assert 'barcode_set' in sample_config

    results = construct_probes(workdir, sample_config, sample_target_fasta)

    assert 'target1' in results
    target_dag = results['target1']

    # 检查是否生成了预期的输出文件
    target1_dir = workdir / 'target1'
    assert (target1_dir / "circle_probe.out").exists()
    assert (target1_dir / "amp_probe.out").exists()
    assert (target1_dir / "circle_probe.part1.out").exists()
    assert (target1_dir / "circle_probe.part2.barcode1.out").exists() # 检查叶子节点

    # 可以添加更详细的检查，例如读取文件内容并验证序列
    # 例如，检查 circle_probe.part1 的输出
    part1_output_path = target1_dir / "circle_probe.part1.out"
    with open(part1_output_path, 'r') as f:
        part1_seq = f.readline().strip()
        # 根据 rc(target_region[0:length]) 和 length=13 计算预期序列
        # target_region[0:13] = AGCTAGCTAGCTA
        # rc(...) = TAGCTAGCTAGCT
        assert part1_seq == "TAGCTAGCTAGCT"

    # 例如，检查 circle_probe.part2.barcode1 的输出
    barcode1_output_path = target1_dir / "circle_probe.part2.barcode1.out"
    with open(barcode1_output_path, 'r') as f:
        barcode1_seq = f.readline().strip()
        # 预期序列来自 config['encoding']['gene1']['barcode1']
        # 在 config['barcode_set'] 中查找对应的序列
        expected_barcode1_id = sample_config['encoding']['gene1']['barcode1']
        expected_barcode1_seq = sample_config['barcode_set'][expected_barcode1_id]
        assert barcode1_seq == expected_barcode1_seq

    # 可以继续添加对其他探针部分的检查...
    # 例如，检查最终的 circle_probe 输出
    circle_probe_output_path = target1_dir / "circle_probe.out"
    with open(circle_probe_output_path, 'r') as f:
        circle_probe_seq = f.readline().strip()
        # 这里需要根据模板和所有部分的序列手动计算预期结果进行断言
        # print(f"Generated circle_probe: {circle_probe_seq}") # 打印出来方便调试
        # assert circle_probe_seq == "EXPECTED_FULL_CIRCLE_PROBE_SEQUENCE"