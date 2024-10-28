"""
This file is taken from ply (https://github.com/dabeaz/ply) and the copyright
notice has been reproduced in full below. The main modifications are:
- a move away from docstring-based parsing rules to a single 'spec' file
that contains all the grammar rules

-----------------------------------------------------------------------------
ply: yacc.py

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

This implements an LR parser that is constructed from grammar rules defined
as Python functions. The grammar is specified by supplying the BNF inside
Python documentation strings.  The inspiration for this technique was borrowed
from John Aycock's Spark parsing system.  PLY might be viewed as cross between
Spark and the GNU bison utility.

The current implementation is only somewhat object-oriented. The
LR parser itself is defined in terms of an object (which allows multiple
parsers to co-exist).  However, most of the variables used during table
construction are defined in terms of global variables.  Users shouldn't
notice unless they are trying to define multiple parsers at the same
time using threads (in which case they should have their head examined).

This implementation supports both SLR and LALR(1) parsing.  LALR(1)
support was originally implemented by Elias Ioup (ezioup@alumni.uchicago.edu),
using the algorithm found in Aho, Sethi, and Ullman "Compilers: Principles,
Techniques, and Tools" (The Dragon Book).  LALR(1) has since been replaced
by the more efficient DeRemer and Pennello algorithm.

:::::::: WARNING :::::::

Construction of LR parsing tables is fairly complicated and expensive.
To make this module run fast, a *LOT* of work has been put into
optimization---often at the expensive of readability and what might
consider to be good Python "coding style."   Modify the code at your
own risk!
----------------------------------------------------------------------------
"""

import re
import types
import sys
import inspect
import string
import typing

from typing import Optional

from veclang.parser.ply.lex import PlyLogger

# -----------------------------------------------------------------------------
#                     === User configurable parameters ===
#
# Change these to modify the default behavior of yacc (if you wish)
# -----------------------------------------------------------------------------

yacc_debug = False
# Debugging mode.  If set, yacc generates a
# a 'parser.out' file in the current directory

debug_file = "parser.out"  # Default name of the debugging file
error_count = 3  # Number of symbols that must be shifted to leave recovery mode
result_limit = 40  # Size limit of results when running in debug mode.

MAXINT = sys.maxsize


# This object is a stand-in for a logging object created by the
# logging module.   PLY will use this by default to create things
# such as the parser.out file.  If a user wants more detailed
# information, they can create their own logging object and pass
# it into PLY.


# Null logger is used when no output is generated. Does nothing.
class NullLogger:
    def __getattribute__(self, name):
        return self

    def __call__(self, *args, **kwargs):
        return self


# Exception raised for yacc-related errors
class YaccError(Exception):
    pass


# Format the result message that the parser produces when running in debug mode.
def format_result(r):
    repr_str = repr(r)
    if "\n" in repr_str:
        repr_str = repr(repr_str)
    if len(repr_str) > result_limit:
        repr_str = repr_str[:result_limit] + " ..."
    result = "<%s @ 0x%x> (%s)" % (type(r).__name__, id(r), repr_str)
    return result


# Format stack entries when the parser is running in debug mode
def format_stack_entry(r):
    repr_str = repr(r)
    if "\n" in repr_str:
        repr_str = repr(repr_str)
    if len(repr_str) < 16:
        return repr_str
    else:
        return "<%s @ 0x%x>" % (type(r).__name__, id(r))


# -----------------------------------------------------------------------------
#                        ===  LR Parsing Engine ===
#
# The following classes are used for the LR parser itself.  These are not
# used during table construction and are independent of the actual LR
# table generation algorithm
# -----------------------------------------------------------------------------


class YaccSymbol:
    """
    This class is used to hold non-terminal grammar symbols during parsing.
    It normally has the following attributes set:
        .type       = Grammar symbol type
        .value      = Symbol value
        .line_no     = Starting line number
        .end_line_no  = Ending line number (optional, set automatically)
        .lex_pos     = Starting lex position
        .end_lex_pos  = Ending lex position (optional, set automatically)
    """

    type: typing.Any
    value: typing.Any
    line_no: typing.Any
    end_line_no: typing.Any
    lex_pos: typing.Any
    end_lex_pos: typing.Any

    def __str__(self):
        return self.type

    def __repr__(self):
        return str(self)


class YaccProduction:
    """
    This class is a wrapper around the objects actually passed to each grammar rule.
    Index lookup and assignment actually assign the .value attribute of the underlying YaccSymbol object.
    The line_no() method returns the line number of a given item (or 0 if not defined).
    The line_span() method returns a tuple of (startline,endline)
    representing the range of lines for a symbol.
    The lex_span() method returns a tuple (lex_pos,end_lex_pos) representing the range
    of positional information for a symbol.
    """

    def __init__(self, s, stack=None):
        self.slice = s
        self.stack = stack
        self.lexer = None
        self.parser = None

    def __getitem__(self, n):
        if isinstance(n, slice):
            return [s.value for s in self.slice[n]]
        elif n >= 0:
            return self.slice[n].value
        else:
            return self.stack[n].value

    def __setitem__(self, n, v):
        self.slice[n].value = v

    def __getslice__(self, i, j):
        return [s.value for s in self.slice[i:j]]

    def __len__(self):
        return len(self.slice)

    def line_no(self, n):
        return getattr(self.slice[n], "line_no", 0)

    def set_line_no(self, n, line_no):
        self.slice[n].line_no = line_no

    def line_span(self, n):
        start_line = getattr(self.slice[n], "line_no", 0)
        end_line = getattr(self.slice[n], "end_line_no", start_line)
        return start_line, end_line

    def lex_pos(self, n):
        return getattr(self.slice[n], "lex_pos", 0)

    def set_lex_pos(self, n, lex_pos):
        self.slice[n].lex_pos = lex_pos

    def lex_span(self, n):
        start_pos = getattr(self.slice[n], "lex_pos", 0)
        end_pos = getattr(self.slice[n], "end_lex_pos", start_pos)
        return start_pos, end_pos

    def error(self):
        raise SyntaxError


class LRParserEngine:
    """
    The LR Parsing engine.
    """

    def __init__(self, lr_table, error_function) -> None:
        self.productions = lr_table.lr_productions
        self.action = lr_table.lr_action
        self.goto = lr_table.lr_goto
        self.error_function = error_function
        self.defaulted_states = {}
        self.token = None
        self.state = None

        self.sym_stack = []
        self.state_stack = []

        self.set_defaulted_states()
        self.error_ok = True

    def error_ok(self):
        self.error_ok = True

    def restart(self):
        del self.state_stack[:]
        del self.sym_stack[:]
        sym = YaccSymbol()
        sym.type = "$end"
        self.sym_stack.append(sym)
        self.state_stack.append(0)

    # Defaulted state support.
    # This method identifies parser states where there is only one possible reduction action.
    # For such states, the parser can make a choose to make a rule reduction without consuming
    # the next look-ahead token.  This delayed invocation of the tokenizer can be useful in
    # certain kinds of advanced parsing situations where the lexer and parser interact with
    # each other or change states (i.e., manipulation of scope, lexer states, etc.).
    #
    # See:  http://www.gnu.org/software/bison/manual/html_node/Default-Reductions.html#Default-Reductions
    def set_defaulted_states(self):
        self.defaulted_states = {}
        for state, actions in self.action.items():
            rules = list(actions.values())
            if len(rules) == 1 and rules[0] < 0:
                self.defaulted_states[state] = rules[0]

    def disable_defaulted_states(self):
        self.defaulted_states = {}

    # parse().
    #
    # This is the core parsing engine.  To operate, it requires a lexer object.
    # Two options are provided.  The debug flag turns on debugging so that you can
    # see the various rule reductions and parsing steps.  tracking turns on position
    # tracking.  In this mode, symbols will record the starting/ending line number and
    # character index.

    def parse(self, parse_input=None, lexer=None, debug=False, tracking=False):
        # If debugging has been specified as a flag, turn it into a logging object
        if isinstance(debug, int) and debug:
            debug = PlyLogger(sys.stderr)

        lookahead = None  # Current lookahead symbol
        lookahead_stack = []  # Stack of lookahead symbols
        actions = (
            self.action
        )  # Local reference to action table (to avoid lookup on self.)
        goto = self.goto  # Local reference to goto table (to avoid lookup on self.)
        prod = (
            self.productions
        )  # Local reference to production list (to avoid lookup on self.)
        defaulted_states = self.defaulted_states  # Local reference to defaulted states
        p_slice = YaccProduction(None)  # Production object passed to grammar rules
        parse_error_count = 0  # Used during error recovery

        if debug:
            debug.info("PLY: PARSE DEBUG START")

        # If no lexer was given, we will try to use the lex module
        if not lexer:
            from . import lex

            lexer = lex.lexer

        # Set up the lexer and parser objects on p_slice
        p_slice.lexer = lexer
        p_slice.parser = self

        # If input was supplied, pass to lexer
        if parse_input is not None:
            lexer.input(parse_input)

        # Set the token function
        get_token = self.token = lexer.token

        # Set up the state and symbol stacks
        state_stack = self.state_stack = []  # Stack of parsing states
        sym_stack = self.sym_stack = []  # Stack of grammar symbols
        p_slice.stack = sym_stack  # Put in the production

        # The start state is assumed to be (0,$end)

        state_stack.append(0)
        sym = YaccSymbol()
        sym.type = "$end"
        sym_stack.append(sym)
        state = 0
        while True:
            # Get the next symbol on the input.  If a lookahead symbol
            # is already set, we just use that. Otherwise, we'll pull
            # the next token off of the lookahead_stack or from the lexer

            if debug:
                debug.debug("State  : %s", state)

            if state not in defaulted_states:
                if not lookahead:
                    if not lookahead_stack:
                        lookahead = get_token()  # Get the next token
                    else:
                        lookahead = lookahead_stack.pop()
                    if not lookahead:
                        lookahead = YaccSymbol()
                        lookahead.type = "$end"

                # Check the action table
                l_type = lookahead.type
                t = actions[state].get(l_type)
            else:
                t = defaulted_states[state]
                if debug:
                    debug.debug("Defaulted state %s: Reduce using %d", state, -t)

            if debug:
                debug.debug(
                    "Stack  : %s",
                    (
                        "%s . %s"
                        % (" ".join([xx.type for xx in sym_stack][1:]), str(lookahead))
                    ).lstrip(),
                )

            if t is not None:
                if t > 0:
                    # shift a symbol on the stack
                    state_stack.append(t)
                    state = t

                    if debug:
                        debug.debug("Action : Shift and goto state %s", t)

                    sym_stack.append(lookahead)
                    lookahead = None

                    # Decrease error count on successful shift
                    if parse_error_count:
                        parse_error_count -= 1
                    continue

                if t < 0:
                    # reduce a symbol on the stack, emit a production
                    p = prod[-t]
                    pname = p.name
                    p_len = p.len

                    # Get production function
                    sym = YaccSymbol()
                    sym.type = pname  # Production name
                    sym.value = None

                    if debug:
                        if p_len:
                            debug.info(
                                "Action : Reduce rule [%s] with %s and goto state %d', p.str",
                                "["
                                + ",".join(
                                    [
                                        format_stack_entry(_v.value)
                                        for _v in sym_stack[-p_len:]
                                    ]
                                )
                                + "]",
                                goto[state_stack[-1 - p_len]][pname],
                            )
                        else:
                            debug.info(
                                "Action : Reduce rule [%s] with %s and goto state %d",
                                p.str,
                                [],
                                goto[state_stack[-1]][pname],
                            )

                    if p_len:
                        targ = sym_stack[-p_len - 1 :]
                        targ[0] = sym

                        if tracking:
                            t1 = targ[1]
                            sym.line_no = t1.line_no
                            sym.lex_pos = t1.lex_pos
                            t1 = targ[-1]
                            sym.end_line_no = getattr(t1, "end_line_no", t1.line_no)
                            sym.end_lex_pos = getattr(t1, "end_lex_pos", t1.lex_pos)

                        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                        # The code enclosed in this section is duplicated
                        # below as a performance optimization.  Make sure
                        # changes get made in both locations.

                        p_slice.slice = targ

                        try:
                            # Call the grammar rule with our special slice object
                            del sym_stack[-p_len:]
                            self.state = state
                            p.callable(p_slice)
                            del state_stack[-p_len:]
                            if debug:
                                debug.info("Result : %s", format_result(p_slice[0]))
                            sym_stack.append(sym)
                            state = goto[state_stack[-1]][pname]
                            state_stack.append(state)
                        except SyntaxError:
                            # If an error was set. Enter error recovery state
                            lookahead_stack.append(
                                lookahead
                            )  # Save the current lookahead token
                            sym_stack.extend(
                                targ[1:-1]
                            )  # Put the production slice back on the stack
                            state_stack.pop()  # Pop back one state (before the reduce)
                            state = state_stack[-1]
                            sym.type = "error"
                            sym.value = "error"
                            lookahead = sym
                            parse_error_count = parse_error_count
                            self.error_ok = False

                        continue

                    else:
                        if tracking:
                            sym.line_no = lexer.line_no
                            sym.lex_pos = lexer.lex_pos

                        targ = [sym]

                        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                        # The code enclosed in this section is duplicated
                        # above as a performance optimization.  Make sure
                        # changes get made in both locations.

                        p_slice.slice = targ

                        try:
                            # Call the grammar rule with our special slice object
                            self.state = state
                            p.callable(p_slice)
                            if debug:
                                debug.info("Result : %s", format_result(p_slice[0]))
                            sym_stack.append(sym)
                            state = goto[state_stack[-1]][pname]
                            state_stack.append(state)
                        except SyntaxError:
                            # If an error was set. Enter error recovery state
                            lookahead_stack.append(
                                lookahead
                            )  # Save the current lookahead token
                            state_stack.pop()  # Pop back one state (before the reduce)
                            state = state_stack[-1]
                            sym.type = "error"
                            sym.value = "error"
                            lookahead = sym
                            parse_error_count = parse_error_count
                            self.error_ok = False

                        continue

                if t == 0:
                    n = sym_stack[-1]
                    result = getattr(n, "value", None)

                    if debug:
                        debug.info("Done   : Returning %s", format_result(result))
                        debug.info("PLY: PARSE DEBUG END")

                    return result

            if t is None:
                if debug:
                    debug.error(
                        "Error  : %s",
                        (
                            "%s . %s"
                            % (
                                " ".join([xx.type for xx in sym_stack][1:]),
                                str(lookahead),
                            )
                        ).lstrip(),
                    )

                # We have some kind of parsing error here.  To handle
                # this, we are going to push the current token onto
                # the token stack and replace it with an 'error' token.
                # If there are any synchronization rules, they may
                # catch it.
                #
                # In addition to pushing the error token, we call call
                # the user defined p_error() function if this is the
                # first syntax error.  This function is only called if
                # error_count == 0.
                if parse_error_count == 0 or self.error_ok:
                    parse_error_count = parse_error_count
                    self.error_ok = False
                    error_token = lookahead
                    if error_token.type == "$end":
                        error_token = None  # End of file!
                    if self.error_function:
                        if error_token and not hasattr(error_token, "lexer"):
                            error_token.lexer = lexer
                        self.state = state
                        tok = self.error_function(error_token)
                        if self.error_ok:
                            # User must have done some kind of panic
                            # mode recovery on their own.  The
                            # returned token is the next lookahead
                            lookahead = tok
                            continue
                    else:
                        if error_token:
                            if hasattr(error_token, "line_no"):
                                line_no = lookahead.line_no
                            else:
                                line_no = 0
                            if line_no:
                                sys.stderr.write(
                                    "yacc: Syntax error at line %d, token=%s\n"
                                    % (line_no, error_token.type)
                                )
                            else:
                                sys.stderr.write(
                                    "yacc: Syntax error, token=%s" % error_token.type
                                )
                        else:
                            sys.stderr.write("yacc: Parse error in input. EOF\n")
                            return

                else:
                    parse_error_count = parse_error_count

                # case 1:  the state stack only has 1 entry on it.  If we're in this state, the
                # entire parse has been rolled back, and we're completely hosed.   The token is
                # discarded and we just keep going.

                if len(state_stack) <= 1 and lookahead.type != "$end":
                    lookahead = None
                    state = 0
                    # Nuke the pushback stack
                    del lookahead_stack[:]
                    continue

                # case 2: the state stack has a couple of entries on it, but we're
                # at the end of the file. nuke the top entry and generate an error token

                # Start nuking entries on the stack
                if lookahead.type == "$end":
                    # Whoa. We're really hosed here. Bail out

                    return

                if lookahead.type != "error":
                    sym = sym_stack[-1]
                    if sym.type == "error":
                        # Error is on top of stack, we'll just nuke input
                        # symbol and continue
                        if tracking:
                            sym.end_line_no = getattr(lookahead, "line_no", sym.line_no)
                            sym.end_lex_pos = getattr(lookahead, "lex_pos", sym.lex_pos)
                        lookahead = None
                        continue

                    # Create the error symbol for the first time and make it the new lookahead symbol
                    t = YaccSymbol()
                    t.type = "error"

                    if hasattr(lookahead, "line_no"):
                        t.line_no = t.end_line_no = lookahead.line_no
                    if hasattr(lookahead, "lex_pos"):
                        t.lex_pos = t.end_lex_pos = lookahead.lex_pos
                    t.value = lookahead
                    lookahead_stack.append(lookahead)
                    lookahead = t
                else:
                    sym = sym_stack.pop()
                    if tracking:
                        lookahead.line_no = sym.line_no
                        lookahead.lex_pos = sym.lex_pos
                    state_stack.pop()
                    state = state_stack[-1]

                continue

            # If we're here, something exceptionally bad happened
            raise RuntimeError("yacc: internal parser error!!!\n")


# -----------------------------------------------------------------------------
#                          === Grammar Representation ===
#
# The following functions, classes, and variables are used to represent and
# manipulate the rules that make up a grammar.
# -----------------------------------------------------------------------------

# regex matching identifiers
_is_identifier = re.compile(r"^[a-zA-Z0-9_-]+$")


# -----------------------------------------------------------------------------
# class Production:
#
# This class stores the raw information about a single production or grammar rule.
# A grammar rule refers to a specification such as this:
#
#       expr : expr PLUS term
#
# Here are the basic attributes defined on all productions
#
#       name     - Name of the production.  For example 'expr'
#       prod     - A list of symbols on the right side ['expr','PLUS','term']
#       precedence_level     - Production precedence level
#       number   - Production number.
#       func     - Function that executes on reduce
#       file     - File where production function is defined
#       line_no   - Line number where production function is defined
#
# The following attributes are defined or optional.
#
#       len       - Length of the production (number of symbols on right hand side)
#       unique_symbols     - Set of unique symbols found in the production
# -----------------------------------------------------------------------------


class Production:
    """
    class Production:

    This class stores the raw information about a single production or grammar rule.
    A grammar rule refers to a specification such as this:
        expr : expr PLUS term

    Here are the basic attributes defined on all productions
        name     - Name of the production.  For example 'expr'
        prod     - A list of symbols on the right side ['expr','PLUS','term']
        precedence_level     - Production precedence level
        number   - Production number.
        func     - Function that executes on reduce
        file     - File where production function is defined
        line_no   - Line number where production function is defined

    The following attributes are defined or optional.
        len       - Length of the production (number of symbols on right hand side)
        unique_symbols     - Set of unique symbols found in the production
    """

    reduced = 0

    def __init__(
        self, number, name, prod, precedence=("right", 0), func=None, file="", line=0
    ):
        self.name = name
        self.prod = tuple(prod)
        self.number = number
        self.func = func
        self.callable = None
        self.file = file
        self.line = line
        self.precedence_level = precedence

        # Internal settings used during table construction

        self.len = len(self.prod)  # Length of the production

        # Create a list of unique production symbols used in the production
        self.unique_symbols = []
        for s in self.prod:
            if s not in self.unique_symbols:
                self.unique_symbols.append(s)

        # List of all LR items for the production
        self.lr_items = []
        self.lr_next = None

        # Create a string representation
        if self.prod:
            self.str = f"{self.name} -> {' '.join(self.prod)}"
        else:
            self.str = f"{self.name} -> <empty>"

    def __str__(self):
        return self.str

    def __repr__(self):
        return f"Production({str(self)})"

    def __len__(self):
        return len(self.prod)

    def __nonzero__(self):
        return 1

    def __getitem__(self, index):
        return self.prod[index]

    def lr_item(self, n):
        """
        Return the nth lr_item from the production (or None if at the end)
        """
        if n > len(self.prod):
            return None
        p = LRItem(self, n)
        # Precompute the list of productions immediately following.
        try:
            p.lr_after = self.prod[p.prod[n + 1]]  # may error out?????
        except (IndexError, KeyError):
            p.lr_after = []
        try:
            p.lr_before = p.prod[n - 1]
        except IndexError:
            p.lr_before = None
        return p

    def bind(self, function_spec):
        """
        Bind the production function name to a callable
        """
        if self.func:
            self.callable = function_spec[self.func]


class LRItem:
    """
    class LRItem
    This class represents a specific stage of parsing a production rule.
    For example:
          expr : expr . PLUS term

    In the above, the "." represents the current location of the parse.  Here
    basic attributes:
          name       - Name of the production.  For example 'expr'
          prod       - A list of symbols on the right side ['expr','.', 'PLUS','term']
          number     - Production number.
          lr_next      Next LR item. Example, if we are ' expr -> expr . PLUS term'
                       then lr_next refers to 'expr -> expr PLUS . term'
          lr_index   - LR item index (location of the ".") in the prod list.
          lookaheads - LALR lookahead symbols for this item
          len        - Length of the production (number of symbols on right hand side)
          lr_after    - List of all productions that immediately follow
          lr_before   - Grammar symbol immediately before
    """

    def __init__(self, p, n):
        self.name = p.name
        self.prod = list(p.prod)
        self.number = p.number
        self.lr_index = n
        self.lookaheads = {}
        self.prod.insert(n, ".")
        self.prod = tuple(self.prod)
        self.len = len(self.prod)
        self.unique_symbols = p.unique_symbols

    def __str__(self):
        if self.prod:
            s = f"{self.name} -> {' '.join(self.prod)}"
        else:
            s = f"{self.name} -> <empty>"
        return s

    def __repr__(self):
        return f"LRItem({str(self)})"


def rightmost_terminal(symbols, terminals):
    """
    rightmost_terminal()
    Return the rightmost terminal from a list of symbols.  Used in add_production()
    """
    i = len(symbols) - 1
    while i >= 0:
        if symbols[i] in terminals:
            return symbols[i]
        i -= 1
    return None


# -----------------------------------------------------------------------------
#                           === GRAMMAR CLASS ===
#
# The following class represents the contents of the specified grammar along
# with various computed properties such as first sets, follow sets, LR items, etc.
# This data is used for critical parts of the table generation process later.
# -----------------------------------------------------------------------------


class GrammarError(YaccError):
    pass


class Grammar(object):
    def __init__(self, terminals):
        self.productions: typing.List[typing.Union[Production, None]] = [None]
        # A list of all of the productions.  The first entry is always reserved for the purpose of
        # building an augmented grammar

        self.prod_names = (
            {}
        )  # A dictionary mapping the names of non-terminals to a list of all
        # productions of that non-terminal.

        self.prod_map = {}  # A dictionary that is only used to detect duplicate
        # productions.

        self.terminals = {}  # A dictionary mapping the names of terminal symbols to a
        # list of the rules where they are used.

        for term in terminals:
            self.terminals[term] = []

        self.terminals["error"] = []

        self.non_terminals = {}  # A dictionary mapping names of non-terminals to a list
        # of rule numbers where they are used.

        self.First = {}  # A dictionary of precomputed FIRST(x) symbols

        self.Follow = {}  # A dictionary of precomputed FOLLOW(x) symbols

        self.Precedence = (
            {}
        )  # Precedence rules for each terminal. Contains tuples of the
        # form ('right',level) or ('nonassoc', level) or ('left',level)

        self.UsedPrecedence = (
            set()
        )  # Precedence rules that were actually used by the grammar.
        # This is only used to provide error checking and to generate
        # a warning about unused precedence rules.

        self.Start = None  # Starting symbol for the grammar

    def __len__(self):
        return len(self.productions)

    def __getitem__(self, index):
        return self.productions[index]

    # -----------------------------------------------------------------------------
    # set_precedence()
    #
    # Sets the precedence for a given terminal. assoc is the associativity such as
    # 'left','right', or 'nonassoc'.  level is a numeric level.
    #
    # -----------------------------------------------------------------------------

    def set_precedence(self, term, assoc, level):
        assert self.productions == [
            None
        ], "Must call set_precedence() before add_production()"
        if term in self.Precedence:
            raise GrammarError("Precedence already specified for terminal %r" % term)
        if assoc not in ["left", "right", "nonassoc"]:
            raise GrammarError(
                "Associativity must be one of 'left','right', or 'nonassoc'"
            )
        self.Precedence[term] = (assoc, level)

    # -----------------------------------------------------------------------------
    # add_production()
    #
    # Given an action function, this function assembles a production rule and
    # computes its precedence level.
    #
    # The production rule is supplied as a list of symbols.   For example,
    # a rule such as 'expr : expr PLUS term' has a production name of 'expr' and
    # symbols ['expr','PLUS','term'].
    #
    # Precedence is determined by the precedence of the right-most non-terminal
    # or the precedence of a terminal specified by %precedence_level.
    #
    # A variety of error checks are performed to make sure production symbols
    # are valid and that %precedence_level is used correctly.
    # -----------------------------------------------------------------------------

    def add_production(self, prod_name, syms, func=None, file="", line=0):
        if prod_name in self.terminals:
            raise GrammarError(
                "%s:%d: Illegal rule name %r. Already defined as a token"
                % (file, line, prod_name)
            )
        if prod_name == "error":
            raise GrammarError(
                "%s:%d: Illegal rule name %r. error is a reserved word"
                % (file, line, prod_name)
            )
        if not _is_identifier.match(prod_name):
            raise GrammarError("%s:%d: Illegal rule name %r" % (file, line, prod_name))

        # Look for literal tokens
        for n, s in enumerate(syms):
            if s[0] in "'\"":
                try:
                    c = eval(s)
                    if len(c) > 1:
                        raise GrammarError(
                            "%s:%d: Literal token %s in rule %r may only be a single character"
                            % (file, line, s, prod_name)
                        )
                    if c not in self.terminals:
                        self.terminals[c] = []
                    syms[n] = c
                    continue
                except SyntaxError:
                    pass
            if not _is_identifier.match(s) and s != "%precedence_level":
                raise GrammarError(
                    "%s:%d: Illegal name %r in rule %r" % (file, line, s, prod_name)
                )

        # Determine the precedence level
        if "%precedence_level" in syms:
            if syms[-1] == "%precedence_level":
                raise GrammarError(
                    "%s:%d: Syntax error. Nothing follows %%precedence_level"
                    % (file, line)
                )
            if syms[-2] != "%precedence_level":
                raise GrammarError(
                    "%s:%d: Syntax error. %%precedence_level can only appear at the end of a grammar rule"
                    % (file, line)
                )
            precedence_name = syms[-1]
            production_precedence = self.Precedence.get(precedence_name)
            if not production_precedence:
                raise GrammarError(
                    "%s:%d: Nothing known about the precedence of %r"
                    % (file, line, precedence_name)
                )
            else:
                self.UsedPrecedence.add(precedence_name)
            del syms[-2:]  # Drop %precedence_level from the rule
        else:
            # If no %precedence_level, precedence is determined by the rightmost terminal symbol
            precedence_name = rightmost_terminal(syms, self.terminals)
            production_precedence = self.Precedence.get(precedence_name, ("right", 0))

        # See if the rule is already in the production map
        rule_map = "%s -> %s" % (prod_name, syms)
        if rule_map in self.prod_map:
            m = self.prod_map[rule_map]
            raise GrammarError(
                "%s:%d: Duplicate rule %s. " % (file, line, m)
                + "Previous definition at %s:%d" % (m.file, m.line)
            )

        # From this point on, everything is valid.  Create a new Production instance
        production_number = len(self.productions)
        if prod_name not in self.non_terminals:
            self.non_terminals[prod_name] = []

        # Add the production number to terminals and non_terminals
        for t in syms:
            if t in self.terminals:
                self.terminals[t].append(production_number)
            else:
                if t not in self.non_terminals:
                    self.non_terminals[t] = []
                self.non_terminals[t].append(production_number)

        # Create a production and add it to the list of productions
        p = Production(
            production_number, prod_name, syms, production_precedence, func, file, line
        )
        self.productions.append(p)
        self.prod_map[rule_map] = p

        # Add to the global productions list
        try:
            self.prod_names[prod_name].append(p)
        except KeyError:
            self.prod_names[prod_name] = [p]

    # -----------------------------------------------------------------------------
    # set_start()
    #
    # Sets the starting symbol and creates the augmented grammar.  Production
    # rule 0 is S' -> start where start is the start symbol.
    # -----------------------------------------------------------------------------

    def set_start(self, start=None):
        if not start:
            start = self.productions[1].name
        if start not in self.non_terminals:
            raise GrammarError("start symbol %s undefined" % start)
        self.productions[0] = Production(0, "S'", [start])
        self.non_terminals[start].append(0)
        self.Start = start

    # -----------------------------------------------------------------------------
    # find_unreachable()
    #
    # Find all of the nonterminal symbols that can't be reached from the starting
    # symbol.  Returns a list of nonterminals that can't be reached.
    # -----------------------------------------------------------------------------

    def find_unreachable(self):
        # Mark all symbols that are reachable from a symbol s
        def mark_reachable_from(s):
            if s in reachable:
                return
            reachable.add(s)
            for p in self.prod_names.get(s, []):
                for r in p.prod:
                    mark_reachable_from(r)

        reachable = set()
        mark_reachable_from(self.productions[0].prod[0])
        return [s for s in self.non_terminals if s not in reachable]

    # -----------------------------------------------------------------------------
    # infinite_cycles()
    #
    # This function looks at the various parsing rules and tries to detect
    # infinite recursion cycles (grammar rules where there is no possible way
    # to derive a string of only terminals).
    # -----------------------------------------------------------------------------

    def infinite_cycles(self):
        terminates = {}

        # terminals:
        for t in self.terminals:
            terminates[t] = True

        terminates["$end"] = True

        # non_terminals:

        # Initialize to false:
        for n in self.non_terminals:
            terminates[n] = False

        # Then propagate termination until no change:
        while True:
            some_change = False
            for n, pl in self.prod_names.items():
                # Nonterminal n terminates iff any of its productions terminates.
                for p in pl:
                    # Production p terminates iff all of its rhs symbols terminate.
                    for s in p.prod:
                        if not terminates[s]:
                            # The symbol s does not terminate,
                            # so production p does not terminate.
                            p_terminates = False
                            break
                    else:
                        # didn't break from the loop,
                        # so every symbol s terminates
                        # so production p terminates.
                        p_terminates = True

                    if p_terminates:
                        # symbol n terminates!
                        if not terminates[n]:
                            terminates[n] = True
                            some_change = True
                        # Don't need to consider any more productions for this n.
                        break

            if not some_change:
                break

        infinite = []
        for s, term in terminates.items():
            if not term:
                if (
                    s not in self.prod_names
                    and s not in self.terminals
                    and s != "error"
                ):
                    # s is used-but-not-defined, and we've already warned of that,
                    # so it would be overkill to say that it's also non-terminating.
                    pass
                else:
                    infinite.append(s)

        return infinite

    # -----------------------------------------------------------------------------
    # undefined_symbols()
    #
    # Find all symbols that were used the grammar, but not defined as tokens or
    # grammar rules.  Returns a list of tuples (sym, prod) where sym in the symbol
    # and prod is the production where the symbol was used.
    # -----------------------------------------------------------------------------
    def undefined_symbols(self):
        result = []
        for p in self.productions:
            if not p:
                continue

            for s in p.prod:
                if (
                    s not in self.prod_names
                    and s not in self.terminals
                    and s != "error"
                ):
                    result.append((s, p))
        return result

    # -----------------------------------------------------------------------------
    # unused_terminals()
    #
    # Find all terminals that were defined, but not used by the grammar.  Returns
    # a list of all symbols.
    # -----------------------------------------------------------------------------
    def unused_terminals(self):
        unused_tok = []
        for s, v in self.terminals.items():
            if s != "error" and not v:
                unused_tok.append(s)

        return unused_tok

    # ------------------------------------------------------------------------------
    # unused_rules()
    #
    # Find all grammar rules that were defined,  but not used (maybe not reachable)
    # Returns a list of productions.
    # ------------------------------------------------------------------------------

    def unused_rules(self):
        unused_prod = []
        for s, v in self.non_terminals.items():
            if not v:
                p = self.prod_names[s][0]
                unused_prod.append(p)
        return unused_prod

    # -----------------------------------------------------------------------------
    # unused_precedence()
    #
    # Returns a list of tuples (term,precedence) corresponding to precedence
    # rules that were never used by the grammar.  term is the name of the terminal
    # on which precedence was applied and precedence is a string such as 'left' or
    # 'right' corresponding to the type of precedence.
    # -----------------------------------------------------------------------------

    def unused_precedence(self):
        unused = []
        for termname in self.Precedence:
            if not (termname in self.terminals or termname in self.UsedPrecedence):
                unused.append((termname, self.Precedence[termname][0]))

        return unused

    # -------------------------------------------------------------------------
    # _first()
    #
    # Compute the value of FIRST1(beta) where beta is a tuple of symbols.
    #
    # During execution of compute_first1, the result may be incomplete.
    # Afterward (e.g., when called from compute_follow()), it will be complete.
    # -------------------------------------------------------------------------
    def _first(self, beta):
        # We are computing First(x1,x2,x3,...,xn)
        result = []
        for x in beta:
            x_produces_empty = False

            # Add all the non-<empty> symbols of First[x] to the result.
            for f in self.First[x]:
                if f == "<empty>":
                    x_produces_empty = True
                else:
                    if f not in result:
                        result.append(f)

            if x_produces_empty:
                # We have to consider the next x in beta,
                # i.e. stay in the loop.
                pass
            else:
                # We don't have to consider any further symbols in beta.
                break
        else:
            # There was no 'break' from the loop,
            # so x_produces_empty was true for all x in beta,
            # so beta produces empty as well.
            result.append("<empty>")

        return result

    # -------------------------------------------------------------------------
    # compute_first()
    #
    # Compute the value of FIRST1(X) for all symbols
    # -------------------------------------------------------------------------
    def compute_first(self):
        if self.First:
            return self.First

        # terminals:
        for t in self.terminals:
            self.First[t] = [t]

        self.First["$end"] = ["$end"]

        # non_terminals:

        # Initialize to the empty set:
        for n in self.non_terminals:
            self.First[n] = []

        # Then propagate symbols until no change:
        while True:
            some_change = False
            for n in self.non_terminals:
                for p in self.prod_names[n]:
                    for f in self._first(p.prod):
                        if f not in self.First[n]:
                            self.First[n].append(f)
                            some_change = True
            if not some_change:
                break

        return self.First

    # ---------------------------------------------------------------------
    # compute_follow()
    #
    # Computes all of the follow sets for every non-terminal symbol.  The
    # follow set is the set of all symbols that might follow a given
    # non-terminal.  See the Dragon book, 2nd Ed. p. 189.
    # ---------------------------------------------------------------------
    def compute_follow(self, start=None):
        # If already computed, return the result
        if self.Follow:
            return self.Follow

        # If first sets not computed yet, do that first.
        if not self.First:
            self.compute_first()

        # Add '$end' to the follow list of the start symbol
        for k in self.non_terminals:
            self.Follow[k] = []

        if not start:
            start = self.productions[1].name

        self.Follow[start] = ["$end"]

        while True:
            didadd = False
            for p in self.productions[1:]:
                # Here is the production set
                for i, B in enumerate(p.prod):
                    if B in self.non_terminals:
                        # Okay. We got a non-terminal in a production
                        fst = self._first(p.prod[i + 1 :])
                        hasempty = False
                        for f in fst:
                            if f != "<empty>" and f not in self.Follow[B]:
                                self.Follow[B].append(f)
                                didadd = True
                            if f == "<empty>":
                                hasempty = True
                        if hasempty or i == (len(p.prod) - 1):
                            # Add elements of follow(a) to follow(b)
                            for f in self.Follow[p.name]:
                                if f not in self.Follow[B]:
                                    self.Follow[B].append(f)
                                    didadd = True
            if not didadd:
                break
        return self.Follow

    # -----------------------------------------------------------------------------
    # build_lritems()
    #
    # This function walks the list of productions and builds a complete set of the
    # LR items.  The LR items are stored in two ways:  First, they are uniquely
    # numbered and placed in the list _lritems.  Second, a linked list of LR items
    # is built for each production.  For example:
    #
    #   E -> E PLUS E
    #
    # Creates the list
    #
    #  [E -> . E PLUS E, E -> E . PLUS E, E -> E PLUS . E, E -> E PLUS E . ]
    # -----------------------------------------------------------------------------

    def build_lritems(self):
        for p in self.productions:
            lastlri = p
            i = 0
            lr_items = []
            while True:
                if i > len(p):
                    lri = None
                else:
                    lri = LRItem(p, i)
                    # Precompute the list of productions immediately following
                    try:
                        lri.lr_after = self.prod_names[lri.prod[i + 1]]
                    except (IndexError, KeyError):
                        lri.lr_after = []
                    try:
                        lri.lr_before = lri.prod[i - 1]
                    except IndexError:
                        lri.lr_before = None

                lastlri.lr_next = lri
                if not lri:
                    break
                lr_items.append(lri)
                lastlri = lri
                i += 1
            p.lr_items = lr_items


# -----------------------------------------------------------------------------
#                           === LR Generator ===
#
# The following classes and functions are used to generate LR parsing tables on
# a grammar.
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# digraph()
# traverse()
#
# The following two functions are used to compute set valued functions
# of the form:
#
#     F(x) = F'(x) U U{F(y) | x R y}
#
# This is used to compute the values of Read() sets as well as FOLLOW sets
# in LALR(1) generation.
#
# Inputs:  X    - An input set
#          R    - A relation
#          FP   - Set-valued function
# ------------------------------------------------------------------------------


def digraph(X, R, FP):
    N = {}
    for x in X:
        N[x] = 0
    stack = []
    F = {}
    for x in X:
        if N[x] == 0:
            traverse(x, N, stack, F, X, R, FP)
    return F


def traverse(x, N, stack, F, X, R, FP):
    stack.append(x)
    d = len(stack)
    N[x] = d
    F[x] = FP(x)  # F(X) <- F'(x)

    rel = R(x)  # Get y's related to x
    for y in rel:
        if N[y] == 0:
            traverse(y, N, stack, F, X, R, FP)
        N[x] = min(N[x], N[y])
        for a in F.get(y, []):
            if a not in F[x]:
                F[x].append(a)
    if N[x] == d:
        N[stack[-1]] = MAXINT
        F[stack[-1]] = F[x]
        element = stack.pop()
        while element != x:
            N[stack[-1]] = MAXINT
            F[stack[-1]] = F[x]
            element = stack.pop()


class LALRError(YaccError):
    pass


# -----------------------------------------------------------------------------
#                             == LRTable ==
#
# This class implements the LR table generation algorithm.  There are no
# public methods.
# -----------------------------------------------------------------------------


class LRTable:
    def __init__(self, grammar, logger=None) -> None:
        self.grammar: Grammar = grammar

        # Set up the logger
        if not logger:
            logger = NullLogger()
        self.logger = logger

        # Internal attributes
        self.lr_action = {}  # Action table
        self.lr_goto = {}  # Goto table
        self.lr_productions = grammar.productions  # Copy of grammar Production array
        self.lr_goto_cache = {}  # Cache of computed gotos
        self.lr_0_cidhash = {}  # Cache of closures

        self._add_count = 0  # Internal counter used to detect cycles

        # Diagnostic information filled in by the table generator
        self.sr_conflict = 0
        self.rr_conflict = 0
        self.conflicts = []  # List of conflicts

        self.sr_conflicts = []
        self.rr_conflicts = []

        # Build the tables
        self.grammar.build_lritems()
        self.grammar.compute_first()
        self.grammar.compute_follow()
        self.lr_parse_table()

    def bind_callables(self, function_spec):
        """Bind all production function names to callable objects in pdict"""
        for p in self.lr_productions:
            p.bind(function_spec)

    # Compute the LR(0) closure operation on I, where I is a set of LR(0) items.

    def lr0_closure(self, items: typing.Set) -> typing.Set:
        self._add_count += 1

        # Add everything in I to J
        J = items[:]
        didadd = True
        while didadd:
            didadd = False
            for j in J:
                for x in j.lr_after:
                    if getattr(x, "lr0_added", 0) == self._add_count:
                        continue
                    # Add B --> .G to J
                    J.append(x.lr_next)
                    x.lr0_added = self._add_count
                    didadd = True

        return J

    # Compute the LR(0) goto function goto(I,X) where I is a set
    # of LR(0) items and X is a grammar symbol.   This function is written
    # in a way that guarantees uniqueness of the generated goto sets
    # (i.e. the same goto set will never be returned as two different Python
    # objects).  With uniqueness, we can later do fast set comparisons using
    # id(obj) instead of element-wise comparison.

    def lr0_goto(self, I, x):
        # First we look for a previously cached entry
        g = self.lr_goto_cache.get((id(I), x))
        if g:
            return g

        # Now we generate the goto set in a way that guarantees uniqueness
        # of the result

        s = self.lr_goto_cache.get(x)
        if not s:
            s = {}
            self.lr_goto_cache[x] = s

        gs = []
        for p in I:
            n = p.lr_next
            if n and n.lr_before == x:
                s1 = s.get(id(n))
                if not s1:
                    s1 = {}
                    s[id(n)] = s1
                gs.append(n)
                s = s1
        g = s.get("$end")
        if not g:
            if gs:
                g = self.lr0_closure(gs)
                s["$end"] = g
            else:
                s["$end"] = gs
        self.lr_goto_cache[(id(I), x)] = g
        return g

    # Compute the LR(0) sets of item function
    def lr0_items(self):
        C = [self.lr0_closure([self.grammar.productions[0].lr_next])]
        i = 0
        for I in C:
            self.lr_0_cidhash[id(I)] = i
            i += 1

        # Loop over the items in C and each grammar symbols
        i = 0
        while i < len(C):
            I = C[i]
            i += 1

            # Collect all of the symbols that could possibly be in the goto(I,X) sets
            asyms = {}
            for ii in I:
                for s in ii.unique_symbols:
                    asyms[s] = None

            for x in asyms:
                g = self.lr0_goto(I, x)
                if not g or id(g) in self.lr_0_cidhash:
                    continue
                self.lr_0_cidhash[id(g)] = len(C)
                C.append(g)

        return C

    # -----------------------------------------------------------------------------
    #                       ==== LALR(1) Parsing ====
    #
    # LALR(1) parsing is almost exactly the same as SLR except that instead of
    # relying upon Follow() sets when performing reductions, a more selective
    # lookahead set that incorporates the state of the LR(0) machine is utilized.
    # Thus, we mainly just have to focus on calculating the lookahead sets.
    #
    # The method used here is due to DeRemer and Pennelo (1982).
    #
    # DeRemer, F. L., and T. J. Pennelo: "Efficient Computation of LALR(1)
    #     Lookahead Sets", ACM Transactions on Programming Languages and Systems,
    #     Vol. 4, No. 4, Oct. 1982, pp. 615-649
    #
    # Further details can also be found in:
    #
    #  J. Tremblay and P. Sorenson, "The Theory and Practice of Compiler Writing",
    #      McGraw-Hill Book Company, (1985).
    #
    # -----------------------------------------------------------------------------

    # -----------------------------------------------------------------------------
    # compute_nullable_nonterminals()
    #
    # Creates a dictionary containing all of the non-terminals that might produce
    # an empty production.
    # -----------------------------------------------------------------------------

    def compute_nullable_nonterminals(self):
        nullable = set()
        num_nullable = 0
        while True:
            for p in self.grammar.productions[1:]:
                if p.len == 0:
                    nullable.add(p.name)
                    continue
                for t in p.prod:
                    if t not in nullable:
                        break
                else:
                    nullable.add(p.name)
            if len(nullable) == num_nullable:
                break
            num_nullable = len(nullable)
        return nullable

    # -----------------------------------------------------------------------------
    # find_nonterminal_trans(C)
    #
    # Given a set of LR(0) items, this functions finds all of the non-terminal
    # transitions.    These are transitions in which a dot appears immediately before
    # a non-terminal.   Returns a list of tuples of the form (state,N) where state
    # is the state number and N is the nonterminal symbol.
    #
    # The input C is the set of LR(0) items.
    # -----------------------------------------------------------------------------

    def find_nonterminal_transitions(self, C):
        trans = []
        for stateno, state in enumerate(C):
            for p in state:
                if p.lr_index < p.len - 1:
                    t = (stateno, p.prod[p.lr_index + 1])
                    if t[1] in self.grammar.non_terminals:
                        if t not in trans:
                            trans.append(t)
        return trans

    # -----------------------------------------------------------------------------
    # dr_relation()
    #
    # Computes the DR(p,A) relationships for non-terminal transitions.  The input
    # is a tuple (state,N) where state is a number and N is a nonterminal symbol.
    #
    # Returns a list of terminals.
    # -----------------------------------------------------------------------------

    def dr_relation(self, C, trans, nullable):
        state, N = trans
        terms = []

        g = self.lr0_goto(C[state], N)
        for p in g:
            if p.lr_index < p.len - 1:
                a = p.prod[p.lr_index + 1]
                if a in self.grammar.terminals:
                    if a not in terms:
                        terms.append(a)

        # This extra bit is to handle the start state
        if state == 0 and N == self.grammar.productions[0].prod[0]:
            terms.append("$end")

        return terms

    # -----------------------------------------------------------------------------
    # reads_relation()
    #
    # Computes the READS() relation (p,A) READS (t,C).
    # -----------------------------------------------------------------------------

    def reads_relation(self, C, trans, empty):
        # Look for empty transitions
        rel = []
        state, N = trans

        g = self.lr0_goto(C[state], N)
        j = self.lr_0_cidhash.get(id(g), -1)
        for p in g:
            if p.lr_index < p.len - 1:
                a = p.prod[p.lr_index + 1]
                if a in empty:
                    rel.append((j, a))

        return rel

    # -----------------------------------------------------------------------------
    # compute_lookback_includes()
    #
    # Determines the lookback and includes relations
    #
    # LOOKBACK:
    #
    # This relation is determined by running the LR(0) state machine forward.
    # For example, starting with a production "N : . A B C", we run it forward
    # to obtain "N : A B C ."   We then build a relationship between this final
    # state and the starting state.   These relationships are stored in a dictionary
    # lookdict.
    #
    # INCLUDES:
    #
    # Computes the INCLUDE() relation (p,A) INCLUDES (p',B).
    #
    # This relation is used to determine non-terminal transitions that occur
    # inside of other non-terminal transition states.   (p,A) INCLUDES (p', B)
    # if the following holds:
    #
    #       B -> LAT, where T -> epsilon and p' -L-> p
    #
    # L is essentially a prefix (which may be empty), T is a suffix that must be
    # able to derive an empty string.  State p' must lead to state p with the string L.
    #
    # -----------------------------------------------------------------------------

    def compute_lookback_includes(self, C, trans, nullable):
        lookdict = {}  # Dictionary of lookback relations
        includedict = {}  # Dictionary of include relations

        # Make a dictionary of non-terminal transitions
        dtrans = {}
        for t in trans:
            dtrans[t] = 1

        # Loop over all transitions and compute lookbacks and includes
        for state, N in trans:
            lookb = []
            includes = []
            for p in C[state]:
                if p.name != N:
                    continue

                # Okay, we have a name match.  We now follow the production all the way
                # through the state machine until we get the . on the right hand side

                lr_index = p.lr_index
                j = state
                while lr_index < p.len - 1:
                    lr_index = lr_index + 1
                    t = p.prod[lr_index]

                    # Check to see if this symbol and state are a non-terminal transition
                    if (j, t) in dtrans:
                        # Yes.  Okay, there is some chance that this is an includes relation
                        # the only way to know for certain is whether the rest of the
                        # production derives empty

                        li = lr_index + 1
                        while li < p.len:
                            if p.prod[li] in self.grammar.terminals:
                                break  # No forget it
                            if p.prod[li] not in nullable:
                                break
                            li = li + 1
                        else:
                            # Appears to be a relation between (j,t) and (state,N)
                            includes.append((j, t))

                    g = self.lr0_goto(C[j], t)  # Go to next set
                    j = self.lr_0_cidhash.get(id(g), -1)  # Go to next state

                # When we get here, j is the final state, now we have to locate the production
                for r in C[j]:
                    if r.name != p.name:
                        continue
                    if r.len != p.len:
                        continue
                    i = 0
                    # This look is comparing a production ". A B C" with "A B C ."
                    while i < r.lr_index:
                        if r.prod[i] != p.prod[i + 1]:
                            break
                        i = i + 1
                    else:
                        lookb.append((j, r))
            for i in includes:
                if i not in includedict:
                    includedict[i] = []
                includedict[i].append((state, N))
            lookdict[(state, N)] = lookb

        return lookdict, includedict

    # -----------------------------------------------------------------------------
    # compute_read_sets()
    #
    # Given a set of LR(0) items, this function computes the read sets.
    #
    # Inputs:  C        =  Set of LR(0) items
    #          ntrans   = Set of nonterminal transitions
    #          nullable = Set of empty transitions
    #
    # Returns a set containing the read sets
    # -----------------------------------------------------------------------------

    def compute_read_sets(self, C, ntrans, nullable):
        FP = lambda x: self.dr_relation(C, x, nullable)
        R = lambda x: self.reads_relation(C, x, nullable)
        F = digraph(ntrans, R, FP)
        return F

    # -----------------------------------------------------------------------------
    # compute_follow_sets()
    #
    # Given a set of LR(0) items, a set of non-terminal transitions, a readset,
    # and an include set, this function computes the follow sets
    #
    # Follow(p,A) = Read(p,A) U U {Follow(p',B) | (p,A) INCLUDES (p',B)}
    #
    # Inputs:
    #            ntrans     = Set of nonterminal transitions
    #            readsets   = Readset (previously computed)
    #            inclsets   = Include sets (previously computed)
    #
    # Returns a set containing the follow sets
    # -----------------------------------------------------------------------------

    def compute_follow_sets(self, ntrans, readsets, inclsets):
        FP = lambda x: readsets[x]
        R = lambda x: inclsets.get(x, [])
        F = digraph(ntrans, R, FP)
        return F

    # -----------------------------------------------------------------------------
    # add_lookaheads()
    #
    # Attaches the lookahead symbols to grammar rules.
    #
    # Inputs:    lookbacks         -  Set of lookback relations
    #            followset         -  Computed follow set
    #
    # This function directly attaches the lookaheads to productions contained
    # in the lookbacks set
    # -----------------------------------------------------------------------------

    def add_lookaheads(self, lookbacks, followset):
        for trans, lb in lookbacks.items():
            # Loop over productions in lookback
            for state, p in lb:
                if state not in p.lookaheads:
                    p.lookaheads[state] = []
                f = followset.get(trans, [])
                for a in f:
                    if a not in p.lookaheads[state]:
                        p.lookaheads[state].append(a)

    # -----------------------------------------------------------------------------
    # add_lalr_lookaheads()
    #
    # This function does all of the work of adding lookahead information for use
    # with LALR parsing
    # -----------------------------------------------------------------------------

    def add_lalr_lookaheads(self, C):
        # Determine all of the nullable nonterminals
        nullable = self.compute_nullable_nonterminals()

        # Find all non-terminal transitions
        trans = self.find_nonterminal_transitions(C)

        # Compute read sets
        readsets = self.compute_read_sets(C, trans, nullable)

        # Compute lookback/includes relations
        lookd, included = self.compute_lookback_includes(C, trans, nullable)

        # Compute LALR FOLLOW sets
        followsets = self.compute_follow_sets(trans, readsets, included)

        # Add all of the lookaheads
        self.add_lookaheads(lookd, followsets)

    # -----------------------------------------------------------------------------
    # lr_parse_table()
    #
    # This function constructs the parse tables for SLR or LALR
    # -----------------------------------------------------------------------------
    def lr_parse_table(self):
        Productions = self.grammar.productions
        Precedence = self.grammar.Precedence
        goto = self.lr_goto  # Goto array
        action = self.lr_action  # Action array
        log = self.logger  # Logger for output

        actionp = {}  # Action production array (temporary)

        # Step 1: Construct C = { I0, I1, ... IN}, collection of LR(0) items
        # This determines the number of states

        C = self.lr0_items()
        self.add_lalr_lookaheads(C)

        # Build the parser table, state by state
        st = 0
        for I in C:
            # Loop over each production in I
            actlist = []  # List of actions
            st_action = {}
            st_actionp = {}
            st_goto = {}
            log.info("")
            log.info("state %d", st)
            log.info("")
            for p in I:
                log.info("    (%d) %s", p.number, p)
            log.info("")

            for p in I:
                if p.len == p.lr_index + 1:
                    if p.name == "S'":
                        # Start symbol. Accept!
                        st_action["$end"] = 0
                        st_actionp["$end"] = p
                    else:
                        # We are at the end of a production.  Reduce!
                        laheads = p.lookaheads[st]
                        for a in laheads:
                            actlist.append(
                                (a, p, "reduce using rule %d (%s)" % (p.number, p))
                            )
                            r = st_action.get(a)
                            if r is not None:
                                # Whoa. Have a shift/reduce or reduce/reduce conflict
                                if r > 0:
                                    # Need to decide on shift or reduce here
                                    # By default we favor shifting. Need to add
                                    # some precedence rules here.

                                    # Shift precedence comes from the token
                                    sprec, slevel = Precedence.get(a, ("right", 0))

                                    # Reduce precedence comes from rule being reduced (p)
                                    rprec, rlevel = Productions[
                                        p.number
                                    ].precedence_level

                                    if (slevel < rlevel) or (
                                        (slevel == rlevel) and (rprec == "left")
                                    ):
                                        # We really need to reduce here.
                                        st_action[a] = -p.number
                                        st_actionp[a] = p
                                        if not slevel and not rlevel:
                                            log.info(
                                                "  ! shift/reduce conflict for %s resolved as reduce",
                                                a,
                                            )
                                            self.sr_conflicts.append((st, a, "reduce"))
                                        Productions[p.number].reduced += 1
                                    elif (slevel == rlevel) and (rprec == "nonassoc"):
                                        st_action[a] = None
                                    else:
                                        # Hmmm. Guess we'll keep the shift
                                        if not rlevel:
                                            log.info(
                                                "  ! shift/reduce conflict for %s resolved as shift",
                                                a,
                                            )
                                            self.sr_conflicts.append((st, a, "shift"))
                                elif r < 0:
                                    # Reduce/reduce conflict.   In this case, we favor the rule
                                    # that was defined first in the grammar file
                                    oldp = Productions[-r]
                                    pp = Productions[p.number]
                                    if oldp.line > pp.line:
                                        st_action[a] = -p.number
                                        st_actionp[a] = p
                                        chosenp, rejectp = pp, oldp
                                        Productions[p.number].reduced += 1
                                        Productions[oldp.number].reduced -= 1
                                    else:
                                        chosenp, rejectp = oldp, pp
                                    self.rr_conflicts.append((st, chosenp, rejectp))
                                    log.info(
                                        "  ! reduce/reduce conflict for %s resolved using rule %d (%s)",
                                        a,
                                        st_actionp[a].number,
                                        st_actionp[a],
                                    )
                                else:
                                    raise LALRError("Unknown conflict in state %d" % st)
                            else:
                                st_action[a] = -p.number
                                st_actionp[a] = p
                                Productions[p.number].reduced += 1
                else:
                    i = p.lr_index
                    a = p.prod[i + 1]  # Get symbol right after the "."
                    if a in self.grammar.terminals:
                        g = self.lr0_goto(I, a)
                        j = self.lr_0_cidhash.get(id(g), -1)
                        if j >= 0:
                            # We are in a shift state
                            actlist.append((a, p, "shift and go to state %d" % j))
                            r = st_action.get(a)
                            if r is not None:
                                # Whoa have a shift/reduce or shift/shift conflict
                                if r > 0:
                                    if r != j:
                                        raise LALRError(
                                            "Shift/shift conflict in state %d" % st
                                        )
                                elif r < 0:
                                    # Do a precedence check.
                                    #   -  if precedence of reduce rule is higher, we reduce.
                                    #   -  if precedence of reduce is same and left assoc, we reduce.
                                    #   -  otherwise we shift

                                    # Shift precedence comes from the token
                                    sprec, slevel = Precedence.get(a, ("right", 0))

                                    # Reduce precedence comes from the rule that could have been reduced
                                    rprec, rlevel = Productions[
                                        st_actionp[a].number
                                    ].precedence_level

                                    if (slevel > rlevel) or (
                                        (slevel == rlevel) and (rprec == "right")
                                    ):
                                        # We decide to shift here... highest precedence to shift
                                        Productions[st_actionp[a].number].reduced -= 1
                                        st_action[a] = j
                                        st_actionp[a] = p
                                        if not rlevel:
                                            log.info(
                                                "  ! shift/reduce conflict for %s resolved as shift",
                                                a,
                                            )
                                            self.sr_conflicts.append((st, a, "shift"))
                                    elif (slevel == rlevel) and (rprec == "nonassoc"):
                                        st_action[a] = None
                                    else:
                                        # Hmmm. Guess we'll keep the reduce
                                        if not slevel and not rlevel:
                                            log.info(
                                                "  ! shift/reduce conflict for %s resolved as reduce",
                                                a,
                                            )
                                            self.sr_conflicts.append((st, a, "reduce"))

                                else:
                                    raise LALRError("Unknown conflict in state %d" % st)
                            else:
                                st_action[a] = j
                                st_actionp[a] = p

            # Print the actions associated with each terminal
            _actprint = {}
            for a, p, m in actlist:
                if a in st_action:
                    if p is st_actionp[a]:
                        log.info("    %-15s %s", a, m)
                        _actprint[(a, m)] = 1
            log.info("")
            # Print the actions that were not used. (debugging)
            not_used = 0
            for a, p, m in actlist:
                if a in st_action:
                    if p is not st_actionp[a]:
                        if not (a, m) in _actprint:
                            log.debug("  ! %-15s [ %s ]", a, m)
                            not_used = 1
                            _actprint[(a, m)] = 1
            if not_used:
                log.debug("")

            # Construct the goto table for this state

            nkeys = {}
            for ii in I:
                for s in ii.unique_symbols:
                    if s in self.grammar.non_terminals:
                        nkeys[s] = None
            for n in nkeys:
                g = self.lr0_goto(I, n)
                j = self.lr_0_cidhash.get(id(g), -1)
                if j >= 0:
                    st_goto[n] = j
                    log.info("    %-30s shift and go to state %d", n, j)

            action[st] = st_action
            actionp[st] = st_actionp
            goto[st] = st_goto
            st += 1


# -----------------------------------------------------------------------------
#                            === INTROSPECTION ===
#
# The following functions and classes are used to implement the PLY
# introspection features followed by the yacc() function itself.
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# get_caller_module_dict()
#
# This function returns a dictionary containing all of the symbols defined within
# a caller further down the call stack.  This is used to get the environment
# associated with the yacc() call if none was provided.
# -----------------------------------------------------------------------------


def get_caller_module_dict(levels):
    f = sys._getframe(levels)
    ldict = f.f_globals.copy()
    if f.f_globals != f.f_locals:
        ldict.update(f.f_locals)
    return ldict


# -----------------------------------------------------------------------------
# parse_grammar()
#
# This takes a raw grammar rule string and parses it into production data
# -----------------------------------------------------------------------------
def parse_grammar(doc, file, line):
    grammar = []
    # Split the doc string into lines
    pstrings = doc.splitlines()
    lastp = None
    dline = line
    for ps in pstrings:
        dline += 1
        p = ps.split()
        if not p:
            continue
        try:
            if p[0] == "|":
                # This is a continuation of a previous rule
                if not lastp:
                    raise SyntaxError("%s:%d: Misplaced '|'" % (file, dline))
                prodname = lastp
                syms = p[1:]
            else:
                prodname = p[0]
                lastp = prodname
                syms = p[2:]
                assign = p[1]
                if assign != ":" and assign != "::=":
                    raise SyntaxError(
                        "%s:%d: Syntax error. Expected ':'" % (file, dline)
                    )

            grammar.append((file, dline, prodname, syms))
        except SyntaxError:
            raise
        except Exception:
            raise SyntaxError(
                "%s:%d: Syntax error in rule %r" % (file, dline, ps.strip())
            )

    return grammar


class ParserReflect:
    """
    This class represents information extracted for building a parser including
    start symbol, error function, tokens, precedence list, action functions, etc.
    """

    def __init__(
        self,
        rule_spec: dict[str, str],
        function_spec: dict[str, typing.Callable],
        tokens: Optional[list[str]],
        precedence: Optional[tuple],
        log=None,
    ):
        self.rule_spec = rule_spec
        self.function_spec = function_spec
        self.start = None
        self.error_func = None
        self.tokens = tokens
        self.precedence = precedence
        self.precedence_list = None
        self.grammar = []
        self.error = False

        if log is None:
            self.log = PlyLogger(sys.stderr)
        else:
            self.log = log

    def get_all(self):
        """Get all the basic information"""
        self.get_start()
        self.get_error_func()

    def validate_all(self):
        """Validate all the information"""
        self.validate_start()
        self.validate_error_func()
        self.validate_tokens()
        self.validate_precedence()
        self.validate_pfunctions()
        return self.error

    def signature(self):
        """Compute a signature over the grammar"""
        parts = []
        try:
            if self.start:
                parts.append(self.start)
            if self.precedence:
                parts.append("".join(["".join(p) for p in self.precedence]))
            if self.tokens:
                parts.append(" ".join(self.tokens))
            for rule_identifier, rule in self.rule_spec:
                parts.append(rule_identifier)
                parts.append(rule)
        except (TypeError, ValueError):
            pass
        return "".join(parts)

    def get_start(self):
        """Get the start symbol"""
        start = self.rule_spec.get("start")
        if start is None:
            raise ValueError("Start rule is not defined.")
        if start.count("\n"):
            raise ValueError(f"Start rule must only have a single symbol.")
        if ":" in start or " " in start:
            start = start.split(":")[1].strip()
        else:
            raise ValueError(f"Start rule '{start}' must be a complete rule.")
        self.start = start

    def validate_start(self):
        """Validate the start symbol"""
        if self.start in self.function_spec:
            return
            raise ValueError("Start rule cannot have an associated function")

    def get_error_func(self):
        """Look for error handler"""
        self.error_func = self.function_spec.get("error")

    def validate_error_func(self):
        """Validate the error function"""
        if self.error_func:
            if isinstance(self.error_func, types.FunctionType):
                ismethod = 0
            elif isinstance(self.error_func, types.MethodType):
                ismethod = 1
            else:
                self.log.error("'p_error' defined, but is not a function or method")
                self.error = True
                return

            eline = self.error_func.__code__.co_firstlineno
            efile = self.error_func.__code__.co_filename

            arg_count = self.error_func.__code__.co_argcount - ismethod
            if arg_count != 1:
                self.log.error(f"{efile}:{eline}: p_error() requires 1 argument")
                self.error = True

    def validate_tokens(self):
        """Validate the tokens"""
        # Validate the tokens.
        if "error" in self.tokens:
            self.log.error("Illegal token name 'error'. Is a reserved word")
            self.error = True
            return

        terminals = set()
        for n in self.tokens:
            if n in terminals:
                self.log.warning(f"Token {n} multiply defined")
            terminals.add(n)

    # Validate and parse the precedence map
    def validate_precedence(self):
        precedence_list = []
        if self.precedence:
            if not isinstance(self.precedence, (list, tuple)):
                self.log.error("precedence must be a list or tuple")
                self.error = True
                return
            for level, p in enumerate(self.precedence):
                if not isinstance(p, (list, tuple)):
                    self.log.error("Bad precedence table")
                    self.error = True
                    return

                if len(p) < 2:
                    self.log.error(
                        f"Malformed precedence entry {p}. Must be (assoc, term, ..., term)"
                    )
                    self.error = True
                    return
                assoc = p[0]
                if not isinstance(assoc, str):
                    self.log.error("precedence associativity must be a string")
                    self.error = True
                    return
                for term in p[1:]:
                    if not isinstance(term, str):
                        self.log.error("precedence items must be strings")
                        self.error = True
                        return
                    precedence_list.append((term, assoc, level + 1))
        self.precedence_list = precedence_list

    def validate_pfunctions(self):
        """Validates all the parsing functions"""
        grammar = []
        # Check for non-empty symbols
        if len(self.function_spec) == 0:
            self.log.error("no rules with associated functions are defined")
            self.error = True
            return

        for rule_identifier, rule_func in self.function_spec.items():
            if rule_identifier == "error":
                continue

            rule_func: typing.Callable
            file = inspect.getsourcefile(rule_func)
            line = rule_func.__code__.co_firstlineno

            if isinstance(rule_func, types.MethodType):
                regular_args = 2
            else:
                regular_args = 1
            if rule_func.__code__.co_argcount > regular_args:
                self.log.error(
                    f"{file}:{line}: Rule {rule_func.__name__} has too many arguments"
                )
                self.error = True
            elif rule_func.__code__.co_argcount < regular_args:
                self.log.error(
                    f"{file}:{line}: Rule {rule_func.__name__} requires an argument"
                )
                self.error = True
            elif rule_identifier not in self.rule_spec:
                self.log.error(
                    f"{file}:{line}: Rule {rule_func.__name__} is not in the rule specification "
                    f"but has associated function"
                )
                self.error = True
            else:
                try:
                    parsed_g = parse_grammar(
                        self.rule_spec[rule_identifier], file, line
                    )
                    for g in parsed_g:
                        grammar.append((rule_identifier, g))
                except SyntaxError as e:
                    self.log.error(str(e))
                    self.error = True

        self.grammar = grammar


def parse_spec(spec_str: str) -> dict[str, str]:
    """
    Parses a multiline grammar specification and returns a dictionary of identifiers and
    their respective rule strings.

    :param spec_str: The specification string
    :return: Returns a dictionary of {identifier: rule_str}
    """
    identifier_chars = string.ascii_letters + string.digits + "_"

    lines = spec_str.split("\n")
    spec = {}
    current_identifier = None
    current_identifier_rules = []

    for line_idx, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith("//"):
            if current_identifier:
                spec[current_identifier] = "\n".join(current_identifier_rules)
            current_identifier = None
            current_identifier_rules = []
            continue

        # parse identifier and regex
        if ":" not in line and "|" not in line:
            raise Exception(f"Error on line {line_idx}: No delimiter")

        if ":" in line:
            # add current rule stuff
            spec[current_identifier] = "\n".join(current_identifier_rules)

            # new rule
            current_identifier = line.split(":", maxsplit=1)[0].strip()
            current_identifier_rules = []

            if not all([char in identifier_chars for char in current_identifier]):
                raise Exception(
                    f"Error on line {line_idx}: "
                    f"Characters not in [a-z, A-Z 0-9, _] for identifier '{current_identifier}'"
                )
            if current_identifier in spec:
                raise Exception(
                    f"Error on line {line_idx}: "
                    f"Identifier '{current_identifier}' is already in the specification"
                )
            current_identifier_rules.append(line.strip())

        elif "|" in line:
            # continuation of existing rule
            if not current_identifier:
                raise Exception(
                    f"Error on line {line_idx}: Continuation of non-existent rule"
                )
            current_identifier_rules.append(line.strip())

    if current_identifier:
        spec[current_identifier] = "\n".join(current_identifier_rules)

    return spec


def yacc(
    rule_spec: str,
    function_spec: dict[str, typing.Callable],
    tokens: Optional[list[str]],
    precedence: Optional[tuple],
    debug=yacc_debug,
    __module=None,
    start=None,
    check_recursion=True,
    _debug_file=debug_file,
    debug_log=None,
    error_log=None,
):
    """
    Build a parser

    :param __module:
    :param precedence:
    :param tokens:
    :param rule_spec:
    :param function_spec:
    :param debug:
    :param start:
    :param check_recursion:
    :param _debug_file:
    :param debug_log:
    :param error_log:
    :return:
    """
    # Reference to the parsing method of the last built parser
    global parse

    if error_log is None:
        error_log = PlyLogger(sys.stderr)

    rule_spec = parse_spec(rule_spec)

    # # Get the module dictionary used for the parser
    # pdict = get_caller_module_dict(2)
    #
    # # Set start symbol if it's specified directly using an argument
    # if start is not None:
    #     pdict["start"] = start

    # Collect parser information from the dictionary
    parser_info = ParserReflect(
        rule_spec, function_spec, tokens, precedence, log=error_log
    )
    parser_info.get_all()

    if parser_info.error:
        raise YaccError("Unable to build parser")

    if debug_log is None:
        if debug:
            try:
                debug_log = PlyLogger(open(_debug_file, "w"))
            except IOError as e:
                error_log.warning("Couldn't open %r. %s" % (_debug_file, e))
                debug_log = NullLogger()
        else:
            debug_log = NullLogger()

    debug_log.info("Created by PLY (http://www.dabeaz.com/ply)")

    errors = False

    # Validate the parser information
    if parser_info.validate_all():
        raise YaccError("Unable to build parser")

    if not parser_info.error_func:
        error_log.warning("no p_error() function is defined")

    # Create a grammar object
    grammar = Grammar(parser_info.tokens)

    # Set precedence level for terminals
    for term, assoc, level in parser_info.precedence_list:
        try:
            grammar.set_precedence(term, assoc, level)
        except GrammarError as e:
            error_log.warning("%s", e)

    # Add productions to the grammar
    for funcname, gram in parser_info.grammar:
        file, line, prodname, syms = gram
        try:
            grammar.add_production(prodname, syms, funcname, file, line)
        except GrammarError as e:
            error_log.error("%s", e)
            errors = True

    # Set the grammar start symbols
    try:
        if start is None:
            grammar.set_start(parser_info.start)
        else:
            grammar.set_start(start)
    except GrammarError as e:
        error_log.error(str(e))
        errors = True

    if errors:
        raise YaccError("Unable to build parser")

    # Verify the grammar structure
    undefined_symbols = grammar.undefined_symbols()
    for sym, prod in undefined_symbols:
        error_log.error(
            "%s:%d: Symbol %r used, but not defined as a token or a rule",
            prod.file,
            prod.line,
            sym,
        )
        errors = True

    unused_terminals = grammar.unused_terminals()
    if unused_terminals:
        debug_log.info("")
        debug_log.info("Unused terminals:")
        debug_log.info("")
        for term in unused_terminals:
            error_log.warning("Token %r defined, but not used", term)
            debug_log.info("    %s", term)

    # Print out all productions to the debug log
    if debug:
        debug_log.info("")
        debug_log.info("Grammar")
        debug_log.info("")
        for n, p in enumerate(grammar.productions):
            debug_log.info("Rule %-5d %s", n, p)

    # Find unused non-terminals
    unused_rules = grammar.unused_rules()
    for prod in unused_rules:
        error_log.warning(
            "%s:%d: Rule %r defined, but not used", prod.file, prod.line, prod.name
        )

    if len(unused_terminals) == 1:
        error_log.warning("There is 1 unused token")
    if len(unused_terminals) > 1:
        error_log.warning("There are %d unused tokens", len(unused_terminals))

    if len(unused_rules) == 1:
        error_log.warning("There is 1 unused rule")
    if len(unused_rules) > 1:
        error_log.warning("There are %d unused rules", len(unused_rules))

    if debug:
        debug_log.info("")
        debug_log.info("terminals, with rules where they appear")
        debug_log.info("")
        terms = list(grammar.terminals)
        terms.sort()
        for term in terms:
            debug_log.info(
                "%-20s : %s", term, " ".join([str(s) for s in grammar.terminals[term]])
            )

        debug_log.info("")
        debug_log.info("non_terminals, with rules where they appear")
        debug_log.info("")
        non_terminals = list(grammar.non_terminals)
        non_terminals.sort()
        for non_terminal in non_terminals:
            debug_log.info(
                "%-20s : %s",
                non_terminal,
                " ".join([str(s) for s in grammar.non_terminals[non_terminal]]),
            )
        debug_log.info("")

    if check_recursion:
        unreachable = grammar.find_unreachable()
        for u in unreachable:
            error_log.warning("Symbol %r is unreachable", u)

        infinite = grammar.infinite_cycles()
        for inf in infinite:
            error_log.error("Infinite recursion detected for symbol %r", inf)
            errors = True

    unused_prec = grammar.unused_precedence()
    for term, assoc in unused_prec:
        error_log.error("Precedence rule %r defined for unknown symbol %r", assoc, term)
        errors = True

    if errors:
        raise YaccError("Unable to build parser")

    # Run the LRTable on the grammar
    lr = LRTable(grammar, debug_log)

    if debug:
        num_sr = len(lr.sr_conflicts)

        # Report shift/reduce and reduce/reduce conflicts
        if num_sr == 1:
            error_log.warning("1 shift/reduce conflict")
        elif num_sr > 1:
            error_log.warning("%d shift/reduce conflicts", num_sr)

        num_rr = len(lr.rr_conflicts)
        if num_rr == 1:
            error_log.warning("1 reduce/reduce conflict")
        elif num_rr > 1:
            error_log.warning("%d reduce/reduce conflicts", num_rr)

    # Write out conflicts to the output file
    if debug and (lr.sr_conflicts or lr.rr_conflicts):
        debug_log.warning("")
        debug_log.warning("Conflicts:")
        debug_log.warning("")

        for state, tok, resolution in lr.sr_conflicts:
            debug_log.warning(
                "shift/reduce conflict for %s in state %d resolved as %s",
                tok,
                state,
                resolution,
            )

        already_reported = set()
        for state, rule, rejected in lr.rr_conflicts:
            if (state, id(rule), id(rejected)) in already_reported:
                continue
            debug_log.warning(
                "reduce/reduce conflict in state %d resolved using rule (%s)",
                state,
                rule,
            )
            debug_log.warning("rejected rule (%s) in state %d", rejected, state)
            error_log.warning(
                "reduce/reduce conflict in state %d resolved using rule (%s)",
                state,
                rule,
            )
            error_log.warning("rejected rule (%s) in state %d", rejected, state)
            already_reported.add((state, id(rule), id(rejected)))

        warned_never = []
        for state, rule, rejected in lr.rr_conflicts:
            if not rejected.reduced and (rejected not in warned_never):
                debug_log.warning(f"Rule ({rejected}) is never reduced")
                error_log.warning(f"Rule ({rejected}) is never reduced")
                warned_never.append(rejected)

    # Build the parser
    lr.bind_callables(parser_info.function_spec)
    parser = LRParserEngine(lr, parser_info.error_func)

    parse = parser.parse
    return parser
