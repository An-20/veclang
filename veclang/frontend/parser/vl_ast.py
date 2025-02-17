"""
AST classes

Side-note: why do we even support serializing and deserializing the AST to JSON?
Next time this file is re-written, maybe just drop that...
"""

import abc
import typing

# Definitions for operators
AugmentedAssignmentOperatorType = typing.Literal[
    "PLUS_ASSIGNMENT",
    "MINUS_ASSIGNMENT",
    "TIMES_ASSIGNMENT",
    "DIVIDE_ASSIGNMENT",
    "MODULUS_ASSIGNMENT",
]

BinaryOperatorType = typing.Literal[
    "PLUS",
    "MINUS",
    "TIMES",
    "DIVIDE",
    "MODULUS",
    "INTEGER_DIVIDE",
    "EXPONENTIATION",
    "BOOLEAN_AND",
    "BOOLEAN_OR",
    "BITWISE_AND",
    "BITWISE_OR",
    "BITWISE_XOR",
    "BITWISE_LEFT_SHIFT",
    "BITWISE_RIGHT_SHIFT",
    "EQUAL_TO",
    "NOT_EQUAL_TO",
    "LESS_THAN",
    "LESS_THAN_OR_EQUAL",
    "GREATER_THAN",
    "GREATER_THAN_OR_EQUAL",
]

UnaryOperatorType = typing.Literal[
    "BOOLEAN_NOT", "BITWISE_NOT", "UNARY_PLUS", "UNARY_MINUS"
]


class ASTPositionInfo(typing.NamedTuple):
    """Position info of an AST node"""

    line_number: int | None
    line_character_number: int | None

    def to_dict(self) -> dict:
        return {
            "line_number": self.line_number,
            "line_character_number": self.line_character_number,
        }

    @classmethod
    def from_dict(cls, input_dict: dict) -> "ASTPositionInfo":
        return cls(input_dict["line_number"], input_dict["line_character_number"])


class ASTNode(abc.ABC):
    """An AST node"""

    def __init__(self, ast_position_info: ASTPositionInfo) -> None:
        self.position_info = ast_position_info

    def __eq__(self, other):
        for attr in [x for x in self.__dir__() if x[:2] != "__"]:
            if not hasattr(other, attr):
                return False
            elif not getattr(self, attr).__eq__(getattr(other, attr)):
                return False
        return True

    def to_dict(self) -> dict:
        return {
            "node_type": self.get_node_type_str(),
            "ast_position_info": self.position_info.to_dict(),
            **self._to_dict(),
        }

    @classmethod
    def from_dict(cls, input_dict: dict) -> "ASTNode":
        if input_dict["node_type"] != cls.get_node_type_str():
            raise ValueError(
                f"Expected node type '{cls.get_node_type_str}', got '{input_dict['node_type']}'"
            )
        ast_position_info = ASTPositionInfo.from_dict(input_dict["ast_position_info"])
        return cls._from_dict(input_dict, ast_position_info)

    @staticmethod
    @abc.abstractmethod
    def get_node_type_str() -> str:
        pass

    @abc.abstractmethod
    def _to_dict(self) -> dict:
        pass

    @classmethod
    @abc.abstractmethod
    def _from_dict(
        cls, input_dict: dict, ast_position_info: ASTPositionInfo
    ) -> "ASTNode":
        pass


class ExprNode(ASTNode, abc.ABC):
    """An AST node for an expression"""


class StmtNode(ASTNode, abc.ABC):
    """An AST node for a statement"""


class DeclNode(StmtNode, abc.ABC):
    """An AST node for a declaration"""


class ProgramNode(ASTNode):
    """An AST node for an entire program"""

    def __init__(
        self,
        stmts: typing.Optional["StmtsNode"],
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super(ProgramNode, self).__init__(ast_position_info)
        self.stmts = stmts

    @staticmethod
    def get_node_type_str() -> str:
        return "ProgramNode"

    def _to_dict(self) -> dict:
        return {
            "stmts": self.stmts.to_dict() if self.stmts else [],
        }

    @classmethod
    def _from_dict(
        cls, input_dict: dict, ast_position_info: ASTPositionInfo
    ) -> "ProgramNode":
        return cls(
            StmtsNode.from_dict(input_dict["stmts"]) if input_dict["stmts"] else None,
            ast_position_info,
        )


class StmtsNode(ASTNode):
    """An AST node for a list of stmts"""

    def __init__(
        self,
        stmts: typing.Optional["StmtsNode"],
        stmt: typing.Optional[StmtNode],
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super(StmtsNode, self).__init__(ast_position_info)
        self.stmts = []
        if stmts:
            self.stmts.extend(stmts.stmts)
        if stmt:
            self.stmts.append(stmt)

    @staticmethod
    def get_node_type_str() -> str:
        return "StmtsNode"

    def _to_dict(self) -> dict:
        return {"stmts": [stmt.to_dict() for stmt in self.stmts] if self.stmts else []}

    @classmethod
    def _from_dict(
        cls, input_dict: dict, ast_position_info: ASTPositionInfo
    ) -> "StmtsNode":
        node = cls(None, None, ast_position_info)
        node.stmts = [stmt_from_dict(stmt) for stmt in input_dict["stmts"]]
        return node


class IdentifierNode(ASTNode):
    """An AST node for an identifier"""

    def __init__(self, name: str, ast_position_info: ASTPositionInfo) -> None:
        super().__init__(ast_position_info)
        self.name = name

    @staticmethod
    def get_node_type_str() -> str:
        return "IdentifierNode"

    def _to_dict(self) -> dict:
        return {"name": self.name}

    @classmethod
    def _from_dict(
        cls, input_dict: dict, ast_position_info: ASTPositionInfo
    ) -> "IdentifierNode":
        return cls(input_dict["name"], ast_position_info)


class TypeNode(IdentifierNode):
    """An AST node for a type"""

    @staticmethod
    def get_node_type_str() -> str:
        return "TypeNode"


class FunctionDeclParameterNode(ASTNode):
    """An AST node for a single function parameter when used in declarations"""

    def __init__(
        self,
        name: IdentifierNode,
        _type: TypeNode,
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super().__init__(ast_position_info)
        self.name = name
        self.type = _type

    @staticmethod
    def get_node_type_str() -> str:
        return "FunctionDeclParameterNode"

    def _to_dict(self) -> dict:
        return {"name": self.name.to_dict(), "type": self.type.to_dict()}

    @classmethod
    def _from_dict(
        cls, input_dict: dict, ast_position_info: ASTPositionInfo
    ) -> "FunctionDeclParameterNode":
        return cls(
            IdentifierNode.from_dict(input_dict["name"]),
            TypeNode.from_dict(input_dict["type"]),
            ast_position_info,
        )


class FunctionDeclParametersNode(ASTNode):
    """An AST node for function arguments when used in declarations"""

    def __init__(
        self,
        parameters: typing.Optional["FunctionDeclParametersNode"],
        parameter: typing.Optional[FunctionDeclParameterNode],
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super().__init__(ast_position_info)
        self.parameters = []
        if parameters:
            self.parameters.extend(parameters.parameters)
        if parameter:
            self.parameters.append(parameter)

    @staticmethod
    def get_node_type_str() -> str:
        return "FunctionDeclParametersNode"

    def _to_dict(self) -> dict:
        return {
            "parameters": (
                [parameter.to_dict() for parameter in self.parameters]
                if self.parameters
                else []
            )
        }

    @classmethod
    def _from_dict(
        cls, input_dict: dict, ast_position_info: ASTPositionInfo
    ) -> "FunctionDeclParametersNode":
        node = cls(None, None, ast_position_info)
        node.stmts = [stmt_from_dict(stmt) for stmt in input_dict["parameters"]]
        return node


# Exprs
# ----------------------------------------


class RangeLiteralExprNode(ExprNode):

    def __init__(
        self,
        start: ExprNode,
        end: ExprNode,
        step: ExprNode,
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super().__init__(ast_position_info)
        self.start = start
        self.end = end
        self.step = step

    @staticmethod
    def get_node_type_str() -> str:
        return "RangeLiteralExprNode"

    def _to_dict(self) -> dict:
        return {
            "start": self.start.to_dict(),
            "end": self.end.to_dict(),
            "step": self.step.to_dict(),
        }

    @classmethod
    def _from_dict(
        cls, input_dict: dict, ast_position_info: ASTPositionInfo
    ) -> "RangeLiteralExprNode":
        return cls(
            expr_from_dict(input_dict["start"]),
            expr_from_dict(input_dict["end"]),
            expr_from_dict(input_dict["step"]),
            ast_position_info,
        )


class ArrayLiteralElementsNode(ASTNode):

    def __init__(
        self,
        exprs: typing.Optional["ArrayLiteralElementsNode"],
        expr: typing.Optional[ExprNode],
        ast_position_info: ASTPositionInfo,
    ):
        super().__init__(ast_position_info)
        self.exprs = []
        if exprs:
            self.exprs.extend(exprs.exprs)
        if expr:
            self.exprs.append(expr)

    @staticmethod
    def get_node_type_str() -> str:
        return "ArrayLiteralElementsNode"

    def _to_dict(self) -> dict:
        return {
            "exprs": ([expr.to_dict() for expr in self.exprs] if self.exprs else [])
        }

    @classmethod
    def _from_dict(
        cls, input_dict: dict, ast_position_info: ASTPositionInfo
    ) -> "ArrayLiteralElementsNode":
        node = cls(None, None, ast_position_info)
        node.stmts = [expr_from_dict(expr) for expr in input_dict["exprs"]]
        return node


class ArrayLiteralExprNode(ExprNode):

    def __init__(
        self,
        elements: ArrayLiteralElementsNode,
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super().__init__(ast_position_info)
        self.elements = elements

    @staticmethod
    def get_node_type_str() -> str:
        return "ArrayLiteralExprNode"

    def _to_dict(self) -> dict:
        return {"elements": self.elements.to_dict()}

    @classmethod
    def _from_dict(
        cls, input_dict: dict, ast_position_info: ASTPositionInfo
    ) -> "ArrayLiteralExprNode":
        return cls(
            ArrayLiteralElementsNode.from_dict(input_dict["elements"]),
            ast_position_info,
        )


class MemberAccessExprNode(ExprNode):

    def __init__(
        self, target: ExprNode, name: IdentifierNode, ast_position_info: ASTPositionInfo
    ) -> None:
        super().__init__(ast_position_info)
        self.target = target
        self.name = name

    @staticmethod
    def get_node_type_str() -> str:
        return "MemberAccessExpr"

    def _to_dict(self) -> dict:
        return {"target": self.target.to_dict(), "name": self.name.to_dict()}

    @classmethod
    def _from_dict(
        cls, input_dict: dict, ast_position_info: ASTPositionInfo
    ) -> "MemberAccessExprNode":
        return cls(
            expr_from_dict(input_dict["target"]),
            IdentifierNode.from_dict(input_dict["name"]),
            ast_position_info,
        )


class IndexElementsNode(ASTNode):

    def __init__(
        self,
        exprs: typing.Optional["IndexElementsNode"],
        expr: typing.Optional[ExprNode],
        ast_position_info: ASTPositionInfo,
    ):
        super().__init__(ast_position_info)
        self.exprs = []
        if exprs:
            self.exprs.extend(exprs.exprs)
        if expr:
            self.exprs.append(expr)

    @staticmethod
    def get_node_type_str() -> str:
        return "IndexElementsNode"

    def _to_dict(self) -> dict:
        return {
            "exprs": ([expr.to_dict() for expr in self.exprs] if self.exprs else [])
        }

    @classmethod
    def _from_dict(
        cls, input_dict: dict, ast_position_info: ASTPositionInfo
    ) -> "IndexElementsNode":
        node = cls(None, None, ast_position_info)
        node.stmts = [expr_from_dict(expr) for expr in input_dict["exprs"]]
        return node


class IndexExprNode(ExprNode):

    def __init__(
        self,
        target: ExprNode,
        indices: IndexElementsNode,
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super().__init__(ast_position_info)
        self.target = target
        self.indices = indices

    @staticmethod
    def get_node_type_str() -> str:
        return "IndexExprNode"

    def _to_dict(self) -> dict:
        return {"target": self.target.to_dict(), "indices": self.indices.to_dict()}

    @classmethod
    def _from_dict(
        cls, input_dict: dict, ast_position_info: ASTPositionInfo
    ) -> "IndexExprNode":
        return cls(
            expr_from_dict(input_dict["target"]),
            IndexElementsNode.from_dict(input_dict["indices"]),
            ast_position_info,
        )


class FunctionCallArgumentsNode(ASTNode):
    """An AST node for function arguments when used in calls"""

    def __init__(
        self,
        arguments: typing.Optional["FunctionCallArgumentsNode"],
        argument: typing.Optional[ExprNode],
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super().__init__(ast_position_info)
        self.arguments = []
        if arguments:
            self.arguments.extend(arguments.arguments)
        if argument:
            self.arguments.append(argument)

    @staticmethod
    def get_node_type_str() -> str:
        return "FunctionCallArgumentsNode"

    def _to_dict(self) -> dict:
        return {
            "arguments": (
                [expr.to_dict() for expr in self.arguments] if self.arguments else []
            )
        }

    @classmethod
    def _from_dict(
        cls, input_dict: dict, ast_position_info: ASTPositionInfo
    ) -> "FunctionCallArgumentsNode":
        node = cls(None, None, ast_position_info)
        node.stmts = [expr_from_dict(expr) for expr in input_dict["arguments"]]
        return node


class FunctionCallExprNode(ExprNode):
    """An AST node for a function call"""

    def __init__(
        self,
        callee: IdentifierNode,
        arguments: FunctionCallArgumentsNode,
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super().__init__(ast_position_info)
        self.callee = callee
        self.arguments = arguments

    @staticmethod
    def get_node_type_str() -> str:
        return "FunctionCallExprNode"

    def _to_dict(self) -> dict:
        return {"callee": self.callee.to_dict(), "arguments": self.arguments.to_dict()}

    @classmethod
    def _from_dict(
        cls, input_dict: dict, ast_position_info: ASTPositionInfo
    ) -> "FunctionCallExprNode":
        return cls(
            IdentifierNode.from_dict(input_dict["callee"]),
            FunctionCallArgumentsNode.from_dict(input_dict["arguments"]),
            ast_position_info,
        )


class BinaryOperationExprNode(ExprNode):
    """An AST node for a binary operation"""

    def __init__(
        self,
        left: ExprNode,
        right: ExprNode,
        operator: BinaryOperatorType,
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super().__init__(ast_position_info)
        self.left = left
        self.right = right
        self.operator = operator

    @staticmethod
    def get_node_type_str() -> str:
        return "BinaryOperationExprNode"

    def _to_dict(self) -> dict:
        return {
            "left": self.left.to_dict(),
            "right": self.right.to_dict(),
            "operator": self.operator,
        }

    @classmethod
    def _from_dict(
        cls, input_dict: dict, ast_position_info: ASTPositionInfo
    ) -> "BinaryOperationExprNode":
        return cls(
            expr_from_dict(input_dict["left"]),
            expr_from_dict(input_dict["right"]),
            input_dict["operator"],
            ast_position_info,
        )


class UnaryOperatorExprNode(ExprNode):
    """An AST node for a unary operation"""

    def __init__(
        self,
        operand: ExprNode,
        operator: UnaryOperatorType,
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super().__init__(ast_position_info)
        self.operand = operand
        self.operator = operator

    @staticmethod
    def get_node_type_str() -> str:
        return "UnaryOperatorExprNode"

    def _to_dict(self) -> dict:
        return {"operand": self.operand.to_dict(), "operator": self.operator}

    @classmethod
    def _from_dict(
        cls, input_dict: dict, ast_position_info: ASTPositionInfo
    ) -> "UnaryOperatorExprNode":
        return cls(
            expr_from_dict(input_dict["operand"]),
            input_dict["operator"],
            ast_position_info,
        )


# Constant exprs
# ----------------------------------------


class ConstantValue:
    """Object for constant value"""

    def __init__(
        self,
        value: int | bool | float | complex | str | None,
        value_type: typing.Literal["int", "bool", "real", "complex", "str", "null"],
    ) -> None:
        self.value = value
        self.type = value_type

    def __str__(self):
        return f"ConstantValue: {self.value} ({self.type})"

    def __repr__(self):
        return self.__str__()

    def to_dict(self):
        return {"value": str(self.value), "type": self.type}

    @classmethod
    def from_dict(cls, input_dict: dict) -> "ConstantValue":
        value = input_dict["value"]
        value_type = input_dict["type"]
        if value_type == "int":
            value = int(value)
        elif value_type == "bool":
            value = bool(value)
        elif value_type == "real":
            value = float(value)
        elif value_type == "complex":
            value = complex(value)
        elif value_type == "str":
            pass
        elif value_type == "null":
            value = None
        else:
            raise ValueError(f"Unknown type '{value_type}' with value '{value}'")
        return cls(value, value_type)


class ConstantExprNode(ExprNode):
    """An AST node for a constant expression"""

    def __init__(
        self, value: ConstantValue, ast_position_info: ASTPositionInfo
    ) -> None:
        super().__init__(ast_position_info)
        self.value = value

    @staticmethod
    def get_node_type_str() -> str:
        return "ConstantExprNode"

    def _to_dict(self) -> dict:
        return {"value": self.value.to_dict()}

    @classmethod
    def _from_dict(
        cls, input_dict: dict, ast_position_info: ASTPositionInfo
    ) -> "ConstantExprNode":
        return cls(
            ConstantValue.from_dict(input_dict["value"]),
            ast_position_info,
        )


class CommentNode(StmtNode):
    """An AST node for a comment"""

    def __init__(self, value: str, ast_position_info: ASTPositionInfo) -> None:
        super().__init__(ast_position_info)
        self.value = value

    @staticmethod
    def get_node_type_str() -> str:
        return "CommentNode"

    def _to_dict(self) -> dict:
        return {"value": self.value}

    @classmethod
    def _from_dict(
        cls, input_dict: dict, ast_position_info: ASTPositionInfo
    ) -> "CommentNode":
        return cls(input_dict["value"], ast_position_info)


# Stmts
# ----------------------------------------
class AttributeTagValuesNode(ASTNode):

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

    @staticmethod
    def get_node_type_str() -> str:
        return "AttributeTagValuesNode"

    def _to_dict(self) -> dict:
        return {
            "values": ([expr.to_dict() for expr in self.values] if self.values else [])
        }

    @classmethod
    def _from_dict(
        cls, input_dict: dict, ast_position_info: ASTPositionInfo
    ) -> "AttributeTagValuesNode":
        node = cls(None, None, ast_position_info)
        node.stmts = [expr_from_dict(expr) for expr in input_dict["values"]]
        return node


class AttributeTagNode(ASTNode):

    def __init__(
        self,
        key: IdentifierNode,
        values: typing.Optional[AttributeTagValuesNode],
        ast_position_info: ASTPositionInfo,
    ):
        super().__init__(ast_position_info)
        self.key = key
        self.values = values

    @staticmethod
    def get_node_type_str() -> str:
        return "AttributeTagNode"

    def _to_dict(self) -> dict:
        return {"key": self.key, "values": self.values.to_dict()}

    @classmethod
    def _from_dict(
        cls, input_dict: dict, ast_position_info: ASTPositionInfo
    ) -> "AttributeTagNode":
        node = cls(input_dict["key"], None, ast_position_info)
        node.values = [expr_from_dict(expr) for expr in input_dict["values"]]
        return node


class AttributeTagsNode(ASTNode):

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

    @staticmethod
    def get_node_type_str() -> str:
        return "AttributeTagsNode"

    def _to_dict(self) -> dict:
        return {"tags": ([tag.to_dict() for tag in self.tags] if self.tags else [])}

    @classmethod
    def _from_dict(
        cls, input_dict: dict, ast_position_info: ASTPositionInfo
    ) -> "AttributeTagsNode":
        node = cls(None, None, ast_position_info)
        node.stmts = [AttributeTagNode.from_dict(tag) for tag in input_dict["tags"]]
        return node


class FunctionDeclNode(DeclNode):
    """An AST node for a function declaration"""

    def __init__(
        self,
        attribute_tags: AttributeTagsNode,
        identifier: IdentifierNode,
        parameters: FunctionDeclParametersNode,
        return_type: TypeNode,
        stmts: StmtsNode,
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super().__init__(ast_position_info)
        self.attribute_tags = attribute_tags
        self.identifier = identifier
        self.parameters = parameters
        self.return_type = return_type
        self.stmts = stmts

    @staticmethod
    def get_node_type_str() -> str:
        return "FunctionDeclNode"

    def _to_dict(self) -> dict:
        return {
            "attribute_tags": self.attribute_tags.to_dict(),
            "identifier": self.identifier.to_dict(),
            "parameters": self.parameters.to_dict(),
            "return_type": self.return_type.to_dict(),
            "stmts": self.stmts.to_dict(),
        }

    @classmethod
    def _from_dict(
        cls, input_dict: dict, ast_position_info: ASTPositionInfo
    ) -> "FunctionDeclNode":
        return cls(
            AttributeTagsNode.from_dict(input_dict["attribute_tags"]),
            IdentifierNode.from_dict(input_dict["identifier"]),
            FunctionDeclParametersNode.from_dict(input_dict["parameters"]),
            TypeNode.from_dict(input_dict["return_type"]),
            StmtsNode.from_dict(input_dict["stmts"]),
            ast_position_info,
        )


class DataDeclNode(DeclNode, abc.ABC):
    """An AST node for variable / constant declaration"""

    def __init__(
        self,
        target: IdentifierNode,
        _type: TypeNode,
        value: ExprNode,
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super().__init__(ast_position_info)
        self.target = target
        self._type = _type
        self.value = value

    def _to_dict(self) -> dict:
        return {
            "target": self.target.to_dict(),
            "_type": self._type.to_dict(),
            "value": self.value.to_dict(),
        }

    @classmethod
    def _from_dict(
        cls, input_dict: dict, ast_position_info: ASTPositionInfo
    ) -> "DataDeclNode":
        return cls(
            IdentifierNode.from_dict(input_dict["target"]),
            TypeNode.from_dict(input_dict["_type"]),
            expr_from_dict(input_dict["value"]),
            ast_position_info,
        )


class VariableDeclNode(DataDeclNode):

    @staticmethod
    def get_node_type_str() -> str:
        return "VariableDeclNode"


class ConstantDeclNode(DataDeclNode):

    @staticmethod
    def get_node_type_str() -> str:
        return "ConstantDeclNode"


class AssignmentStmtNode(StmtNode):
    """An AST node for assignment"""

    def __init__(
        self,
        target: ExprNode,
        value: ExprNode,
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super().__init__(ast_position_info)
        self.target = target
        self.value = value

    @staticmethod
    def get_node_type_str() -> str:
        return "AssignmentStmtNode"

    def _to_dict(self) -> dict:
        return {
            "target": self.target.to_dict(),
            "value": self.value.to_dict(),
        }

    @classmethod
    def _from_dict(
        cls, input_dict: dict, ast_position_info: ASTPositionInfo
    ) -> "AssignmentStmtNode":
        return cls(
            expr_from_dict(input_dict["target"]),
            expr_from_dict(input_dict["value"]),
            ast_position_info,
        )


class AugmentedAssignmentStmtNode(StmtNode):
    """An AST node for augmented assignment"""

    def __init__(
        self,
        target: ExprNode,
        operator: AugmentedAssignmentOperatorType,
        value: ExprNode,
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super().__init__(ast_position_info)
        self.target = target
        self.operator = operator
        self.value = value

    @staticmethod
    def get_node_type_str() -> str:
        return "AugmentedAssignmentStmtNode"

    def _to_dict(self) -> dict:
        return {
            "target": self.target.to_dict(),
            "operator": self.operator,
            "value": self.value.to_dict(),
        }

    @classmethod
    def _from_dict(
        cls, input_dict: dict, ast_position_info: ASTPositionInfo
    ) -> "AugmentedAssignmentStmtNode":
        return cls(
            expr_from_dict(input_dict["target"]),
            input_dict["operator"],
            expr_from_dict(input_dict["value"]),
            ast_position_info,
        )


class ExprStmtNode(StmtNode):
    """An AST node for a statement that is formed by an expression e.g. a();"""

    def __init__(self, expr: ExprNode, ast_position_info: ASTPositionInfo) -> None:
        super().__init__(ast_position_info)
        self.expr = expr

    @staticmethod
    def get_node_type_str() -> str:
        return "ExprStmt"

    def _to_dict(self) -> dict:
        return {"expr": self.expr.to_dict()}

    @classmethod
    def _from_dict(
        cls, input_dict: dict, ast_position_info: ASTPositionInfo
    ) -> "ExprStmtNode":
        return cls(
            expr_from_dict(input_dict["expr"]),
            ast_position_info,
        )


class IfStmtNode(StmtNode):
    """An AST node for if stmts"""

    def __init__(
        self,
        condition: ExprNode,
        stmts: StmtsNode,
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super().__init__(ast_position_info)
        self.condition = condition
        self.stmts = stmts

    @staticmethod
    def get_node_type_str() -> str:
        return "IfStmtNode"

    def _to_dict(self) -> dict:
        return {"condition": self.condition.to_dict(), "stmts": self.stmts.to_dict()}

    @classmethod
    def _from_dict(
        cls, input_dict: dict, ast_position_info: ASTPositionInfo
    ) -> "IfStmtNode":
        return cls(
            expr_from_dict(input_dict["condition"]),
            StmtsNode.from_dict(input_dict["stmts"]),
            ast_position_info,
        )


class ElseifStmtNode(IfStmtNode):
    """An AST node for elseif stmts"""

    @staticmethod
    def get_node_type_str() -> str:
        return "ElseifStmtNode"


class ElseStmtNode(StmtNode):
    """An AST node for else stmts"""

    def __init__(self, stmts: StmtsNode, ast_position_info: ASTPositionInfo) -> None:
        super().__init__(ast_position_info)
        self.stmts = stmts

    @staticmethod
    def get_node_type_str() -> str:
        return "ElseStmtNode"

    def _to_dict(self) -> dict:
        return {"stmts": self.stmts.to_dict()}

    @classmethod
    def _from_dict(
        cls, input_dict: dict, ast_position_info: ASTPositionInfo
    ) -> "ElseStmtNode":
        return cls(
            StmtsNode.from_dict(input_dict["stmts"]),
            ast_position_info,
        )


class ForInitialisationStmtNode(StmtNode):
    """An AST node for variable declaration for a for loop"""

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

    @staticmethod
    def get_node_type_str() -> str:
        return "ForInitialisationStmt"

    def _to_dict(self) -> dict:
        return {
            "target": self.target.to_dict(),
            "init_type": self.init_type.to_dict(),
            "value": self.value.to_dict(),
        }

    @classmethod
    def _from_dict(
        cls, input_dict: dict, ast_position_info: ASTPositionInfo
    ) -> "ForInitialisationStmtNode":
        return cls(
            IdentifierNode.from_dict(input_dict["target"]),
            TypeNode.from_dict(input_dict["init_type"]),
            expr_from_dict(input_dict["value"]),
            ast_position_info,
        )


class ForStmtNode(StmtNode):
    """An AST node for for loops"""

    def __init__(
        self,
        init_stmt: ForInitialisationStmtNode,
        stmts: StmtsNode,
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super().__init__(ast_position_info)
        self.init_stmt = init_stmt
        self.stmts = stmts

    @staticmethod
    def get_node_type_str() -> str:
        return "ForStmtNode"

    def _to_dict(self) -> dict:
        return {"init_stmt": self.init_stmt.to_dict(), "stmts": self.stmts.to_dict()}

    @classmethod
    def _from_dict(
        cls, input_dict: dict, ast_position_info: ASTPositionInfo
    ) -> "ForStmtNode":
        return cls(
            ForInitialisationStmtNode.from_dict(input_dict["init_stmt"]),
            StmtsNode.from_dict(input_dict["stmts"]),
            ast_position_info,
        )


class WhileStmtNode(StmtNode):
    """An AST node for while loops"""

    def __init__(
        self,
        condition: ExprNode,
        stmts: StmtsNode,
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super().__init__(ast_position_info)
        self.condition = condition
        self.stmts = stmts

    @staticmethod
    def get_node_type_str() -> str:
        return "WhileStmtNode"

    def _to_dict(self) -> dict:
        return {"condition": self.condition.to_dict(), "stmts": self.stmts.to_dict()}

    @classmethod
    def _from_dict(
        cls, input_dict: dict, ast_position_info: ASTPositionInfo
    ) -> "WhileStmtNode":
        return cls(
            expr_from_dict(input_dict["condition"]),
            StmtsNode.from_dict(input_dict["stmts"]),
            ast_position_info,
        )


class ReturnStmtNode(StmtNode):
    """An AST node for returning"""

    def __init__(self, value: ExprNode, ast_position_info: ASTPositionInfo) -> None:
        super().__init__(ast_position_info)
        self.value = value

    @staticmethod
    def get_node_type_str() -> str:
        return "ReturnStmtNode"

    def _to_dict(self) -> dict:
        return {"value": self.value.to_dict()}

    @classmethod
    def _from_dict(
        cls, input_dict: dict, ast_position_info: ASTPositionInfo
    ) -> "ReturnStmtNode":
        return cls(
            expr_from_dict(input_dict["value"]),
            ast_position_info,
        )


class StatelessStmtNode(StmtNode, abc.ABC):

    def _to_dict(self) -> dict:
        return {}

    @classmethod
    def _from_dict(
        cls, input_dict: dict, ast_position_info: ASTPositionInfo
    ) -> "StatelessStmtNode":
        return cls(ast_position_info)


class BreakStmtNode(StatelessStmtNode):
    """An AST node for break"""

    @staticmethod
    def get_node_type_str() -> str:
        return "BreakStmtNode"


class ContinueStmtNode(StatelessStmtNode):
    """An AST node for continue"""

    @staticmethod
    def get_node_type_str() -> str:
        return "ContinueStmtNode"


def expr_from_dict(input_dict: dict) -> ExprNode:
    if input_dict["node_type"] == "RangeLiteralExprNode":
        return RangeLiteralExprNode.from_dict(input_dict)


def stmt_from_dict(input_dict: dict) -> StmtNode:
    if input_dict["node_type"] == "FunctionDeclStmtNode":
        return FunctionDeclNode.from_dict(input_dict)
