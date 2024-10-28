"""
This file is taken from ply (https://github.com/dabeaz/ply) and the copyright
notice has been reproduced in full below. The main modifications are:
- a move away from docstring-based parsing regexes to a single 'spec' file
that contains all the regexes

-----------------------------------------------------------------------------
ply: lex.py

Copyright (C) 2001-2022
David M. Beazley (Dabeaz LLC)
All rights reserved.

Latest version: https://github.com/dabeaz/ply

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

* Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.
* Neither the name of David Beazley or Dabeaz LLC may be used to
  endorse or promote products derived from this software without
  specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
-----------------------------------------------------------------------------
"""

import re
import string
import sys
import copy
import types
import typing
import inspect

# This tuple contains acceptable string types
StringTypes = (str,)

# This regular expression is used to match valid token names
_is_identifier = re.compile(r"^[a-zA-Z0-9_]+$")


lexer = None
lexer_input = None


LOG: bool = True


class LexError(Exception):
    """
    Exception thrown when invalid token encountered and no default error handler is defined.
    """

    def __init__(self, message, s):
        self.args = (message,)
        self.text = s


class LexToken:
    """
    Token class. This class is used to represent the tokens produced.
    """

    type: typing.Any
    value: typing.Any
    line_no: int
    lex_pos: int

    def __repr__(self):
        return f"LexToken({self.type},{self.value!r},{self.line_no},{self.lex_pos})"

    def to_dict(self):
        """
        Returns a dictionary representation of the token.
        """
        return {
            "type": self.type,
            "value": self.value,
            "line_no": self.line_no,
            "lex_pos": self.lex_pos,
        }


class PlyLogger:
    """
    This object is a stand-in for a logging object created by the logging module.
    """

    def __init__(self, f):
        self.f = f

    def critical(
        self,
        msg,
        *args,
    ):
        """Emits a critical warning if logging is enabled"""
        if LOG:
            self.f.write((msg % args) + "\n")

    def warning(self, msg, *args):
        """Emits a warning if logging is enabled"""
        if LOG:
            self.f.write("WARNING: " + (msg % args) + "\n")

    def error(self, msg, *args):
        """Emits an error if logging is enabled"""
        if LOG:
            self.f.write("ERROR: " + (msg % args) + "\n")

    def info(
        self,
        msg,
        *args,
    ):
        """Emits a logging info if logging is enabled"""
        if LOG:
            self.f.write("INFO: " + (msg % args) + "\n")

    def debug(self, msg, *args):
        """Emits a logging debug if logging is enabled"""
        if LOG:
            self.f.write("DEBUG: " + (msg % args) + "\n")


class Lexer:
    """
    Lexing Engine

    The following Lexer class implements the lexer runtime. There are only a few public methods and attributes:
    - input() - Store a new string in the lexer
    - token() - Get the next token
    - clone() - Clone the lexer
    - line_no - Current line number
    - lex_pos - Current position in the input string
    """

    def __init__(self):
        self.lex_match = None
        self.lex_re = None  # Master regular expression. This is a list of
        # tuples (re, findex) where re is a compiled
        # regular expression and findex is a list
        # mapping regex group numbers to rules
        self.lex_re_text = None  # Current regular expression strings
        self.lex_state_re = {}  # Dictionary mapping lexer states to master regexes
        self.lex_state_re_text = {}  # Dictionary mapping lexer states to regex strings
        self.lex_state_re_names = {}  # Dictionary mapping lexer states to symbol names
        self.lex_state = "INITIAL"  # Current lexer state
        self.lex_state_stack = []  # Stack of lexer states
        self.lex_state_info = None  # State information
        self.lex_state_ignore = {}  # Dictionary of ignored characters for each state
        self.lex_state_error_functions = (
            {}
        )  # Dictionary of error functions for each state
        self.lex_state_eof_functions = {}  # Dictionary of eof functions for each state
        self.lex_re_flags = 0  # Optional re compile flags
        self.lex_data = None  # Actual input data (as a string)
        self.lex_pos = 0  # Current position in input text
        self.lex_len = 0  # Length of the input text
        self.lex_error_f = None  # Error rule (if any)
        self.lex_eof_f = None  # EOF rule (if any)
        self.lex_tokens = None  # List of valid tokens
        self.lex_ignore = ""  # Ignored characters
        self.lex_literals = ""  # Literal characters that can be passed through
        self.lex_module = None  # Module
        self.line_no = 1  # Current line number

    def clone(self, input_object=None):
        """Clones the lexer"""
        c = copy.copy(self)

        # If the object parameter has been supplied, it means we are attaching the
        # lexer to a new object.  In this case, we have to rebind all methods in
        # the lex_state_re and lex_state_error_functions tables.
        cre = 0
        new_f_index = 0

        if input_object:
            new_tab = {}
            for key, r_item in self.lex_state_re.items():
                new_re = []
                for cre, f_index in r_item:
                    new_f_index = []
                    for f in f_index:
                        if not f or not f[0]:
                            new_f_index.append(f)
                            continue
                        new_f_index.append((getattr(input_object, f[0].__name__), f[1]))
                new_re.append((cre, new_f_index))
                new_tab[key] = new_re
            c.lex_state_re = new_tab
            c.lex_state_error_functions = {}
            for key, ef in self.lex_state_error_functions.items():
                c.lex_state_error_functions[key] = getattr(input_object, ef.__name__)
            c.lex_module = input_object
        return c

    def input(self, s):
        """Push a new string into the lexer"""
        self.lex_data = s
        self.lex_pos = 0
        self.lex_len = len(s)

    def begin(self, state):
        """Changes the lexing state"""
        if state not in self.lex_state_re:
            raise ValueError(f"Undefined state {state!r}")
        self.lex_re = self.lex_state_re[state]
        self.lex_re_text = self.lex_state_re_text[state]
        self.lex_ignore = self.lex_state_ignore.get(state, "")
        self.lex_error_f = self.lex_state_error_functions.get(state, None)
        self.lex_eof_f = self.lex_state_eof_functions.get(state, None)
        self.lex_state = state

    def push_state(self, state):
        """Changes the lexing state and saves old on stack"""
        self.lex_state_stack.append(self.lex_state)
        self.begin(state)

    def pop_state(self):
        """Restores the previous state"""
        self.begin(self.lex_state_stack.pop())

    def current_state(self):
        """Returns the current lexing state"""
        return self.lex_state

    def skip(self, n):
        """Skip ahead n characters"""
        self.lex_pos += n

    def token(self):
        """
        Return the next token from the Lexer

        Note: This function has been carefully implemented to be as fast as possible.
        Don't make changes unless you really know what you are doing
        """

        # Make local copies of frequently referenced attributes
        lex_pos = self.lex_pos
        lex_len = self.lex_len
        lex_ignore = self.lex_ignore
        lex_data = self.lex_data

        while lex_pos < lex_len:
            # This code provides some short-circuit code for whitespace, tabs, and other ignored characters
            if lex_data[lex_pos] in lex_ignore:
                lex_pos += 1
                continue

            # Look for a regular expression match
            for lex_re, lex_index_func in self.lex_re:
                m = lex_re.match(lex_data, lex_pos)
                if not m:
                    continue

                # Create a token for return
                tok = LexToken()
                tok.value = m.group()
                tok.line_no = self.line_no
                tok.lex_pos = lex_pos

                i = m.lastindex
                func, tok.type = lex_index_func[i]

                if not func:
                    # If no token type was set, it's an ignored token
                    if tok.type:
                        self.lex_pos = m.end()
                        return tok
                    else:
                        lex_pos = m.end()
                        break

                lex_pos = m.end()

                # If token is processed by a function, call it

                tok.lexer = self  # Set additional attributes useful in token rules
                self.lex_match = m
                self.lex_pos = lex_pos
                new_token = func(tok)
                del tok.lexer
                del self.lex_match

                # Every function must return a token, if nothing, we just move to next token
                if not new_token:
                    lex_pos = (
                        self.lex_pos
                    )  # This is here in case user has updated lex_pos.
                    lex_ignore = (
                        self.lex_ignore
                    )  # This is here in case there was a state change
                    break
                return new_token
            else:
                # No match, see if in literals
                if lex_data[lex_pos] in self.lex_literals:
                    tok = LexToken()
                    tok.value = lex_data[lex_pos]
                    tok.line_no = self.line_no
                    tok.type = tok.value
                    tok.lex_pos = lex_pos
                    self.lex_pos = lex_pos + 1
                    return tok

                # No match. Call t_error() if defined.
                if self.lex_error_f:
                    tok = LexToken()
                    tok.value = self.lex_data[lex_pos:]
                    tok.line_no = self.line_no
                    tok.type = "error"
                    tok.lexer = self
                    tok.lex_pos = lex_pos
                    self.lex_pos = lex_pos
                    new_token = self.lex_error_f(tok)
                    if lex_pos == self.lex_pos:
                        # Error method didn't change text position at all. This is an error.
                        raise LexError(
                            f"Scanning error. Illegal character {lex_data[lex_pos]!r}",
                            lex_data[lex_pos:],
                        )
                    lex_pos = self.lex_pos
                    if not new_token:
                        continue
                    return new_token

                self.lex_pos = lex_pos
                raise LexError(
                    f"Illegal character {lex_data[lex_pos]!r} at index {lex_pos}",
                    lex_data[lex_pos:],
                )

        if self.lex_eof_f:
            tok = LexToken()
            tok.type = "eof"
            tok.value = ""
            tok.line_no = self.line_no
            tok.lex_pos = lex_pos
            tok.lexer = self
            self.lex_pos = lex_pos
            new_token = self.lex_eof_f(tok)
            return new_token

        self.lex_pos = lex_pos + 1
        if self.lex_data is None:
            raise RuntimeError("No input string given with input()")
        return None

    # Iterator interface
    def __iter__(self):
        return self

    def __next__(self):
        t = self.token()
        if t is None:
            raise StopIteration
        return t


# -----------------------------------------------------------------------------
#                           ==== Lex Builder ===
#
# The functions and classes below are used to collect lexing information
# and build a Lexer object from it.
# -----------------------------------------------------------------------------


def _form_master_re(re_list, re_flags, token_spec, function_spec, token_names):
    """
    This function takes a list of all the regex components and attempts to
    form the master regular expression.  Given limitations in the Python re
    module, it may be necessary to break the master regex into separate expressions.
    """
    if not re_list:
        return [], [], []
    regex = "|".join(re_list)
    try:
        lex_re = re.compile(regex, re_flags)

        # Build the index to function map for the matching engine
        lex_index_func: typing.List = [None] * (max(lex_re.groupindex.values()) + 1)
        lex_index_names = lex_index_func[:]

        for f, i in lex_re.groupindex.items():
            reg = token_spec.get(f, None)
            if f in function_spec:
                # lex_index_func[i] = (handle, token_names[f])
                lex_index_func[i] = (function_spec[f], f)
                lex_index_names[i] = f

            elif reg is not None:
                lex_index_names[i] = f
                if f.find("ignore_") > 0:
                    lex_index_func[i] = (None, None)
                else:
                    # lex_index_func[i] = (None, token_names[f])
                    lex_index_func[i] = (None, f)

        return [(lex_re, lex_index_func)], [regex], [lex_index_names]

    except Exception:
        m = (len(re_list) // 2) + 1
        l_list, l_re, l_names = _form_master_re(
            re_list[:m], re_flags, token_spec, function_spec, token_names
        )
        r_list, r_re, r_names = _form_master_re(
            re_list[m:], re_flags, token_spec, function_spec, token_names
        )
        return (l_list + r_list), (l_re + r_re), (l_names + r_names)


def __state_token(s, names):
    """
    Given a declaration name s of the form "t_" and a dictionary whose keys are
    state names, this function returns a tuple (states, token_name) where states
    is a tuple of state names and token_name is the name of the token.  For example,
    calling this with s = "t_foo_bar_SPAM" might return (('foo','bar'),'SPAM')
    """
    parts = s.split("_")
    i = 0
    for i, part in enumerate(parts[1:], 1):
        if part not in names and part != "ANY":
            break

    if i > 1:
        states = tuple(parts[1:i])
    else:
        states = ("INITIAL",)

    if "ANY" in states:
        states = tuple(names)

    token_name = "_".join(parts[i:])
    return states, token_name


class LexerReflect:
    """
    This class represents information needed to build a lexer as extracted from
    a user's input file.
    """

    def __init__(
        self,
        token_spec: dict[str, str],
        function_spec: dict[str, typing.Callable],
        log=None,
        re_flags=0,
    ):
        self.token_spec = token_spec
        self.function_spec = function_spec
        self.error_func = None
        self.tokens = list(token_spec.keys())
        self.re_flags = re_flags
        self.state_info = {"INITIAL": "inclusive"}
        self.modules = set()
        self.error = False
        self.log = PlyLogger(sys.stderr) if log is None else log

        # placeholder values
        self.func_sym = {}  # Symbols defined as functions
        self.str_sym = {}  # Symbols defined as strings
        self.ignore = {}  # Ignore strings by state
        self.error_functions = {}  # Error functions by state
        self.eof_functions = {}  # EOF functions by state
        self.states: typing.Iterable = []

    def get_all(self):
        """Get all the basic information"""
        self.get_rules()

    def validate_all(self):
        """Validate all the information"""
        self.validate_tokens()
        self.validate_rules()
        return self.error

    def validate_tokens(self):
        """Validate the tokens"""
        terminals = {}
        for n in self.tokens:
            if not _is_identifier.match(n):
                self.log.error(f"Bad token name {n!r}")
                self.error = True
            if n in terminals:
                self.log.warning(f"Token {n!r} multiply defined")
            terminals[n] = 1

    def get_rules(self):
        """
        Get all the symbols with a t_ prefix and sort them into various
        categories (functions, strings, error functions, and ignore characters)
        """
        # Now build up a list of functions and a list of strings
        self.func_sym = {}  # Symbols defined as functions
        self.str_sym = {}  # Symbols defined as strings
        self.ignore = {}  # Ignore strings by state
        self.error_functions = {}  # Error functions by state
        self.eof_functions = {}  # EOF functions by state

        for s in self.state_info:
            self.func_sym[s] = []
            self.str_sym[s] = []

        for token in self.token_spec:
            states = ["INITIAL"]
            if token in self.function_spec:
                fn: typing.Callable = self.function_spec[token]
                if token == "error":
                    for s in states:
                        self.error_functions[s] = self.function_spec[token]
                elif token == "eof":
                    for s in states:
                        self.eof_functions[s] = self.function_spec[token]
                elif token == "ignore":
                    self.log.error(f"Rule {token} must be defined as a string")
                    self.error = True
                else:
                    for s in states:
                        self.func_sym[s].append((token, fn))

            else:
                if token == "ignore":
                    for s in states:
                        self.ignore[s] = self.token_spec[token]
                    if "\\" in token:
                        self.log.warning(f"{token} contains a literal backslash '\\'")

                elif token == "error":
                    self.log.error(f"Rule {token} must be defined as a function")
                    self.error = True
                else:
                    for s in states:
                        self.str_sym[s].append((token, self.token_spec[token]))

        # Sort the functions by line number
        for f in self.func_sym.values():
            f.sort(key=lambda x: x[1].__code__.co_firstlineno)

        # Sort the strings by regular expression length
        for s in self.str_sym.values():
            s.sort(key=lambda x: len(x[1]), reverse=True)

    def validate_rules(self):
        """Validate all the rules collected"""
        for state in self.state_info:
            # Validate all rules defined by functions

            for token, func in self.func_sym[state]:
                if token == "ignore":
                    continue

                line = func.__code__.co_firstlineno
                file = func.__code__.co_filename
                module = inspect.getmodule(func)
                self.modules.add(module)

                if isinstance(func, types.MethodType):
                    req_args = 2
                else:
                    req_args = 1
                nargs = func.__code__.co_argcount
                if nargs > req_args:
                    self.log.error(
                        f"{file}:{line}: Rule {func.__name__} has too many arguments"
                    )
                    self.error = True
                    continue

                if nargs < req_args:
                    self.log.error(
                        f"{file}:{line}: Rule {func.__name__} requires an argument"
                    )
                    self.error = True
                    continue

                if token not in self.token_spec:
                    self.log.error(
                        f"{file}:{line}: No regular expression for rule {func.__name__}"
                    )
                    self.error = True
                    continue

                try:
                    c = re.compile(
                        "(?P<%s>%s)" % (token, self.token_spec[token]), self.re_flags
                    )
                    if c.match(""):
                        self.log.error(
                            f"{file}:{line}: Regular expression for rule {func.__name__}"
                            f" matches empty string"
                        )
                        self.error = True

                except re.error as e:
                    self.log.error(
                        f"{file}:{line}: Invalid regular expression for rule {func.__name__}"
                        f": {e}"
                    )
                    if "#" in self.token_spec[token]:
                        self.log.error(
                            f"{file}:{line}: Make sure '#' in rule %{func.__name__} is escaped with '\\#'"
                            f": {e}"
                        )
                    self.error = True

            # Validate all rules defined by strings
            for token, regex in self.str_sym[state]:
                if token == "error":
                    self.log.error("Rule %r must be defined as a function", token)
                    self.error = True
                    continue

                if token not in self.tokens and token.find("ignore_") < 0:
                    self.log.error(
                        "Rule %r defined for an unspecified token %s", token, token
                    )
                    self.error = True
                    continue

                try:
                    c = re.compile("(?P<%s>%s)" % (token, regex), self.re_flags)
                    if c.match(""):
                        self.log.error(
                            "Regular expression for rule %r matches empty string", token
                        )
                        self.error = True
                except re.error as e:
                    self.log.error(
                        "Invalid regular expression for rule %r. %s", token, e
                    )
                    if "#" in regex:
                        self.log.error(
                            "Make sure '#' in rule %r is escaped with '\\#'", token
                        )
                    self.error = True

            if not self.func_sym[state] and not self.str_sym[state]:
                self.log.error("No rules defined for state %r", state)
                self.error = True

            # Validate the error function
            efunc = self.error_functions.get(state, None)
            if efunc:
                func = efunc
                line = getattr(func, "__code__").co_firstlineno
                file = getattr(func, "__code__").co_filename
                module = inspect.getmodule(func)
                self.modules.add(module)

                if isinstance(func, types.MethodType):
                    req_args = 2
                else:
                    req_args = 1

                nargs = getattr(func, "__code__").co_argcount
                if nargs > req_args:
                    self.log.error(
                        f"{file}:{line}: Rule {func.__name__} has too many arguments"
                    )
                    self.error = True

                if nargs < req_args:
                    self.log.error(
                        f"{file}:{line}: Rule {func.__name__} requires an argument"
                    )
                    self.error = True

        for module in self.modules:
            self.validate_module(module)

    def validate_module(self, module):
        """
        This checks to see if there are duplicated t_rule_name() functions or strings
        in the parser input file.  This is done using a simple regular expression
        match on each line in the source code of the given module.
        """
        try:
            lines, linen = inspect.getsourcelines(module)
        except IOError:
            return

        fre = re.compile(r"\s*def\s+(t_[a-zA-Z_0-9]*)\(")
        sre = re.compile(r"\s*(t_[a-zA-Z_0-9]*)\s*=")

        count_hash = {}
        linen += 1
        for line in lines:
            m = fre.match(line)
            if not m:
                m = sre.match(line)
            if m:
                name = m.group(1)
                prev = count_hash.get(name)
                if not prev:
                    count_hash[name] = linen
                else:
                    filename = inspect.getsourcefile(module)
                    self.log.error(
                        f"{filename}: {linen}: Rule {name} redefined. Previously defined on line {prev}"
                    )
                    self.error = True
            linen += 1


def parse_spec(spec_str: str) -> dict[str, str]:
    """
    Parses a multiline token specification and returns a dictionary of identifiers and
    their respective regexes.

    :param spec_str: The specification string
    :return: Returns a dictionary of {identifier: regex}
    """
    identifier_chars = string.ascii_letters + string.digits + "_"

    lines = spec_str.split("\n")
    spec = {}
    for line_idx, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        if line.startswith("//"):
            continue

        # parse identifier and regex
        if line.count(":") < 1:
            raise Exception(f"Error on line {line_idx}: No colon delimiter")
        identifier = line.split(":", maxsplit=1)[0].strip()
        regex = line.split(":", maxsplit=1)[1].strip()

        # check identifier
        if not identifier or not all([char in identifier_chars for char in identifier]):
            raise Exception(
                f"Error on line {line_idx}: "
                f"Characters not in [a-z, A-Z 0-9, _] for identifier '{identifier}'"
            )

        # check regex
        if not regex or regex[0] != '"' or regex[-1] != '"':
            raise Exception(
                f"Error on line {line_idx}: "
                f"Regex string does not start and end with '\"' for regex '{regex}'"
            )
        if len(regex) <= 2:
            raise Exception(f"Error on line {line_idx}: Empty regex string '{regex}'")

        spec[identifier] = regex[1:-1]

    return spec


def get_tokens(spec_str: str, function_spec: dict[str, typing.Callable]) -> list[str]:
    """
    Parses a multiline token specification and returns a list of token names

    :param spec_str: The specification string
    :param function_spec: The function specification
    :return: Returns a list of token names (strings)
    """
    identifier_chars = string.ascii_letters + string.digits + "_"

    lines = spec_str.split("\n")
    tokens = []
    for line_idx, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        if line[:2] == "//":
            continue

        # parse identifier and regex
        if line.count(":") < 1:
            raise Exception(f"Error on line {line_idx}: No colon delimiter")
        identifier = line.split(":", maxsplit=1)[0].strip()
        if identifier == "ignore":
            continue

        # check identifier
        if not all([char in identifier_chars for char in identifier]):
            raise Exception(
                f"Error on line {line_idx}: "
                f"Characters not in [a-z, A-Z 0-9, _] for identifier '{identifier}'"
            )

        if identifier == "error":
            continue

        tokens.append(identifier)

    for identifier in function_spec.keys():
        # check identifier
        if not all([char in identifier_chars for char in identifier]):
            raise Exception(
                f"Characters not in [a-z, A-Z 0-9, _] for identifier '{identifier}'"
            )

        if identifier == "error":
            continue

        tokens.append(identifier)

    return tokens


def lex(
    token_spec: str,
    function_spec: dict[str, typing.Callable],
    debug=False,
    re_flags=int(re.VERBOSE),
    debug_log=None,
    error_log=None,
) -> Lexer:
    """
    Build all the regular expression rules from definitions in the supplied module
    """
    global lexer, token, lexer_input

    lexer_obj = Lexer()

    if error_log is None:
        error_log = PlyLogger(sys.stderr)

    if debug:
        if debug_log is None:
            debug_log = PlyLogger(sys.stderr)

    # fix spex
    for token, fn in function_spec.items():
        token_spec += f'\n{token}: "{fn.__doc__}"'
    token_spec += "\n"
    spec = parse_spec(token_spec)

    # Collect parser information from the dictionary
    l_info = LexerReflect(spec, function_spec, log=error_log, re_flags=re_flags)
    l_info.get_all()
    if l_info.validate_all():
        raise SyntaxError("Can't build lexer")

    # Dump some basic debugging information
    if debug:
        debug_log.info("lex: tokens   = %r", l_info.tokens)
        debug_log.info("lex: states   = %r", l_info.state_info)

    # Build a dictionary of valid token names
    lexer_obj.lex_tokens = set()
    for n in l_info.tokens:
        lexer_obj.lex_tokens.add(n)

    lexer_obj.lex_tokens_all = lexer_obj.lex_tokens

    # Get the state_info dictionary
    stateinfo = l_info.state_info

    regexes = {}
    # Build the master regular expressions
    for state in stateinfo:
        regex_list = []

        # Add rules defined by functions first
        for token, f in l_info.func_sym[state]:
            regex_list.append("(?P<%s>%s)" % (token, l_info.token_spec[token]))
            if debug:
                debug_log.info(
                    "lex: Adding rule %s -> '%s' (state '%s')",
                    token,
                    l_info.token_spec[token],
                    state,
                )

        # Now add all of the simple rules
        for name, r in l_info.str_sym[state]:
            regex_list.append("(?P<%s>%s)" % (name, r))
            if debug:
                debug_log.info(
                    "lex: Adding rule %s -> '%s' (state '%s')", name, r, state
                )

        regexes[state] = regex_list

    # Build the master regular expressions

    if debug:
        debug_log.info("lex: ==== MASTER REGEXES FOLLOW ====")

    for state in regexes:
        lex_re, re_text, re_names = _form_master_re(
            regexes[state],
            re_flags,
            l_info.token_spec,
            l_info.function_spec,
            l_info.tokens,
        )
        lexer_obj.lex_state_re[state] = lex_re
        lexer_obj.lex_state_re_text[state] = re_text
        lexer_obj.lex_state_re_names[state] = re_names
        if debug:
            for i, text in enumerate(re_text):
                debug_log.info("lex: state '%s' : regex[%d] = '%s'", state, i, text)

    # For inclusive states, we need to add the regular expressions from the INITIAL state
    for state, stype in stateinfo.items():
        if state != "INITIAL" and stype == "inclusive":
            lexer_obj.lex_state_re[state].extend(lexer_obj.lex_state_re["INITIAL"])
            lexer_obj.lex_state_re_text[state].extend(
                lexer_obj.lex_state_re_text["INITIAL"]
            )
            lexer_obj.lex_state_re_names[state].extend(
                lexer_obj.lex_state_re_names["INITIAL"]
            )

    lexer_obj.lex_state_info = stateinfo
    lexer_obj.lex_re = lexer_obj.lex_state_re["INITIAL"]
    lexer_obj.lex_re_text = lexer_obj.lex_state_re_text["INITIAL"]
    lexer_obj.lex_re_flags = re_flags

    # Set up ignore variables
    lexer_obj.lex_state_ignore = l_info.ignore
    lexer_obj.lex_ignore = lexer_obj.lex_state_ignore.get("INITIAL", "")

    # Set up error functions
    lexer_obj.lex_state_error_functions = l_info.error_functions
    lexer_obj.lex_error_f = l_info.error_functions.get("INITIAL", None)
    if not lexer_obj.lex_error_f:
        error_log.warning("No t_error rule is defined")

    # Set up eof functions
    lexer_obj.lex_state_eof_functions = l_info.eof_functions
    lexer_obj.lex_eof_f = l_info.eof_functions.get("INITIAL", None)

    # Check state information for ignore and error rules
    for s, stype in stateinfo.items():
        if stype == "exclusive":
            if s not in l_info.error_functions:
                error_log.warning("No error rule is defined for exclusive state %r", s)
            if s not in l_info.ignore and lexer_obj.lex_ignore:
                error_log.warning("No ignore rule is defined for exclusive state %r", s)
        elif stype == "inclusive":
            if s not in l_info.error_functions:
                l_info.error_functions[s] = l_info.error_functions.get("INITIAL", None)
            if s not in l_info.ignore:
                l_info.ignore[s] = l_info.ignore.get("INITIAL", "")

    # Create global versions of the token() and input() functions
    token = lexer_obj.token
    lexer_input = lexer_obj.input
    lexer = lexer_obj

    return lexer_obj
