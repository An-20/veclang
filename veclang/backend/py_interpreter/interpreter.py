"""
A standalone tree-walk interpreter for a basic subset of the Veclang language
written in about 4 hours.
"""

import typing

import io
from contextlib import redirect_stdout

import math


from veclang.frontend.parser.vl_ast import (
    AugmentedAssignmentOperatorType,
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
    FunctionDeclParameterNode,
    FunctionDeclParametersNode,
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
    FunctionDeclNode,
    DataDeclNode,
    VariableDeclNode,
    ConstantDeclNode,
    AssignmentStmtNode,
    AugmentedAssignmentStmtNode,
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

from veclang.frontend.parser.vl_parser import parse


import abc

import numpy as np
from PIL import Image


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
    def get_type_into(
        self,
    ) -> dict[VlTypeStr, typing.Callable[["VlTypeABC"], "VlTypeABC"]]:
        pass

    @abc.abstractmethod
    def get_attributes(self) -> dict[str, typing.Callable[["VlTypeABC"], "VlTypeABC"]]:
        pass

    @abc.abstractmethod
    def get_methods(self) -> dict[str, "VlFunction"]:
        pass

    def __str__(self):
        return f"{self.value}: {self.get_type_name()}"


class VlFunction(VlTypeABC):

    def __init__(
        self,
        param_types: list[VlTypeStr],
        ret_type: VlTypeStr,
        fn: typing.Callable[[list["VlTypeABC"]], "VlTypeABC"],
    ):
        super().__init__(None)
        self.arg_types = param_types
        self.ret_type = ret_type
        self.fn = fn

    @staticmethod
    def get_type_name() -> VlTypeStr:
        return "VlFunction"

    def get_type_into(self) -> dict[str, typing.Callable[["VlTypeABC"], "VlTypeABC"]]:
        return {}

    def get_attributes(self) -> dict[str, typing.Callable[["VlTypeABC"], "VlTypeABC"]]:
        return {}

    def get_methods(self) -> dict[str, "VlFunction"]:
        return {}


class VlBool(VlTypeABC):

    @staticmethod
    def get_type_name() -> VlTypeStr:
        return "bool"

    def get_type_into(self) -> dict[str, typing.Callable[["VlTypeABC"], "VlTypeABC"]]:
        return {}

    def get_attributes(self) -> dict[str, typing.Callable[["VlTypeABC"], "VlTypeABC"]]:
        return {}

    def get_methods(self) -> dict[str, VlFunction]:
        return {}


class VlInt(VlTypeABC):

    @staticmethod
    def get_type_name() -> VlTypeStr:
        return "int"

    def get_type_into(self) -> dict[str, typing.Callable[["VlTypeABC"], "VlTypeABC"]]:
        return {
            "real": lambda x: VlReal(float(x.value)),
            "complex": lambda x: VlComplex(complex(float(x.value))),
        }

    def get_attributes(self) -> dict[str, typing.Callable[["VlTypeABC"], "VlTypeABC"]]:
        return {}

    def get_methods(self) -> dict[str, VlFunction]:
        return {}


class VlReal(VlTypeABC):

    @staticmethod
    def get_type_name() -> VlTypeStr:
        return "real"

    def get_type_into(self) -> dict[str, typing.Callable[["VlTypeABC"], "VlTypeABC"]]:
        return {
            "complex": lambda x: VlComplex(complex(float(x.value))),
        }

    def get_attributes(self) -> dict[str, typing.Callable[["VlTypeABC"], "VlTypeABC"]]:
        return {}

    def get_methods(self) -> dict[str, VlFunction]:
        return {}


class VlComplex(VlTypeABC):

    @staticmethod
    def get_type_name() -> VlTypeStr:
        return "complex"

    def get_type_into(self) -> dict[str, typing.Callable[["VlTypeABC"], "VlTypeABC"]]:
        return {}

    def get_attributes(self) -> dict[str, typing.Callable[["VlTypeABC"], "VlTypeABC"]]:
        return {
            "re": lambda x: VlReal(x.value.real),
            "im": lambda x: VlReal(x.value.imag),
            "mod": lambda x: VlReal(abs(x.value)),
            "arg": lambda x: VlReal(math.atan2(x.value.imag, x.value.real)),
        }

    def get_methods(self) -> dict[str, VlFunction]:
        return {}


class VlVecABC(VlTypeABC, abc.ABC):

    def __init__(self, value: typing.Any):
        stripped = [x.value for x in value]
        super().__init__(stripped)

    def get_type_into(self) -> dict[str, typing.Callable[["VlTypeABC"], "VlTypeABC"]]:
        return {}

    def __str__(self):
        return f"[{', '.join([str(v) for v in self.value])}]: {self.get_type_name()}"

    def get_attributes(self) -> dict[str, typing.Callable[["VlTypeABC"], "VlTypeABC"]]:
        return {}

    def get_methods(self) -> dict[str, VlFunction]:
        return {}


class VlVec2(VlVecABC):

    @staticmethod
    def get_type_name() -> VlTypeStr:
        return "vec2"

    def get_attributes(self) -> dict[str, typing.Callable[["VlTypeABC"], "VlTypeABC"]]:
        return {"x": lambda x: VlReal(x.value[0]), "y": lambda x: VlReal(x.value[1])}

    def get_methods(self) -> dict[str, VlFunction]:
        return {
            "dot": VlFunction(
                ["vec2"],
                "real",
                lambda x: VlReal(
                    self.value[0] * x.value[0] + self.value[1] * x.value[1]
                ),
            )
        }


class VlVec3(VlVecABC):

    @staticmethod
    def get_type_name() -> VlTypeStr:
        return "vec3"


class VlVec4(VlVecABC):

    @staticmethod
    def get_type_name() -> VlTypeStr:
        return "vec4"


# dictionary (left_type, operator, right_type): (return_type, fn[left_type, right_type] -> return_type)
BINARY_OPERATIONS: dict[
    tuple[VlTypeStr, BinaryOperatorType, VlTypeStr],
    tuple[VlTypeStr, typing.Callable[[VlTypeABC, VlTypeABC], VlTypeABC]],
] = {
    # integers
    # ====================
    ("int", "PLUS", "int"): ("int", lambda x, y: VlInt(x.value + y.value)),
    ("int", "MINUS", "int"): ("int", lambda x, y: VlInt(x.value - y.value)),
    ("int", "TIMES", "int"): ("int", lambda x, y: VlInt(x.value * y.value)),
    ("int", "DIVIDE", "int"): ("real", lambda x, y: VlReal(x.value / y.value)),
    ("int", "MODULUS", "int"): ("int", lambda x, y: VlInt(x.value % y.value)),
    ("int", "INTEGER_DIVIDE", "int"): ("int", lambda x, y: VlInt(x.value // y.value)),
    ("int", "EXPONENTIATION", "int"): ("real", lambda x, y: VlInt(x.value**y.value)),
    ("int", "EQUAL_TO", "int"): ("bool", lambda x, y: VlBool(x.value == y.value)),
    ("int", "NOT_EQUAL_TO", "int"): ("bool", lambda x, y: VlBool(x.value != y.value)),
    ("int", "LESS_THAN", "int"): ("bool", lambda x, y: VlBool(x.value < y.value)),
    ("int", "LESS_THAN_OR_EQUAL", "int"): (
        "bool",
        lambda x, y: VlBool(x.value <= y.value),
    ),
    ("int", "GREATER_THAN", "int"): ("bool", lambda x, y: VlBool(x.value > y.value)),
    ("int", "GREATER_THAN_OR_EQUAL", "int"): (
        "bool",
        lambda x, y: VlBool(x.value >= y.value),
    ),
    # reals
    # ====================
    ("real", "PLUS", "real"): ("real", lambda x, y: VlReal(x.value + y.value)),
    ("real", "MINUS", "real"): ("real", lambda x, y: VlReal(x.value - y.value)),
    ("real", "TIMES", "real"): ("real", lambda x, y: VlReal(x.value * y.value)),
    ("real", "DIVIDE", "real"): ("real", lambda x, y: VlReal(x.value / y.value)),
    ("real", "MODULUS", "real"): ("real", lambda x, y: VlReal(x.value % y.value)),
    ("real", "INTEGER_DIVIDE", "real"): (
        "real",
        lambda x, y: VlReal(x.value // y.value),
    ),
    ("real", "EXPONENTIATION", "real"): ("real", lambda x, y: VlReal(x.value**y.value)),
    ("real", "EQUAL_TO", "real"): ("real", lambda x, y: VlBool(x.value == y.value)),
    ("real", "NOT_EQUAL_TO", "real"): ("real", lambda x, y: VlBool(x.value != y.value)),
    ("real", "LESS_THAN", "real"): ("bool", lambda x, y: VlBool(x.value < y.value)),
    ("real", "LESS_THAN_OR_EQUAL", "real"): (
        "bool",
        lambda x, y: VlBool(x.value <= y.value),
    ),
    ("real", "GREATER_THAN", "real"): ("bool", lambda x, y: VlBool(x.value > y.value)),
    ("real", "GREATER_THAN_OR_EQUAL", "real"): (
        "bool",
        lambda x, y: VlBool(x.value >= y.value),
    ),
    # complexes
    # ====================
    ("complex", "PLUS", "complex"): (
        "complex",
        lambda x, y: VlComplex(x.value + y.value),
    ),
    ("complex", "MINUS", "complex"): (
        "complex",
        lambda x, y: VlComplex(x.value - y.value),
    ),
    ("complex", "TIMES", "complex"): (
        "complex",
        lambda x, y: VlComplex(x.value * y.value),
    ),
    ("complex", "DIVIDE", "complex"): (
        "complex",
        lambda x, y: VlComplex(x.value / y.value),
    ),
    ("complex", "EXPONENTIATION", "complex"): (
        "complex",
        lambda x, y: VlComplex(x.value**y.value),
    ),
    ("complex", "EQUAL_TO", "complex"): ("complex", lambda x, y: VlBool(x == y)),
    ("complex", "NOT_EQUAL_TO", "complex"): ("complex", lambda x, y: VlBool(x != y)),
    # vectors
    # ====================
    ("vec2", "PLUS", "vec2"): (
        "vec2",
        lambda x, y: VlVec2([a + b for a, b in zip(x.value, y.value)]),
    ),
    ("vec2", "MINUS", "vec2"): (
        "vec2",
        lambda x, y: VlVec2([a - b for a, b in zip(x.value, y.value)]),
    ),
    ("float", "TIMES", "vec2"): (
        "vec2",
        lambda x, y: VlVec2([a - b for a, b in zip(x.value, y.value)]),
    ),
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

    fns: list[FunctionDeclNode]

    in_function: bool
    function_ret_val: VlTypeABC | None

    if_elif_stack_sc: bool | None

    in_loop: bool
    loop_break: bool

    stdout_buffer: list[str]


def create_new_state() -> InterpreterState:
    return {
        "global_vars": {},
        "local_vars": {},
        "global_consts": {},
        "local_consts": {},
        "fns": [],
        "in_function": False,
        "function_ret_val": None,
        "in_loop": False,
        "loop_break": False,
        "if_elif_stack_sc": None,
        "stdout_buffer": [],
    }


def resolve_var(identifier_name: str, state: InterpreterState) -> VlTypeABC:
    if identifier_name in state["local_vars"]:
        return state["local_vars"][identifier_name]
    elif identifier_name in state["local_consts"]:
        return state["local_consts"][identifier_name]
    elif identifier_name in state["global_vars"]:
        return state["global_vars"][identifier_name]
    elif identifier_name in state["global_consts"]:
        return state["global_consts"][identifier_name]
    else:
        raise ValueError(f"Identifier {identifier_name} could not be resolved")


def resolve_fn(identifier_name: str, state: InterpreterState) -> FunctionDeclNode:
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
        if len(node.stmts) == 1 and isinstance(node.stmts[0], ExprStmtNode):
            # convenience for when exprs are entered in the REPL
            return eval_vl(node.stmts[0].expr, state)

        for stmt in node.stmts:
            if isinstance(stmt, BreakStmtNode):
                if state["in_loop"]:
                    state["loop_break"] = True
                    return
                else:
                    raise ValueError(f"Break used outside of loop")

            elif isinstance(stmt, ContinueStmtNode):
                if state["in_loop"]:
                    return
                else:
                    raise ValueError(f"Continue used outside of loop")

            elif isinstance(stmt, ReturnStmtNode):
                if state["in_function"]:
                    val = eval_vl(stmt.value, state)
                    state["function_ret_val"] = val
                else:
                    raise ValueError(f"Return used outside of function")

            eval_vl(stmt, state)
            if state["function_ret_val"]:
                return
            if state["loop_break"]:
                return

        return

    elif isinstance(node, IdentifierNode):
        return resolve_var(node.name, state)

    elif isinstance(node, TypeNode):
        return

    elif isinstance(node, FunctionDeclParameterNode):
        return

    elif isinstance(node, FunctionDeclParametersNode):
        return

    elif isinstance(node, RangeLiteralExprNode):
        return

    elif isinstance(node, ArrayLiteralElementsNode):
        exprs = node.exprs
        if len(exprs) == 2:
            c = VlVec2
        elif len(exprs) == 3:
            c = VlVec3
        elif len(exprs) == 4:
            c = VlVec4
        else:
            raise ValueError("Expected array literal to have length 2, 3, or 4")
        exprs = [eval_vl(n, state) for n in exprs]
        return c(exprs)

    elif isinstance(node, ArrayLiteralExprNode):
        return eval_vl(node.elements, state)

    elif isinstance(node, MemberAccessExprNode):
        node_val = eval_vl(node.target, state)
        if node.name.name in node_val.get_attributes():
            attr_val = node_val.get_attributes()[node.name.name](node_val)
            return attr_val
        if node.name.name in node_val.get_methods():
            return node_val.get_methods()[node.name.name]

        else:
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

        try:
            callee_val = eval_vl(node.callee, state)
            if isinstance(callee_val, VlFunction):
                arg_vals = []
                for param_t, argument in zip(
                    callee_val.arg_types, node.arguments.arguments
                ):
                    argument_val = eval_vl(argument, state)
                    actual_type = argument_val.get_type_name()
                    if param_t != actual_type:
                        raise ValueError(
                            f"Expected parameter to be of type {param_t}, not {actual_type}"
                        )
                    arg_vals.append(argument_val)
                return callee_val.fn(*arg_vals)
        except:
            pass

        if state["in_function"]:
            raise ValueError("Nested functions are not supported")

        fn = resolve_fn(node.callee.name, state)
        expected_parameters = len(fn.parameters.parameters)
        actual_parameters = len(node.arguments.arguments)
        if expected_parameters != actual_parameters:
            raise ValueError(f"Expected {expected_parameters}, got {actual_parameters}")

        new_locals = {}
        for parameter, argument in zip(
            fn.parameters.parameters, node.arguments.arguments
        ):
            parameter: FunctionDeclParameterNode

            argument_val = eval_vl(argument, state)
            expected_type = parameter.type.name
            actual_type = argument_val.get_type_name()
            if expected_type != actual_type:
                raise ValueError(
                    f"Expected parameter '{parameter.name}' to be of type {expected_type}, not {actual_type}"
                )
            new_locals[parameter.name.name] = argument_val

        state["in_function"] = True
        state["local_vars"].update(new_locals)

        eval_vl(fn.stmts, state)
        return_val = state["function_ret_val"]
        for local_var in new_locals:
            del state["local_vars"][local_var]

        state["in_function"] = False
        state["function_ret_val"] = None

        if return_val.get_type_name() != fn.return_type.name:
            raise ValueError(
                f"Expected return type of function to be '{fn.return_type.get_node_type_str()}', got '{return_val.get_type_name()}'"
            )

        return return_val

    elif isinstance(node, BinaryOperationExprNode):
        left = eval_vl(node.left, state)
        right = eval_vl(node.right, state)
        operator = node.operator

        left_t = left.get_type_name()
        right_t = right.get_type_name()

        exec_fn = None
        # resolve internal function
        if (left_t, operator, right_t) in BINARY_OPERATIONS:
            _, exec_fn = BINARY_OPERATIONS[(left_t, operator, right_t)]
        else:
            # try casting right hand side
            for right_into_t in right.get_type_into():
                if (left_t, operator, right_into_t) in BINARY_OPERATIONS:
                    right = right.get_type_into()[right_into_t](right)
                    _, exec_fn = BINARY_OPERATIONS[(left_t, operator, right_into_t)]
                    break

            if not exec_fn:
                # try casting left hand side
                for left_into_t in left.get_type_into():
                    if (left_into_t, operator, right_t) in BINARY_OPERATIONS:
                        left = left.get_type_into()[left_into_t](left)
                        _, exec_fn = BINARY_OPERATIONS[(left_into_t, operator, right_t)]
                        break

        if not exec_fn:
            raise ValueError(
                f"Operator '{operator}' not supported between instances of '{left_t}' and '{right_t}' (exhausted possible casts)"
            )

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
        elif isinstance(node.value.value, float):
            return VlReal(node.value.value)
        elif isinstance(node.value.value, complex):
            return VlComplex(node.value.value)
        else:
            raise ValueError(f"Constant type '{node.value.type}' not implemented yet")

    elif isinstance(
        node, (AttributeTagValuesNode, AttributeTagNode, AttributeTagsNode)
    ):
        return

    elif isinstance(node, FunctionDeclNode):
        if state["in_function"]:
            raise ValueError("Cannot declare function inside function")
        state["fns"].append(node)
        return

    elif isinstance(node, VariableDeclNode):
        expr = eval_vl(node.value, state)
        expr_t = expr.get_type_name()
        expected_t = node.vl_type.name

        if expected_t != expr_t:
            if expected_t in expr.get_type_into():
                expr = expr.get_type_into()[expected_t](expr)
            else:
                raise ValueError(f"Expected type '{expected_t}', got type '{expr_t}'")

        if state["in_function"]:
            state["local_vars"][node.target.name] = expr
        else:
            state["global_vars"][node.target.name] = expr

    elif isinstance(node, ConstantDeclNode):
        expr = eval_vl(node.value, state)
        expr_t = expr.get_type_name()
        expected_t = node.vl_type.name

        if expected_t != expr_t:
            if expected_t in expr.get_type_into():
                expr = expr.get_type_into()[expected_t](expr)
            else:
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
                # attempt cast
                if expected_t in expr.get_type_into():
                    expr = expr.get_type_into()[expected_t](expr)
                else:
                    raise ValueError(
                        f"Expected type '{expected_t}', got type '{expr_t}'"
                    )
            state["local_vars"][identifier] = expr

        else:
            expected_t = state["global_vars"][identifier].get_type_name()
            if expected_t != expr_t:
                # attempt cast
                if expected_t in expr.get_type_into():
                    expr = expr.get_type_into()[expected_t](expr)
                else:
                    raise ValueError(
                        f"Expected type '{expected_t}', got type '{expr_t}'"
                    )
            state["global_vars"][identifier] = expr

        return

    elif isinstance(node, AugmentedAssignmentStmtNode):
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

    elif isinstance(node, ForInitialisationStmtNode):
        return None

    elif isinstance(node, ForStmtNode):
        identifier = node.init_stmt.target.name
        try:
            resolve_var(identifier, state)
            raise ValueError(
                f"Identifier {identifier} is already in use, cannot be used for for loop"
            )
        except Exception:
            pass

        rg = node.init_stmt.value
        if not isinstance(rg, RangeLiteralExprNode):
            raise ValueError(f"For loop expected RangeLiteralExpr, got {type(rg)}")

        start = eval_vl(rg.start, state)
        end = eval_vl(rg.end, state)
        step = eval_vl(rg.step, state)

        if not isinstance(start, VlInt):
            raise ValueError(
                f"Start for range literal must be int, got {start.get_type_name()}"
            )
        if not isinstance(end, VlInt):
            raise ValueError(
                f"End for range literal must be int, got {end.get_type_name()}"
            )
        if not isinstance(step, VlInt):
            raise ValueError(
                f"Step for range literal must be int, got {step.get_type_name()}"
            )

        for val in range(start.value, end.value, step.value):
            if state["in_function"]:
                state["local_vars"][identifier] = VlInt(val)
            else:
                state["global_vars"][identifier] = VlInt(val)

            state["in_loop"] = True
            eval_vl(node.stmts, state)
            if state["loop_break"] or state["function_ret_val"]:
                state["loop_break"] = False
                break

        state["in_loop"] = False
        state["loop_break"] = False

    elif isinstance(node, WhileStmtNode):
        while True:
            condition = eval_vl(node.condition, state)
            if not isinstance(condition, VlBool):
                raise ValueError(
                    f"Expected condition to be bool, not '{condition.get_type_name()}'"
                )
            if not condition.value:
                break

            state["in_loop"] = True
            eval_vl(node.stmts, state)
            if state["loop_break"] or state["function_ret_val"]:
                state["loop_break"] = False
                break

        state["in_loop"] = False
        state["loop_break"] = False

    elif isinstance(node, (ReturnStmtNode, BreakStmtNode, ContinueStmtNode)):
        pass
        # these are all handled along with statements

    else:
        raise ValueError(f"Unknown node type {type(node)}")


def eval_full(ast_node: ProgramNode, state: InterpreterState | None = None):
    if state is None:
        state = create_new_state()
    return eval_vl(ast_node, state), state


def eval_all(input_str: str):
    # print(input_str)
    ast_node = parse(input_str)
    # print(pretty_print_ast(ast_node))
    out, state = eval_full(ast_node)
    print(f"Output: {out}")
    print("\n".join(state["stdout_buffer"]))


def eval_exp(s: str, state: InterpreterState) -> str:
    out_s: str = ""
    try:
        with io.StringIO() as buf, redirect_stdout(buf):
            ast_node = parse(s)
            output = buf.getvalue()

        if ast_node is None:
            ast_node = parse(s + ";")

        if ast_node is None:
            raise ValueError(f"Syntax error: {output}")

        out, state = eval_full(ast_node, state)
        if out:
            out_s = str(out)
        out_s += "\n".join(state["stdout_buffer"])
        state["stdout_buffer"].clear()

    except Exception as e:
        out_s += f"Error during execution: {e}"

        # reset state
        state["in_function"] = False
        state["in_loop"] = False
        state["loop_break"] = False

    return out_s


def eval_img(res_x: int, res_y: int, state: InterpreterState, output_fp: str) -> bool:
    arr = np.zeros(shape=(res_x, res_y, 3))

    for fn in state["fns"]:
        if (
            fn.attribute_tags.tags
            and fn.attribute_tags.tags[0]
            and fn.attribute_tags.tags[0].key.name == "generate_img"
        ):
            for y in range(res_y):
                print(y)
                for x in range(res_x):
                    try:
                        bp_info = ASTPositionInfo(0, 0)
                        function_call_arguments = FunctionCallArgumentsNode(
                            None, None, bp_info
                        )
                        function_call_arguments.arguments = [
                            ConstantExprNode(ConstantValue(x, "int"), bp_info),
                            ConstantExprNode(ConstantValue(y, "int"), bp_info),
                            ConstantExprNode(ConstantValue(res_x, "int"), bp_info),
                            ConstantExprNode(ConstantValue(res_y, "int"), bp_info),
                        ]
                        out = eval_vl(
                            FunctionCallExprNode(
                                IdentifierNode(fn.identifier.name, bp_info),
                                function_call_arguments,
                                bp_info,
                            ),
                            state,
                        )
                        if not isinstance(out, VlVec3):
                            raise ValueError(
                                "Image generating function should return type Vec3"
                            )
                        r = max(min(out.value[0].value, 255), 0)
                        g = max(min(out.value[1].value, 255), 0)
                        b = max(min(out.value[2].value, 255), 0)
                        arr[y][x] = [r, g, b]

                    except Exception as e:
                        print(f"Error during execution: {e}")

            image = Image.fromarray(arr.astype("uint8"), "RGB")
            image.save(output_fp)
            return True

    return False


if __name__ == "__main__":
    print("\n" * 10, "VECLANG 2.0 REPL ('exit' to exit)")
    state: InterpreterState = create_new_state()

    eval_full(
        parse(
            """
<generate_img>
fn mandlebrot(
    x: int,
    y: int,
    res_x: int,
    res_y: int
) -> vec3 {
    const ITERATIONS: int = 50;
    const THRESHOLD: real = 10.0;
    let c: complex = x / res_x + (y / res_y) * 1i;
    let z: complex = 0;
    for (_: int in 0:ITERATIONS) {
        if (z.re * z.re + z.im * z.im > THRESHOLD) {
            return [0, 0, 0];
        }
        z = z * z + c;
    }
    return [255, 255, 255];
}
    """
        ),
        state,
    )

    while True:
        try:
            s = input(">>> ")

            if s == "exit":
                break

            with io.StringIO() as buf, redirect_stdout(buf):
                ast_node = parse(s)
                output = buf.getvalue()

            if ast_node is None:
                ast_node = parse(s + ";")

            if ast_node is None:
                print(output)
                continue

            out, state = eval_full(ast_node, state)
            if out:
                print(f"{out}")
            print("\n".join(state["stdout_buffer"]))
            state["stdout_buffer"].clear()

        except Exception as e:
            print(f"Error during execution: {e}")

            # reset state
            state["in_function"] = False
            state["in_loop"] = False
            state["loop_break"] = False

    eval_img(255, 255, state, "out.png")

"""
<generate_img>
fn main(x: int, y: int, res_x: int, res_y: int) -> vec3 { return [255, 255, 255]; }

<generate_img>
fn mandlebrot(
    x: int,
    y: int,
    res_x: int,
    res_y: int
) -> vec3 {
    const ITERATIONS: int = 50;
    const THRESHOLD: real = 100;
    let c: complex = x / res_x + (y / res_y) * 1i;
    let z: complex = 0;
    for (_: int in 0:ITERATIONS) {
        if (z.re * z.re + z.im * z.im > THRESHOLD) {
            return [0, 0, 0];
        }
        z = z * z + c;
    }
    return [255, 255, 255];
}
"""
