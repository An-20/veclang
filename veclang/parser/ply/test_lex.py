import veclang.parser.ply.lex as lex

# is this a slightly unergonomic solution because i want to escape the tab? yes.
spec = """
PLUS: "\\+"
MINUS: "-"

LEFT_PARENTHESIS: "\\("
RIGHT_PARENTHESIS: "\\)"
SEMICOLON: ";"
"""
spec += '\nignore: "\t "\n'


def parse_integer_literal(t):
    r"[+-]?\d+"
    t.value = int(str(t.value))
    return t


def parse_float_literal(t):
    r"[+-]?\d+\.\d+"
    t.value = float(str(t.value))
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


lexer_function_spec = {
    "FLOAT_LITERAL": parse_float_literal,
    "INTEGER_LITERAL": parse_integer_literal,
    "newline": t_newline,
    "error": t_error,
}


def test_lex():
    lexer = lex.lex(spec, lexer_function_spec, debug=True)

    lexer.line_no = 0
    lexer_tokens = []
    # Give the lexer some input
    lexer.input("1 + 2")

    # Tokenize
    while True:
        tok = lexer.token()
        if not tok:
            break  # No more input
        lexer_tokens.append(tok)

    print(lexer_tokens)
