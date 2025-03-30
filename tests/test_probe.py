import yaml
import pytest
from pathlib import Path
from uprobe.gen.probe import DAG

HERE = Path(__file__).parent

def load_test_config():
    """加载测试配置文件"""
    config_path = HERE / "data" / "test_probe.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)

def test_probe_generation():
    """测试探针生成流程"""
    # 创建工作目录
    workdir = HERE / "test_output"
    workdir.mkdir(exist_ok=True)
    
    # 加载配置
    config = load_test_config()
    
    # 创建并运行DAG
    dag = DAG()
    dag.from_config(config, workdir)
    dag.run()
    
    # 验证基础序列探针
    with open(workdir / "base_seq.out") as f:
        result = f.read().strip()
        assert result == "CGATCGAT"  # ATCGATCG的反向互补序列
    
    # 验证目标序列探针
    with open(workdir / "target_seq.out") as f:
        result = f.read().strip()
        assert result == "GCTAGCTA"
    
    # 验证表达式探针
    with open(workdir / "expr_probe.out") as f:
        result = f.read().strip()
        assert result == "CGATCGAT"  # 应该与base_seq相同
    
    # 验证模板探针
    with open(workdir / "template_probe.out") as f:
        result = f.read().strip()
        assert result == "AAAACGATCGATTTTT"
    
    # 验证复杂组合探针
    with open(workdir / "complex_probe.out") as f:
        result = f.read().strip()
        assert result == "GCTAGCTACGATCGATAAAACGATCGATTTTT"

def test_config_validation():
    """测试配置验证"""
    workdir = HERE / "test_output"
    workdir.mkdir(exist_ok=True)
    dag = DAG()
    
    # 测试缺少必要字段
    with pytest.raises(AssertionError):
        dag.from_config({"probes": {}}, workdir)
    
    # 测试无效的探针类型
    invalid_config = {
        "probes": {
            "invalid_probe": {
                "invalid_type": "something"
            }
        }
    }
    with pytest.raises(ValueError):
        dag.from_config(invalid_config, workdir)
