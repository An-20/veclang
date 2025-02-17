"""Input/output functions for a HIR tree"""

from veclang.frontend.parser.vl_ast import ConstantValue
from veclang.midend.vl_hir import HIRNode


def format_hir(ast_node: HIRNode, depth: int = 0) -> str:
    """Formats a HIR tree"""
    output_str = "  " * depth + ast_node.__class__.__name__ + ":"
    for x in [
        y
        for y in dir(ast_node)
        if y[:2] != "__"
        and y not in {"_abc_impl", "position_info"}
        and not callable(ast_node.__getattribute__(y))
    ]:
        attr_value = ast_node.__getattribute__(x)
        if isinstance(attr_value, HIRNode):
            output_str += f"\n{'  ' * (depth + 1)}{x}: "
            output_str += f"\n{format_hir(attr_value, depth + 2)}"

        elif isinstance(attr_value, list):
            if not attr_value:
                output_str += f"\n{'  ' * (depth + 1)}{x}: <empty list>"
            else:
                output_str += f"\n{'  ' * (depth + 1)}{x}:"
                for z in attr_value:
                    output_str += f"\n{format_hir(z, depth + 2)}"
                    if depth < 3:
                        output_str += "\n"

        elif isinstance(attr_value, str):
            output_str += f"\n{'  ' * (depth + 1)}{x}: '{str(attr_value)}'"

        elif isinstance(attr_value, ConstantValue):
            # ConstantValues are handled by calling the __str__ method
            output_str += f"\n{'  ' * (depth + 1)}{x}: {str(attr_value)}"

        else:
            output_str += f"\n{'  ' * (depth + 1)}{x}: {str(attr_value)}"
    return output_str


def print_hir(ast_node: HIRNode, depth: int = 0):
    """Prints out a HIR tree"""
    print(format_hir(ast_node, depth).strip())
