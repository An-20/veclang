import typing
import veclang.parser.ply.lex as lex
import veclang.parser.ply.yacc as yacc


class ASTPositionInfo(typing.NamedTuple):
    """Position info of an AST node"""

    line_number: typing.Optional[int]
    line_character_number: typing.Optional[int]


class ASTNode:
    """
    An AST node
    """

    def __init__(self, ast_position_info: ASTPositionInfo) -> None:
        self.position_info = ast_position_info

    def __eq__(self, other):
        for attr in [x for x in self.__dir__() if x[:2] != "__"]:
            if not hasattr(other, attr):
                return False
            elif not getattr(self, attr).__eq__(getattr(other, attr)):
                return False
        return True


class ExpressionNode(ASTNode):
    """
    An AST node for an expression
    """


class StatementNode(ASTNode):
    """
    An AST node for a statement
    """


class ExpressionStatementNode(StatementNode):
    """
    An AST node for an expression
    """

    def __init__(
        self,
        expr: ExpressionNode,
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super(ExpressionStatementNode, self).__init__(ast_position_info)
        self.expr = expr


class BinaryOperatorNode(ASTNode):
    """
    An AST node for an operator
    """


class AdditionBinaryOperatorNode(BinaryOperatorNode):
    """
    An AST node for the addition operator
    """


class SubtractionBinaryOperatorNode(BinaryOperatorNode):
    """
    An AST node for the subtraction operator
    """


class BinaryOperationExpressionNode(ExpressionNode):
    """
    An AST node for a binary operation
    """

    def __init__(
        self,
        left: ExpressionNode,
        right: ExpressionNode,
        operator: BinaryOperatorNode,
        ast_position_info: ASTPositionInfo,
    ) -> None:
        super(BinaryOperationExpressionNode, self).__init__(ast_position_info)
        self.left = left
        self.right = right
        self.operator = operator


def p_add_binary_operator(p):
    """AdditionBinaryOperatorNode"""
    p[0] = AdditionBinaryOperatorNode(ASTPositionInfo(p.line_no(1), p.lex_pos(1)))


class NumberLiteralExpressionNode(ExpressionNode):
    """
    An AST node for a constant
    """

    def __init__(self, value: typing.Any, ast_position_info: ASTPositionInfo) -> None:
        super(NumberLiteralExpressionNode, self).__init__(ast_position_info)
        self.value = value


class FloatLiteralExpressionNode(NumberLiteralExpressionNode):
    """
    An AST node for a constant float
    """

    def __init__(self, value: float, ast_position_info: ASTPositionInfo) -> None:
        super(FloatLiteralExpressionNode, self).__init__(value, ast_position_info)


class IntegerLiteralExpressionNode(NumberLiteralExpressionNode):
    """
    An AST node for a constant int
    """

    def __init__(self, value: int, ast_position_info: ASTPositionInfo) -> None:
        super(IntegerLiteralExpressionNode, self).__init__(value, ast_position_info)


def p_integer_literal_expression(p):
    """integer_literal : INTEGER_LITERAL"""
    p[0] = IntegerLiteralExpressionNode(
        p[1], ASTPositionInfo(p.line_no(1), p.lex_pos(1))
    )


def p_float_literal_expression(p):
    """float_literal : FLOAT_LITERAL"""
    p[0] = FloatLiteralExpressionNode(p[1], ASTPositionInfo(p.line_no(1), p.lex_pos(1)))


def p_number_literal_expression(p):
    """float_literal : FLOAT_LITERAL"""
    p[0] = NumberLiteralExpressionNode(
        p[1], ASTPositionInfo(p.line_no(1), p.lex_pos(1))
    )


def p_addition_binary_operator(p):
    """addition_binary_operator : PLUS"""
    p[0] = AdditionBinaryOperatorNode(ASTPositionInfo(p.line_no(1), p.lex_pos(1)))


def p_subtraction_binary_operator(p):
    """subtraction_binary_operator : MINUS"""
    p[0] = SubtractionBinaryOperatorNode(ASTPositionInfo(p.line_no(1), p.lex_pos(1)))


def p_binary_operator(p):
    """binary_operator : addition_binary_operator
    | subtraction_binary_operator;
    """
    p[0] = p[1]


def p_binary_operation_expression(p):
    """binary_operation_expression : comparable_expression binary_operator comparable_expression"""
    p[0] = BinaryOperationExpressionNode(
        p[1], p[3], p[2], ASTPositionInfo(p.line_no(1), p.lex_pos(1))
    )


def p_parenthesis_expression(p):
    """parenthesis_expression : LEFT_PARENTHESIS expression RIGHT_PARENTHESIS"""
    p[0] = p[2]


def p_expression(p):
    """expression : integer_literal
    | float_literal
    | parenthesis_expression"""
    p[0] = p[1]


def p_expression_statement(p):
    """expression_statement: expression SEMICOLON;"""
    p[0] = p[1]


def p_statement(p):
    """uhh"""
    p[0] = p[1]


def parse_integer_literal(t):
    r"[+-]?\d+"
    t.value = float(str(t.value))
    return t


def parse_float_literal(t):
    r"[+-]?\d+\.\d+"
    t.value = float(str(t.value))
    return t


# is this a slightly unergonomic solution because i want to escape the tab? yes.
lex_test_spec = """
PLUS: "\\+"
MINUS: "-"

LEFT_PARENTHESIS: "\\("
RIGHT_PARENTHESIS: "\\)"
SEMICOLON: ";"
"""
lex_test_spec += '\nignore: "\t "'

lexer_function_spec = {
    "FLOAT_LITERAL": parse_float_literal,
    "INTEGER_LITERAL": parse_integer_literal,
}


yacc_test_spec = """
int_number_literal_expression : INTEGER_LITERAL
float_number_literal_expression : FLOAT_LITERAL
number_literal_expression : int_number_literal_expression
                          | float_number_literal_expression

addition_binary_operator : PLUS
subtraction_binary_operator : MINUS
binary_operator : addition_binary_operator
                | subtraction_binary_operator

binary_operation_expression : expression binary_operator expression

parenthesis_expression : LEFT_PARENTHESIS expression RIGHT_PARENTHESIS

expression : number_literal_expression
           | binary_operation_expression
           | parenthesis_expression

expression_statement : expression SEMICOLON

statement : expression_statement

start : statement
"""


parser_function_spec = {
    "int_number_literal_expression": p_integer_literal_expression,
    "float_number_literal_expression": p_float_literal_expression,
    "number_literal_expression": p_number_literal_expression,
    "addition_binary_operator": p_addition_binary_operator,
    "subtraction_binary_operator": p_subtraction_binary_operator,
    "binary_operator": p_binary_operator,
    "binary_operation_expression": p_binary_operation_expression,
    "parenthesis_expression": p_parenthesis_expression,
    "expression": p_expression,
    "expression_statement": p_expression_statement,
    "statement": p_statement,
}


parser = yacc.yacc(
    yacc_test_spec,
    parser_function_spec,
    lex.get_tokens(lex_test_spec, lexer_function_spec),
    (("left", "PLUS", "MINUS"),),
    debug=True,
)

parser.lexer = lex.lex(
    lex_test_spec,
    lexer_function_spec,
    debug=True,
)


def test_yacc():
    sample_texts = ["1 + 1;", "23 + 3;"]
    for sample_text in sample_texts:
        print(parser.parse(sample_text))
