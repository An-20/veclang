"""High-level intermediate representation lowerer"""

import abc
import dataclasses
import typing

from veclang.frontend.parser import vl_ast
from veclang.frontend.parser.parser import (
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
    IdentifierExprNode,
    ArrayLiteralExprNode,
    MemberAccessExprNode,
    IndexExprNode,
    FunctionCallExprNode,
    BinaryOperationExprNode,
    UnaryOperatorExprNode,
    ConstantExprNode,
    FunctionDeclNode,
    DataDeclNode,
    UsingDeclNode,
    AssignmentStmtNode,
    AugmentedAssignmentStmtNode,
    ExprStmtNode,
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


class Lowerer:

    def __init__(self):
        self.global_variables: dict[str, VlType] = {}
        self.global_constants: dict[str, VlTypeABC] = {}
        self.functions: dict[str, VlFunctionTypeProfile] = {
            "print": VlFunctionTypeProfile(
                "print", [VlFunctionParameterTypeProfile("arg", VlInt)], VlNull
            )
        }

        self.imported_constants: list[tuple[str, str]] = []
        self.imported_functions: list[tuple[str, str]] = []

        self.ctx_function_name: str | None = None
        self.ctx_function_local_variables: dict[str, VlType] = {}
        self.ctx_function_local_constants: dict[str, VlTypeABC] = {}

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

    def lower_identifier_expr(self, expr: vl_ast.IdentifierNode) -> IdentifierExprNode:
        # Not to be called when the identifier identifies a function
        vl_type: VlType
        identifier = expr.name
        if identifier in self.global_constants:
            vl_type = type(self.global_constants[identifier])
            return IdentifierExprNode(identifier, True, vl_type, expr.position_info)

        elif identifier in self.global_variables:
            vl_type = self.global_variables[identifier]
            return IdentifierExprNode(identifier, False, vl_type, expr.position_info)

        elif identifier in self.ctx_function_local_constants:
            vl_type = type(self.ctx_function_local_constants[identifier])
            return IdentifierExprNode(identifier, True, vl_type, expr.position_info)

        elif identifier in self.global_variables:
            vl_type = self.global_variables[identifier]
            return IdentifierExprNode(identifier, False, vl_type, expr.position_info)

        else:
            raise ValueError(f"Unknown identifier '{expr.name}")
            # TODO: FIXME

    def lower_array_literal_expr(
        self, expr: vl_ast.ArrayLiteralExprNode
    ) -> ArrayLiteralExprNode:
        # TODO: FIXME FOR DIFFERENT LENGTHS
        if len(expr.elements.exprs) in [2, 3, 4]:
            vl_type_str = f"vec{len(expr.elements.exprs)}"
        else:
            raise ValueError(f"Unsupported array literal with length {len(expr)}")

        return ArrayLiteralExprNode(
            [self.lower_expr(x) for x in expr.elements.exprs],
            False,
            self.lower_vl_type(vl_type_str),
            expr.position_info,
        )

    def lower_member_access_expr(
        self, expr: vl_ast.MemberAccessExprNode
    ) -> MemberAccessExprNode:
        pass

    def lower_index_expr(self, expr: vl_ast.IndexExprNode) -> IndexExprNode:
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
            expr.callee.name,
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

        # TODO: FIXME for type casting, etc.
        operation = [
            x
            for x in left.vl_type.get_operations()
            if x.op_arity == "BINARY"
            and x.op_type == operator
            and x.operand_types == [right.vl_type.to_vl_type_str()]
        ]
        if not operation:
            raise ValueError(
                f"Unsupported operation '{operator}' between '{left.vl_type.to_vl_type_str()}' and '{right.vl_type.to_vl_type_str()}'"
            )
        elif len(operation) > 1:
            raise ValueError("Internal error: multiple operations found")
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
        return ConstantExprNode(
            expr.value,
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
        stmts = self.lower_stmts(decl.stmts)
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
        return DataDeclNode(
            isinstance(decl, vl_ast.ConstantDeclNode),
            decl.target.name,
            self.lower_vl_type(decl._type.name),
            self.lower_expr(decl.value),
            decl.position_info,
        )

    def lower_using_decl(self, decl: vl_ast.UsingDeclNode) -> UsingDeclNode:
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
        return UsingDeclNode(
            namespace_identifiers, scoped_identifiers, decl.position_info
        )

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
        blocks = [
            SelectionStackStmt.SelectionBlock(
                self.lower_expr(x.condition), self.lower_stmts(x.stmts)
            )
            for x in conditioned
        ]
        else_stmts = self.lower_stmts(stmts[-1].stmts) if has_else else None
        return SelectionStackStmt(blocks, else_stmts, stmts[0].position_info)

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
                # TODO: FIXME
                pass
            elif isinstance(stmt, vl_ast.AugmentedAssignmentStmtNode):
                # TODO: FIXME
                pass

            elif isinstance(stmt, vl_ast.ForStmtNode):
                # TODO: FIXME
                pass
            elif isinstance(stmt, vl_ast.WhileStmtNode):
                # TODO: FIXME
                pass
            elif isinstance(stmt, vl_ast.BreakStmtNode):
                # TODO: FIXME
                pass
            elif isinstance(stmt, vl_ast.ContinueStmtNode):
                # TODO: FIXME
                pass
            elif isinstance(stmt, vl_ast.ReturnStmtNode):
                # TODO: FIXME
                pass

            elif isinstance(stmt, vl_ast.ExprStmtNode):
                out_stmts.append(self.lower_expr_stmt(stmt))

            elif isinstance(stmt, vl_ast.CommentNode):
                pass
            else:
                raise ValueError(f"Unknown stmt type '{type(stmt)}'")

        # if there are still selection statements left over
        if selection_stmts:
            out_stmts.append(SelectionStackStmt(selection_stmts))
        return out_stmts

    def lower_decl(self, decl: vl_ast.DeclNode) -> "DeclNode":
        if isinstance(decl, vl_ast.FunctionDeclNode):
            return self.lower_function_decl(decl)
        elif isinstance(decl, (vl_ast.VariableDeclNode, vl_ast.ConstantDeclNode)):
            return self.lower_data_decl(decl)
        else:
            raise ValueError(f"Unknown decl type '{type(decl)}'")

    def lower_expr(self, expr: vl_ast.ExprNode) -> "ExprNode":
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
