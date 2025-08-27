import veclang.frontend.ply.lex as lex
from veclang.frontend.parser.vl_ast import ConstantValue


DEBUG: bool = False

LEXER_TOKEN_SPEC_STR = """
ASSIGNMENT: "="
PLUS: "\\+"
MINUS: "-"
TIMES: "\\*"
DIVIDE: "/"
MODULUS: "%"
EXPONENTIATION: "\\*\\*"

PLUS_ASSIGNMENT: "\\+="
MINUS_ASSIGNMENT: "-="
TIMES_ASSIGNMENT: "\\*="
DIVIDE_ASSIGNMENT: "/="
MODULUS_ASSIGNMENT: "%="

TYPE: "(int|bool|real|complex|vec2|vec3|vec4|mat2|mat3|mat4|str)"
IMAGINARY_UNIT: "i"

RIGHT_ARROW: "-\\>"

EQUAL_TO: "=="
NOT_EQUAL_TO: "!="
LEFT_ANGLE_BRACKET: "\\<"
LESS_THAN_OR_EQUAL: "\\<="
RIGHT_ANGLE_BRACKET: "\\>"
GREATER_THAN_OR_EQUAL: "\\>="

BOOLEAN_AND: "(&&|and)"
BOOLEAN_OR: "(\\|\\||or)"
BOOLEAN_NOT: "(!|not)"

BITWISE_AND: "&"
BITWISE_OR: "\\|"
BITWISE_XOR: "\\^"
BITWISE_NOT: "~"
BITWISE_LEFT_SHIFT: "\\<\\<"
BITWISE_RIGHT_SHIFT: "\\>\\>"

LEFT_PARENTHESIS: "\\("
RIGHT_PARENTHESIS: "\\)"
LEFT_SQUARE_BRACKET: "\\["
RIGHT_SQUARE_BRACKET: "\\]"
LEFT_CURLY_BRACKET: "\\{"
RIGHT_CURLY_BRACKET: "\\}"

DOT: "\\."
COMMA: "\\,"
SCOPE_RESOLUTION: "\\:\\:"
COLON: "\\:"
SEMICOLON: ";"

USING: "using"
LET: "let"
CONST: "const"
CONSTEXPR: "constexpr"
IN: "in"
    
FN: "fn"
IF: "if"
ELIF: "elif"
ELSE: "else"
FOR: "for"
WHILE: "while"
BREAK: "break"
CONTINUE: "continue"
RETURN: "return"
"""
LEXER_TOKEN_SPEC_STR += '\nignore: "\t "\n'

RESERVED_KEYWORDS = [
    "using",
    "let",
    "const",
    "constexpr",
    "in",
    "fn",
    "if",
    "elif",
    "else",
    "for",
    "while",
    "break",
    "continue",
    "return",
    "i",
    "true",
    "false",
    "null",
    "int",
    "uint",
    "bool",
    "real",
    "complex",
    "vec2",
    "vec3",
    "vec4",
    "mat2",
    "mat3",
    "mat4",
    "str",
]
IDENTIFIER_REGEX = (
    r"\b(?!" + r"\b|".join(RESERVED_KEYWORDS) + r"\b)[a-zA-Z_][a-zA-Z_0-9]*"
)
LEXER_TOKEN_SPEC_STR += f'IDENTIFIER: "{IDENTIFIER_REGEX}"\n'


# noinspection PyPep8Naming
# noinspection PySingleQuotedDocstring
def t_REAL_LITERAL(t):
    r"((0|[1-9]\d*)(\.\d+)([eE][+\-]?\d+)?)|((0|[1-9]\d*)(\.\d+)?[eE][+\-]?\d+)"
    t.value = ConstantValue(float(str(t.value)), "real")
    return t


# noinspection PyPep8Naming
# noinspection PySingleQuotedDocstring
def t_INT_LITERAL(t):
    r"((0x[0-9a-fA-F]+)|(0b[01]+)|\d+)"
    value_str: str | ConstantValue = str(t.value)  # type hinting shenanigans
    if "0x" in value_str[:3]:  # could have leading +/-
        value_int = int(value_str, 16)
    elif "0b" in value_str[:3]:
        value_int = int(value_str, 2)
    else:
        value_int = int(value_str)
    t.value = ConstantValue(value_int, "int")
    return t


# noinspection PyPep8Naming
# noinspection PySingleQuotedDocstring
def t_BOOL_LITERAL(t):
    r"(true|false)"
    if t.value in {"true", "false"}:
        t.value = ConstantValue(t.value == "true", "bool")
    else:
        raise ValueError("Bool literal must be 'true' or 'false'")
    return t


# noinspection PyPep8Naming
# noinspection PySingleQuotedDocstring
def t_STR_LITERAL(t):
    r"(\"\"\"(.|\s)*?\"\"\"|\".*\")"
    t.value = t.value[1:-1]
    if t.value and t.value[0] == '"':
        # triple quoted
        t.value = t.value[2:-2]
    if '"' in t.value:
        raise ValueError("String cannot contain '\"' character.")
    t.value = ConstantValue(t.value, "str")
    return t


# noinspection PyPep8Naming
# noinspection PySingleQuotedDocstring
def t_NULL_LITERAL(t):
    r"null"
    t.value = ConstantValue(None, "null")
    return t


# noinspection PyPep8Naming
# noinspection PySingleQuotedDocstring
def t_COMMENT(t):
    r"""(\/\*(.|\s)*?\*\/|\/\/.*)"""
    if t.value[1] == "*":
        # multiline comment
        t.value = t.value[2:-2]
    else:
        t.value = t.value[2:]
    return t


# Define a rule to track line numbers
# noinspection PySingleQuotedDocstring
def t_newline(t):
    r"\n+"
    t.lexer.line_no += len(t.value)


# Error handling rule
def t_error(t):
    """Error handling rule"""
    print(f"Illegal character {t.value[0]}")
    t.lexer.skip(1)


LEXER_FUNCTION_SPEC = {
    "INT_LITERAL": t_INT_LITERAL,
    "BOOL_LITERAL": t_BOOL_LITERAL,
    "REAL_LITERAL": t_REAL_LITERAL,
    "STR_LITERAL": t_STR_LITERAL,
    "NULL_LITERAL": t_NULL_LITERAL,
    "COMMENT": t_COMMENT,
    "newline": t_newline,
    "error": t_error,
}


lexer = lex.lex(LEXER_TOKEN_SPEC_STR, LEXER_FUNCTION_SPEC, debug=DEBUG)
