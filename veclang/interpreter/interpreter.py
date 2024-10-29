import typing

from veclang.parser.vl_ast import (
    BinaryAssignmentOperatorType,
    BinaryOperatorType,
    UnaryOperatorType,
    ASTPositionInfo,
    ASTNode,
    ExprNode,
    StmtNode,
    ProgramNode,
    StmtsNode,
    IdentifierNode,
    TypeNode,
    FunctionDeclarationParameterNode,
    FunctionDeclarationParametersNode,
    RangeLiteralExprNode,
    ArrayLiteralElementsNode,
    ArrayLiteralExprNode,
    MemberAccessExprNode,
    IndexElementsNode,
    IndexExprNode,
    FunctionCallArgumentsNode,
    FunctionCallExprNode,
    BinaryOperationExprNode,
    UnaryOperatorExprNode,
    ConstantValue,
    ConstantExprNode,
    CommentNode,
    AttributeTagValuesNode,
    AttributeTagNode,
    AttributeTagsNode,
    FunctionDeclarationStmtNode,
    DataDeclarationStmtNode,
    VariableDeclarationStmtNode,
    ConstantDeclarationStmtNode,
    AssignmentStmtNode,
    BinaryAssignmentStmtNode,
    ExprStmtNode,
    IfStmtNode,
    ElseifStmtNode,
    ElseStmtNode,
    ForInitialisationStmtNode,
    ForStmtNode,
    WhileStmtNode,
    ReturnStmtNode,
    StatelessStmtNode,
    BreakStmtNode,
    ContinueStmtNode,
)

from veclang.parser.parser import parse
from veclang.parser.vl_ast_io import pretty_print_ast

import abc


VlTypeStr = typing.Literal[
    "bool",
    "int",
    "uint",
    "long",
    "ulong",
    "real",
    "complex",
    "vec2",
    "vec3",
    "vec4",
    "mat2",
    "mat3",
    "mat4",
]


class VlTypeABC(abc.ABC):

    def __init__(self, value: typing.Any):
        self.value = value

    @staticmethod
    @abc.abstractmethod
    def get_type_name() -> VlTypeStr:
        pass

    @abc.abstractmethod
    def get_type_into(self) -> dict[str, typing.Callable[["VlTypeABC"], "VlTypeABC"]]:
        pass

    def __str__(self):
        return f"{self.value}: {self.get_type_name()}"


class VlBool(VlTypeABC):

    @staticmethod
    def get_type_name() -> VlTypeStr:
        return "bool"

    def get_type_into(self) -> dict[str, typing.Callable[["VlTypeABC"], "VlTypeABC"]]:
        return {}


class VlInt(VlTypeABC):

    @staticmethod
    def get_type_name() -> VlTypeStr:
        return "int"

    def get_type_into(self) -> dict[str, typing.Callable[["VlTypeABC"], "VlTypeABC"]]:
        return {}


# dictionary (left_type, operator, right_type): (return_type, fn[left_type, right_type] -> return_type)
BINARY_OPERATIONS: dict[
    tuple[VlTypeStr, BinaryOperatorType, VlTypeStr],
    tuple[VlTypeStr, typing.Callable[[VlTypeABC, VlTypeABC], VlTypeABC]],
] = {
    ("int", "PLUS", "int"): ("int", lambda x, y: VlInt(x.value + y.value)),
    ("int", "MINUS", "int"): ("int", lambda x, y: VlInt(x.value - y.value)),
    ("int", "TIMES", "int"): ("int", lambda x, y: VlInt(x.value * y.value)),
    ("int", "DIVIDE", "int"): ("int", lambda x, y: VlInt(x.value / y.value)),
    ("int", "MODULUS", "int"): ("int", lambda x, y: VlInt(x.value % y.value)),
    ("int", "INTEGER_DIVIDE", "int"): ("int", lambda x, y: VlInt(x.value // y.value)),
    ("int", "EXPONENTIATION", "int"): ("real", lambda x, y: VlInt(x.value**y.value)),
    ("bool", "EQUAL_TO", "bool"): ("bool", lambda x, y: VlBool(x == y)),
    ("bool", "NOT_EQUAL_TO", "bool"): ("bool", lambda x, y: VlBool(x != y)),
    ("bool", "LESS_THAN", "bool"): ("bool", lambda x, y: VlBool(x < y)),
    ("bool", "LESS_THAN_OR_EQUAL", "bool"): ("bool", lambda x, y: VlBool(x <= y)),
    ("bool", "GREATER_THAN", "bool"): ("bool", lambda x, y: VlBool(x > y)),
    ("bool", "GREATER_THAN_OR_EQUAL", "bool"): ("bool", lambda x, y: VlBool(x >= y)),
}


# dictionary (operator, operand_type): (return_type, fn[operand_type] -> return_type)
UNARY_OPERATIONS: dict[
    tuple[UnaryOperatorType, VlTypeStr],
    tuple[VlTypeStr, typing.Callable[[VlTypeABC], VlTypeABC]],
] = {
    ("UNARY_MINUS", "int"): ("int", lambda x: -x),
    ("UNARY_PLUS", "int"): ("int", lambda x: x),
}


# dictionary


class InterpreterState(typing.TypedDict):
    global_vars: dict[str, VlTypeABC]
    local_vars: dict[str, VlTypeABC]

    global_consts: dict[str, VlTypeABC]
    local_consts: dict[str, VlTypeABC]

    fns: list[FunctionDeclarationStmtNode]

    in_function: bool
    if_elif_stack_sc: bool | None

    stdout_buffer: list[str]


def resolve_var(identifier_name: str, state: InterpreterState) -> VlTypeABC:
    if identifier_name in state["global_vars"]:
        return state["global_vars"][identifier_name]
    elif identifier_name in state["local_vars"]:
        return state["global_vars"][identifier_name]
    elif identifier_name in state["global_consts"]:
        return state["global_consts"][identifier_name]
    elif identifier_name in state["global_vars"]:
        return state["global_vars"][identifier_name]
    else:
        raise ValueError(f"Identifier {identifier_name} could not be resolved")


def resolve_fn(
    identifier_name: str, state: InterpreterState
) -> FunctionDeclarationStmtNode:
    for declaration in state["fns"]:
        if declaration.identifier.name == identifier_name:
            return declaration
    raise ValueError(f"Identifier {identifier_name} could not be resolved")


def eval_vl(node: ASTNode, state: InterpreterState) -> VlTypeABC | None:
    if isinstance(node, StmtNode) and not isinstance(
        node, (IfStmtNode, ElseifStmtNode, ElseStmtNode)
    ):
        state["if_elif_stack_sc"] = None

    if isinstance(node, ProgramNode):
        return eval_vl(node.stmts, state)

    elif isinstance(node, StmtsNode):
        for stmt in node.stmts:
            eval_vl(stmt, state)
            return

    elif isinstance(node, IdentifierNode):
        return resolve_var(node.name, state)

    elif isinstance(node, TypeNode):
        return

    elif isinstance(node, FunctionDeclarationParameterNode):
        return

    elif isinstance(node, FunctionDeclarationParametersNode):
        return

    elif isinstance(node, RangeLiteralExprNode):
        return

    elif isinstance(node, ArrayLiteralElementsNode):
        return

    elif isinstance(node, ArrayLiteralExprNode):
        return

    elif isinstance(node, MemberAccessExprNode):
        raise ValueError("Feature not implemented")

    elif isinstance(node, IndexElementsNode):
        return None

    elif isinstance(node, IndexExprNode):
        return None

    elif isinstance(node, FunctionCallArgumentsNode):
        return None

    elif isinstance(node, FunctionCallExprNode):
        if node.callee.name == "print":
            out = ""
            for argument in node.arguments.arguments:
                out += str(eval_vl(argument, state)) + " "
            state["stdout_buffer"].append(out)
            return

        if state["in_function"]:
            raise ValueError("Nested functions are not supported")

        fn = resolve_fn(node.callee.name, state)
        expected_parameters = len(fn.parameters.parameters)
        actual_parameters = len(node.arguments.arguments)
        if expected_parameters == actual_parameters:
            raise ValueError(f"Expected {expected_parameters}, got {actual_parameters}")

        new_locals = {}
        for parameter, argument in zip(
            fn.parameters.parameters, node.arguments.arguments
        ):
            argument_val = eval_vl(argument, state)
            expected_type = parameter._type.name
            actual_type = argument_val.get_type_name()
            if expected_type != actual_type:
                raise ValueError(
                    f"Expected parameter '{parameter.name}' to be of type {expected_type}, not {actual_type}"
                )
            new_locals[parameter.name] = argument_val

        state["in_function"] = True
        state["local_vars"].update(new_locals)

        return_val = eval_vl(fn.stmts, state)
        for local_var in new_locals:
            del state["local_vars"][local_var]

        state["in_function"] = False
        return return_val

    elif isinstance(node, BinaryOperationExprNode):
        left = eval_vl(node.left, state)
        right = eval_vl(node.right, state)
        operator = node.operator

        left_t = left.get_type_name()
        right_t = right.get_type_name()

        # resolve internal function
        key = (left_t, operator, right_t)
        if key not in BINARY_OPERATIONS:
            raise ValueError(
                f"Operator '{operator}' not supported between instances of '{left_t}' and '{right_t}'"
            )

        _, exec_fn = BINARY_OPERATIONS[key]
        return exec_fn(left, right)

    elif isinstance(node, UnaryOperatorExprNode):
        operand = eval_vl(node.operand, state)
        operator = node.operator

        operand_t = operand.get_type_name()

        # resolve internal function
        key = (operator, operand_t)
        if key not in BINARY_OPERATIONS:
            raise ValueError(
                f"Operator '{operator}' not supported for instance of '{operand_t}'"
            )

        _, exec_fn = UNARY_OPERATIONS[key]
        return exec_fn(operand)

    elif isinstance(node, ConstantExprNode):
        if isinstance(node.value.value, bool):
            return VlBool(node.value.value)
        elif isinstance(node.value.value, int):
            return VlInt(node.value.value)
        else:
            raise ValueError(f"Constant type '{node.value.type}' not implemented yet")

    elif isinstance(
        node, (AttributeTagValuesNode, AttributeTagNode, AttributeTagsNode)
    ):
        return

    elif isinstance(node, FunctionDeclarationStmtNode):
        if state["in_function"]:
            raise ValueError("Cannot declare function inside function")
        state["fns"].append(node)
        return

    elif isinstance(node, VariableDeclarationStmtNode):
        expr = eval_vl(node.value, state)
        expr_t = expr.get_type_name()
        expected_t = node._type.name

        if expr_t != expected_t:
            raise ValueError(f"Expected type '{expected_t}', got type '{expr_t}'")

        if state["in_function"]:
            state["local_vars"][node.target.name] = expr
        else:
            state["global_vars"][node.target.name] = expr

    elif isinstance(node, ConstantDeclarationStmtNode):
        expr = eval_vl(node.value, state)
        expr_t = expr.get_type_name()
        expected_t = node._type.name

        if expr_t != expected_t:
            raise ValueError(f"Expected type '{expected_t}', got type '{expr_t}'")

        if state["in_function"]:
            state["local_consts"][node.target.name] = expr
        else:
            state["global_consts"][node.target.name] = expr

    elif isinstance(node, AssignmentStmtNode):
        expr = eval_vl(node.value, state)
        expr_t = expr.get_type_name()

        if not isinstance(node.target, IdentifierNode):
            raise ValueError("Expected identifier on LHS of assignment")
        identifier = node.target.name
        if (
            identifier not in state["local_vars"]
            and identifier not in state["global_vars"]
        ):
            raise ValueError(f"Unknown identifier {identifier}")

        if state["in_function"] and identifier in state["local_vars"]:
            expected_t = state["local_vars"][identifier].get_type_name()
            if expected_t != expr_t:
                raise ValueError(f"Expected type '{expected_t}', got type '{expr_t}'")
            state["local_vars"][identifier] = expr

        else:
            expected_t = state["global_vars"][identifier].get_type_name()
            if expected_t != expr_t:
                raise ValueError(f"Expected type '{expected_t}', got type '{expr_t}'")
            state["global_vars"][identifier] = expr

        return

    elif isinstance(node, BinaryAssignmentStmtNode):
        raise ValueError("Not yet implemented")

    elif isinstance(node, ExprStmtNode):
        return eval_vl(node.expr, state)

    elif isinstance(node, IfStmtNode):
        state["if_elif_stack_sc"] = False
        condition = eval_vl(node.condition, state)
        if condition.get_type_name() != "bool":
            raise ValueError(
                f"Expected condition to be bool, not '{condition.get_type_name()}'"
            )

        if condition.value:
            eval_vl(node.stmts, state)
            state["if_elif_stack_sc"] = True

    elif isinstance(node, ElseifStmtNode):
        if state["if_elif_stack_sc"] is None:
            raise ValueError("Elif statement not after if or elif statement")

        condition = eval_vl(node.condition, state)
        if condition.get_type_name() != "bool":
            raise ValueError(
                f"Expected condition to be bool, not '{condition.get_type_name()}'"
            )

        if state["if_elif_stack_sc"] is not True and condition.value:
            eval_vl(node.stmts, state)
            state["if_elif_stack_sc"] = True

    elif isinstance(node, ElseStmtNode):
        if state["if_elif_stack_sc"] is None:
            raise ValueError("Else statement not after if or elif statement")

        if state["if_elif_stack_sc"] is not True:
            eval_vl(node.stmts, state)
        state["if_elif_stack_sc"] = None


def eval_full(ast_node: ProgramNode, state: InterpreterState | None = None):
    if state is None:
        state = {
            "global_vars": {},
            "local_vars": {},
            "global_consts": {},
            "local_consts": {},
            "fns": [],
            "in_function": False,
            "if_elif_stack_sc": None,
            "stdout_buffer": [],
        }
    return eval_vl(ast_node, state), state


def eval_all(input_str: str):
    print(input_str)
    ast_node = parse(input_str)
    print(pretty_print_ast(ast_node))
    out, state = eval_full(ast_node)
    print(f"Output: {out}")
    print("\n".join(state["stdout_buffer"]))


eval_all("let a: int = 1 + 1;")

print("\n" * 10, "VECLANG 2.0 REPL")
state = {
    "global_vars": {},
    "local_vars": {},
    "global_consts": {},
    "local_consts": {},
    "fns": [],
    "in_function": False,
    "if_elif_stack_sc": None,
    "stdout_buffer": [],
}
while True:
    s = input(">>> ")
    ast_node = parse(s)
    # print(pretty_print_ast(ast_node))
    out, state = eval_full(ast_node, state)
    if out:
        print(f"{out}")
    print("\n".join(state["stdout_buffer"]))
    state["stdout_buffer"].clear()
