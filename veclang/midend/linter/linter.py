"""Analyzer for functions"""

import typing
import warnings

import veclang.frontend.parser.vl_ast as ast

import veclang.midend.hir.vl_hir as hir

from veclang.midend.linter.util_types import (
    IdentifiedTypeProfiles,
    FunctionTypesProfile,
    LinterItem,
    LinterCodeLiteral,
)
import veclang.midend.hir.vl_types as vl_types

from veclang.midend.linter.util_case import (
    check_snake_case,
    check_constant_case,
)

from veclang.midend.linter.util_imports import (
    get_available_namespaces,
    get_available_functions,
)


def profile_function_types(
    ast_node: hir.FunctionDeclNode,
) -> FunctionTypesProfile:
    """Profiles the types used for a function"""
    return_type = ast_node.return_type.get_name()
    parameter_types = {x.name: x.vl_type for x in ast_node.parameters}
    return FunctionTypesProfile(parameter_types, return_type)


def format_operator(operator: ast.VlOperatorType) -> str:
    return {
        "PLUS_ASSIGNMENT": "+=",
        "MINUS_ASSIGNMENT": "-=",
        "TIMES_ASSIGNMENT": "*=",
        "DIVIDE_ASSIGNMENT": "/=",
        "MODULUS_ASSIGNMENT": "%=",
        "PLUS": "+",
        "MINUS": "-",
        "TIMES": "*",
        "DIVIDE": "/",
        "MODULUS": "%",
        "INTEGER_DIVIDE": "//",
        "EXPONENTIATION": "^",
        "BOOLEAN_AND": "&&",
        "BOOLEAN_OR": "||",
        "BITWISE_AND": "&",
        "BITWISE_OR": "|",
        "BITWISE_XOR": "^",
        "BITWISE_LEFT_SHIFT": "<<",
        "BITWISE_RIGHT_SHIFT": ">>",
        "EQUAL_TO": "==",
        "NOT_EQUAL_TO": "!=",
        "LESS_THAN": "<",
        "LESS_THAN_OR_EQUAL": "<=",
        "GREATER_THAN": ">",
        "GREATER_THAN_OR_EQUAL": ">=",
        "BOOLEAN_NOT": "!",
        "BITWISE_NOT": "~",
        "UNARY_PLUS": "+",
        "UNARY_MINUS": "-",
    }[type(operator)]


class Linter:

    def __init__(self):
        self.global_vars: IdentifiedTypeProfiles = {}
        self.global_consts: IdentifiedTypeProfiles = {}
        self.functions: dict[str, FunctionTypesProfile] = {}

        self.global_var_ref_count: typing.Dict[str, int] = {}
        self.global_const_ref_count: typing.Dict[str, int] = {}
        self.function_ref_count: typing.Dict[str, int] = {}
        self.stack_trace: typing.List = []

        # Other utility values
        self.ctx_function_name: str = ""
        self.ctx_function_return_type: str = ""
        self.ctx_loop_depth: int = 0

        self.ctx_last_position_info: ast.ASTPositionInfo = ast.ASTPositionInfo(0, 0)

        self.items: list[LinterItem] = []

    def emit_item(self, code: LinterCodeLiteral, message: str) -> None:
        self.items.append(
            LinterItem(
                self.ctx_last_position_info, code, ":".join(self.stack_trace), message
            )
        )

    def node(self, node: hir.HIRNode):
        self.ctx_last_position_info = node.position_info

    def lint_expr(self, node: hir.ExprNode) -> vl_types.VlType | None:
        self.node(node)
        if isinstance(node, hir.ConstantExprNode):
            if type(node.value.value) in {int, float, bool, None}:
                if isinstance(node.value.value, bool):
                    return vl_types.VlBool
                elif isinstance(node.value.value, int):
                    return vl_types.VlInt
                elif isinstance(node.value.value, float):
                    return vl_types.VlReal
                elif node.value.value is None:
                    return vl_types.VlNone
            self.emit_item("E400", f"Unknown constant type '{type(node.value.value)}'")
            return None


def lint_expression(
    node: ast.ExprNode,
    linter_context: LinterContext,
    flags: typing.Dict[str, bool],
) -> typing.Tuple[LinterItems, LinterContext, g_TYPE]:
    """Gets type of expression when evaluated"""
    if isinstance(
        node,
        (
            ast.BinaryOperationExpressionNode,
            ast.BooleanOperationExpressionNode,
            ast.ComparativeOperatorExpressionNode,
        ),
    ):
        # expressions with two operands
        # noinspection PyTypeChecker
        linter_items: LinterItems = []
        operator_name = operator_conversions[type(node.operator)]
        left = lint_expression(node.left, linter_context, flags)
        if left[0]:
            linter_items.extend(left[0])
        right = lint_expression(node.right, linter_context, flags)
        if right[0]:
            linter_items.extend(right[0])

        if (left[2], operator_name, right[2]) in AllAllowedOperations:
            return (
                linter_items,
                linter_context,
                AllAllowedOperations[(left[2], operator_name, right[2])],
            )
        else:
            linter_items.append(
                LinterError(
                    convert_pos_info(node.position_info),
                    "E100",
                    "<program>",
                    f"Operator {format_operator(node.operator)}"
                    f" not supported between instances of {left[2]} and {right[2]}",
                )
            )
            return (linter_items, linter_context, "NO_EVAL")

    elif isinstance(node, ast.UnaryOperatorExpressionNode):
        linter_items: LinterItems = []
        # noinspection PyTypeChecker
        operator_name = operator_conversions[type(node.operator)]
        linted = lint_expression(node.operand, linter_context, flags)
        if linted[0]:
            linter_items.extend(linted[0])
        if (linted[2], operator_name, "NO_EVAL") in AllAllowedOperations:
            return (
                linter_items,
                linter_context,
                AllAllowedOperations[(linted[2], operator_name, "NO_EVAL")],
            )
        else:
            linter_items.append(
                LinterError(
                    convert_pos_info(node.position_info),
                    "E100",
                    "<program>",
                    f"Operator {format_operator(node.operator)}"
                    f" not supported on instance of {linted[2]}",
                )
            )
            return (linter_items, linter_context, "NO_EVAL")

    elif isinstance(node, ast.FunctionCallExpressionNode):
        # noinspection PyTypeChecker
        linter_items: LinterItems = []
        function_name = node.callee.full_name()

        if function_name == linter_context["current_function_name"]:
            linter_items.append(
                LinterError(
                    convert_pos_info(node.position_info),
                    "E301",
                    "<program>",
                    f"E301: Potential for recursion",
                )
            )
            return (linter_items, linter_context, "NO_EVAL")

        if function_name in linter_context["functions"]:
            # check that function signature matches
            num_args = len(node.arguments.arguments)
            expected_num_args = len(
                linter_context["functions"][function_name].input_types
            )
            if num_args != expected_num_args:
                linter_items.append(
                    LinterError(
                        convert_pos_info(node.position_info),
                        "E210",
                        "<program>",
                        f"E210: Function {function_name} expects {expected_num_args} arguments, "
                        f"not {num_args} arguments",
                    )
                )
                return (linter_items, linter_context, "NO_EVAL")

            for idx, (arg_node, expected_arg_type) in enumerate(
                zip(
                    node.arguments.arguments,
                    linter_context["functions"][function_name].input_types,
                )
            ):
                expected_arg_type_name = expected_arg_type.type_name
                expression_linted = lint_expression(arg_node, linter_context, flags)
                if expression_linted[0]:
                    linter_items.extend(expression_linted[0])
                if expected_arg_type_name != expression_linted[2]:
                    linter_items.append(
                        LinterError(
                            convert_pos_info(node.position_info),
                            "E211",
                            "<program>",
                            f"E211: Function {function_name} expects parameter #{idx} to be type"
                            f" {expected_arg_type_name}, not type {expression_linted[2]}",
                        )
                    )

            linter_context["function_ref_count"][function_name] += 1

            return (linter_items, linter_context, "NO_EVAL")

        else:
            linter_items.append(
                LinterError(
                    convert_pos_info(node.position_info),
                    "E200",
                    "<program>",
                    f"Unresolved identifier {node.callee.full_name()}",
                )
            )
            return (linter_items, linter_context, "NO_EVAL")

    elif isinstance(node, ast.NamedObjectExpression):
        # noinspection PyTypeChecker
        linter_items = []
        object_name = node.full_name()
        if object_name == "output_data":
            linter_items.append(
                LinterError(
                    convert_pos_info(node.position_info),
                    "E201",
                    "<program>",
                    f"'{object_name} is a reserved name",
                )
            )
            return (linter_items, linter_context, "NO_EVAL")

        if object_name in linter_context["identifiers"]:
            linter_context["identifier_ref_count"][object_name] += 1
            # noinspection PyTypeChecker
            return (
                linter_items,
                linter_context,
                linter_context["identifiers"][object_name].type_name,
            )
        else:
            linter_items.append(
                LinterError(
                    convert_pos_info(node.position_info),
                    "E200",
                    "<program>",
                    f"Unresolved identifier {object_name}",
                )
            )
            return (linter_items, linter_context, "NO_EVAL")

    elif isinstance(node, ast.SubscriptionExpressionNode):
        pass

    elif isinstance(node, ast.SmartSubscriptionExpressionNode):
        # smart subscription always returns a float
        linter_items = []
        object_name = node.target.full_name()
        if object_name in linter_context["identifiers"]:
            linter_context["identifier_ref_count"][object_name] += 1
            # noinspection PyTypeChecker
            return ([], linter_context, "float")
        else:
            linter_items.append(
                LinterError(
                    convert_pos_info(node.position_info),
                    "E200",
                    "<program>",
                    f"Unresolved identifier {object_name}",
                )
            )
            return (linter_items, linter_context, "NO_EVAL")

    else:
        warnings.warn(f"i dont know how to handle {type(node)}")

    return ([], linter_context, "NO_EVAL")


def lint_statements(
    node: ast.ASTNode, linter_context: LinterContext, flags: typing.Dict[str, bool]
) -> typing.Tuple[LinterItems, LinterContext]:
    # noinspection PyTypeChecker
    operator_conversions: typing.Dict[ast.ASTNode, g_OPERATOR] = {
        ast.AssignmentStmtNode: "assignment",
        ast.AdditionBinaryOperatorNode: "binary_plus",
        ast.SubtractionBinaryOperatorNode: "binary_minus",
        ast.MultiplicationBinaryOperatorNode: "binary_multiply",
        ast.DivisionBinaryOperatorNode: "binary_divide",
        ast.IntegerDivisionBinaryOperatorNode: "binary_integer_divide",
        ast.ModulusBinaryOperatorNode: "binary_modulus",
        ast.ExponentiationBinaryOperatorNode: "binary_exponentiation",
        ast.InplaceAdditionBinaryOperatorNode: "binary_inplace_plus",
        ast.InplaceSubtractionBinaryOperatorNode: "binary_inplace_minus",
        ast.InplaceMultiplicationBinaryOperatorNode: "binary_inplace_multiply",
        ast.InplaceDivisionBinaryOperatorNode: "binary_inplace_divide",
        ast.EqualToComparativeOperatorNode: "comparative_equality",
        ast.NotEqualToComparativeOperatorNode: "comparative_inequality",
        ast.LessThanComparativeOperatorNode: "comparative_less_than",
        ast.LessThanOrEqualToComparativeOperatorNode: "comparative_less_than_or_equal",
        ast.GreaterThanComparativeOperatorNode: "comparative_greater_than",
        ast.GreaterThanOrEqualToComparativeOperatorNode: "comparative_greater_than_or_equal",
        ast.AndBooleanOperatorNode: "boolean_and",
        ast.OrBooleanOperatorNode: "boolean_or",
        ast.NegatorUnaryOperatorNode: "unary_not",
    }

    linter_items: LinterItems = []

    # PROGRAM NODES
    # ----------------------------------------

    if isinstance(node, ast.ProgramNode):
        # lint the program node:
        linter_context["current_function_name"] = ""
        linter_context["stack_trace"] = ["<program>"]

        using_statements_linted = lint_statements(
            node.using_statements, linter_context, flags
        )
        if using_statements_linted[0]:
            linter_items.extend(using_statements_linted[0])

        if flags.pop("strict", False):
            # Strict mode
            for x in node.declarations.declarations:
                if not isinstance(x, ast.FunctionDeclarationStmtNode):
                    linter_items.append(
                        LinterError(
                            convert_pos_info(node.position_info),
                            "E011",
                            "<program>",
                            f"Usage of forbidden language features in strict mode",
                        )
                    )
                    return linter_items, linter_context

                else:
                    linter_context["functions"][x.identifier] = FunctionTypesProfile(
                        type_specifier_node_to_type_profile(x.return_type),
                        declaration_arguments_list_node_to_identified_type_profiles(
                            x.arguments
                        ),
                    )

            if "main" not in linter_context["functions"]:
                linter_items.append(
                    LinterError(
                        convert_pos_info(node.position_info),
                        "E000",
                        "<program>",
                        f"No main function in program",
                    )
                )
                return linter_items, linter_context

            if linter_context["functions"]["main"].return_type.type_name != "boolean":
                linter_items.append(
                    LinterError(
                        convert_pos_info(node.position_info),
                        "E001",
                        "<program>",
                        f"Function main should have return type boolean",
                    )
                )
                return linter_items, linter_context

            num_functions = len(
                [
                    x
                    for x in node.declarations.declarations
                    if isinstance(x, ast.FunctionDeclarationStmtNode)
                ]
            )
            if num_functions > 1:
                linter_items.append(
                    LinterError(
                        convert_pos_info(node.position_info),
                        "E002",
                        "<program>",
                        f"E002: Only function main should be declared",
                    )
                )
                return linter_items, linter_context

            if len(node.declarations.declarations) > 1:
                if num_functions > 1:
                    linter_items.append(
                        LinterError(
                            convert_pos_info(node.position_info),
                            "E011",
                            "<program>",
                            f"E011: Usage of forbidden language features - "
                            f"initialization in program body",
                        )
                    )
                    return linter_items, linter_context

            linter_context["stack_trace"].append("main")
            linter_context["current_function_name"] = "main"
            linter_context["current_function_return_type_name"] = linter_context[
                "functions"
            ]["main"].return_type.type_name

            return lint_statements(
                node.declarations.declarations[0], linter_context, flags
            )

        else:
            num_functions = len(
                [
                    x
                    for x in node.declarations.declarations
                    if isinstance(x, ast.FunctionDeclarationStmtNode)
                ]
            )
            if num_functions > 1:
                # TODO: temp guard against multiple functions
                linter_items.append(
                    LinterError(
                        convert_pos_info(node.position_info),
                        "E002",
                        "<program>",
                        f"E002: Only function main should be declared",
                    )
                )
                return linter_items, linter_context

            # just get the initializations and function definitions
            for x in node.declarations.declarations:
                if isinstance(x, ast.FunctionDeclarationStmtNode):
                    linter_context["functions"][x.identifier] = FunctionTypesProfile(
                        type_specifier_node_to_type_profile(x.return_type),
                        declaration_arguments_list_node_to_identified_type_profiles(
                            x.arguments
                        ),
                    )

            if "main" not in linter_context["functions"]:
                linter_items.append(
                    LinterError(
                        convert_pos_info(node.position_info),
                        "E000",
                        "<program>",
                        f"No main function in program",
                    )
                )
                return linter_items, linter_context

            for x in node.declarations.declarations:
                if isinstance(x, ast.FunctionDeclarationStmtNode):
                    linter_context["stack_trace"].append(x.identifier)
                    linter_context["current_function_name"] = x.identifier
                    linter_context["current_function_return_type_name"] = (
                        linter_context["functions"]["main"].return_type.type_name
                    )
                linter_items.extend(lint_statements(x, linter_context, flags)[0])

    # INITIALIZATION NODES
    # ----------------------------------------

    elif isinstance(node, ast.InitializationStmtNode):
        if (
            node.target.full_name() in linter_context["functions"]
            or node.target.full_name() in linter_context["identifiers"]
        ):
            linter_items.append(
                LinterError(
                    convert_pos_info(node.position_info),
                    "E201",
                    "<program>",
                    f"Identifier {node.target.full_name()} has already been initialized",
                )
            )
        if node.init_type.qualifier == "input":
            linter_items.append(
                LinterError(
                    convert_pos_info(node.position_info),
                    "E106",
                    "<program>",
                    f"Type qualifier input used outside of function declaration",
                )
            )
        elif node.init_type.qualifier == "optimized":
            linter_items.append(
                LinterError(
                    convert_pos_info(node.position_info),
                    "E107",
                    "<program>",
                    f"Type qualifier optimized used outside of function declaration",
                )
            )
        elif node.init_type.qualifier == "output":
            linter_items.append(
                LinterError(
                    convert_pos_info(node.position_info),
                    "E108",
                    "<program>",
                    f"Type qualifier output used outside of function declaration",
                )
            )

        if node.init_type.qualifier == "constant":
            if not check_constant_case(node.target.full_name()):
                linter_items.append(
                    LinterWeakWarning(
                        convert_pos_info(node.position_info),
                        "X000",
                        "<program>",
                        f"X000: `constant` identifier {node.target.full_name()} should be uppercase CONSTANT_CASE",
                    )
                )
        else:
            if not check_snake_case(node.target.full_name()):
                linter_items.append(
                    LinterWeakWarning(
                        convert_pos_info(node.position_info),
                        "X001",
                        "<program>",
                        f"X001: variable identifier {node.target.full_name()} should be lowercase snake_case",
                    )
                )

        linted = lint_expression(node.value, linter_context, flags)
        if linted[0]:
            linter_items.extend(linted[0])

        if linted[2] != node.init_type.type_name:
            linter_items.append(
                LinterError(
                    convert_pos_info(node.position_info),
                    "E101",
                    "<program>",
                    f"Variable {node.target.full_name()} is type {node.init_type.type_name},"
                    f" got type {linted[2]}",
                )
            )
        if node.init_type.qualifier == "constant":
            if not isinstance(node.value, ast.ConstantExpressionNode):
                linter_items.append(
                    LinterError(
                        convert_pos_info(node.position_info),
                        "E120",
                        "<program>",
                        f"E120: Assignment of non-constant expression to "
                        f"constant {node.target.full_name()}",
                    )
                )
        elif node.init_type.type_name in {"mdata", "idata", "odata"}:
            linter_items.append(
                LinterError(
                    convert_pos_info(node.position_info),
                    "E123",
                    "<program>",
                    f"E123: Illegal initialization type {node.init_type.type_name}",
                )
            )

        linter_context["identifiers"][node.target.full_name()] = TypeProfile(
            node.init_type.type_name, node.init_type.qualifier
        )
        linter_context["identifier_ref_count"][node.target.full_name()] = 0

    # ASSIGNMENT NODES
    # ----------------------------------------

    elif isinstance(node, ast.AssignmentStmtNode):
        # lint the named object
        target_linted = lint_expression(node.target, linter_context, flags)
        if target_linted[0]:
            linter_items.extend(target_linted[0])
            # return early because there might be an unresolved reference
            return linter_items, linter_context

        # assume that the named object does exist now
        target_type = linter_context["identifiers"][node.target.full_name()]
        if target_type.type_qualifier == "constant":
            linter_items.append(
                LinterError(
                    convert_pos_info(node.position_info),
                    "E121",
                    "<program>",
                    f"E121: Assignment to constant object {node.target.full_name()} after initialization",
                )
            )
        elif target_type.type_qualifier == "optimized":
            linter_items.append(
                LinterError(
                    convert_pos_info(node.position_info),
                    "E122",
                    "<program>",
                    f"E122: E122: Assignment to optimized object {node.target.full_name()}",
                )
            )

        # add one to reference count
        linter_context["identifier_ref_count"][node.target.full_name()] += 1

        # lint the value
        value_linted = lint_expression(node.value, linter_context, flags)
        if value_linted[0]:
            linter_items.extend(value_linted[0])
            # return early because there might be an unresolved reference
            return linter_items, linter_context

        if value_linted[2] != target_type.type_name:
            linter_items.append(
                LinterError(
                    convert_pos_info(node.position_info),
                    "E101",
                    "<program>",
                    f"E101: Variable {node.target.full_name()} is type {target_type.type_name}, "
                    f"got type {value_linted[2]}",
                )
            )

    # AUGMENTED ASSIGNMENT NODES
    # ----------------------------------------

    elif isinstance(node, ast.AugmentedAssignmentStmtNode):
        # lint the named object
        target_linted = lint_expression(node.target, linter_context, flags)
        if target_linted[0]:
            linter_items.extend(target_linted[0])
            # return early because there might be an unresolved reference
            return linter_items, linter_context

        # assume that the named object does exist now
        target_type = linter_context["identifiers"][node.target.full_name()]
        if target_type.type_qualifier == "constant":
            linter_items.append(
                LinterError(
                    convert_pos_info(node.position_info),
                    "E121",
                    "<program>",
                    f"E121: Assignment to constant object {node.target.full_name()} after initialization",
                )
            )
        elif target_type.type_qualifier == "optimized":
            linter_items.append(
                LinterError(
                    convert_pos_info(node.position_info),
                    "E122",
                    "<program>",
                    f"E122: Assignment to optimized object {node.target.full_name()}",
                )
            )

        # add one to reference count
        linter_context["identifier_ref_count"][node.target.full_name()] += 1

        # lint the value
        value_linted = lint_expression(node.value, linter_context, flags)
        if value_linted[0]:
            linter_items.extend(value_linted[0])
            # return early because there might be an unresolved reference
            return linter_items, linter_context

        # check if target, operator, and value work together
        # noinspection PyTypeChecker
        if (
            target_type.type_name,
            operator_conversions[type(node.operator)],
            value_linted[2],
        ) not in AllAllowedOperations:
            linter_items.append(
                LinterError(
                    convert_pos_info(node.position_info),
                    "E100",
                    "<program>",
                    f"E100: Operator {format_operator(node.operator)} not "
                    f"supported between instances of {target_type.type_name} and {value_linted[2]}",
                )
            )

    # FUNCTION DECLARATION NODES
    # ----------------------------------------

    elif isinstance(node, ast.FunctionDeclarationStmtNode):
        # check the types
        if node.return_type.qualifier != "output":
            linter_items.append(
                LinterError(
                    convert_pos_info(node.position_info),
                    "E105",
                    "<program>",
                    f"E105: Expected return qualified type to have type qualifier output,"
                    f" got type qualifier {node.return_type.qualifier}",
                )
            )

        for x in node.arguments.arguments:
            if x.type.qualifier not in {"input", "optimized"}:
                linter_items.append(
                    LinterError(
                        convert_pos_info(node.position_info),
                        "E104",
                        "<program>",
                        f"E104: Expected parameter qualified type to have type qualifier input or optimized,"
                        f" got type qualifier {x.type.qualifier}",
                    )
                )
                continue
            if not check_snake_case(x.name.full_name()):
                linter_items.append(
                    LinterWeakWarning(
                        convert_pos_info(node.position_info),
                        "X001",
                        "<program>",
                        f"X001: {x.type.qualifier} identifier {x.name.full_name()} should be lowercase snake_case",
                    )
                )
            linter_context["identifiers"][x.name.full_name()] = TypeProfile(
                x.type.type_name, x.type.qualifier
            )
            linter_context["identifier_ref_count"][x.name.full_name()] = 0

        linter_items.extend(lint_statements(node.statements, linter_context, flags)[0])

    # STATEMENT LIST NODES
    # ----------------------------------------

    elif isinstance(node, ast.StmtsListNode):
        last_node_idx = len(node.statements) - 1
        num_breaks = len(
            [x for x in node.statements if isinstance(x, ast.BreakStmtNode)]
        )
        num_continues = len(
            [x for x in node.statements if isinstance(x, ast.ContinueStmtNode)]
        )
        num_returns = len(
            [x for x in node.statements if isinstance(x, ast.ReturnStmtNode)]
        )
        if num_returns > 1:
            linter_items.append(
                LinterError(
                    convert_pos_info(node.position_info),
                    "E320",
                    "<program>",
                    f"E313: More than one return statement in statement list",
                )
            )
            return linter_items, linter_context

        if num_breaks != 0 and linter_context["current_loop_depth"] == 0:
            linter_items.append(
                LinterError(
                    convert_pos_info(node.position_info),
                    "E310",
                    "<program>",
                    f"E310: Use of break statement outside of loop",
                )
            )
            return linter_items, linter_context

        if num_continues != 0 and linter_context["current_loop_depth"] == 0:
            linter_items.append(
                LinterError(
                    convert_pos_info(node.position_info),
                    "E311",
                    "<program>",
                    f"E311: Use of continue statement outside of loop",
                )
            )
            return linter_items, linter_context

        if num_breaks + num_continues > 1:
            linter_items.append(
                LinterError(
                    convert_pos_info(node.position_info),
                    "E312",
                    "<program>",
                    f"E312: More than one break or continue statement in statement list",
                )
            )
            return linter_items, linter_context

        in_if_chain = False

        for idx, sub_node in enumerate(node.statements):
            if isinstance(sub_node, ast.ReturnStmtNode) and idx != last_node_idx:
                linter_items.append(
                    LinterStrongWarning(
                        convert_pos_info(node.position_info),
                        "W010",
                        "<program>",
                        f"W010: Unreachable code after return statement",
                    )
                )
            elif isinstance(sub_node, ast.BreakStmtNode) and idx != last_node_idx:
                linter_items.append(
                    LinterStrongWarning(
                        convert_pos_info(node.position_info),
                        "W011",
                        "<program>",
                        f"W011: Unreachable code after break statement",
                    )
                )
            elif isinstance(sub_node, ast.ContinueStmtNode) and idx != last_node_idx:
                linter_items.append(
                    LinterStrongWarning(
                        convert_pos_info(node.position_info),
                        "W012",
                        "<program>",
                        f"W012: Unreachable code after continue statement",
                    )
                )
            if isinstance(sub_node, ast.FunctionDeclarationStmtNode):
                linter_items.append(
                    LinterError(
                        convert_pos_info(node.position_info),
                        "E300",
                        "<program>",
                        f"E300: Function declaration within function declaration",
                    )
                )
                continue

            # checks for if-elseif-else chains
            if isinstance(sub_node, ast.IfStmtNode):
                in_if_chain = True
            elif isinstance(sub_node, ast.ElseifStmtNode) and not in_if_chain:
                linter_items.append(
                    LinterError(
                        convert_pos_info(node.position_info),
                        "E330",
                        "<program>",
                        f"E330: Use of elseif statement not in an if-elseif-else chain",
                    )
                )
            elif isinstance(sub_node, ast.ElseStmtNode) and not in_if_chain:
                linter_items.append(
                    LinterError(
                        convert_pos_info(node.position_info),
                        "E331",
                        "<program>",
                        f"E331: Use of else statement not in an if-elseif-else chain",
                    )
                )

            if isinstance(sub_node, ast.ElseStmtNode):
                in_if_chain = False

            linter_items.extend(lint_statements(sub_node, linter_context, flags)[0])

    # USING STATEMENT LIST NODES
    # ----------------------------------------

    elif isinstance(node, ast.UsingStmtListNode):
        for x in node.statements:
            linted = lint_statements(x, linter_context, flags)
            if linted[0]:
                linter_items.extend(linted[0])

    # USING STATEMENT NODES
    # ----------------------------------------

    elif isinstance(node, ast.UsingStmtNode):
        namespace_name = node.named_object.namespace_name
        local_name = node.named_object.local_name
        full_name = node.named_object.full_name()
        if namespace_name not in linter_context["available_namespaces"]:
            linter_items.append(
                LinterError(
                    convert_pos_info(node.position_info),
                    "E400",
                    "<program>",
                    f"E400: Unknown namespace {namespace_name}",
                )
            )
            return linter_items, linter_context
        if full_name not in linter_context["namespace_available_functions"]:
            linter_items.append(
                LinterError(
                    convert_pos_info(node.position_info),
                    "E401",
                    "<program>",
                    f"E401: Unknown name {local_name} in namespace {namespace_name}",
                )
            )
            return linter_items, linter_context
        if full_name in linter_context["functions"]:
            linter_items.append(
                LinterError(
                    convert_pos_info(node.position_info),
                    "E410",
                    "<program>",
                    f"E410: Name {local_name} has already been imported from {namespace_name}",
                )
            )
            return linter_items, linter_context
        linter_context["functions"][full_name] = linter_context[
            "namespace_available_functions"
        ][full_name]
        linter_context["function_ref_count"][full_name] = 0

    # RETURN NODES
    # ----------------------------------------

    elif isinstance(node, ast.ReturnStmtNode):
        linted = lint_expression(node.value, linter_context, flags)
        if linted[0]:
            linter_items.extend(linted[0])

        if linted[2] != linter_context["current_function_return_type_name"]:
            linter_items.append(
                LinterError(
                    convert_pos_info(node.position_info),
                    "E102",
                    "<program>",
                    f"E102: Expected return type of {linter_context['current_function_return_type_name']},"
                    f" got type {linted[2]}",
                )
            )

    # FOR STATEMENT NODES
    # ----------------------------------------

    elif isinstance(node, ast.ForStmtNode):
        # lint the statements and expression
        init_statement_linted = lint_statements(node.init_stmt, linter_context, flags)
        if init_statement_linted[0]:
            linter_items.extend(init_statement_linted[0])

        test_expression_linted = lint_expression(
            node.test_expression, linter_context, flags
        )
        if test_expression_linted[0]:
            linter_items.extend(test_expression_linted[0])
        if test_expression_linted[2] != "boolean":
            linter_items.append(
                LinterError(
                    convert_pos_info(node.position_info),
                    "E113",
                    "<program>",
                    f"E113: for statement condition should be type boolean, got type {test_expression_linted[2]}",
                )
            )

        update_statement_linted = lint_statements(
            node.update_statement, linter_context, flags
        )
        if update_statement_linted[0]:
            linter_items.extend(update_statement_linted[0])

        # add one to loop depth
        linter_context["current_loop_depth"] += 1

        # lint the statements inside the for loop
        statements_linted = lint_statements(node.stmts, linter_context, flags)
        if statements_linted[0]:
            linter_items.extend(statements_linted[0])

        # subtract one from loop depth
        linter_context["current_loop_depth"] -= 1

    # WHILE STATEMENT NODES
    # ----------------------------------------

    elif isinstance(node, ast.WhileStmtNode):
        condition_linted = lint_expression(node.condition, linter_context, flags)
        if condition_linted[0]:
            linter_items.extend(condition_linted[0])
        if condition_linted[2] != "boolean":
            linter_items.append(
                LinterError(
                    convert_pos_info(node.position_info),
                    "E112",
                    "<program>",
                    f"E112: while statement condition should be type boolean, got type {condition_linted[2]}",
                )
            )

        # add one to loop depth
        linter_context["current_loop_depth"] += 1

        # lint the statements inside the while loop
        statements_linted = lint_statements(node.stmts, linter_context, flags)
        if statements_linted[0]:
            linter_items.extend(statements_linted[0])

        # subtract one from loop depth
        linter_context["current_loop_depth"] -= 1

    # IF STATEMENT NODES
    # ----------------------------------------

    elif isinstance(node, ast.IfStmtNode):
        condition_linted = lint_expression(node.condition, linter_context, flags)
        if condition_linted[0]:
            linter_items.extend(condition_linted[0])
        if condition_linted[2] != "boolean":
            linter_items.append(
                LinterError(
                    convert_pos_info(node.position_info),
                    "E110",
                    "<program>",
                    f"E110: if statement condition should be type boolean, got type {condition_linted[2]}",
                )
            )
        # lint the statements inside the if statement
        statements_linted = lint_statements(node.stmts, linter_context, flags)
        if statements_linted[0]:
            linter_items.extend(statements_linted[0])

    # ELSEIF STATEMENT NODES
    # ----------------------------------------

    elif isinstance(node, ast.ElseifStmtNode):
        condition_linted = lint_expression(node.condition, linter_context, flags)
        if condition_linted[0]:
            linter_items.extend(condition_linted[0])
        if condition_linted[2] != "boolean":
            linter_items.append(
                LinterError(
                    convert_pos_info(node.position_info),
                    "E111",
                    "<program>",
                    f"E111: elseif statement condition should be type boolean, got type {condition_linted[2]}",
                )
            )
        # lint the statements inside the elseif statement
        statements_linted = lint_statements(node.stmts, linter_context, flags)
        if statements_linted[0]:
            linter_items.extend(statements_linted[0])

    # ELSE STATEMENT NODES
    # ----------------------------------------

    elif isinstance(node, ast.ElseStmtNode):
        # lint the statements inside the else statement
        statements_linted = lint_statements(node.stmts, linter_context, flags)
        if statements_linted[0]:
            linter_items.extend(statements_linted[0])

    elif isinstance(node, ast.FunctionCallExprNode):
        # treated as expression
        linted = lint_expression(node, linter_context, flags)
        if linted[0]:
            linter_items.extend(linted[0])

    # BREAK AND CONTINUE NODES
    # ----------------------------------------

    elif isinstance(
        node,
        (
            ast.BreakStmtNode,
            ast.ContinueStmtNode,
        ),
    ):
        # skip these nodes because they can only be linted with more context
        # from higher up in the stack
        pass

    else:
        warnings.warn(
            f"The linter does not know how to handle nodes of type {type(node)}"
        )

    return linter_items, linter_context


def lint_program(
    program_node: ast.ProgramNode, flags: typing.Dict[str, bool]
) -> typing.Tuple[LinterItems, LinterContext]:
    linter_items, linter_context = lint_statements(
        program_node,
        {
            "identifiers": {},
            "functions": {},
            "identifier_ref_count": {},
            "function_ref_count": {},
            "available_namespaces": get_available_namespaces(),
            "namespace_available_functions": get_available_functions(),
            "stack_trace": [],
            "current_function_name": "",
            "current_function_return_type_name": "",
            "current_loop_depth": 0,
        },
        flags,
    )

    # perform additional checks
    for identifier_name, ref_count in linter_context["identifier_ref_count"].items():
        if ref_count == 0:
            linter_items.append(
                LinterStrongWarning(
                    PositionInfo(0, 0),
                    "W020",
                    "<program>",
                    f"W020: Identifier {identifier_name} is never used",
                )
            )

    for function_name, ref_count in linter_context["function_ref_count"].items():
        if ref_count == 0:
            linter_items.append(
                LinterStrongWarning(
                    PositionInfo(0, 0),
                    "W021",
                    "<program>",
                    f"W021: Function {function_name} is never used",
                )
            )

    return linter_items, linter_context
