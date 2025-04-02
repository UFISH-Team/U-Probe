
from pathlib import Path
import typing as T
from ..utils import reverse_complement
from .utils import parse_expression


def read_lines(path: Path, comment: str = '#'):
    with open(path) as f:
        for line in f:
            if line.startswith(comment):
                continue
            yield line.strip()


class DAG():
    def __init__(self) -> None:
        self.nodes: T.List[Node] = []

    def from_config(self, config: dict, workdir: Path):
        assert 'probes' in config, "probes key not found"
        assert isinstance(config['probes'], dict), "probes should be a dict"
        for probe_name, probe_config in config['probes'].items():
            assert 'template' in probe_config or 'expr' in probe_config, \
                "template or expr key not found"
            probe = TemplateProbe(self, workdir, probe_name, probe_config)
            self.nodes.append(probe)
        for node in self.nodes:
            if isinstance(node, ExprProbe):
                node.parse_expr()
        import ipdb; ipdb.set_trace()

    def get_downstream_nodes(self, node: "Node") -> T.List["Node"]:
        downstream = []
        for probe in self.nodes:
            if node in probe.deps:
                downstream.append(probe)
        return downstream

    def get_node_by_name(self, name: str) -> T.Optional["Node"]:
        for probe in self.nodes:
            if probe.name == name:
                return probe
        return None

    def get_all_0_deps(self) -> T.List["Node"]:
        return [probe for probe in self.nodes if len(probe.deps) == 0]

    def run(self):
        """Run the DAG, build all probes."""
        pass


class Node:
    def __init__(self, dag: DAG, workdir: Path, name: str, config: dict):
        self.dag = dag
        self.workdir = workdir
        self.name = name
        self.config = config
        self.deps: T.List[Probe] = []
        self.done = False
        self.output_file = workdir / f"{name}.out"

    def build(self):
        for dep in self.deps:
            assert dep.done, f"Dependency {dep.name} not done"


class Probe(Node):
    pass


class ExprProbe(Probe):
    def __init__(self, dag: DAG, workdir: Path, name: str, config: dict):
        super().__init__(dag, workdir, name, config)
        assert 'expr' in config, "expr key not found"
        self.expr = config['expr']
        self.external_deps: T.List[str] = []

    def parse_expr(self):
        """Parse the dependency from the expression"""
        deps = parse_expression(self.expr)
        for dep in deps:
            print(dep)
            node = self.dag.get_node_by_name(dep)
            if node is None:
                self.external_deps.append(dep)
            else:
                self.deps.append(node)


class TemplateProbe(Probe):
    def __init__(self, dag: DAG, workdir: Path, name: str, config: dict):
        super().__init__(dag, workdir, name, config)
        assert 'template' in config, "template key not found"
        assert 'parts' in config, "parts key not found"
        self.parts: T.List[Probe] = []
        self.template: str = config['template']
        self.resolve_parts()

    def resolve_parts(self) -> None:
        self.parts.clear()
        for part_name, part_config in self.config['parts'].items():
            part: Node
            new_name = f"{self.name}.{part_name}"
            if 'template' in part_config:
                part = TemplateProbe(
                    self.dag, self.workdir, new_name, part_config)
            elif 'expr' in part_config:
                part = ExprProbe(
                    self.dag, self.workdir, new_name, part_config)
            else:
                raise ValueError(f"Invalid part config: {part_config}")
            self.parts.append(part)
            self.dag.nodes.append(part)
        self.deps = self.parts

    def build(self):
        super().build()
        readers = {
            part.name: read_lines(part.output_file)
            for part in self.parts
        }
        with open(self.output_file, 'w') as f:
            while True:
                name2seq = {}
                for name, reader in readers.items():
                    try:
                        seq_ = next(reader)
                    except StopIteration:
                        break
                    name2seq[name] = seq_
                else:
                    seq = self.template.format(**name2seq)
                    f.write(seq + "\n")
                    continue
                break

    def __getitem__(self, item: str):
        for part in self.parts:
            if part.name == item:
                return part
        raise ValueError(f"Part {item} not found")

def construct_probes(workdir: Path, config, target_seqs_path: Path):
    dag = DAG()
    dag.from_config(config, workdir)
    dag.run()
