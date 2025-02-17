"""Parser for Veclang"""

import veclang.frontend.ply.lex as lex
import veclang.frontend.ply.yacc as yacc


from veclang.frontend.parser.lexer import (
    LEXER_TOKEN_SPEC_STR,
    LEXER_FUNCTION_SPEC,
    lexer,
)
from veclang.frontend.parser.vl_ast import (
    AugmentedAssignmentOperatorType,
    BinaryOperatorType,
    UnaryOperatorType,
    ASTPositionInfo,
    ProgramNode,
    StmtsNode,
    IdentifierNode,
    TypeNode,
    FunctionDeclParameterNode,
    FunctionDeclParametersNode,
    CommentNode,
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
    AttributeTagValuesNode,
    AttributeTagNode,
    AttributeTagsNode,
    FunctionDeclNode,
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
    BreakStmtNode,
    ContinueStmtNode,
)
from veclang.frontend.parser.vl_ast_io import format_ast


DEBUG: bool = False

PARSER_SPEC_STR = """
comment : COMMENT
type : TYPE

start : program
program : stmts

stmts : stmt
      | stmts stmt

block : LEFT_CURLY_BRACKET stmts RIGHT_CURLY_BRACKET

decl : function_decl
     | variable_decl
     | constant_decl

stmt : decl
     | assignment_stmt
     | augmented_assignment_stmt
     | expr_stmt
     | if_stmt
     | elif_stmt
     | else_stmt
     | for_stmt
     | while_stmt
     | break_stmt
     | continue_stmt
     | return_stmt
     | comment


attribute_tags : attribute_tags attribute_tag
               | attribute_tag
               |

attribute_tag : LEFT_ANGLE_BRACKET identifier COLON attribute_tag_values RIGHT_ANGLE_BRACKET
              | LEFT_ANGLE_BRACKET identifier RIGHT_ANGLE_BRACKET

attribute_tag_values : attribute_tag_values COMMA simple_literal
                     | simple_literal

function_decl_parameter : identifier COLON type
function_decl_parameters : function_decl_parameter
                         | function_decl_parameters COMMA function_decl_parameter
                         |

function_decl : attribute_tags FN identifier LEFT_PARENTHESIS function_decl_parameters RIGHT_PARENTHESIS RIGHT_ARROW type block


variable_decl : LET identifier COLON type ASSIGNMENT expr SEMICOLON
constant_decl : CONST identifier COLON type ASSIGNMENT expr SEMICOLON

assignment_stmt : identifier ASSIGNMENT expr SEMICOLON
augmented_assignment_stmt : identifier augmented_assignment_operator expr SEMICOLON

expr_stmt : expr SEMICOLON


if_stmt : IF LEFT_PARENTHESIS expr RIGHT_PARENTHESIS block
elif_stmt : ELIF LEFT_PARENTHESIS expr RIGHT_PARENTHESIS block
else_stmt : ELSE block

for_initialisation_stmt : identifier COLON type IN range_literal
for_stmt : FOR LEFT_PARENTHESIS for_initialisation_stmt RIGHT_PARENTHESIS block
while_stmt : WHILE LEFT_PARENTHESIS expr RIGHT_PARENTHESIS block


break_stmt : BREAK SEMICOLON
continue_stmt : CONTINUE SEMICOLON
return_stmt : RETURN expr SEMICOLON


augmented_assignment_operator : PLUS_ASSIGNMENT
                              | MINUS_ASSIGNMENT
                              | TIMES_ASSIGNMENT
                              | DIVIDE_ASSIGNMENT
                              | MODULUS_ASSIGNMENT

comparison_operator : EQUAL_TO
                    | NOT_EQUAL_TO
                    | LEFT_ANGLE_BRACKET
                    | LESS_THAN_OR_EQUAL
                    | RIGHT_ANGLE_BRACKET
                    | GREATER_THAN_OR_EQUAL


// Operators, in order of precedence from lowest to highest
disjunction_prec_expr : conjunction_prec_expr BOOLEAN_OR conjunction_prec_expr
                      | conjunction_prec_expr

conjunction_prec_expr : inversion_prec_expr BOOLEAN_AND inversion_prec_expr
                      | inversion_prec_expr

inversion_prec_expr : BOOLEAN_NOT inversion_prec_expr
                    | comparison_prec_expr

comparison_prec_expr : bitwise_or_prec_expr comparison_operator bitwise_or_prec_expr
                     | bitwise_or_prec_expr

bitwise_or_prec_expr : bitwise_or_prec_expr BITWISE_OR bitwise_xor_prec_expr
                     | bitwise_xor_prec_expr

bitwise_xor_prec_expr : bitwise_xor_prec_expr BITWISE_XOR bitwise_and_prec_expr
                      | bitwise_and_prec_expr

bitwise_and_prec_expr : bitwise_and_prec_expr BITWISE_AND bitwise_shift_prec_expr
                      | bitwise_shift_prec_expr

bitwise_shift_prec_expr : bitwise_shift_prec_expr BITWISE_LEFT_SHIFT addition_prec_expr
                        | bitwise_shift_prec_expr BITWISE_RIGHT_SHIFT addition_prec_expr
                        | addition_prec_expr

addition_prec_expr : addition_prec_expr PLUS multiplication_prec_expr
                   | addition_prec_expr MINUS multiplication_prec_expr
                   | multiplication_prec_expr

multiplication_prec_expr : multiplication_prec_expr TIMES unary_prec_expr
                         | multiplication_prec_expr DIVIDE unary_prec_expr
                         | multiplication_prec_expr INTEGER_DIVIDE unary_prec_expr
                         | multiplication_prec_expr MODULUS unary_prec_expr
                         | unary_prec_expr

unary_prec_expr : PLUS unary_prec_expr
                | MINUS unary_prec_expr
                | BITWISE_NOT unary_prec_expr
                | exponentiation_prec_expr

exponentiation_prec_expr : primary_expr EXPONENTIATION exponentiation_prec_expr
                         | primary_expr


// Literal expressions
int_literal : INT_LITERAL
bool_literal : BOOL_LITERAL
real_literal : REAL_LITERAL
str_literal : STR_LITERAL

num_literal : int_literal
            | real_literal

simple_literal : num_literal
               | bool_literal
               | str_literal

imaginary_literal : num_literal IMAGINARY_UNIT

range_literal : LEFT_PARENTHESIS expr COLON expr RIGHT_PARENTHESIS
              | LEFT_PARENTHESIS expr COLON expr COLON expr RIGHT_PARENTHESIS

array_literal_elements : expr
                       | array_literal_elements COMMA expr

array_literal : LEFT_SQUARE_BRACKET array_literal_elements RIGHT_SQUARE_BRACKET

identifier : IDENTIFIER

atomic_expr : simple_literal
            | imaginary_literal
            | range_literal
            | array_literal
            | identifier


function_call_arguments : expr
                        | function_call_arguments COMMA expr
                        |
function_call_expr : primary_expr LEFT_PARENTHESIS function_call_arguments RIGHT_PARENTHESIS

member_access_expr : primary_expr DOT identifier

index_elements : expr
               | index_elements COMMA expr
index_expr : primary_expr LEFT_SQUARE_BRACKET index_elements RIGHT_SQUARE_BRACKET

parenthesised_expr : LEFT_PARENTHESIS expr RIGHT_PARENTHESIS

primary_expr : atomic_expr
             | member_access_expr
             | function_call_expr
             | index_expr
             | parenthesised_expr

expr : disjunction_prec_expr

"""


def get_ast_pos_info(p):
    try:
        return ASTPositionInfo(p.line_no(1), p.lex_pos(1))
    except IndexError:
        return ASTPositionInfo(0, 0)


def p_program(p):
    p[0] = ProgramNode(p[1], get_ast_pos_info(p))


def p_comment(p):
    p[0] = CommentNode(p[1], get_ast_pos_info(p))


def p_type(p):
    p[0] = TypeNode(p[1], get_ast_pos_info(p))


def p_stmts(p):
    if len(p) == 3:
        # Multiple statements
        p[0] = StmtsNode(p[1], p[2], get_ast_pos_info(p))
    else:
        p[0] = StmtsNode(None, p[1], get_ast_pos_info(p))


def p_block(p):
    p[0] = p[2]


def p_attribute_tags(p):
    if len(p) == 3:
        # Multi-tag: <a> \n <b>
        p[0] = AttributeTagsNode(p[1], p[2], get_ast_pos_info(p))
    elif len(p) == 2:
        # One element: <a>
        p[0] = AttributeTagsNode(None, p[1], get_ast_pos_info(p))
    else:
        p[0] = AttributeTagsNode(None, None, get_ast_pos_info(p))


def p_attribute_tag(p):
    if len(p) == 6:
        # key: value
        p[0] = AttributeTagNode(p[2], p[4], get_ast_pos_info(p))
    else:
        # just key
        p[0] = AttributeTagNode(p[2], None, get_ast_pos_info(p))


def p_attribute_tag_values(p):
    if len(p) == 4:
        # Multi-value: a, b
        p[0] = AttributeTagValuesNode(p[1], p[3], get_ast_pos_info(p))
    else:
        # Just one value
        p[0] = AttributeTagValuesNode(None, p[1], get_ast_pos_info(p))


def p_function_decl_parameter(p):
    p[0] = FunctionDeclParameterNode(p[1], p[3], get_ast_pos_info(p))


def p_function_decl_parameters(p):
    if len(p) == 4:
        # Multi-element: a, b...
        p[0] = FunctionDeclParametersNode(p[1], p[3], get_ast_pos_info(p))
    elif len(p) == 2:
        # One element: a
        p[0] = FunctionDeclParametersNode(None, p[1], get_ast_pos_info(p))
    else:
        p[0] = FunctionDeclParametersNode(None, None, get_ast_pos_info(p))


def p_function_decl(p):
    p[0] = FunctionDeclNode(p[1], p[3], p[5], p[8], p[9], get_ast_pos_info(p))


def p_variable_decl(p):
    p[0] = VariableDeclNode(p[2], p[4], p[6], get_ast_pos_info(p))


def p_constant_decl(p):
    p[0] = ConstantDeclNode(p[2], p[4], p[6], get_ast_pos_info(p))


def p_assignment_stmt(p):
    p[0] = AssignmentStmtNode(p[1], p[3], get_ast_pos_info(p))


def p_augmented_assignment_stmt(p):
    operator: AugmentedAssignmentOperatorType
    if p[2] == "+=":
        operator = "PLUS_ASSIGNMENT"
    elif p[2] == "-":
        operator = "MINUS_ASSIGNMENT"
    elif p[2] == "/=":
        operator = "DIVIDE_ASSIGNMENT"
    elif p[2] == "*=":
        operator = "TIMES_ASSIGNMENT"
    elif p[2] == "%":
        operator = "MODULUS_ASSIGNMENT"
    else:
        raise ValueError(f"Unknown operator type '{p[2]}'")
    p[0] = AugmentedAssignmentStmtNode(p[1], operator, p[3], get_ast_pos_info(p))


def p_expr_stmt(p):
    p[0] = ExprStmtNode(p[1], get_ast_pos_info(p))


def p_if_stmt(p):
    p[0] = IfStmtNode(p[3], p[5], get_ast_pos_info(p))


def p_elif_stmt(p):
    p[0] = ElseifStmtNode(p[3], p[5], get_ast_pos_info(p))


def p_else_stmt(p):
    p[0] = ElseStmtNode(p[2], get_ast_pos_info(p))


def p_for_initialisation_stmt(p):
    p[0] = ForInitialisationStmtNode(p[1], p[3], p[5], get_ast_pos_info(p))


def p_for_stmt(p):
    p[0] = ForStmtNode(p[3], p[5], get_ast_pos_info(p))


def p_while_stmt(p):
    p[0] = WhileStmtNode(p[3], p[5], get_ast_pos_info(p))


def p_break_stmt(p):
    p[0] = BreakStmtNode(get_ast_pos_info(p))


def p_continue_stmt(p):
    p[0] = ContinueStmtNode(get_ast_pos_info(p))


def p_return_stmt(p):
    p[0] = ReturnStmtNode(p[2], get_ast_pos_info(p))


def p_passthrough(p):
    p[0] = p[1]


def p_disjunction_prec_expr(p):
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = BinaryOperationExprNode(p[1], p[3], "BOOLEAN_OR", get_ast_pos_info(p))


def p_conjunction_prec_expr(p):
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = BinaryOperationExprNode(p[1], p[3], "BOOLEAN_AND", get_ast_pos_info(p))


def p_inversion_prec_expr(p):
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = UnaryOperatorExprNode(p[2], "BOOLEAN_NOT", get_ast_pos_info(p))


def p_comparison_prec_expr(p):
    if len(p) == 2:
        p[0] = p[1]
    else:
        operator: BinaryOperatorType
        if p[2] == "==":
            operator = "EQUAL_TO"
        elif p[2] == "!=":
            operator = "NOT_EQUAL_TO"
        elif p[2] == "<":
            operator = "LESS_THAN"
        elif p[2] == "<=":
            operator = "LESS_THAN_OR_EQUAL"
        elif p[2] == ">":
            operator = "GREATER_THAN"
        elif p[2] == ">=":
            operator = "GREATER_THAN_OR_EQUAL"
        else:
            raise ValueError(f"Unknown operator '{p[2]}'")
        p[0] = BinaryOperationExprNode(p[1], p[3], operator, get_ast_pos_info(p))


def p_bitwise_or_prec_expr(p):
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = BinaryOperationExprNode(p[1], p[3], "BITWISE_OR", get_ast_pos_info(p))


def p_bitwise_xor_prec_expr(p):
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = BinaryOperationExprNode(p[1], p[3], "BITWISE_XOR", get_ast_pos_info(p))


def p_bitwise_and_prec_expr(p):
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = BinaryOperationExprNode(p[1], p[3], "BITWISE_AND", get_ast_pos_info(p))


def p_bitwise_shift_prec_expr(p):
    if len(p) == 2:
        p[0] = p[1]
    else:
        operator: BinaryOperatorType
        if p[2] == "<<":
            operator = "BITWISE_LEFT_SHIFT"
        elif p[2] == ">>":
            operator = "BITWISE_RIGHT_SHIFT"
        else:
            raise ValueError(f"Unknown operator '{p[2]}'")
        p[0] = BinaryOperationExprNode(p[1], p[3], operator, get_ast_pos_info(p))


def p_addition_prec_expr(p):
    if len(p) == 2:
        p[0] = p[1]
    else:
        operator: BinaryOperatorType
        if p[2] == "+":
            operator = "PLUS"
        elif p[2] == "-":
            operator = "MINUS"
        else:
            raise ValueError(f"Unknown operator '{p[2]}'")
        p[0] = BinaryOperationExprNode(p[1], p[3], operator, get_ast_pos_info(p))


def p_multiplication_prec_expr(p):
    if len(p) == 2:
        p[0] = p[1]
    else:
        operator: BinaryOperatorType
        if p[2] == "*":
            operator = "TIMES"
        elif p[2] == "/":
            operator = "DIVIDE"
        elif p[2] == "//":
            operator = "INTEGER_DIVIDE"
        elif p[2] == "%":
            operator = "MODULUS"
        else:
            raise ValueError(f"Unknown operator '{p[2]}'")
        p[0] = BinaryOperationExprNode(p[1], p[3], operator, get_ast_pos_info(p))


def p_unary_prec_expr(p):
    if len(p) == 2:
        p[0] = p[1]
    else:
        operator: UnaryOperatorType
        if p[2] == "+":
            operator = "UNARY_PLUS"
        elif p[2] == "-":
            operator = "UNARY_MINUS"
        elif p[2] == "~":
            operator = "BITWISE_NOT"
        else:
            raise ValueError(f"Unknown operator '{p[2]}'")
        p[0] = UnaryOperatorExprNode(p[2], operator, get_ast_pos_info(p))


def p_exponentiation_prec_expr(p):
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = BinaryOperationExprNode(
            p[1], p[3], "EXPONENTIATION", get_ast_pos_info(p)
        )


def p_int_literal(p):
    p[0] = ConstantExprNode(p[1], get_ast_pos_info(p))


def p_bool_literal(p):
    p[0] = ConstantExprNode(p[1], get_ast_pos_info(p))


def p_real_literal(p):
    p[0] = ConstantExprNode(p[1], get_ast_pos_info(p))


def p_str_literal(p):
    p[0] = ConstantExprNode(p[1], get_ast_pos_info(p))


def p_imaginary_literal(p):
    value = ConstantValue(complex(0, p[1].value.value), "complex")
    p[0] = ConstantExprNode(value, get_ast_pos_info(p))


def p_range_literal(p):
    if len(p) == 6:
        # start : end (assume step = 1)
        step_expr_node = ConstantExprNode(ConstantValue(1, "int"), get_ast_pos_info(p))
        p[0] = RangeLiteralExprNode(p[2], p[4], step_expr_node, get_ast_pos_info(p))
    else:
        # start : end : step
        p[0] = RangeLiteralExprNode(p[2], p[4], p[6], get_ast_pos_info(p))


def p_array_literal_elements(p):
    if len(p) == 4:
        # Multi-element: a, b...
        p[0] = ArrayLiteralElementsNode(p[1], p[3], get_ast_pos_info(p))
    elif len(p) == 2:
        # One element: a
        p[0] = ArrayLiteralElementsNode(None, p[1], get_ast_pos_info(p))
    else:
        p[0] = ArrayLiteralElementsNode(None, None, get_ast_pos_info(p))


def p_array_literal(p):
    p[0] = ArrayLiteralExprNode(p[2], get_ast_pos_info(p))


def p_identifier(p):
    p[0] = IdentifierNode(p[1], get_ast_pos_info(p))


def p_function_call_arguments(p):
    if len(p) == 4:
        # Multi-element: a, b...
        p[0] = FunctionCallArgumentsNode(p[1], p[3], get_ast_pos_info(p))
    elif len(p) == 2:
        # One element: a
        p[0] = FunctionCallArgumentsNode(None, p[1], get_ast_pos_info(p))
    else:
        p[0] = FunctionCallArgumentsNode(None, None, get_ast_pos_info(p))


def p_function_call_expr(p):
    p[0] = FunctionCallExprNode(p[1], p[3], get_ast_pos_info(p))


def p_member_access_expr(p):
    p[0] = MemberAccessExprNode(p[1], p[3], get_ast_pos_info(p))


def p_index_elements(p):
    if len(p) == 4:
        # Multi-element: a, b...
        p[0] = IndexElementsNode(p[1], p[3], get_ast_pos_info(p))
    elif len(p) == 2:
        # One element: a
        p[0] = IndexElementsNode(None, p[1], get_ast_pos_info(p))
    else:
        raise ValueError("Index elements must have at least one expr")


def p_index_expr(p):
    p[0] = IndexExprNode(p[1], p[3], get_ast_pos_info(p))


def p_parenthesised_expr(p):
    p[0] = p[2]


def p_error(p):
    """Parser error"""
    # get formatted representation of stack
    stack_state_str = " ".join([symbol.type for symbol in parser.sym_stack][1:])
    print(f"Syntax error in input! Parser State:{parser.state} {stack_state_str} . {p}")


PARSER_FUNCTION_SPEC = {
    "start": p_passthrough,
    "comment": p_comment,
    "type": p_type,
    "program": p_program,
    "stmts": p_stmts,
    "block": p_block,
    "stmt": p_passthrough,
    "decl": p_passthrough,
    "attribute_tags": p_attribute_tags,
    "attribute_tag": p_attribute_tag,
    "attribute_tag_values": p_attribute_tag_values,
    "function_decl_parameter": p_function_decl_parameter,
    "function_decl_parameters": p_function_decl_parameters,
    "function_decl": p_function_decl,
    "variable_decl": p_variable_decl,
    "constant_decl": p_constant_decl,
    "assignment_stmt": p_assignment_stmt,
    "augmented_assignment_stmt": p_augmented_assignment_stmt,
    "expr_stmt": p_expr_stmt,
    "if_stmt": p_if_stmt,
    "elif_stmt": p_elif_stmt,
    "else_stmt": p_else_stmt,
    "for_initialisation_stmt": p_for_initialisation_stmt,
    "for_stmt": p_for_stmt,
    "while_stmt": p_while_stmt,
    "break_stmt": p_break_stmt,
    "continue_stmt": p_continue_stmt,
    "return_stmt": p_return_stmt,
    "comparison_operator": p_passthrough,
    "augmented_assignment_operator": p_passthrough,
    "disjunction_prec_expr": p_disjunction_prec_expr,
    "conjunction_prec_expr": p_conjunction_prec_expr,
    "inversion_prec_expr": p_inversion_prec_expr,
    "comparison_prec_expr": p_comparison_prec_expr,
    "bitwise_or_prec_expr": p_bitwise_or_prec_expr,
    "bitwise_xor_prec_expr": p_bitwise_xor_prec_expr,
    "bitwise_and_prec_expr": p_bitwise_and_prec_expr,
    "bitwise_shift_prec_expr": p_bitwise_shift_prec_expr,
    "addition_prec_expr": p_addition_prec_expr,
    "multiplication_prec_expr": p_multiplication_prec_expr,
    "unary_prec_expr": p_unary_prec_expr,
    "exponentiation_prec_expr": p_exponentiation_prec_expr,
    "num_literal": p_passthrough,
    "int_literal": p_int_literal,
    "bool_literal": p_bool_literal,
    "real_literal": p_real_literal,
    "str_literal": p_str_literal,
    "simple_literal": p_passthrough,
    "imaginary_literal": p_imaginary_literal,
    "range_literal": p_range_literal,
    "array_literal_elements": p_array_literal_elements,
    "array_literal": p_array_literal,
    "identifier": p_identifier,
    "atomic_expr": p_passthrough,
    "function_call_arguments": p_function_call_arguments,
    "function_call_expr": p_function_call_expr,
    "member_access_expr": p_member_access_expr,
    "index_elements": p_index_elements,
    "index_expr": p_index_expr,
    "parenthesised_expr": p_parenthesised_expr,
    "primary_expr": p_passthrough,
    "expr": p_passthrough,
    "error": p_error,
}


# Build the parser
parser = yacc.yacc(
    PARSER_SPEC_STR,
    PARSER_FUNCTION_SPEC,
    lex.get_tokens(LEXER_TOKEN_SPEC_STR, LEXER_FUNCTION_SPEC),
    (),
    debug=DEBUG,
)
parser.lexer = lexer


def parse(input_str: str) -> ProgramNode:
    """Parse a string and return an AST"""
    result = parser.parse(input_str)
    return result


if __name__ == "__main__":

    def t(input_str: str):
        result = parser.parse(input_str)
        print(format_ast(result))

    t(
        """
    fn main() -> int {
        return 0;
    }
    """
    )
