import ast

class ExpressionVisitor(ast.NodeVisitor):
    def __init__(self):
        self.expressions = set()

    def visit_Name(self, node):
        self.expressions.add(node.id)

    def visit_Attribute(self, node):
        self.expressions.add(f"{self.get_full_attribute(node)}")

    def get_full_attribute(self, node):
        if isinstance(node.value, ast.Name):
            return f"{node.value.id}.{node.attr}"
        elif isinstance(node.value, ast.Attribute):
            return f"{self.get_full_attribute(node.value)}.{node.attr}"
        return node.attr


def parse_expression(expr):
    tree = ast.parse(expr)
    visitor = ExpressionVisitor()
    visitor.visit(tree)
    return visitor.expressions