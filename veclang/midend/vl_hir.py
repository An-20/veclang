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


def verify_vl_type(vl_type: str) -> VlType:
    if vl_type not in VlTypes:
        raise ValueError(f"Unknown type '{vl_type}'")
    vl_type: VlType
    return vl_type


class HIRNode(abc.ABC):
    """A HIR node"""

    def __init__(self, ast_node: vl_ast.ASTNode) -> None:
        self.position_info = ast_node.position_info

    def __eq__(self, other):
        for attr in [x for x in self.__dir__() if x[:2] != "__"]:
            if not hasattr(other, attr):
                return False
            elif not getattr(self, attr).__eq__(getattr(other, attr)):
                return False
        return True


class ExprNode(HIRNode, abc.ABC):
    """A HIR node for an expression"""


class StmtNode(HIRNode, abc.ABC):
    """A HIR node for a statement"""


class DeclNode(StmtNode, abc.ABC):
    """A HIR node for a declaration"""


class ProgramNode(HIRNode):
    """A HIR node for an entire program"""

    def __init__(self, ast_node: vl_ast.ASTNode) -> None:
        super().__init__(ast_node)
        if not isinstance(ast_node, vl_ast.ProgramNode):
            raise ValueError(
                "HIR ProgramNode must be constructed from AST ProgramNode."
            )
        self.stmts = ast_node.stmts.stmts


class IdentifierNode(HIRNode):
    """A HIR node for an identifier"""

    def __init__(self, ast_node: vl_ast.ASTNode) -> None:
        super().__init__(ast_node)
        if not isinstance(ast_node, vl_ast.IdentifierNode):
            raise ValueError(
                "HIR ProgramNode must be constructed from AST IdentifierNode."
            )
        self.name = ast_node.name


# Exprs
# ----------------------------------------
class ArrayLiteralExprNode(ExprNode):

    def __init__(self, ast_node: vl_ast.ASTNode) -> None:
        super().__init__(ast_node)
        if not isinstance(ast_node, vl_ast.ArrayLiteralExprNode):
            raise ValueError(
                "HIR ArrayLiteralExprNode must be constructed from AST ArrayLiteralExprNode."
            )
        self.elements = [get_expr(x) for x in ast_node.elements.exprs]


# class MemberAccessExprNode(ExprNode):
#
#     def __init__(
#         self, target: ExprNode, name: IdentifierNode, ast_position_info: ASTPositionInfo
#     ) -> None:
#         super().__init__(ast_position_info)
#         self.target = target
#         self.name = name


class IndexExprNode(ExprNode):

    def __init__(self, ast_node: vl_ast.ASTNode) -> None:
        super().__init__(ast_node)
        if not isinstance(ast_node, vl_ast.IndexExprNode):
            raise ValueError(
                "HIR IndexExprNode must be constructed from AST IndexExprNode."
            )
        self.target = get_expr(ast_node.target)
        self.indices = [get_expr(x) for x in ast_node.indices.exprs]


class FunctionCallExprNode(ExprNode):
    """A HIR node for a function call"""

    def __init__(self, ast_node: vl_ast.ASTNode) -> None:
        super().__init__(ast_node)
        if not isinstance(ast_node, vl_ast.FunctionCallExprNode):
            raise ValueError(
                "HIR FunctionCallExprNode must be constructed from AST FunctionCallExprNode."
            )
        self.callee = ast_node.callee.name
        self.indices = [get_expr(x) for x in ast_node.arguments.arguments]


class BinaryOperationExprNode(ExprNode):
    """A HIR node for a binary operation"""

    def __init__(self, ast_node: vl_ast.ASTNode) -> None:
        super().__init__(ast_node)
        if not isinstance(ast_node, vl_ast.BinaryOperationExprNode):
            raise ValueError(
                "HIR BinaryOperationExprNode must be constructed from AST BinaryOperationExprNode."
            )
        self.left = get_expr(ast_node.left)
        self.right = get_expr(ast_node.right)
        self.operator = ast_node.operator


class UnaryOperatorExprNode(ExprNode):
    """A HIR node for a unary operation"""

    def __init__(self, ast_node: vl_ast.ASTNode) -> None:
        super().__init__(ast_node)
        if not isinstance(ast_node, vl_ast.UnaryOperatorExprNode):
            raise ValueError(
                "HIR UnaryOperatorExprNode must be constructed from AST UnaryOperatorExprNode."
            )
        self.operand = get_expr(ast_node.operand)
        self.operator = ast_node.operator


# Constant exprs
# ----------------------------------------


class ConstantExprNode(ExprNode):
    """A HIR node for a constant expression"""

    def __init__(
        self, value: vl_ast.ConstantValue, ast_position_info: ASTPositionInfo
    ) -> None:
        super().__init__(ast_position_info)
        self.value = value


# Stmts
# ----------------------------------------
class AttributeTagValuesNode(HIRNode):

    def __init__(
        self,
        values: typing.Optional["AttributeTagValuesNode"],
        value: typing.Optional[ExprNode],
        ast_position_info: ASTPositionInfo,
    ):
        super().__init__(ast_position_info)
        self.values = []
        if values:
            self.values.extend(values.values)
        if value:
            self.values.append(value)


class AttributeTagNode(HIRNode):

    def __init__(
        self,
        key: IdentifierNode,
        values: typing.Optional[AttributeTagValuesNode],
        ast_position_info: ASTPositionInfo,
    ):
        super().__init__(ast_position_info)
        self.key = key
        self.values = values


class AttributeTagsNode(HIRNode):

    def __init__(
        self,
        tags: typing.Optional["AttributeTagsNode"],
        tag: typing.Optional[AttributeTagNode],
        ast_position_info: ASTPositionInfo,
    ):
        super().__init__(ast_position_info)
        self.tags = []
        if tags:
            self.tags.extend(tags.tags)
        if tag:
            self.tags.append(tag)


class FunctionDeclNode(StmtNode):
    """A HIR node for a function declaration"""

    @dataclasses.dataclass
    class FunctionDeclParameter:
        name: str
        _type: VlType

    def __init__(self, ast_node: vl_ast.ASTNode) -> None:
        super().__init__(ast_node)
        if not isinstance(ast_node, vl_ast.FunctionDeclNode):
            raise ValueError(
                "HIR FunctionDeclNode must be constructed from AST FunctionDeclNode node."
            )
        # self.attribute_tags = attribute_tags TODO: fixme
        self.identifier = ast_node.identifier.name
        self.parameters = [
            self.FunctionDeclParameter(x.name.name, verify_vl_type(x.type.name))
            for x in ast_node.parameters.parameters
        ]
        self.return_type = ast_node.return_type
        self.stmts = [StmtNode(x) for x in ast_node.stmts.stmts]


class DataDeclNode(StmtNode, abc.ABC):
    """A HIR node for variable / constant declaration"""

    def __init__(self, ast_node: vl_ast.ASTNode) -> None:
        super().__init__(ast_node)
        if not isinstance(ast_node, vl_ast.DataDeclNode):
            raise ValueError(
                "HIR DataDeclNode must be constructed from AST VariableDeclNode or ConstantDeclNode."
            )
        self.constant = isinstance(ast_node, vl_ast.ConstantDeclNode)
        self.target = ast_node.target.name
        self._type = verify_vl_type(ast_node._type.name)
        self.value = ast_node.value


class AssignmentStmtNode(StmtNode):
    """A HIR node for assignment"""

    def __init__(self, ast_node: vl_ast.ASTNode) -> None:
        super().__init__(ast_node)
        if not isinstance(ast_node, vl_ast.AssignmentStmtNode):
            raise ValueError(
                "HIR AssignmentStmtNode must be constructed from AST AssignmentStmtNode."
            )
        self.target = ast_node.target
        self.value = ast_node.value


class AugmentedAssignmentStmtNode(StmtNode):
    """A HIR node for augmented assignment"""

    def __init__(self, ast_node: vl_ast.ASTNode) -> None:
        super().__init__(ast_node)
        if not isinstance(ast_node, vl_ast.AugmentedAssignmentStmtNode):
            raise ValueError(
                "HIR AugmentedAssignmentStmtNode must be constructed from AST AugmentedAssignmentStmtNode."
            )
        self.target = ast_node.target
        self.operator = ast_node.operator
        self.value = ast_node.value


class ExprStmtNode(StmtNode):
    """A HIR node for a statement that is formed by an expression e.g. a();"""

    def __init__(self, ast_node: vl_ast.ASTNode) -> None:
        super().__init__(ast_node)
        if not isinstance(ast_node, vl_ast.ExprStmtNode):
            raise ValueError(
                "HIR ExprStmtNode must be constructed from AST ExprStmtNode."
            )
        self.expr = get_expr(ast_node.expr)


class IfStmtNode(StmtNode):
    """A HIR node for if stmts"""

    def __init__(
        self,
        condition: ExprNode,
        stmts: StmtsNode,
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super().__init__(ast_position_info)
        self.condition = condition
        self.stmts = stmts


class ElseifStmtNode(IfStmtNode):
    """A HIR node for elseif stmts"""


class ElseStmtNode(StmtNode):
    """A HIR node for else stmts"""

    def __init__(self, stmts: StmtsNode, ast_position_info: ASTPositionInfo) -> None:
        super().__init__(ast_position_info)
        self.stmts = stmts


class ForInitialisationStmtNode(StmtNode):
    """A HIR node for variable declaration for a for loop"""

    def __init__(
        self,
        target: IdentifierNode,
        init_type: TypeNode,
        value: ExprNode,
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super().__init__(ast_position_info)
        self.target = target
        self.init_type = init_type
        self.value = value


class ForStmtNode(StmtNode):
    """A HIR node for for loops"""

    def __init__(
        self,
        init_stmt: ForInitialisationStmtNode,
        stmts: StmtsNode,
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super().__init__(ast_position_info)
        self.init_stmt = init_stmt
        self.stmts = stmts


class WhileStmtNode(StmtNode):
    """A HIR node for while loops"""

    def __init__(
        self,
        condition: ExprNode,
        stmts: StmtsNode,
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super().__init__(ast_position_info)
        self.condition = condition
        self.stmts = stmts


class ReturnStmtNode(StmtNode):
    """A HIR node for returning"""

    def __init__(self, value: ExprNode, ast_position_info: ASTPositionInfo) -> None:
        super().__init__(ast_position_info)
        self.value = value


class StatelessStmtNode(StmtNode, abc.ABC):
    pass


class BreakStmtNode(StatelessStmtNode):
    """A HIR node for break"""


class ContinueStmtNode(StatelessStmtNode):
    """A HIR node for continue"""


def get_expr(ast_node: vl_ast.ExprNode) -> ExprNode:
    pass


def get_stmt(ast_node: vl_ast.StmtNode) -> StmtNode:
    pass


def get_decl(ast_node: vl_ast.DeclNode) -> DeclNode:
    pass
