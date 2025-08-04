"""High-level intermediate representation classes"""

import abc
import dataclasses

from veclang.frontend.parser import vl_ast
from veclang.frontend.parser.vl_parser import (
    AugmentedAssignmentOperatorType,
    BinaryOperatorType,
    UnaryOperatorType,
    ASTPositionInfo,
)

from veclang.midend.vl_core.vl_type import VlOperation
from veclang.midend.vl_core import VlType, VlTypeABC, VlFunctionParameterTypeProfile


class HIRNode(abc.ABC):
    """A HIR node"""

    def __init__(self, ast_position_info: ASTPositionInfo) -> None:
        self.ast_position_info: ASTPositionInfo = ast_position_info

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
        self, constexpr: bool, vl_type: VlType, ast_position_info: ASTPositionInfo
    ) -> None:
        super().__init__(ast_position_info)
        self.constexpr: bool = constexpr
        self.vl_type: VlType = vl_type

    def update_constexpr(self, *children):
        self.constexpr = all(child.constexpr for child in children)


class StmtNode(HIRNode, abc.ABC):
    """A HIR node for a statement"""


class DeclNode(StmtNode, abc.ABC):
    """A HIR node for a declaration"""


class ProgramNode(HIRNode):
    """A HIR node for an entire program"""

    def __init__(
        self, stmts: list[StmtNode], ast_position_info: ASTPositionInfo
    ) -> None:
        super().__init__(ast_position_info)
        self.stmts = stmts


# Exprs
# ----------------------------------------
class RvalueIdentifierExprNode(ExprNode):
    """
    A HIR node for an identifier expression when used in a rvalue.
    Note this is not a general vl_ast.IdentifierNode.
    """

    def __init__(
        self,
        identifier: str,
        constexpr: bool,
        vl_type: VlType,
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super().__init__(constexpr, vl_type, ast_position_info)
        self.identifier = identifier


class FunctionCallExprNode(ExprNode):
    """A HIR node for a function call"""

    def __init__(
        self,
        callee_fn_id: int,
        arguments: list[ExprNode],
        constexpr: bool,
        vl_type: VlType,
        ast_position_info: ASTPositionInfo,
        is_type_cast: bool = False,
        is_method: bool = False,
        is_property: bool = False,
    ) -> None:
        super().__init__(constexpr, vl_type, ast_position_info)
        self.callee_fn_id = callee_fn_id
        self.arguments = arguments
        self.is_type_cast = is_type_cast
        self.is_method = is_method
        self.is_property = is_property


class BinaryOperationExprNode(ExprNode):
    """A HIR node for a binary operation"""

    def __init__(
        self,
        left: ExprNode,
        right: ExprNode,
        operator: BinaryOperatorType,
        operation: VlOperation,
        constexpr: bool,
        vl_type: VlType,
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super().__init__(constexpr, vl_type, ast_position_info)
        self.left = left
        self.right = right
        self.operator = operator
        self.operation = operation


class UnaryOperatorExprNode(ExprNode):
    """A HIR node for a unary operation"""

    def __init__(
        self,
        operand: ExprNode,
        operator: UnaryOperatorType,
        operation: VlOperation,
        constexpr: bool,
        vl_type: VlType,
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super().__init__(constexpr, vl_type, ast_position_info)
        self.operand = operand
        self.operator = operator
        self.operation = operation


# Constant exprs
# ----------------------------------------
class ConstantExprNode(ExprNode):
    """A HIR node for a constant expression"""

    def __init__(
        self,
        constant_value: VlTypeABC,
        constexpr: bool,
        vl_type: VlType,
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super().__init__(constexpr, vl_type, ast_position_info)
        self.value: VlTypeABC = constant_value


# Stmts
# ----------------------------------------
class FunctionDeclNode(DeclNode):
    """A HIR node for a function declaration"""

    def __init__(
        self,
        attribute_tags: dict[str, list[ExprNode]],
        identifier: str,
        parameters: list[VlFunctionParameterTypeProfile],
        return_type: VlType,
        stmts: list[StmtNode],
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super().__init__(ast_position_info)
        self.attribute_tags: dict[str, list[ExprNode]] = attribute_tags
        self.identifier: str = identifier
        self.parameters: list[VlFunctionParameterTypeProfile] = parameters
        self.return_type: VlType = return_type
        self.stmts: list[StmtNode] = stmts


class DataDeclNode(DeclNode):
    """A HIR node for variable / constant declaration"""

    def __init__(
        self,
        constant: bool,
        target: str,
        vl_type: VlType,
        value: ExprNode,
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super().__init__(ast_position_info)
        ast_node: vl_ast.DataDeclNode
        self.constant: bool = constant
        self.target: str = target
        self.vl_type: VlType = vl_type
        self.value: ExprNode = value


class AssignmentStmtNode(StmtNode):
    """A HIR node for assignment"""

    def __init__(
        self,
        target: str,
        value: ExprNode,
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super().__init__(ast_position_info)
        self.target: str = target
        self.value: ExprNode = value


class AugmentedAssignmentStmtNode(StmtNode):
    """A HIR node for augmented assignment"""

    def __init__(
        self,
        target: str,
        operator: AugmentedAssignmentOperatorType,
        value: ExprNode,
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super().__init__(ast_position_info)
        self.target: str = target
        self.operator: AugmentedAssignmentOperatorType = operator
        self.value: ExprNode = value


class ExprStmtNode(StmtNode):
    """A HIR node for a statement that is formed by an expression e.g. a();"""

    def __init__(
        self,
        expr: ExprNode,
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super().__init__(ast_position_info)
        self.expr: ExprNode = expr


@dataclasses.dataclass
class SelectionBlock:
    condition: ExprNode
    stmts: list[StmtNode]


class SelectionStackStmt(StmtNode):
    """A HIR node for if, elif, and elseif stmts"""

    def __init__(
        self,
        blocks: list[SelectionBlock],
        else_stmts: list[StmtNode] | None,
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super().__init__(ast_position_info)
        self.blocks: list[SelectionBlock] = blocks
        self.else_stmts: list[StmtNode] | None = else_stmts


class RangedForStmtNode(StmtNode):
    """A HIR node for range-based for loops"""

    def __init__(
        self,
        loop_var_identifier: str,
        loop_var_type: VlType,
        loop_var_start: ExprNode,
        loop_var_end: ExprNode,
        loop_var_step: ExprNode,
        stmts: list[StmtNode],
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super().__init__(ast_position_info)
        self.loop_var_identifier: str = loop_var_identifier
        self.loop_var_type: VlType = loop_var_type
        self.loop_var_start: ExprNode = loop_var_start
        self.loop_var_end: ExprNode = loop_var_end
        self.loop_var_step: ExprNode = loop_var_step
        self.stmts: list[StmtNode] = stmts


class WhileStmtNode(StmtNode):
    """A HIR node for while loops"""

    def __init__(
        self,
        condition: ExprNode,
        stmts: list[StmtNode],
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


class BreakStmtNode(StmtNode):
    """A HIR node for break"""

    def __init__(self, ast_position_info: ASTPositionInfo) -> None:
        super().__init__(ast_position_info)


class ContinueStmtNode(StmtNode):
    """A HIR node for continue"""

    def __init__(self, ast_position_info: ASTPositionInfo) -> None:
        super().__init__(ast_position_info)
