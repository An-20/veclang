"""High-level intermediate representation lowerer"""

import abc
import collections
import dataclasses
import typing

from veclang.frontend.parser import vl_ast
from veclang.frontend.parser.vl_parser import (
    AugmentedAssignmentOperatorType,
    BinaryOperatorType,
    UnaryOperatorType,
    ASTPositionInfo,
)

from veclang.midend.hir.vl_hir import (
    HIRNode,
    ExprNode,
    StmtNode,
    DeclNode,
    ProgramNode,
    RvalueIdentifierExprNode,
    FunctionCallExprNode,
    BinaryOperationExprNode,
    UnaryOperatorExprNode,
    ConstantExprNode,
    FunctionDeclNode,
    DataDeclNode,
    AssignmentStmtNode,
    AugmentedAssignmentStmtNode,
    ExprStmtNode,
    SelectionBlock,
    SelectionStackStmt,
    RangedForStmtNode,
    WhileStmtNode,
    ReturnStmtNode,
    BreakStmtNode,
    ContinueStmtNode,
)

from veclang.midend.vl_core import (
    VlType,
    VlTypeABC,
    VlTypeStr,
    VlTypeStrs,
    VlFunctionTypeProfile,
    VlFunctionParameterTypeProfile,
    VlNull,
    VlInt,
    VlReal,
    VlBool,
    VlComplex,
    VlMat2,
    VlMat3,
    VlMat4,
    VlVec2,
    VlVec3,
    VlVec4,
)

from veclang.midend.hir.vl_lowerer_utils import ScopeTracker


class Lowerer:

    def __init__(self):
        self.imported_constants: list[tuple[str, str]] = []
        self.imported_functions: list[tuple[str, str]] = []
        self.functions: dict[str, VlFunctionTypeProfile] = {
            "print": VlFunctionTypeProfile(
                "print", 0x0000, [VlFunctionParameterTypeProfile("arg", VlInt)], VlNull
            ),
            "printr": VlFunctionTypeProfile(
                "printr",
                0x0001,
                [VlFunctionParameterTypeProfile("arg", VlReal)],
                VlNull,
            ),
        }

        self.ctx_function_name: str | None = None
        self.ctx_scopes: ScopeTracker = ScopeTracker()

    def lower(self, ast_node: vl_ast.ProgramNode) -> ProgramNode:
        return ProgramNode(self.lower_stmts(ast_node.stmts), ast_node.position_info)

    @staticmethod
    def lower_vl_type(vl_type_str: str) -> VlType:
        if vl_type_str not in VlTypeStrs:
            raise ValueError(f"Unknown type '{vl_type_str}'")
        return {
            "int": VlInt,
            "real": VlReal,
            "bool": VlBool,
            "complex": VlComplex,
            "mat2": VlMat2,
            "mat3": VlMat3,
            "mat4": VlMat4,
            "vec2": VlVec2,
            "vec3": VlVec3,
            "vec4": VlVec4,
        }[vl_type_str]

    def lower_identifier_expr(
        self, expr: vl_ast.IdentifierNode
    ) -> RvalueIdentifierExprNode:
        # Not to be called when the identifier identifies a function
        identifier = expr.name
        vl_type_or_val, is_variable = self.ctx_scopes.resolve(identifier)
        vl_type = vl_type_or_val if is_variable else vl_type_or_val.__class__
        # TODO: FIXME FOR CONSTEXPR
        return RvalueIdentifierExprNode(identifier, False, vl_type, expr.position_info)

    @classmethod
    def try_widen_cast_expr(
        cls, expr: ExprNode, desired_type: VlTypeStr
    ) -> ExprNode | None:
        """Attempts a widening cast to cast expr into desired_type"""
        for cast in expr.vl_type.get_casts():
            if cast.to_type == desired_type:
                return FunctionCallExprNode(
                    cast.fn_id,
                    [expr],
                    expr.constexpr,
                    cls.lower_vl_type(cast.to_type),
                    expr.ast_position_info,
                    is_type_cast=True,
                )
        return None

    def lower_array_literal_expr(
        self, expr: vl_ast.ArrayLiteralExprNode
    ) -> FunctionCallExprNode:
        # TODO: Support matrices
        if len(expr.elements.exprs) in [2, 3, 4]:
            vl_type_str = f"vec{len(expr.elements.exprs)}"
        else:
            raise ValueError(
                f"Unsupported array literal with length {len(expr.elements.exprs)}"
            )

        is_constant_value = True
        elements = [self.lower_expr(x) for x in expr.elements.exprs]
        casted_elements = []
        for element in elements:
            if element.vl_type.to_vl_type_str() == "real":
                is_constant_value = is_constant_value and element.constexpr
                casted_elements.append(element)
                continue
            is_constant_value = False
            casted_element = self.try_widen_cast_expr(element, "real")
            if casted_element is None:
                # TODO: FIX error msg
                raise ValueError("Could not cast array literal element to real")
            casted_elements.append(casted_element)

        # TODO: Emitting a constant to add to constant table instead of calling the function
        constructor_fn_id = {"vec2": 0x1300, "vec3": 0x1301, "vec4": 0x1302}[
            vl_type_str
        ]
        return FunctionCallExprNode(
            constructor_fn_id,
            casted_elements,
            False,
            self.lower_vl_type(vl_type_str),
            expr.position_info,
        )

    def lower_member_access_expr(
        self, expr: vl_ast.MemberAccessExprNode
    ) -> FunctionCallExprNode:
        target = self.lower_expr(expr.target)
        identifier = expr.name.name
        # TODO: FIXME FOR METHODS
        for method in target.vl_type.get_properties():
            if identifier != method.name:
                continue
            return FunctionCallExprNode(
                method.fn_id,
                [target],
                False,
                self.lower_vl_type(method.return_type),
                expr.position_info,
                is_property=True,
            )
        else:
            raise ValueError(
                f"Member access on resolved type '{target.vl_type.to_vl_type_str()}' which does not have identifier '{identifier}'"
            )

    def lower_index_expr(self, expr: vl_ast.IndexExprNode) -> FunctionCallExprNode:
        """Call the underlying index fn"""
        pass

    def lower_function_call_expr(
        self, expr: vl_ast.FunctionCallExprNode
    ) -> FunctionCallExprNode:
        if expr.callee.name not in self.functions:
            raise ValueError("asdfas")
        function = self.functions[expr.callee.name]

        arguments: list[ExprNode] = [
            self.lower_expr(x) for x in expr.arguments.arguments
        ]
        if len(arguments) != len(function.parameters):
            raise ValueError("len(arguments) != len(function.parameters)")
        for argument, parameter in zip(arguments, function.parameters):
            if argument.vl_type != parameter.vl_type:
                raise ValueError("argument.vl_type != parameter.vl_type")

        function_profile = self.functions[expr.callee.name]
        return FunctionCallExprNode(
            function_profile.fn_id,
            arguments,
            False,
            function_profile.return_type,
            expr.position_info,
        )

    def lower_binary_operation_expr(
        self, expr: vl_ast.BinaryOperationExprNode
    ) -> BinaryOperationExprNode:
        left = self.lower_expr(expr.left)
        right = self.lower_expr(expr.right)
        operator = expr.operator

        # First, resolve operation simply
        operation = [
            x
            for x in left.vl_type.get_operations()
            if x.op_arity == "BINARY"
            and x.op_type == operator
            and x.operand_types == [right.vl_type.to_vl_type_str()]
        ]
        if len(operation) > 1:
            raise ValueError("Internal error: multiple operations found")
        if operation:
            operation = operation[0]
            return BinaryOperationExprNode(
                left,
                right,
                expr.operator,
                operation,
                False,
                self.lower_vl_type(operation.result_type),
                expr.position_info,
            )

        # Next, try coercing right
        for operation in left.vl_type.get_operations():
            if operation.op_arity != "BINARY" or operation.op_type != operator:
                continue
            right_widened = self.try_widen_cast_expr(right, operation.operand_types[0])
            if right_widened:
                return BinaryOperationExprNode(
                    left,
                    right_widened,
                    expr.operator,
                    operation,
                    False,
                    self.lower_vl_type(operation.result_type),
                    expr.position_info,
                )

        # Next, try coercing left
        for operation in right.vl_type.get_operations():
            if operation.op_arity != "BINARY" or operation.op_type != operator:
                continue
            left_widened = self.try_widen_cast_expr(left, operation.operand_types[0])
            if left_widened:
                return BinaryOperationExprNode(
                    left_widened,
                    right,
                    expr.operator,
                    operation,
                    False,
                    self.lower_vl_type(operation.result_type),
                    expr.position_info,
                )

    def lower_unary_operation_expr(
        self, expr: vl_ast.UnaryOperatorExprNode
    ) -> UnaryOperatorExprNode:
        operand = self.lower_expr(expr.operand)
        operator = expr.operator

        # TODO: FIXME for type casting, etc.
        operation = [
            x
            for x in operand.vl_type.get_operations()
            if x.op_arity == "UNARY" and x.op_type == operator
        ]
        if not operation:
            raise ValueError(
                f"Unsupported operation '{operator}' for '{operand.vl_type.to_vl_type_str()}'"
            )
        elif len(operation) > 1:
            raise ValueError("Internal error: multiple operations found")
        operation = operation[0]

        return UnaryOperatorExprNode(
            operand,
            expr.operator,
            operation,
            False,
            self.lower_vl_type(operation.result_type),
            expr.position_info,
        )

    def lower_constant_expr(self, expr: vl_ast.ConstantExprNode) -> ConstantExprNode:
        if isinstance(expr.value.value, int):
            value = VlInt(expr.value.value)
        elif isinstance(expr.value.value, bool):
            value = VlBool(expr.value.value)
        elif isinstance(expr.value.value, float):
            value = VlReal(expr.value.value)
        elif isinstance(expr.value.value, complex):
            value = VlComplex(expr.value.value)
        else:
            raise ValueError("TODO")

        return ConstantExprNode(
            value,
            True,
            self.lower_vl_type(expr.value.type),
            expr.position_info,
        )

    def lower_function_decl(self, decl: vl_ast.FunctionDeclNode) -> FunctionDeclNode:
        # Construct attribute tags
        attribute_tags_dict = {}
        for tag in decl.attribute_tags.tags:
            if tag.key.name in attribute_tags_dict:
                raise ValueError(f"TODO: Duplicate attribute tag key '{tag.key.name}'")
            if not tag.values:
                attribute_tags_dict[tag.key.name] = None
            else:
                tag_values = []
                for value in tag.values.values:
                    lowered_value = self.lower_expr(value)
                    if not isinstance(lowered_value, ConstantExprNode):
                        raise ValueError(
                            f"TODO: Attribute tag value (for key '{tag.key.name}') must be a constant value."
                        )
                    tag_values.append(lowered_value)
                attribute_tags_dict[tag.key.name] = tag_values

        identifier = decl.identifier.name
        parameters = [
            VlFunctionParameterTypeProfile(x.name.name, self.lower_vl_type(x.type.name))
            for x in decl.parameters.parameters
        ]
        return_type = self.lower_vl_type(decl.return_type.name)

        # Check for duplicate parameter identifiers
        parameters_counter = collections.Counter([x.identifier for x in parameters])
        has_duplicates = any([x > 1 for x in parameters_counter.values()])
        if has_duplicates:
            raise ValueError(
                f"Duplicate parameters given to function: {', '.join([k for k, v in parameters_counter.items() if v > 1])}"
            )

        self.ctx_scopes.scope_in_fn(decl.identifier.name, decl.position_info)
        for parameter in decl.parameters.parameters:
            self.ctx_scopes.init_variable(
                parameter.name.name, self.lower_vl_type(parameter.type.name)
            )
        stmts = self.lower_stmts(decl.stmts)
        self.ctx_scopes.scope_out_fn()

        return FunctionDeclNode(
            attribute_tags_dict,
            identifier,
            parameters,
            return_type,
            stmts,
            decl.position_info,
        )

    def lower_data_decl(
        self, decl: vl_ast.ConstantDeclNode | vl_ast.VariableDeclNode
    ) -> DataDeclNode:
        value_lowered = self.lower_expr(decl.value)
        vl_type = self.lower_vl_type(decl._type.name)

        if isinstance(decl, vl_ast.VariableDeclNode):
            self.ctx_scopes.init_variable(decl.target.name, vl_type)
        else:
            # check that we are assigning a ConstantValue
            # major bodge: it is acceptable to lower a constant to a variable instead
            # if it is the result of a type cast, as a temporary fix for assigning
            # complex literals, etc, until compile time constant folding / type casts
            # are implemented: TODO!
            if isinstance(value_lowered, ConstantExprNode):
                self.ctx_scopes.init_constant(decl.target.name, value_lowered.value)
            elif isinstance(value_lowered, FunctionCallExprNode):
                # FIXME!
                if not value_lowered.is_type_cast:
                    raise ValueError
                self.ctx_scopes.init_variable(decl.target.name, vl_type)
            else:
                raise ValueError

        if not value_lowered.vl_type.to_vl_type_str() == vl_type.to_vl_type_str():
            # Attempt a type widening cast
            value_widened = self.try_widen_cast_expr(
                value_lowered, vl_type.to_vl_type_str()
            )
            if value_widened:
                value_lowered = value_widened
            else:
                raise ValueError(
                    "value_lowered.vl_type == vl_type.to_vl_type_str(), could not widen cast"
                )

        return DataDeclNode(
            isinstance(decl, vl_ast.ConstantDeclNode),
            decl.target.name,
            self.lower_vl_type(decl._type.name),
            value_lowered,
            decl.position_info,
        )

    def lower_using_decl(self, decl: vl_ast.UsingDeclNode) -> None:
        # TODO: FIXME, add the identifiers to the ProgramNode

        # namespace_identifiers: a list of namespaces that have been imported
        # scoped_identifiers: a list of tuples of (namespace, identifier) that have been imported
        namespace_identifiers: list[str] | None = None
        scoped_identifiers: list[tuple[str, str]] | None = None

        if decl.namespace_identifiers:
            namespace_identifiers = [
                x.name for x in decl.namespace_identifiers.identifiers
            ]
        if decl.namespace_and_identifiers:
            namespace = decl.namespace_and_identifiers[0].name
            scoped_identifiers = [
                (namespace, x.name)
                for x in decl.namespace_and_identifiers[1].identifiers
            ]
        if decl.namespace_identifiers and decl.namespace_and_identifiers:
            raise ValueError(
                "TODO: Expected exactly one non-None argument for initializing UsingDeclNode from AST UsingDeclNode"
            )

        # TODO: RUN THE IMPORT then add to context

    def lower_assignment_stmt(self, stmt: vl_ast.AssignmentStmtNode) -> StmtNode:
        target = self.lower_expr(stmt.target)
        # TODO: add special handling for indexing and member access (lvalues)
        if not isinstance(target, RvalueIdentifierExprNode):
            raise ValueError("TODO")

        value_lowered = self.lower_expr(stmt.value)
        vl_type_or_val, is_variable = self.ctx_scopes.resolve(target.identifier)
        vl_type = vl_type_or_val if is_variable else vl_type_or_val.__class__
        if not is_variable:
            raise ValueError("Cant assign to a constant!")

        if not value_lowered.vl_type.to_vl_type_str() == vl_type.to_vl_type_str():
            # Attempt a type widening cast
            value_widened = self.try_widen_cast_expr(
                value_lowered, vl_type.to_vl_type_str()
            )
            if value_widened:
                value_lowered = value_widened
            else:
                raise ValueError(
                    "value_lowered.vl_type == vl_type.to_vl_type_str(), could not widen cast"
                )

        return AssignmentStmtNode(target.identifier, value_lowered, stmt.position_info)

    def lower_selection_stack_stmt(
        self, stmts: list[vl_ast.StmtNode]
    ) -> SelectionStackStmt:
        if not stmts:
            raise ValueError("Selection stack must not be empty")
        if not isinstance(stmts[0], vl_ast.IfStmtNode):
            raise ValueError("Selection stack must stack with an if statement.")
        if not all(isinstance(x, vl_ast.ElseifStmtNode) for x in stmts[1:-1]):
            raise ValueError(
                "Selection stack can only have elif statements in the middle."
            )
        if not isinstance(
            stmts[-1], (vl_ast.IfStmtNode, vl_ast.ElseifStmtNode, vl_ast.ElseStmtNode)
        ):
            raise ValueError(
                "Selection stack must only consist of if, else if, or else statements."
            )

        has_else = isinstance(stmts[-1], vl_ast.ElseStmtNode)
        if has_else and len(stmts) == 1:
            # TODO: FIXME
            pass

        # noinspection PyTypeChecker
        conditioned: list[vl_ast.IfStmtNode] = stmts[:-1] if has_else else stmts
        blocks = []
        for block in conditioned:
            self.ctx_scopes.scope_in_selection(
                "elseif" if isinstance(block, vl_ast.ElseifStmtNode) else "if",
                block.position_info,
            )
            blocks.append(
                SelectionBlock(
                    self.lower_expr(block.condition), self.lower_stmts(block.stmts)
                )
            )
            self.ctx_scopes.scope_out_selection()

        if has_else:
            else_stmt = stmts[-1]
            if not isinstance(else_stmt, vl_ast.ElseStmtNode):
                raise ValueError("UNREACHABLE")
            self.ctx_scopes.scope_in_selection("else", else_stmt.position_info)
            else_stmts = self.lower_stmts(else_stmt.stmts)
            self.ctx_scopes.scope_out_selection()

        else:
            else_stmts = None

        return SelectionStackStmt(blocks, else_stmts, stmts[0].position_info)

    def lower_ranged_for_stmt(self, stmt: vl_ast.ForStmtNode) -> RangedForStmtNode:
        identifier = stmt.init_stmt.target.name
        vl_type_str = stmt.init_stmt.init_type.name
        range_node = stmt.init_stmt.value
        if not isinstance(range_node, vl_ast.RangeLiteralExprNode):
            raise ValueError("TODO")
        if vl_type_str != "int":
            raise ValueError("TODO")

        # lower stmts with updated loop context
        self.ctx_scopes.scope_in_loop("for", stmt.position_info)
        self.ctx_scopes.init_variable(identifier, self.lower_vl_type(vl_type_str))
        stmts = self.lower_stmts(stmt.stmts)
        self.ctx_scopes.scope_out_loop()

        return RangedForStmtNode(
            identifier,
            self.lower_vl_type(stmt.init_stmt.init_type.name),
            self.lower_expr(range_node.start),
            self.lower_expr(range_node.end),
            self.lower_expr(range_node.step),
            stmts,
            stmt.position_info,
        )

    def lower_expr_stmt(self, stmt: vl_ast.ExprStmtNode) -> ExprStmtNode:
        return ExprStmtNode(self.lower_expr(stmt.expr), stmt.position_info)

    def lower_stmts(self, stmts: vl_ast.StmtsNode) -> list["StmtNode"]:
        out_stmts = []
        selection_stmts = []
        for stmt in stmts.stmts:
            # first, handle selection statements (because ordering matters)
            if isinstance(stmt, vl_ast.ElseifStmtNode):
                selection_stmts.append(stmt)
                continue
            if isinstance(stmt, vl_ast.ElseStmtNode):
                if selection_stmts and isinstance(
                    selection_stmts[-1], vl_ast.ElseStmtNode
                ):
                    raise ValueError("Multiple else statements in one selection block")
                selection_stmts.append(stmt)
                continue
            if selection_stmts:
                out_stmts.append(self.lower_selection_stack_stmt(selection_stmts))
                selection_stmts = []
            if isinstance(stmt, vl_ast.IfStmtNode):
                selection_stmts.append(stmt)
                continue

            # handle other statements now
            if isinstance(stmt, vl_ast.DeclNode):
                out_stmts.append(self.lower_decl(stmt))

            elif isinstance(stmt, vl_ast.AssignmentStmtNode):
                out_stmts.append(self.lower_assignment_stmt(stmt))

            elif isinstance(stmt, vl_ast.AugmentedAssignmentStmtNode):
                # TODO: FIXME
                pass

            elif isinstance(stmt, vl_ast.ForStmtNode):
                out_stmts.append(self.lower_ranged_for_stmt(stmt))

            elif isinstance(stmt, vl_ast.WhileStmtNode):
                # TODO: FIXME
                pass

            elif isinstance(stmt, vl_ast.BreakStmtNode):
                # TODO: check if in loop first
                out_stmts.append(BreakStmtNode(stmt.position_info))

            elif isinstance(stmt, vl_ast.ContinueStmtNode):
                # TODO: check if in loop first
                out_stmts.append(ContinueStmtNode(stmt.position_info))

            elif isinstance(stmt, vl_ast.ReturnStmtNode):
                # TODO: check if in fn first, and check ret type
                out_stmts.append(
                    ReturnStmtNode(self.lower_expr(stmt.value), stmt.position_info)
                )

            elif isinstance(stmt, vl_ast.ExprStmtNode):
                out_stmts.append(self.lower_expr_stmt(stmt))

            elif isinstance(stmt, vl_ast.CommentNode):
                pass
            else:
                raise ValueError(f"Unknown stmt type '{type(stmt)}'")

        # if there are still selection statements left over
        if selection_stmts:
            out_stmts.append(self.lower_selection_stack_stmt(selection_stmts))
        return out_stmts

    def lower_decl(self, decl: vl_ast.DeclNode) -> "DeclNode":
        if isinstance(decl, vl_ast.FunctionDeclNode):
            return self.lower_function_decl(decl)
        elif isinstance(decl, (vl_ast.VariableDeclNode, vl_ast.ConstantDeclNode)):
            return self.lower_data_decl(decl)
        else:
            raise ValueError(f"Unknown decl type '{type(decl)}'")

    def lower_expr(self, expr: vl_ast.ExprNode) -> "ExprNode":
        """Only to be called on rvalue exprs"""
        if isinstance(expr, vl_ast.IdentifierNode):
            return self.lower_identifier_expr(expr)
        elif isinstance(expr, vl_ast.ArrayLiteralExprNode):
            return self.lower_array_literal_expr(expr)
        elif isinstance(expr, vl_ast.MemberAccessExprNode):
            return self.lower_member_access_expr(expr)
        elif isinstance(expr, vl_ast.IndexExprNode):
            return self.lower_index_expr(expr)
        elif isinstance(expr, vl_ast.FunctionCallExprNode):
            return self.lower_function_call_expr(expr)
        elif isinstance(expr, vl_ast.BinaryOperationExprNode):
            return self.lower_binary_operation_expr(expr)
        elif isinstance(expr, vl_ast.UnaryOperatorExprNode):
            return self.lower_unary_operation_expr(expr)
        elif isinstance(expr, vl_ast.ConstantExprNode):
            return self.lower_constant_expr(expr)
        else:
            raise ValueError(f"Unknown expr type '{type(expr)}'")


def lower(ast_node: vl_ast.ProgramNode) -> ProgramNode:
    lowerer = Lowerer()
    return lowerer.lower(ast_node)
