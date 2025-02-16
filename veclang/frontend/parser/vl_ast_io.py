"""Input/output functions for AST"""

from veclang.frontend.parser.vl_ast import ASTNode, ConstantValue


def pretty_print_ast(ast_node: ASTNode, depth: int = 0) -> str:
    """Prints out an AST"""
    output_str = "  " * depth + ast_node.__class__.__name__ + ":"
    for x in [
        y
        for y in dir(ast_node)
        if y[:2] != "__"
        and y not in {"_abc_impl"}
        and not callable(ast_node.__getattribute__(y))
    ]:
        if isinstance(ast_node.__getattribute__(x), ASTNode):
            output_str += "\n" + "  " * (depth + 1) + x + ": "
            output_str += "\n" + pretty_print_ast(
                ast_node.__getattribute__(x), depth + 2
            )

        elif isinstance(ast_node.__getattribute__(x), list):
            if not ast_node.__getattribute__(x):
                output_str += "\n" + "  " * (depth + 1) + "<empty list>"
            else:
                output_str += "\n" + "  " * (depth + 1) + x + ":"
                for z in ast_node.__getattribute__(x):
                    output_str += "\n" + pretty_print_ast(z, depth + 2)
                    if depth < 3:
                        output_str += "\n"

        elif isinstance(ast_node.__getattribute__(x), (str, ConstantValue)):
            # ConstantValues are handled by calling the __str__ method
            output_str += (
                "\n"
                + "  " * (depth + 1)
                + x
                + ': "'
                + str(ast_node.__getattribute__(x))
                + '"'
            )

        else:
            output_str += (
                "\n" + "  " * (depth + 1) + x + ": " + str(ast_node.__getattribute__(x))
            )
    return output_str


def print_ast(ast_node: ASTNode, depth: int = 0):
    """Prints out an AST"""
    print(pretty_print_ast(ast_node, depth))
