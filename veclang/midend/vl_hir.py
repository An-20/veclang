"""High-level intermediate representation classes"""

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


VlType = typing.Literal[
    "int",
    "bool",
    "real",
    "complex",
    "vec2",
    "vec3",
    "vec4",
    "mat2",
    "mat3",
    "mat4",
]
VlTypes = [
    "int",
    "bool",
    "real",
    "complex",
    "vec2",
    "vec3",
    "vec4",
    "mat2",
    "mat3",
    "mat4",
]


def lower_vl_type(vl_type: str) -> VlType:
    if vl_type not in VlTypes:
        raise ValueError(f"Unknown type '{vl_type}'")
    vl_type: VlType
    return vl_type


def lower_stmts(stmts: vl_ast.StmtsNode) -> list["StmtNode"]:
    out_stmts = []
    selection_stmts = []
    for stmt in stmts.stmts:
        # first, handle selection statements (because ordering matters)
        if isinstance(stmt, vl_ast.ElseifStmtNode):
            selection_stmts.append(stmt)
            continue
        if isinstance(stmt, vl_ast.ElseStmtNode):
            if selection_stmts and isinstance(selection_stmts[-1], vl_ast.ElseStmtNode):
                raise ValueError("Multiple else statements in one selection block")
            selection_stmts.append(stmt)
            continue
        if selection_stmts:
            out_stmts.append(SelectionStackStmt(selection_stmts))
            selection_stmts = []
        if isinstance(stmt, vl_ast.IfStmtNode):
            selection_stmts.append(stmt)
            continue

        # handle other statements now
        if isinstance(stmt, vl_ast.DeclNode):
            out_stmts.append(lower_decl(stmt))
        elif isinstance(stmt, vl_ast.AssignmentStmtNode):
            out_stmts.append(AssignmentStmtNode(stmt))
        elif isinstance(stmt, vl_ast.AugmentedAssignmentStmtNode):
            out_stmts.append(AugmentedAssignmentStmtNode(stmt))
        elif isinstance(stmt, vl_ast.ForStmtNode):
            # future: may need to be changed
            out_stmts.append(RangedForStmtNode(stmt))
        elif isinstance(stmt, vl_ast.WhileStmtNode):
            out_stmts.append(WhileStmtNode(stmt))
        elif isinstance(stmt, vl_ast.BreakStmtNode):
            out_stmts.append(BreakStmtNode(stmt))
        elif isinstance(stmt, vl_ast.ContinueStmtNode):
            out_stmts.append(ContinueStmtNode(stmt))
        elif isinstance(stmt, vl_ast.ReturnStmtNode):
            out_stmts.append(ReturnStmtNode(stmt))
        elif isinstance(stmt, vl_ast.CommentNode):
            pass
        else:
            raise ValueError(f"Unknown stmt type '{type(stmt)}'")

    # if there are still selection statements left over
    if selection_stmts:
        out_stmts.append(SelectionStackStmt(selection_stmts))
    return out_stmts


def lower_decl(decl: vl_ast.DeclNode) -> "DeclNode":
    if isinstance(decl, vl_ast.FunctionDeclNode):
        return FunctionDeclNode(decl)
    elif isinstance(decl, vl_ast.VariableDeclNode):
        return DataDeclNode(decl)
    elif isinstance(decl, vl_ast.ConstantDeclNode):
        return DataDeclNode(decl)
    else:
        raise ValueError(f"Unknown decl type '{type(decl)}'")


def lower_expr(expr: vl_ast.ExprNode) -> "ExprNode":
    if isinstance(expr, vl_ast.IdentifierNode):
        return IdentifierExprNode(expr)
    elif isinstance(expr, vl_ast.ArrayLiteralExprNode):
        return ArrayLiteralExprNode(expr)
    elif isinstance(expr, vl_ast.MemberAccessExprNode):
        return MemberAccessExprNode(expr)
    elif isinstance(expr, vl_ast.IndexExprNode):
        return IndexExprNode(expr)
    elif isinstance(expr, vl_ast.FunctionCallExprNode):
        return FunctionCallExprNode(expr)
    elif isinstance(expr, vl_ast.BinaryOperationExprNode):
        return BinaryOperationExprNode(expr)
    elif isinstance(expr, vl_ast.UnaryOperatorExprNode):
        return UnaryOperatorExprNode(expr)
    elif isinstance(expr, vl_ast.ConstantExprNode):
        return ConstantExprNode(expr)
    else:
        raise ValueError(f"Unknown expr type '{type(expr)}'")


class HIRNode(abc.ABC):
    """A HIR node"""

    def __init__(
        self,
        ast_node: vl_ast.ASTNode,
        hir_node_name: str | None,
        ast_node_types: (
            typing.Type[vl_ast.ASTNode] | tuple[typing.Type[vl_ast.ASTNode]]
        ) | None,
    ) -> None:
        if (
            hir_node_name
            and ast_node_types
            and not isinstance(ast_node, ast_node_types)
        ):
            raise ValueError(
                f"HIR {hir_node_name} must be constructed from AST {ast_node_types}."
            )
        self.position_info: ASTPositionInfo = ast_node.position_info

    def __eq__(self, other):
        for attr in [x for x in self.__dir__() if x[:2] != "__"]:
            if not hasattr(other, attr):
                return False
            elif not getattr(self, attr).__eq__(getattr(other, attr)):
                return False
        return True


class ExprNode(HIRNode, abc.ABC):
    """A HIR node for an expression"""

    def __init__(
        self,
        ast_node: vl_ast.ASTNode,
        hir_node_name: str,
        ast_node_types: (
            typing.Type[vl_ast.ASTNode] | tuple[typing.Type[vl_ast.ASTNode]]
        ),
    ) -> None:
        super().__init__(ast_node, hir_node_name, ast_node_types)
        self.constexpr = False

    def update_constexpr(self, *children):
        self.constexpr = all(child.constexpr for child in children)


class StmtNode(HIRNode, abc.ABC):
    """A HIR node for a statement"""


class DeclNode(StmtNode, abc.ABC):
    """A HIR node for a declaration"""


class ProgramNode(HIRNode):
    """A HIR node for an entire program"""

    def __init__(self, ast_node: vl_ast.ASTNode) -> None:
        super().__init__(ast_node, "ProgramNode", vl_ast.ProgramNode)
        ast_node: vl_ast.ProgramNode
        self.stmts = lower_stmts(ast_node.stmts)


# Exprs
# ----------------------------------------
class IdentifierExprNode(ExprNode):
    """A HIR node for an identifier expression. Note this is not a general vl_ast.IdentifierNode"""

    def __init__(self, ast_node: vl_ast.ASTNode) -> None:
        super().__init__(ast_node, "IdentifierExprNode", vl_ast.IdentifierNode)
        ast_node: vl_ast.IdentifierNode
        self.name = ast_node.name


class ArrayLiteralExprNode(ExprNode):

    def __init__(self, ast_node: vl_ast.ASTNode) -> None:
        super().__init__(ast_node, "ArrayLiteralExprNode", vl_ast.ArrayLiteralExprNode)
        ast_node: vl_ast.ArrayLiteralExprNode
        self.elements = [lower_expr(x) for x in ast_node.elements.exprs]


class MemberAccessExprNode(ExprNode):

    def __init__(self, ast_node: vl_ast.ASTNode) -> None:
        super().__init__(ast_node, "MemberAccessExprNode", vl_ast.MemberAccessExprNode)
        ast_node: vl_ast.MemberAccessExprNode
        self.target = lower_expr(ast_node.target)
        self.name = ast_node.name.name


class IndexExprNode(ExprNode):

    def __init__(self, ast_node: vl_ast.ASTNode) -> None:
        super().__init__(ast_node, "IndexExprNode", vl_ast.IndexExprNode)
        ast_node: vl_ast.IndexExprNode
        self.target = lower_expr(ast_node.target)
        self.indices = [lower_expr(x) for x in ast_node.indices.exprs]


class FunctionCallExprNode(ExprNode):
    """A HIR node for a function call"""

    def __init__(self, ast_node: vl_ast.ASTNode) -> None:
        super().__init__(ast_node, "FunctionCallExprNode", vl_ast.FunctionCallExprNode)
        ast_node: vl_ast.FunctionCallExprNode
        self.callee = ast_node.callee.name
        self.indices = [lower_expr(x) for x in ast_node.arguments.arguments]


class BinaryOperationExprNode(ExprNode):
    """A HIR node for a binary operation"""

    def __init__(self, ast_node: vl_ast.ASTNode) -> None:
        super().__init__(
            ast_node, "BinaryOperationExprNode", vl_ast.BinaryOperationExprNode
        )
        ast_node: vl_ast.BinaryOperationExprNode
        self.left = lower_expr(ast_node.left)
        self.right = lower_expr(ast_node.right)
        self.operator: BinaryOperatorType = ast_node.operator
        self.update_constexpr(self.left, self.right)


class UnaryOperatorExprNode(ExprNode):
    """A HIR node for a unary operation"""

    def __init__(self, ast_node: vl_ast.ASTNode) -> None:
        super().__init__(
            ast_node, "UnaryOperatorExprNode", vl_ast.UnaryOperatorExprNode
        )
        ast_node: vl_ast.UnaryOperatorExprNode
        self.operand = lower_expr(ast_node.operand)
        self.operator: UnaryOperatorType = ast_node.operator
        self.update_constexpr(self.operator)


# Constant exprs
# ----------------------------------------
class ConstantExprNode(ExprNode):
    """A HIR node for a constant expression"""

    def __init__(self, ast_node: vl_ast.ASTNode) -> None:
        super().__init__(ast_node, "ConstantExprNode", vl_ast.ConstantExprNode)
        ast_node: vl_ast.ConstantExprNode
        self.value: vl_ast.ConstantValue = ast_node.value


# Stmts
# ----------------------------------------
class AttributeTagsNode(HIRNode):

    def __init__(self, ast_node: vl_ast.ASTNode) -> None:
        super().__init__(ast_node, "AttributeTagsNode", vl_ast.AttributeTagsNode)
        ast_node: vl_ast.AttributeTagsNode
        self.tags = {}
        for tag in ast_node.tags:
            if tag.key.name in self.tags:
                raise ValueError(f"Duplicate attribute tag key '{tag.key.name}'")
            self.tags[tag.key.name] = tag.values


class FunctionDeclNode(DeclNode):
    """A HIR node for a function declaration"""

    @dataclasses.dataclass
    class FunctionDeclParameter:
        name: str
        _type: VlType

    def __init__(self, ast_node: vl_ast.ASTNode) -> None:
        super().__init__(ast_node, "FunctionDeclNode", vl_ast.FunctionDeclNode)
        ast_node: vl_ast.FunctionDeclNode
        self.attribute_tags = AttributeTagsNode(ast_node.attribute_tags)
        self.identifier = ast_node.identifier.name
        self.parameters = [
            self.FunctionDeclParameter(x.name.name, lower_vl_type(x.type.name))
            for x in ast_node.parameters.parameters
        ]
        self.return_type = lower_vl_type(ast_node.return_type.name)
        self.stmts = lower_stmts(ast_node.stmts)


class DataDeclNode(DeclNode, abc.ABC):
    """A HIR node for variable / constant declaration"""

    def __init__(self, ast_node: vl_ast.ASTNode) -> None:
        super().__init__(ast_node, "DataDeclNode", vl_ast.DataDeclNode)
        ast_node: vl_ast.DataDeclNode
        self.constant = isinstance(ast_node, vl_ast.ConstantDeclNode)
        self.target = ast_node.target.name
        self._type = lower_vl_type(ast_node._type.name)
        self.value = lower_expr(ast_node.value)


class AssignmentStmtNode(StmtNode):
    """A HIR node for assignment"""

    def __init__(self, ast_node: vl_ast.ASTNode) -> None:
        super().__init__(ast_node, "AssignmentStmtNode", vl_ast.AssignmentStmtNode)
        ast_node: vl_ast.AssignmentStmtNode
        self.target = lower_expr(ast_node.target)
        self.value = lower_expr(ast_node.value)


class AugmentedAssignmentStmtNode(StmtNode):
    """A HIR node for augmented assignment"""

    def __init__(self, ast_node: vl_ast.ASTNode) -> None:
        super().__init__(
            ast_node, "AugmentedAssignmentStmtNode", vl_ast.AugmentedAssignmentStmtNode
        )
        ast_node: vl_ast.AugmentedAssignmentStmtNode
        self.target = lower_expr(ast_node.target)
        self.operator: AugmentedAssignmentOperatorType = ast_node.operator
        self.value = lower_expr(ast_node.value)


class ExprStmtNode(StmtNode):
    """A HIR node for a statement that is formed by an expression e.g. a();"""

    def __init__(self, ast_node: vl_ast.ASTNode) -> None:
        super().__init__(ast_node, "ExprStmtNode", vl_ast.ExprStmtNode)
        ast_node: vl_ast.ExprStmtNode
        self.expr = lower_expr(ast_node.expr)


class SelectionStackStmt(StmtNode):
    """A HIR node for if, elif, and elseif stmts"""

    @dataclasses.dataclass
    class SelectionBlock:
        condition: ExprNode
        stmts: list[StmtNode]

    def __init__(self, stmts: list[vl_ast.StmtNode]) -> None:
        super().__init__(stmts[0], None, None)
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
        # noinspection PyTypeChecker
        conditioned: list[vl_ast.IfStmtNode] = stmts[:-1] if has_else else stmts
        self.blocks = [
            self.SelectionBlock(lower_expr(x.condition), lower_stmts(x.stmts))
            for x in conditioned
        ]
        # noinspection PyUnresolvedReferences
        self._else = lower_stmts(stmts[-1].stmts) if has_else else None


class RangedForStmtNode(StmtNode):
    """A HIR node for range-based for loops"""

    def __init__(self, ast_node: vl_ast.ASTNode) -> None:
        super().__init__(ast_node, "RangedForStmtNode", vl_ast.ForStmtNode)
        ast_node: vl_ast.ForStmtNode
        if not isinstance(ast_node.init_stmt.value, vl_ast.RangeLiteralExprNode):
            raise ValueError(
                "For statement loop variable must only be set to a range literal"
            )
        self.loop_var_identifier = ast_node.init_stmt.target.name
        self.loop_var_type = lower_vl_type(ast_node.init_stmt.init_type.name)
        self.loop_var_start = lower_expr(ast_node.init_stmt.value.start)
        self.loop_var_end = lower_expr(ast_node.init_stmt.value.end)
        self.loop_var_step = lower_expr(ast_node.init_stmt.value.step)
        self.stmts = lower_stmts(ast_node.stmts)


class WhileStmtNode(StmtNode):
    """A HIR node for while loops"""

    def __init__(self, ast_node: vl_ast.ASTNode) -> None:
        super().__init__(ast_node, "WhileStmtNode", vl_ast.WhileStmtNode)
        ast_node: vl_ast.WhileStmtNode
        self.condition = lower_expr(ast_node.condition)
        self.stmts = lower_stmts(ast_node.stmts)


class ReturnStmtNode(StmtNode):
    """A HIR node for returning"""

    def __init__(self, ast_node: vl_ast.ASTNode) -> None:
        super().__init__(ast_node, "ReturnStmtNode", vl_ast.ReturnStmtNode)
        ast_node: vl_ast.ReturnStmtNode
        self.value = lower_expr(ast_node.value)


class BreakStmtNode(StmtNode):
    """A HIR node for break"""

    def __init__(self, ast_node: vl_ast.ASTNode) -> None:
        super().__init__(ast_node, "BreakStmtNode", vl_ast.BreakStmtNode)
        ast_node: vl_ast.BreakStmtNode


class ContinueStmtNode(StmtNode):
    """A HIR node for continue"""

    def __init__(self, ast_node: vl_ast.ASTNode) -> None:
        super().__init__(ast_node, "ContinueStmtNode", vl_ast.ContinueStmtNode)
        ast_node: vl_ast.ContinueStmtNode
