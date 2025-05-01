from pathlib import Path
import typing as T
from ..utils import reverse_complement 
from .utils import parse_expression
from collections import deque


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
        #import ipdb; ipdb.set_trace()

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

    def run(self, context: dict):
        """Run the DAG for a given context, building nodes in dependency order."""     
        for node in self.nodes:
            node.done = False
        queue = deque(self.get_all_0_deps())     
        built_count = 0
        while queue:
            node = queue.popleft()           
            all_deps_done = all(dep.done for dep in node.deps)           
            if not node.done and all_deps_done: 
                print(f"Building node: {node.name}")
                try:
                    node.build(context)
                    built_count += 1
                except Exception as e:
                    print(f"Error building node {node.name}: {e}")
                    continue 
                for down_node in self.get_downstream_nodes(node):
                    if not down_node.done and all(dep.done for dep in down_node.deps):
                         if down_node not in queue:
                            print(f"  Adding downstream node to queue: {down_node.name}")
                            queue.append(down_node)        
        print(f"DAG run completed. Built {built_count} nodes.")


class Node:
    def __init__(self, dag: DAG, workdir: Path, name: str, config: dict):
        self.dag = dag
        self.workdir = workdir
        self.name = name
        self.config = config
        self.deps: T.List[Probe] = []
        self.done = False
        self.output_file = workdir / f"{name}.out"

    def build(self, context: dict):
        pass 

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
    
    def build(self, context: dict):
        eval_globals = {"rc": reverse_complement} 
        eval_locals = context.copy()
        dep_name_map = {}
        print(f"  Loading dependencies for {self.name}: {[dep.name for dep in self.deps]}")
        for dep in self.deps:
            if not dep.done:
                raise RuntimeError(f"Dependency {dep.name} was not built before {self.name}")
            try:
                dep_value = dep.output_file.read_text().strip() 
                safe_dep_name = dep.name.replace('.', '_') 
                dep_name_map[dep.name] = safe_dep_name
                eval_locals[safe_dep_name] = dep_value 
                print(f"    Loaded {dep.name} as {safe_dep_name} = '{dep_value[:20]}...'")
            except FileNotFoundError:
                 raise RuntimeError(f"Output file for dependency {dep.name} not found")
            except Exception as e:
                 raise RuntimeError(f"Error reading output file for dependency {dep.name}: {e}")
        modified_expr = self.expr
        for original_name in sorted(dep_name_map.keys(), key=len, reverse=True):
            safe_name = dep_name_map[original_name]
            modified_expr = modified_expr.replace(original_name, safe_name)
        if modified_expr != self.expr:
             print(f"  Original expression: {self.expr}")
             print(f"  Modified expression for eval: {modified_expr}")
        print(f"  Evaluating expression for {self.name}: {modified_expr}")
        try:
            with open(self.output_file, 'w') as f:
                result = eval(modified_expr, eval_globals, eval_locals)
                f.write(str(result))
            self.done = True
            print(f"  Successfully built {self.name}")
        except Exception as e:
            print(f"  Error evaluating {self.name}: {e}")
            print(f"    Expression evaluated: {modified_expr}")
            print(f"    Evaluation context (locals): {{k: (v[:50] + '...' if isinstance(v, str) and len(v) > 50 else v) for k, v in eval_locals.items()}}") # Log context safely
            self.done = False
            raise

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

    def build(self, context: dict):
        print(f"  Formatting template for {self.name}: {self.template}")
        if not all(part.done for part in self.parts):
             missing_deps = [p.name for p in self.parts if not p.done]
             raise RuntimeError(f"Cannot build {self.name}, missing dependencies: {missing_deps}")
        readers = {
            part.name.split('.')[-1]: read_lines(part.output_file)
            for part in self.parts
        }
        try:
            with open(self.output_file, 'w') as f:
                while True:
                    name2seq = {}
                    try:
                        for name, reader in readers.items():
                            seq_ = next(reader)
                            name2seq[name] = seq_
                    except StopIteration:
                        break 
                    
                    seq = self.template.format(**name2seq)
                    f.write(seq + "\n")
            self.done = True
            print(f"  Successfully built {self.name}")
        except Exception as e:
            print(f"  Error formatting template {self.name}: {e}")
            self.done = False
            raise

    def __getitem__(self, item: str):
        for part in self.parts:
            if part.name == item:
                return part


def construct_probes(workdir: Path, config, context: dict):

    dag = DAG()
    dag.from_config(config, workdir)
    dag.run(context) 