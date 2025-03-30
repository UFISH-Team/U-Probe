from pathlib import Path
import typing as T
from ..utils import reverse_complement
from .utils import parse_expression

class SequenceProcessor:
    """Base class for sequence processing"""
    def process(self, sequence: str) -> str:
        raise NotImplementedError

class ReverseComplementProcessor(SequenceProcessor):
    """Process sequence by reverse complementing it"""
    def process(self, sequence: str) -> str:
        return reverse_complement(sequence)

class SequenceSource:
    """Base class for sequence sources"""
    def get_sequence(self) -> str:
        raise NotImplementedError

class TargetSource(SequenceSource):
    """Get sequence from target sequences"""
    def __init__(self, sequence: str):
        self.sequence = sequence
        
    def get_sequence(self) -> str:
        return self.sequence

class ExternalSource(SequenceSource):
    """Get sequence from external input"""
    def __init__(self, sequence: str):
        self.sequence = sequence
        
    def get_sequence(self) -> str:
        return self.sequence


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
        """Create DAG from configuration dictionary"""
        assert 'probes' in config, "probes key not found"
        assert isinstance(config['probes'], dict), "probes should be a dict"
        
        for probe_name, probe_config in config['probes'].items():
            probe: Probe
            
            # Determine probe type from config
            if 'template' in probe_config:
                probe = TemplateProbe(self, workdir, probe_name, probe_config)
            elif 'expr' in probe_config:
                probe = ExprProbe(self, workdir, probe_name, probe_config)
            elif 'source' in probe_config:
                probe = Probe(self, workdir, probe_name, probe_config)
            else:
                raise ValueError(f"Invalid probe config for {probe_name}: missing type identifier")
                
            self.nodes.append(probe)
            
        # Parse expressions after all nodes are created
        for node in self.nodes:
            if isinstance(node, ExprProbe):
                node.parse_expr()

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
        # Topological sort using Kahn's algorithm
        in_degree = {node: 0 for node in self.nodes}
        for node in self.nodes:
            for dep in node.deps:
                in_degree[dep] += 1

        queue = [node for node in self.nodes if in_degree[node] == 0]
        built_nodes = []
        
        while queue:
            node = queue.pop(0)
            try:
                node.build()
                node.done = True
                built_nodes.append(node)
            except Exception as e:
                print(f"Failed to build {node.name}: {str(e)}")
                continue
                
            # Update in-degree of dependents
            for dependent in self.get_downstream_nodes(node):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # Check for cycles or build failures
        if len(built_nodes) != len(self.nodes):
            remaining = [n.name for n in self.nodes if not n.done]
            raise ValueError(f"Circular dependency or build failure in: {remaining}")


class Node:
    def __init__(self, dag: DAG, workdir: Path, name: str, config: dict):
        self.dag = dag
        self.workdir = workdir
        self.name = name
        self.config = config
        self.deps: T.List[Probe] = []
        self.done = False
        self.output_file = workdir / f"{name}.out"
        self.processors: T.List[SequenceProcessor] = []
        self.sequence_source: T.Optional[SequenceSource] = None
        self._setup_source()
        self._setup_processors()

    def _setup_source(self):
        """Set up sequence source based on config"""
        if 'source' not in self.config:
            return
            
        if self.config['source'] == 'target':
            if 'sequence' in self.config:
                self.sequence_source = TargetSource(self.config['sequence'])
        elif self.config['source'] == 'external':
            if 'sequence' in self.config:
                self.sequence_source = ExternalSource(self.config['sequence'])

    def _setup_processors(self):
        """Set up sequence processors based on config"""
        if 'process' not in self.config:
            return
            
        for proc in self.config['process']:
            if proc['type'] == 'reverse_complement':
                self.processors.append(ReverseComplementProcessor())
            # Add more processor types as needed

    def process_sequence(self, sequence: str) -> str:
        """Apply all processors to the sequence"""
        for processor in self.processors:
            sequence = processor.process(sequence)
        return sequence

    def build(self):
        """Build the node by processing dependencies and sequence"""
        for dep in self.deps:
            assert dep.done, f"Dependency {dep.name} not done"
            
        if self.sequence_source:
            sequence = self.sequence_source.get_sequence()
            sequence = self.process_sequence(sequence)
            with open(self.output_file, 'w') as f:
                f.write(sequence + '\n')


class Probe(Node):
    """Base class for all probe types"""
    def __init__(self, dag: DAG, workdir: Path, name: str, config: dict):
        super().__init__(dag, workdir, name, config)
        self.sequence = ""
        
    def build(self):
        """Build the probe by processing dependencies and sequence"""
        super().build()
        
        # Process sequence from source if available
        if self.sequence_source:
            self.sequence = self.sequence_source.get_sequence()
            self.sequence = self.process_sequence(self.sequence)
            with open(self.output_file, 'w') as f:
                f.write(self.sequence + '\n')


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

    def __getitem__(self, item: str) -> "Probe":
        """Get a part by name"""
        for part in self.parts:
            if part.name == item:
                return part
        raise KeyError(f"Part {item} not found")
