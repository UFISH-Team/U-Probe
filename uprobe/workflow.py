from pathlib import Path
import yaml


def parse_yaml(path: Path) -> dict:
    content = path.read_text(encoding="utf-8")
    res = yaml.load(content, Loader=yaml.FullLoader)
    return res


def check_probe_yaml(res: dict):
    assert "genome" in res, "genome key not found"
    assert "name" in res, "name key not found"


def check_genome_yaml(res: dict):
    pass
