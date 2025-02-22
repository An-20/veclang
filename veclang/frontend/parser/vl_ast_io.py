"""Input/output functions for AST"""

from veclang.frontend.parser.vl_ast import ASTNode, ConstantValue


def format_ast(ast_node: ASTNode, depth: int = 0) -> str:
    """Formats an AST"""
    output_str = "  " * depth + ast_node.__class__.__name__ + ":"
    for x in [
        y
        for y in dir(ast_node)
        if y[:2] != "__"
        and y not in {"_abc_impl"}
        and not callable(ast_node.__getattribute__(y))
    ]:
        attr_value = ast_node.__getattribute__(x)
        if isinstance(attr_value, ASTNode):
            output_str += f"\n{'  ' * (depth + 1)}{x}: "
            output_str += f"\n{format_ast(attr_value, depth + 2)}"

        elif isinstance(attr_value, list):
            if not attr_value:
                output_str += f"\n{'  ' * (depth + 1)}{x}: <empty list>"
            else:
                output_str += f"\n{'  ' * (depth + 1)}{x}:"
                for z in attr_value:
                    output_str += f"\n{format_ast(z, depth + 2)}"
                    if depth < 3:
                        output_str += "\n"

        elif isinstance(attr_value, (str, ConstantValue)):
            # ConstantValues are handled by calling the __str__ method
            output_str += "\n" + "  " * (depth + 1) + x + ': "' + str(attr_value) + '"'

        else:
            output_str += f"\n{'  ' * (depth + 1)}{x}: {str(attr_value)}"

    return output_str


def print_ast(ast_node: ASTNode, depth: int = 0):
    """Prints out an AST"""
    print(format_ast(ast_node, depth).strip())
