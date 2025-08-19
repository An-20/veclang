"""
High-level intermediate representation lowerer

This is where most Veclang features are actually implemented.
"""

import traceback
import collections

from veclang.frontend.parser import vl_ast
from veclang.frontend.parser.vl_ast import (
    ASTPositionInfo,
    augmented_assignment_operator_translation,
)

from veclang.midend.hir.vl_hir import (
    ExprNode,
    StmtNode,
    DeclNode,
    ProgramNode,
    RvalueIdentifierExprNode,
    BuiltinFunctionCallExprNode,
    UserdefFunctionCallExprNode,
    BinaryOperationExprNode,
    UnaryOperatorExprNode,
    ConstantExprNode,
    FunctionDeclNode,
    DataDeclNode,
    AssignmentStmtNode,
    ExprStmtNode,
    SelectionBlock,
    SelectionStackStmt,
    RangedForStmtNode,
    WhileStmtNode,
    ReturnStmtNode,
    BreakStmtNode,
    ContinueStmtNode,
)

from veclang.midend.vl_core import (
    VlType,
    VlTypeABC,
    VlTypeStr,
    VlTypeStrs,
    VlOperation,
    VlConstexprOperation,
    VlConstexprCast,
    VlNull,
    VlInt,
    VlReal,
    VlBool,
    VlComplex,
    VlMat2,
    VlMat3,
    VlMat4,
    VlVec2,
    VlVec3,
    VlVec4,
)

from veclang.midend.vl_stdlib import VlStdlib, StdlibFunction, StdlibConstexpr

from veclang.midend.hir.vl_lowerer_utils import (
    Scope,
    IdentifierData,
    VlFnParamTypeProfile,
    VlImportedFunctionProfile,
    VlUserdefFunctionProfile,
    VlQualifier,
    VlQualifierValues,
    vl_qualifier_to_hr,
    format_operator,
    check_snake_case,
    check_constant_case,
)

from veclang.common import Diagnostic, DiagnosticCode, FatalCompileError, CompilerFlags

GLOBAL_FN_NAME = "!vl_global"


class Lowerer:

    def __init__(self, compiler_flags: CompilerFlags):
        self.compiler_flags: CompilerFlags = compiler_flags

        self.userdef_functions: dict[str, VlUserdefFunctionProfile] = {}
        self.scopes: list[Scope] = [
            self.create_scope(GLOBAL_FN_NAME, None, None, None, ASTPositionInfo(0, 0))
        ]

        self.error: bool = False
        self.diagnostics: list[Diagnostic] = []

    def add_diagnostic(
        self, code: DiagnosticCode, message: str, ast_position_info: ASTPositionInfo
    ):
        if code.startswith("E"):
            self.error = True
        self.diagnostics.append(
            Diagnostic(
                ast_position_info.line_number,
                ast_position_info.line_character_number,
                code,
                self.get_stack_trace_hr(),
                message.strip(),
            )
        )

    # Scope tracking
    # ====================
    # These functions are also convenient for linting because all new scopes / variables
    # have to go through them

    @staticmethod
    def create_scope(
        fn_name: str | None,
        fn_return_type: VlType | None,
        loop_name: str | None,
        selection_name: str | None,
        ast_position_info: ASTPositionInfo,
    ) -> Scope:
        return Scope(
            fn_name,
            fn_return_type,
            loop_name,
            selection_name,
            ast_position_info,
            {},
            {},
        )

    def get_stack_trace_hr(self) -> str:
        def ast_position_info_to_hr(ast_position_info: ASTPositionInfo) -> str:
            return f"{ast_position_info.line_number}:{ast_position_info.line_character_number}"

        out_lines = []
        for scope in self.scopes:
            if scope.fn_name:
                fn_name = scope.fn_name
                line = f"Function '{fn_name}' at {ast_position_info_to_hr(scope.ast_position_info)}"
            elif scope.loop_name:
                line = f"Loop '{scope.loop_name}' at {ast_position_info_to_hr(scope.ast_position_info)}"
            elif scope.selection_name:
                line = f"Selection '{scope.selection_name}' at {ast_position_info_to_hr(scope.ast_position_info)}"
            else:
                raise FatalCompileError(f"IE: Unknown scope: {scope}")
            out_lines.append(line)
        return "\n".join(out_lines)

    def check_unused_identifiers(self):
        for identifier, data in self.scopes[-1].data.items():
            if data.ref_read_count == 0 and data.is_import:
                self.add_diagnostic(
                    "W001",
                    f"Unused imported identifier '{identifier}'",
                    data.ast_position_info,
                )
            elif data.ref_read_count == 0 and identifier[0] != "_":
                self.add_diagnostic(
                    "W001",
                    f"Unused identifier '{identifier}' - prefix with '_' to suppress",
                    data.ast_position_info,
                )
            elif (
                data.ref_write_count == 0
                and identifier[0] != "_"
                and data.vl_qualifier == "var"
                and not data.is_loop_var
            ):
                self.add_diagnostic(
                    "W002",
                    f"Variable '{identifier}' is never written to after initialisation "
                    f"- prefix with '_' to suppress",
                    data.ast_position_info,
                )
            elif data.ref_read_count != 0 and identifier[0] == "_":
                self.add_diagnostic(
                    "X003",
                    f"Identifier '{identifier}' - only unused identifiers should be prefixed with '_'",
                    data.ast_position_info,
                )

        for fr_identifier, data in self.scopes[-1].imported_functions.items():
            if data.ref_read_count == 0:
                self.add_diagnostic(
                    "W001",
                    f"Unused imported function '{fr_identifier}'",
                    self.scopes[-1].ast_position_info,
                )

    def scope_in_fn(
        self, fn_name: str, fn_return_type: VlType, ast_position_info: ASTPositionInfo
    ) -> None:
        self.scopes.append(
            self.create_scope(fn_name, fn_return_type, None, None, ast_position_info)
        )

    def scope_out_fn(self) -> None:
        if self.in_global_scope():
            raise FatalCompileError("IE: Cannot scope out of global scope!")
        if not self.scopes[-1].fn_name:
            raise FatalCompileError(
                "IE: Mismatched scope: current scope is not a function scope"
            )
        self.check_unused_identifiers()
        self.scopes.pop()

    def scope_in_loop(self, loop_name: str, ast_position_info: ASTPositionInfo) -> None:
        self.scopes.append(
            self.create_scope(None, None, loop_name, None, ast_position_info)
        )

    def scope_out_loop(self) -> None:
        if self.in_global_scope():
            raise FatalCompileError("IE: Cannot scope out of global scope!")
        if not self.scopes[-1].loop_name:
            raise FatalCompileError(
                "IE: Mismatched scope: current scope is not a loop scope"
            )
        self.check_unused_identifiers()
        self.scopes.pop()

    def scope_in_selection(
        self, selection_name: str, ast_position_info: ASTPositionInfo
    ) -> None:
        self.scopes.append(
            self.create_scope(None, None, None, selection_name, ast_position_info)
        )

    def scope_out_selection(self) -> None:
        if self.in_global_scope():
            raise FatalCompileError("IE: Cannot scope out of global scope!")
        if not self.scopes[-1].selection_name:
            raise FatalCompileError(
                "IE: Mismatched scope: current scope is not a selection scope"
            )
        self.check_unused_identifiers()
        self.scopes.pop()

    def in_global_scope(self) -> bool:
        return len(self.scopes) == 1

    def check_in_loop_scope(self) -> bool:
        """Returns a bool of whether the current scope is in a loop"""
        for scope in reversed(self.scopes):
            if scope.loop_name:
                return True
            if scope.fn_name:
                raise FatalCompileError(
                    "IE: Illegal construction: function declaration inside loop"
                )
        return False

    def check_in_fn_scope(self) -> VlType | None:
        """Returns a VlType of the current function's return type, or None if not in a function"""
        for scope in reversed(self.scopes):
            if scope.fn_name and scope.fn_name != GLOBAL_FN_NAME:
                if not scope.fn_return_type:
                    raise FatalCompileError(
                        "IE: Scope with fn_name without fn_return_type"
                    )
                return scope.fn_return_type
        return None

    def resolve_lvalue_identifier(
        self, identifier: str, ast_position_info: ASTPositionInfo
    ) -> IdentifierData:
        for scope in reversed(self.scopes):
            if identifier not in scope.data:
                continue
            if scope.fn_name == GLOBAL_FN_NAME:
                self.add_diagnostic(
                    "E200",
                    f"Identifier '{identifier}' is in the global scope "
                    f"and can't be used as an lvalue (assigned to)",
                    ast_position_info,
                )
                raise FatalCompileError()
            scope.data[identifier].ref_write_count += 1
            return scope.data[identifier]

        self.add_diagnostic(
            "E200", f"Unresolved identifier '{identifier}'", ast_position_info
        )
        raise FatalCompileError()

    def resolve_rvalue_identifier(
        self, identifier: str, ast_position_info: ASTPositionInfo
    ) -> IdentifierData:
        for scope in reversed(self.scopes):
            if identifier in scope.data:
                scope.data[identifier].ref_read_count += 1
                return scope.data[identifier]

        self.add_diagnostic(
            "E200", f"Unresolved identifier '{identifier}'", ast_position_info
        )
        raise FatalCompileError()

    def resolve_function_identifier(
        self, fr_identifier: str, ast_position_info: ASTPositionInfo
    ) -> VlImportedFunctionProfile | VlUserdefFunctionProfile:
        if fr_identifier in self.userdef_functions:
            return self.userdef_functions[fr_identifier]

        for scope in reversed(self.scopes):
            if fr_identifier in scope.imported_functions:
                scope.imported_functions[fr_identifier].ref_read_count += 1
                return scope.imported_functions[fr_identifier]

        self.add_diagnostic(
            "E200",
            f"Unresolved function identifier '{fr_identifier}'",
            ast_position_info,
        )
        raise FatalCompileError()

    def _check_if_data_identifier_declared(
        self, identifier: str, ast_position_info: ASTPositionInfo
    ) -> None:
        for scope_idx, parent_scope in enumerate(reversed(self.scopes)):
            if identifier in parent_scope.data:
                identifier_data = parent_scope.data[identifier]

                if scope_idx == 0:
                    scope_hr = "this scope"
                elif scope_idx == len(self.scopes) - 1:
                    scope_hr = "global scope"
                else:
                    scope_hr = f"parent scope with ASTPositionInfo {parent_scope.ast_position_info}"

                additional_details = ""
                if identifier_data.is_loop_var:
                    additional_details = "(as a loop variable)"
                if identifier_data.is_parameter:
                    additional_details = "(as a parameter)"
                if identifier_data.is_import:
                    additional_details = "(as an import)"
                self.add_diagnostic(
                    "E201",
                    f"{vl_qualifier_to_hr(identifier_data.vl_qualifier).capitalize()} '{identifier}' "
                    f"already declared in {scope_hr} {additional_details}",
                    ast_position_info,
                )

    def _check_if_function_identifier_declared(
        self, fr_identifier: str, ast_position_info: ASTPositionInfo
    ) -> None:
        if fr_identifier in self.userdef_functions:
            self.add_diagnostic(
                "E202",
                f"User-defined function '{fr_identifier}' already declared in global scope",
                ast_position_info,
            )

        for scope_idx, parent_scope in enumerate(reversed(self.scopes)):
            if fr_identifier in parent_scope.imported_functions:
                if scope_idx == 0:
                    scope_hr = "this scope"
                elif scope_idx == len(self.scopes) - 1:
                    scope_hr = "global scope"
                else:
                    scope_hr = f"parent scope with ASTPositionInfo {parent_scope.ast_position_info}"
                self.add_diagnostic(
                    "E202",
                    f"Imported function '{fr_identifier}' already declared in {scope_hr}",
                    ast_position_info,
                )

    def _init_data(
        self,
        identifier: str,
        vl_qualifier: VlQualifier,
        vl_type: VlType,
        vl_value: VlTypeABC | None,
        ast_position_info: ASTPositionInfo,
        is_loop_var: bool = False,
        is_parameter: bool = False,
        is_import: bool = False,
    ):
        if vl_qualifier not in VlQualifierValues:
            raise FatalCompileError(f"IE: Unknown VlQualifier {vl_qualifier}")
        if vl_qualifier == "var" and not check_snake_case(identifier):
            self.add_diagnostic(
                "X001",
                f"Variable identifier '{identifier}' should be lowercase snake_case",
                ast_position_info,
            )
        if (
            (vl_qualifier == "const" or vl_qualifier == "constexpr")
            and not check_constant_case(identifier)
            and not is_parameter
            and not is_import
        ):
            self.add_diagnostic(
                "X001",
                f"Constant identifier '{identifier}' should be uppercase SNAKE_CASE",
                ast_position_info,
            )
        self._check_if_data_identifier_declared(identifier, ast_position_info)
        scope = self.scopes[-1]

        if vl_qualifier == "constexpr" and vl_value is None:
            raise FatalCompileError("IE: constexpr data must have a vl_value")
        scope.data[identifier] = IdentifierData(
            ast_position_info,
            vl_qualifier,
            vl_type,
            vl_value,
            0,
            0,
            is_loop_var,
            is_parameter,
            is_import,
        )

    def init_variable(
        self, identifier: str, vl_type: VlType, ast_position_info: ASTPositionInfo
    ) -> None:
        self._init_data(identifier, "var", vl_type, None, ast_position_info)

    def init_constant(
        self, identifier: str, vl_type: VlType, ast_position_info: ASTPositionInfo
    ) -> None:
        self._init_data(identifier, "const", vl_type, None, ast_position_info)

    def init_constexpr(
        self, identifier: str, vl_value: VlTypeABC, ast_position_info: ASTPositionInfo
    ) -> None:
        self._init_data(
            identifier, "constexpr", type(vl_value), vl_value, ast_position_info
        )

    def init_parameter(
        self, identifier: str, vl_type: VlType, ast_position_info: ASTPositionInfo
    ) -> None:
        self._init_data(
            identifier, "const", vl_type, None, ast_position_info, is_parameter=True
        )

    def init_loop_var(
        self, identifier: str, vl_type: VlType, ast_position_info: ASTPositionInfo
    ) -> None:
        self._init_data(
            identifier, "var", vl_type, None, ast_position_info, is_loop_var=True
        )

    def init_imported_constexpr(
        self,
        fr_identifier: str,
        constexpr_data: StdlibConstexpr,
        ast_position_info: ASTPositionInfo,
    ) -> None:
        self._init_data(
            fr_identifier,
            "constexpr",
            type(constexpr_data.constexpr_value),
            constexpr_data.constexpr_value,
            ast_position_info,
            is_import=True,
        )

    def add_imported_function(
        self,
        fr_identifier: str,
        stdlib_fn: StdlibFunction,
        ast_position_info: ASTPositionInfo,
    ) -> None:
        self._check_if_function_identifier_declared(fr_identifier, ast_position_info)
        scope = self.scopes[-1]
        scope.imported_functions[fr_identifier] = VlImportedFunctionProfile(
            fr_identifier,
            stdlib_fn.fn_id,
            [
                VlFnParamTypeProfile(x.name, self.lower_vl_type(x.vl_type))
                for x in stdlib_fn.fn_params
            ],
            self.lower_vl_type(stdlib_fn.fn_return_type),
            0,
        )

    # Lowering
    # ====================

    def lower(
        self, ast_node: vl_ast.ProgramNode
    ) -> tuple[ProgramNode | None, list[Diagnostic]]:
        """
        Lowers an AST to a HIR, returning a tuple of:
        - a HIR ProgramNode or None
        - a list[Diagnostic]
        """
        self.error = False
        self.diagnostics = []

        stmts_lowered = None
        try:
            # lookahead all functions
            for stmt in ast_node.stmts.stmts:
                if isinstance(stmt, vl_ast.FunctionDeclNode):
                    self.lookahead_function_decl(stmt)

            # add `using core::*;`
            api = ASTPositionInfo(0, 0)
            stmts = [
                vl_ast.UsingDeclNode(
                    None,
                    (
                        vl_ast.IdentifierNode("core", api),
                        vl_ast.UsingDeclIdentifiersNode(
                            None, vl_ast.IdentifierNode("*", api), api
                        ),
                    ),
                    api,
                )
            ] + ast_node.stmts.stmts
            stmts_lowered = self.lower_stmts(stmts)

        except Exception as e:
            if isinstance(e, FatalCompileError):
                self.add_diagnostic(
                    "E900",
                    "The previous error that occurred during HIR lowering was fatal and compilation has terminated.",
                    ast_node.position_info,
                )
            else:
                self.add_diagnostic(
                    "E900",
                    f"Internal error: {e}; {traceback.format_exc()}",
                    ast_node.position_info,
                )

        if self.error:
            return None, self.diagnostics

        return (
            ProgramNode(
                stmts_lowered,
                ast_node.position_info,
            ),
            self.diagnostics,
        )

    @staticmethod
    def lower_vl_type(vl_type_str: str) -> VlType:
        if vl_type_str not in VlTypeStrs:
            raise FatalCompileError(f"IE: Unknown type '{vl_type_str}'")
        return {
            "int": VlInt,
            "real": VlReal,
            "bool": VlBool,
            "complex": VlComplex,
            "mat2": VlMat2,
            "mat3": VlMat3,
            "mat4": VlMat4,
            "vec2": VlVec2,
            "vec3": VlVec3,
            "vec4": VlVec4,
            "null": VlNull,
        }[vl_type_str]

    def lower_identifier_expr(
        self, expr: vl_ast.IdentifierNode
    ) -> RvalueIdentifierExprNode:
        """Only to be called for rvalue identifiers referring to a piece of data (var, const, constexpr)"""
        identifier = expr.name
        identifier_data = self.resolve_rvalue_identifier(identifier, expr.position_info)
        if identifier_data.vl_qualifier == "constexpr" and not identifier_data.vl_value:
            raise FatalCompileError("IE: Constexpr without vl_value")

        return RvalueIdentifierExprNode(
            identifier,
            identifier_data.vl_type,
            identifier_data.vl_value,
            expr.position_info,
        )

    def lower_scoped_identifier_expr(
        self, expr: vl_ast.ScopedIdentifierNode
    ) -> ConstantExprNode:
        """Only to be called for scoped identifiers"""
        fr_identifier = "::".join([x.name for x in expr.identifiers])
        identifier_data = self.resolve_rvalue_identifier(
            fr_identifier, expr.position_info
        )
        if identifier_data.vl_qualifier != "constexpr":
            raise FatalCompileError("IE: expected scoped identifier to be constexpr")
        if not identifier_data.vl_value:
            raise FatalCompileError("IE: expected scoped identifier to have vl_value")
        return ConstantExprNode(
            identifier_data.vl_type, identifier_data.vl_value, expr.position_info
        )

    @classmethod
    def try_widen_cast_expr(
        cls, expr: ExprNode, desired_type: VlTypeStr
    ) -> ExprNode | None:
        """Attempts a widening cast to cast expr into desired_type"""
        for cast in expr.vl_type.get_casts():
            if cast.to_type == desired_type:
                # attempt constexpr cast
                if isinstance(cast, VlConstexprCast) and expr.constexpr_value:
                    constexpr_value = cast.evaluate(expr.constexpr_value)
                else:
                    constexpr_value = None

                return BuiltinFunctionCallExprNode(
                    cast.fn_id,
                    [expr],
                    cls.lower_vl_type(cast.to_type),
                    constexpr_value,
                    expr.ast_position_info,
                    is_type_cast=True,
                )
        return None

    def lower_array_literal_expr(self, expr: vl_ast.ArrayLiteralExprNode) -> ExprNode:
        # TODO: Support matrices
        if len(expr.elements.exprs) in [2, 3, 4]:
            vl_type_str = f"vec{len(expr.elements.exprs)}"
        else:
            raise FatalCompileError(
                f"Unsupported array literal with length {len(expr.elements.exprs)}"
            )

        elements = [self.lower_expr(x) for x in expr.elements.exprs]
        casted_elements = []
        for element in elements:
            if element.vl_type.to_vl_type_str() == "real":
                casted_elements.append(element)
                continue

            casted_element = self.try_widen_cast_expr(element, "real")
            if casted_element is None:
                self.add_diagnostic(
                    "E100",
                    f"Array elements must be castable to real, got type '{element.vl_type.to_vl_type_str()}'",
                    element.ast_position_info,
                )
            casted_elements.append(casted_element)

        is_constexpr = all([element.constexpr_value for element in casted_elements])
        if is_constexpr:
            vl_type = {"vec2": VlVec2, "vec3": VlVec3, "vec4": VlVec4}[vl_type_str]
            constexpr_value = vl_type(
                [element.constexpr_value.underlying for element in casted_elements]
            )
        else:
            constexpr_value = None

        # the constructor fn won't be used if is_constexpr
        constructor_fn_id = {"vec2": 0x1300, "vec3": 0x1301, "vec4": 0x1302}[
            vl_type_str
        ]
        return BuiltinFunctionCallExprNode(
            constructor_fn_id,
            casted_elements,
            self.lower_vl_type(vl_type_str),
            constexpr_value,
            expr.position_info,
        )

    def lower_rvalue_member_access_expr(
        self, expr: vl_ast.MemberAccessExprNode
    ) -> BuiltinFunctionCallExprNode:
        """
        Lowers a 'rvalue member access expression'
        A member access is permitted to be used:
        - In a lvalue for assignment e.g. vec2Instance.x = 15;
        - In a rvalue expression for calling a property e.g. complexInstance.real
        - In a rvalue expression for calling a method e.g. a.dot(b)

        This function only handles member access for calling a property.
        Calling a method is handled separately as function calls have a
         separate callee resolution process separate from main expr lowering.
        """

        target = self.lower_expr(expr.target)
        identifier = expr.name.name

        for method in target.vl_type.get_methods():
            if identifier != method.name:
                continue
            self.add_diagnostic(
                "E106",
                "Member access results in callable; Veclang does not support first-class functions.",
                expr.position_info,
            )

        for _property in target.vl_type.get_properties():
            if identifier != _property.name:
                continue
            return BuiltinFunctionCallExprNode(
                _property.fn_id,
                [target],
                self.lower_vl_type(_property.return_type),
                None,  # no such thing as static member access
                expr.position_info,
                is_property=True,
            )
        else:
            raise FatalCompileError(
                f"Member access on resolved type '{target.vl_type.to_vl_type_str()}' "
                f"which does not have identifier '{identifier}'"
            )

    def lower_rvalue_index_expr(
        self, expr: vl_ast.IndexExprNode
    ) -> BuiltinFunctionCallExprNode:
        """
        Lowers a 'rvalue index expression'
        An index expression is permitted to be used:
        - In a lvalue for assignment e.g. vec2Instance[0] = 15;
        - In a rvalue to resolve to a VlType e.g. printr(a[0]);

        This function only handles indexing that results in a VlType,
        by calling the index function.
        """
        # TODO

    def lower_function_call_expr(self, expr: vl_ast.FunctionCallExprNode) -> ExprNode:
        if isinstance(expr.callee, vl_ast.MemberAccessExprNode):
            # special pathway just for method calls
            # this avoids us needing an internal compiler type for 'function'
            # because Veclang doesn't have first class functions
            callee = expr.callee
            target_lowered = self.lower_expr(callee.target)
            vl_type = target_lowered.vl_type
            for method in vl_type.get_methods():
                if method.name != callee.name.name:
                    continue
                arguments: list[ExprNode] = [
                    self.lower_expr(x) for x in expr.arguments.arguments
                ]
                if len(arguments) != len(method.arg_types):
                    self.add_diagnostic(
                        "E110",
                        f"Function {expr.callee.name} expected {len(method.arg_types)} arguments, got {len(arguments)}",
                        expr.position_info,
                    )
                for idx, (argument, parameter_type_str) in enumerate(
                    zip(arguments, method.arg_types)
                ):
                    if argument.vl_type.to_vl_type_str() != parameter_type_str:
                        self.add_diagnostic(
                            "E111",
                            f"Function '{expr.callee.name}' expects argument #{idx} "
                            f"to be type {parameter_type_str}, got {argument.vl_type.to_vl_type_str()}",
                            expr.position_info,
                        )

                return BuiltinFunctionCallExprNode(
                    method.fn_id,
                    [target_lowered],
                    self.lower_vl_type(method.return_type),
                    None,
                    expr.position_info,
                    is_method=True,
                )
            self.add_diagnostic(
                "E200",
                f"Unresolved identifier: {vl_type.to_vl_type_str()} has no method '{callee.name.name}'",
                expr.position_info,
            )
            raise FatalCompileError()

        elif isinstance(expr.callee, vl_ast.IdentifierNode):
            fr_identifier = expr.callee.name

        elif isinstance(expr.callee, vl_ast.ScopedIdentifierNode):
            fr_identifier = expr.callee.fully_resolve()

        else:
            self.add_diagnostic(
                "E113",
                f"Calling non-callable expression '{type(expr.callee)}'",
                expr.position_info,
            )
            raise FatalCompileError()

        function_data = self.resolve_function_identifier(
            fr_identifier, expr.position_info
        )
        arguments: list[ExprNode] = [
            self.lower_expr(x) for x in expr.arguments.arguments
        ]
        if len(arguments) != len(function_data.parameters):
            self.add_diagnostic(
                "E110",
                f"Function {expr.callee.name} expected {len(function_data.parameters)} arguments, got {len(arguments)}",
                expr.position_info,
            )

        for idx, (argument, parameter) in enumerate(
            zip(arguments, function_data.parameters)
        ):
            if argument.vl_type != parameter.vl_type:
                self.add_diagnostic(
                    "E111",
                    f"Function '{expr.callee.name}' expects argument #{idx} "
                    f"to be type {parameter.vl_type.to_vl_type_str()}, got {argument.vl_type.to_vl_type_str()}",
                    expr.position_info,
                )

        if isinstance(function_data, VlImportedFunctionProfile):
            return BuiltinFunctionCallExprNode(
                function_data.builtin_fn_id,
                arguments,
                function_data.return_type,
                None,  # no such thing as constexpr function call apart from casts
                expr.position_info,
            )
        elif isinstance(function_data, VlUserdefFunctionProfile):
            return UserdefFunctionCallExprNode(
                function_data.userdef_fn_idx,
                arguments,
                function_data.return_type,
                None,
                expr.position_info,
            )
        else:
            raise FatalCompileError("IE: unknown function_data type")

    def lower_cast_expr(self, expr: vl_ast.CastExprNode) -> BuiltinFunctionCallExprNode:
        argument = self.lower_expr(expr.argument)
        desired_type = self.lower_vl_type(expr.cast_type.name)

        for cast in argument.vl_type.get_casts():
            if cast.to_type == desired_type:
                # attempt constexpr cast
                if isinstance(cast, VlConstexprCast) and argument.constexpr_value:
                    constexpr_value = cast.evaluate(argument.constexpr_value)
                else:
                    constexpr_value = None

                return BuiltinFunctionCallExprNode(
                    cast.fn_id,
                    [argument],
                    self.lower_vl_type(cast.to_type),
                    constexpr_value,
                    expr.position_info,
                    is_type_cast=True,
                )
        self.add_diagnostic(
            "E105",
            f"Cannot cast from {argument.vl_type.to_vl_type_str()} to {desired_type.to_vl_type_str()}",
            expr.position_info,
        )
        raise FatalCompileError()

    @staticmethod
    def _try_eval_constexpr_binary_operation_expr(
        left: ExprNode, right: ExprNode, operation: VlOperation
    ) -> VlTypeABC | None:
        if not left.constexpr_value or not right.constexpr_value:
            return None
        if not isinstance(operation, VlConstexprOperation):
            return None
        return operation.evaluate(left.constexpr_value, right.constexpr_value)

    def lower_binary_operation_expr(
        self, expr: vl_ast.BinaryOperationExprNode
    ) -> BinaryOperationExprNode:
        left = self.lower_expr(expr.left)
        right = self.lower_expr(expr.right)
        operator = expr.operator

        # First, resolve operation simply
        operation = [
            x
            for x in left.vl_type.get_operations()
            if x.op_arity == "BINARY"
            and x.op_type == operator
            and x.operand_types == [right.vl_type.to_vl_type_str()]
        ]
        if len(operation) > 1:
            raise FatalCompileError(
                f"IE: Multiple operations found for '{operator}' with left "
                f"'{left.vl_type.to_vl_type_str()}', right '{right.vl_type.to_vl_type_str()}'"
            )
        if operation:
            operation = operation[0]
            constexpr_value = self._try_eval_constexpr_binary_operation_expr(
                left, right, operation
            )
            return BinaryOperationExprNode(
                left,
                right,
                expr.operator,
                operation,
                self.lower_vl_type(operation.result_type),
                constexpr_value,
                expr.position_info,
            )

        # Next, try coercing right
        for operation in left.vl_type.get_operations():
            if operation.op_arity != "BINARY" or operation.op_type != operator:
                continue
            right_widened = self.try_widen_cast_expr(right, operation.operand_types[0])
            if not right_widened:
                continue
            constexpr_value = self._try_eval_constexpr_binary_operation_expr(
                left, right_widened, operation
            )
            return BinaryOperationExprNode(
                left,
                right_widened,
                expr.operator,
                operation,
                self.lower_vl_type(operation.result_type),
                constexpr_value,
                expr.position_info,
            )

        # Next, try coercing left
        for operation in right.vl_type.get_operations():
            if operation.op_arity != "BINARY" or operation.op_type != operator:
                continue
            left_widened = self.try_widen_cast_expr(left, operation.operand_types[0])
            if not left_widened:
                continue
            constexpr_value = self._try_eval_constexpr_binary_operation_expr(
                left_widened, right, operation
            )
            return BinaryOperationExprNode(
                left_widened,
                right,
                expr.operator,
                operation,
                self.lower_vl_type(operation.result_type),
                constexpr_value,
                expr.position_info,
            )

        self.add_diagnostic(
            "E104",
            f"Operator {format_operator(expr.operator)} "
            f"not supported between instances of {left.vl_type.to_vl_type_str()} "
            f"and {right.vl_type.to_vl_type_str()} (after attempted widening)",
            expr.position_info,
        )

    def lower_unary_operation_expr(
        self, expr: vl_ast.UnaryOperatorExprNode
    ) -> UnaryOperatorExprNode:
        operand = self.lower_expr(expr.operand)
        operator = expr.operator

        operation = [
            x
            for x in operand.vl_type.get_operations()
            if x.op_arity == "UNARY" and x.op_type == operator
        ]
        if not operation:
            self.add_diagnostic(
                "E104",
                f"Operator {format_operator(expr.operator)} "
                f"not supported for instance of {operand.vl_type.to_vl_type_str()}",
                expr.position_info,
            )
        elif len(operation) > 1:
            raise FatalCompileError(
                f"IE: Multiple operations found for '{operator}' with operand {operand.vl_type.to_vl_type_str()}"
            )
        operation = operation[0]

        # try constexpr eval
        if operand.constexpr_value and isinstance(operation, VlConstexprOperation):
            constexpr_value = operation.evaluate(operand.constexpr_value)
        else:
            constexpr_value = None

        return UnaryOperatorExprNode(
            operand,
            expr.operator,
            operation,
            self.lower_vl_type(operation.result_type),
            constexpr_value,
            expr.position_info,
        )

    def lower_constant_expr(self, expr: vl_ast.ConstantExprNode) -> ConstantExprNode:
        if isinstance(expr.value.value, int):
            value = VlInt(expr.value.value)
        elif isinstance(expr.value.value, bool):
            value = VlBool(expr.value.value)
        elif isinstance(expr.value.value, float):
            value = VlReal(expr.value.value)
        elif isinstance(expr.value.value, complex):
            value = VlComplex(expr.value.value)
        else:
            raise FatalCompileError(
                f"IE: Unknown constant expr value type {type(expr.value.value)}"
            )

        return ConstantExprNode(
            self.lower_vl_type(expr.value.type),
            value,
            expr.position_info,
        )

    def filter_fn_decl_attribute_tags(
        self, parsed_tags: dict, position_info: ASTPositionInfo
    ) -> dict:
        final_tags: dict[str, int] = {}
        for key, value in parsed_tags.items():
            if key == "generate_img":
                final_tags["generate_img"] = 1
            # elif...
            else:
                self.add_diagnostic(
                    "W020", f"Unknown attribute tag key: '{key}'", position_info
                )
        return final_tags

    def filter_fn_param_attribute_tags(
        self, parsed_tags: dict, position_info: ASTPositionInfo
    ) -> dict:
        final_tags: dict[str, int] = {}
        for key, value in parsed_tags.items():
            self.add_diagnostic(
                "W020", f"Unknown attribute tag key: '{key}'", position_info
            )
        return final_tags

    def lower_attribute_tags(self, node: vl_ast.AttributeTagsNode) -> dict:
        parsed_tags: dict = {}
        for tag in node.tags:
            if tag.key.name in parsed_tags:
                self.add_diagnostic(
                    "E211",
                    f"Attribute tag parsing error: duplicate key '{tag.key.name}'",
                    tag.position_info,
                )

            if not tag.values:
                parsed_tags[tag.key.name] = None
            else:
                tag_values = []
                for value in tag.values.values:
                    lowered_value = self.lower_expr(value)
                    if not isinstance(lowered_value, ConstantExprNode):
                        self.add_diagnostic(
                            "E211",
                            f"Attribute tag parsing error: value (for key '{tag.key.name}') must be a constant",
                            tag.position_info,
                        )
                        raise FatalCompileError
                    tag_values.append(lowered_value.value.underlying)
                parsed_tags[tag.key.name] = tag_values
        return parsed_tags

    def lookahead_function_decl(self, decl: vl_ast.FunctionDeclNode) -> None:
        """
        Lookahead to get information on builtin functions before they are actually lowered.
        """
        identifier = decl.identifier.name
        if identifier in self.userdef_functions:
            self.add_diagnostic(
                "E202",
                f"Function '{decl.identifier.name}' has already been declared",
                decl.position_info,
            )

        parameters: list[VlFnParamTypeProfile] = []
        attribute_tags: dict[str, int] = {}
        for idx, parameter in enumerate(decl.parameters.parameters):
            parameters.append(
                VlFnParamTypeProfile(
                    parameter.name.name, self.lower_vl_type(parameter.type.name)
                )
            )
            param_attribute_tags = self.filter_fn_param_attribute_tags(
                self.lower_attribute_tags(parameter.attribute_tags),
                parameter.position_info,
            )
            param_attribute_tags = {
                f"param_{idx}::{k}": v for k, v in param_attribute_tags.items()
            }
            attribute_tags.update(param_attribute_tags)

        return_type = self.lower_vl_type(decl.return_type.name)

        # Check for duplicate parameter identifiers
        parameters_counter = collections.Counter([x.identifier for x in parameters])
        has_duplicates = any([x > 1 for x in parameters_counter.values()])
        if has_duplicates:
            self.add_diagnostic(
                "E210",
                f"Duplicate parameter(s) '{', '.join([k for k, v in parameters_counter.items() if v > 1])}' "
                f"in declaration for function '{decl.identifier.name}'",
                decl.position_info,
            )

        userdef_fn_idx = len(self.userdef_functions)
        attribute_tags.update(
            self.filter_fn_decl_attribute_tags(
                self.lower_attribute_tags(decl.attribute_tags), decl.position_info
            )
        )

        self.userdef_functions[identifier] = VlUserdefFunctionProfile(
            identifier, userdef_fn_idx, parameters, return_type, attribute_tags, 0
        )

    def lower_function_decl(self, decl: vl_ast.FunctionDeclNode) -> FunctionDeclNode:
        if not self.in_global_scope():
            self.add_diagnostic(
                "E300", "Nested function declarations", decl.position_info
            )

        if decl.identifier.name not in self.userdef_functions:
            raise FatalCompileError(
                "IE: decl.identifier.name not in self.userdef_functions"
            )
        fn_data = self.userdef_functions[decl.identifier.name]
        attribute_tags = fn_data.attribute_tags
        identifier = fn_data.identifier
        parameters = fn_data.parameters
        return_type = fn_data.return_type

        self.scope_in_fn(
            identifier,
            return_type,
            decl.position_info,
        )
        for parameter in parameters:
            self.init_parameter(
                parameter.identifier,
                parameter.vl_type,
                decl.position_info,
            )
        stmts = self.lower_stmts(decl.stmts.stmts)
        self.scope_out_fn()

        if not isinstance(decl.stmts.stmts[-1], vl_ast.ReturnStmtNode):
            self.add_diagnostic(
                "E321",
                "No return statement at end of statement list in function",
                decl.stmts.stmts[-1].position_info,
            )

        return FunctionDeclNode(
            attribute_tags,
            identifier,
            parameters,
            return_type,
            stmts,
            decl.position_info,
        )

    def lower_data_decl(
        self,
        decl: (
            vl_ast.ConstantDeclNode | vl_ast.VariableDeclNode | vl_ast.ConstexprDeclNode
        ),
    ) -> DataDeclNode | None:
        identifier = decl.target.name
        vl_type = self.lower_vl_type(decl.vl_type.name)
        value_lowered = self.lower_expr(decl.value)
        if value_lowered.vl_type != vl_type:
            # Attempt a type widening cast
            value_widened = self.try_widen_cast_expr(
                value_lowered, vl_type.to_vl_type_str()
            )
            if value_widened:
                value_lowered = value_widened
            else:
                self.add_diagnostic(
                    "E100",
                    f"Data '{identifier}' is type {vl_type.to_vl_type_str()}, got "
                    f"{value_lowered.vl_type.to_vl_type_str()}",
                    decl.position_info,
                )

        if isinstance(decl, vl_ast.VariableDeclNode):
            vl_qualifier = "var"
            self.init_variable(identifier, vl_type, decl.position_info)

        elif isinstance(decl, vl_ast.ConstantDeclNode):
            if value_lowered.constexpr_value:
                vl_qualifier = "constexpr"
                self.add_diagnostic(
                    "X100",
                    f"Constant '{identifier}' could be declared as constexpr",
                    decl.position_info,
                )
                self.init_constexpr(
                    identifier, value_lowered.constexpr_value, decl.position_info
                )
            else:
                vl_qualifier = "const"
                self.init_constant(identifier, vl_type, decl.position_info)

        elif isinstance(decl, vl_ast.ConstexprDeclNode):
            if value_lowered.constexpr_value:
                vl_qualifier = "constexpr"
                self.init_constexpr(
                    decl.target.name, value_lowered.constexpr_value, decl.position_info
                )
            else:
                self.add_diagnostic(
                    "E101",
                    f"Assignment of non-constexpr expression to constexpr '{identifier}'",
                    decl.position_info,
                )
                raise FatalCompileError()

        else:
            raise FatalCompileError(f"IE: Unknown data decl type {type(decl)}")

        if vl_qualifier == "constexpr":
            # we have nothing to do with a constexpr
            return None

        return DataDeclNode(
            isinstance(decl, vl_ast.ConstantDeclNode),
            decl.target.name,
            self.lower_vl_type(decl.vl_type.name),
            value_lowered,
            decl.position_info,
        )

    def lower_using_decl(self, decl: vl_ast.UsingDeclNode) -> None:
        # namespace_identifiers: a list of namespaces that have been imported
        # scoped_identifiers: a list of tuples of (namespace, identifier) that have been imported
        namespace_identifiers: list[str]
        scoped_identifiers: list[tuple[str, str]]

        if decl.namespace_identifiers:
            namespace_identifiers = [
                x.name for x in decl.namespace_identifiers.identifiers
            ]
            scoped_identifiers = []
        elif decl.namespace_and_identifiers:
            namespace_identifiers = []
            namespace = decl.namespace_and_identifiers[0].name
            scoped_identifiers = [
                (namespace, x.name)
                for x in decl.namespace_and_identifiers[1].identifiers
            ]
        else:
            raise FatalCompileError("IE: empty using decl created by parser")

        if decl.namespace_identifiers and decl.namespace_and_identifiers:
            raise FatalCompileError(
                "IE: malformed using decl created by parser with both attrs"
            )

        # importing whole namespaces
        for namespace in namespace_identifiers:
            if namespace not in VlStdlib.namespaces:
                self.add_diagnostic(
                    "E400", f"Unresolved namespace '{namespace}'", decl.position_info
                )
                raise FatalCompileError()

            for fn in VlStdlib.namespaces[namespace].functions:
                fr_identifier = f"{namespace}::{fn.fn_name}"
                self.add_imported_function(fr_identifier, fn, decl.position_info)

            for ce in VlStdlib.namespaces[namespace].constexprs:
                fr_identifier = f"{namespace}::{ce.constexpr_name}"
                self.init_imported_constexpr(fr_identifier, ce, decl.position_info)

        # importing specific identifiers from namespaces
        is_wildcard = any(x[1] == "*" for x in scoped_identifiers)
        for namespace, identifier in scoped_identifiers:
            if namespace not in VlStdlib.namespaces:
                self.add_diagnostic(
                    "E400", f"Unresolved namespace '{namespace}'", decl.position_info
                )
                raise FatalCompileError()

            found = is_wildcard
            for fn in VlStdlib.namespaces[namespace].functions:
                if fn.fn_name != identifier and not is_wildcard:
                    continue
                self.add_imported_function(fn.fn_name, fn, decl.position_info)
                found = True

            for ce in VlStdlib.namespaces[namespace].constexprs:
                if ce.constexpr_name != identifier and not is_wildcard:
                    continue
                self.init_imported_constexpr(ce.constexpr_name, ce, decl.position_info)
                found = True

            if not found:
                self.add_diagnostic(
                    "E401",
                    f"Unresolved identifier '{identifier}' in namespace '{namespace}'",
                    decl.position_info,
                )
                raise FatalCompileError()

    def lower_assignment_stmt(self, stmt: vl_ast.AssignmentStmtNode) -> StmtNode | None:
        if isinstance(stmt.target, vl_ast.IdentifierNode):
            pass

        # TODO: add special handling for indexing and member access (lvalues)
        else:
            self.add_diagnostic(
                "E104",
                f"Assignment to non-lvalue, node type {type(stmt.target)}",
                stmt.position_info,
            )
            raise FatalCompileError()

        target_identifier = stmt.target.name
        value_lowered = self.lower_expr(stmt.value)

        identifier_data = self.resolve_lvalue_identifier(
            target_identifier, stmt.position_info
        )
        vl_type = identifier_data.vl_type
        vl_qualifier = identifier_data.vl_qualifier
        if vl_qualifier != "var":
            if identifier_data.is_parameter:
                hr_qualifier = vl_qualifier_to_hr(vl_qualifier).capitalize()
            else:
                hr_qualifier = "const parameter"
            self.add_diagnostic(
                "E102",
                f"Assignment to {hr_qualifier} '{target_identifier}' "
                f"after initialization",
                stmt.position_info,
            )

        if not value_lowered.vl_type == vl_type:
            # Attempt a type widening cast
            value_widened = self.try_widen_cast_expr(
                value_lowered, vl_type.to_vl_type_str()
            )
            if value_widened:
                value_lowered = value_widened
            else:
                self.add_diagnostic(
                    "E100",
                    f"Data '{stmt.target}' is type {vl_type.to_vl_type_str()}, got "
                    f"{value_lowered.vl_type.to_vl_type_str()}",
                    stmt.position_info,
                )

        # check for statements like 'x = x;'
        if (
            isinstance(stmt.value, vl_ast.IdentifierNode)
            and stmt.value.name == target_identifier
        ):
            self.add_diagnostic(
                "W014",
                f"Statement has no effect",
                stmt.position_info,
            )
            return

        return AssignmentStmtNode(target_identifier, value_lowered, stmt.position_info)

    def lower_augmented_assignment_stmt(
        self, stmt: vl_ast.AugmentedAssignmentStmtNode
    ) -> StmtNode:
        return self.lower_assignment_stmt(
            vl_ast.AssignmentStmtNode(
                stmt.target,
                vl_ast.BinaryOperationExprNode(
                    stmt.target,
                    stmt.value,
                    augmented_assignment_operator_translation[stmt.operator],
                    stmt.position_info,
                ),
                stmt.position_info,
            )
        )

    def lower_selection_stack_stmt(
        self, stmts: list[vl_ast.StmtNode]
    ) -> SelectionStackStmt:
        if not stmts:
            raise FatalCompileError("Selection stack must not be empty")
        if not isinstance(stmts[0], vl_ast.IfStmtNode):
            raise FatalCompileError("Selection stack must stack with an if statement.")
        if not all(isinstance(x, vl_ast.ElseifStmtNode) for x in stmts[1:-1]):
            raise FatalCompileError(
                "Selection stack can only have elif statements in the middle."
            )
        if not isinstance(
            stmts[-1], (vl_ast.IfStmtNode, vl_ast.ElseifStmtNode, vl_ast.ElseStmtNode)
        ):
            raise FatalCompileError(
                "Selection stack must only consist of if, else if, or else statements."
            )

        has_else = isinstance(stmts[-1], vl_ast.ElseStmtNode)
        if has_else and len(stmts) == 1:
            self.add_diagnostic(
                "E331",
                f"Use of `else` statement not in an `if-elseif-else` stack",
                stmts[0].position_info,
            )

        # noinspection PyTypeChecker
        conditioned: list[vl_ast.IfStmtNode] = stmts[:-1] if has_else else stmts
        blocks = []
        for block in conditioned:
            self.scope_in_selection(
                "elseif" if isinstance(block, vl_ast.ElseifStmtNode) else "if",
                block.position_info,
            )
            blocks.append(
                SelectionBlock(
                    self.lower_expr(block.condition),
                    self.lower_stmts(block.stmts.stmts),
                )
            )
            self.scope_out_selection()

        if has_else:
            else_stmt = stmts[-1]
            if not isinstance(else_stmt, vl_ast.ElseStmtNode):
                raise FatalCompileError(
                    "IE: Unreachable, already checked else_stmt was a ElseStmtNode"
                )
            self.scope_in_selection("else", else_stmt.position_info)
            else_stmts = self.lower_stmts(else_stmt.stmts.stmts)
            self.scope_out_selection()

        else:
            else_stmts = None

        return SelectionStackStmt(blocks, else_stmts, stmts[0].position_info)

    def lower_ranged_for_stmt(self, stmt: vl_ast.ForStmtNode) -> RangedForStmtNode:
        identifier = stmt.init_stmt.target.name
        vl_type_str = stmt.init_stmt.init_type.name
        range_node = stmt.init_stmt.value
        if not isinstance(range_node, vl_ast.RangeLiteralExprNode):
            raise FatalCompileError(
                "IE: For loops only work when iterating through a range literal"
            )
        if vl_type_str != "int":
            raise FatalCompileError(
                "IE: For loops only work for integer indices FIXME!"
            )

        # lower stmts with updated loop context
        self.scope_in_loop("for", stmt.position_info)
        self.init_loop_var(
            identifier, self.lower_vl_type(vl_type_str), stmt.position_info
        )
        stmts_lowered = self.lower_stmts(stmt.stmts.stmts)
        self.scope_out_loop()

        start = self.lower_expr(range_node.start)
        end = self.lower_expr(range_node.end)
        step = self.lower_expr(range_node.step)
        for val_name, val in [("start", start), ("end", end), ("step", step)]:
            if val.vl_type != VlInt:
                self.add_diagnostic(
                    "E123",
                    f"for statement range literal {val_name} must be an int",
                    range_node.start.position_info,
                )

        if start.constexpr_value and end.constexpr_value:
            is_ascending = (
                start.constexpr_value.underlying <= end.constexpr_value.underlying
            )
        elif step.constexpr_value:
            is_ascending = step.constexpr_value.underlying >= 0
        else:
            self.add_diagnostic(
                "E123",
                f"for statement range literal must either be start:stop:constexpr_step "
                f"or constexpr_start:constexpr_stop:step",
                range_node.start.position_info,
            )
            # non-fatal because we don't need to know asc/desc until bytecode emission
            is_ascending = True

        return RangedForStmtNode(
            identifier,
            self.lower_vl_type(stmt.init_stmt.init_type.name),
            start,
            end,
            step,
            is_ascending,
            stmts_lowered,
            stmt.position_info,
        )

    def lower_while_stmt(self, stmt: vl_ast.WhileStmtNode) -> WhileStmtNode:
        condition_lowered = self.lower_expr(stmt.condition)
        if condition_lowered.vl_type.to_vl_type_str() != "bool":
            self.add_diagnostic(
                "E122",
                f"while statement condition should be type bool, "
                f"got type '{condition_lowered.vl_type.to_vl_type_str()}'",
                stmt.position_info,
            )

        # lower stmts with updated loop context
        self.scope_in_loop("while", stmt.position_info)
        stmts_lowered = self.lower_stmts(stmt.stmts.stmts)
        self.scope_out_loop()

        return WhileStmtNode(
            condition_lowered,
            stmts_lowered,
            stmt.position_info,
        )

    def lower_break_stmt(self, stmt: vl_ast.BreakStmtNode) -> BreakStmtNode:
        if not self.check_in_loop_scope():
            self.add_diagnostic(
                "E310",
                "Use of break statement outside of loop",
                stmt.position_info,
            )
        return BreakStmtNode(stmt.position_info)

    def lower_continue_stmt(self, stmt: vl_ast.ContinueStmtNode) -> ContinueStmtNode:
        if not self.check_in_loop_scope():
            self.add_diagnostic(
                "E311",
                "Use of break statement outside of loop",
                stmt.position_info,
            )
        return ContinueStmtNode(stmt.position_info)

    def lower_return_stmt(self, stmt: vl_ast.ReturnStmtNode) -> ReturnStmtNode:
        ret_type_or_none = self.check_in_fn_scope()
        if not ret_type_or_none:
            self.add_diagnostic(
                "E320",
                "Use of return statement outside of function",
                stmt.position_info,
            )
        expr_lowered = self.lower_expr(stmt.value)
        if expr_lowered.vl_type != ret_type_or_none:
            self.add_diagnostic(
                "E112",
                f"Expected return type of '{ret_type_or_none.to_vl_type_str()}', "
                f"got type '{expr_lowered.vl_type.to_vl_type_str()}'",
                stmt.position_info,
            )
        return ReturnStmtNode(self.lower_expr(stmt.value), stmt.position_info)

    def lower_expr_stmt(self, stmt: vl_ast.ExprStmtNode) -> ExprStmtNode:
        if not isinstance(stmt.expr, vl_ast.FunctionCallExprNode):
            self.add_diagnostic(
                "W013", "Expression statement has no effect", stmt.position_info
            )
        return ExprStmtNode(self.lower_expr(stmt.expr), stmt.position_info)

    def lower_stmts(self, stmts: list[vl_ast.StmtNode]) -> list[StmtNode]:
        out_stmts: list[StmtNode] = []
        selection_stmts = []

        has_return = False
        has_break = False
        has_continue = False
        emitted_unreachable_diagnostic = False

        for stmt in stmts:
            for has_x, x_str, x_code in [
                (has_return, "return", "W010"),
                (has_break, "break", "W011"),
                (has_continue, "continue", "W012"),
            ]:
                if has_x and not emitted_unreachable_diagnostic:
                    x_code: DiagnosticCode
                    self.add_diagnostic(
                        x_code,
                        f"Unreachable code after {x_str} statement",
                        stmt.position_info,
                    )
                    # to suppress further unreachable code diagnostics
                    emitted_unreachable_diagnostic = False

            # first, handle selection statements (because ordering matters)
            if isinstance(stmt, vl_ast.ElseifStmtNode):
                selection_stmts.append(stmt)
                continue

            if isinstance(stmt, vl_ast.ElseStmtNode):
                if selection_stmts and isinstance(
                    selection_stmts[-1], vl_ast.ElseStmtNode
                ):
                    self.add_diagnostic(
                        "E331",
                        f"Use of `else` statement not in an `if-elseif-else` stack",
                        stmt.position_info,
                    )
                selection_stmts.append(stmt)
                continue

            if selection_stmts:
                out_stmts.append(self.lower_selection_stack_stmt(selection_stmts))
                selection_stmts = []

            if isinstance(stmt, vl_ast.IfStmtNode):
                selection_stmts.append(stmt)
                continue

            # handle other statements now
            if isinstance(stmt, vl_ast.DeclNode):
                stmt_lowered = self.lower_decl(stmt)

            elif isinstance(stmt, vl_ast.AssignmentStmtNode):
                stmt_lowered = self.lower_assignment_stmt(stmt)

            elif isinstance(stmt, vl_ast.AugmentedAssignmentStmtNode):
                stmt_lowered = self.lower_augmented_assignment_stmt(stmt)

            elif isinstance(stmt, vl_ast.ForStmtNode):
                stmt_lowered = self.lower_ranged_for_stmt(stmt)

            elif isinstance(stmt, vl_ast.WhileStmtNode):
                stmt_lowered = self.lower_while_stmt(stmt)

            elif isinstance(stmt, vl_ast.BreakStmtNode):
                stmt_lowered = self.lower_break_stmt(stmt)
                has_break = True

            elif isinstance(stmt, vl_ast.ContinueStmtNode):
                stmt_lowered = self.lower_continue_stmt(stmt)
                has_continue = True

            elif isinstance(stmt, vl_ast.ReturnStmtNode):
                stmt_lowered = self.lower_return_stmt(stmt)
                has_return = True

            elif isinstance(stmt, vl_ast.ExprStmtNode):
                stmt_lowered = self.lower_expr_stmt(stmt)

            elif isinstance(stmt, vl_ast.CommentNode):
                stmt_lowered = None

            else:
                raise FatalCompileError(f"IE: Unknown stmt type '{type(stmt)}'")

            if stmt_lowered:
                out_stmts.append(stmt_lowered)

        # if there are still selection statements left over
        if selection_stmts:
            out_stmts.append(self.lower_selection_stack_stmt(selection_stmts))
        return out_stmts

    def lower_decl(self, decl: vl_ast.DeclNode) -> DeclNode | None:
        if isinstance(decl, vl_ast.UsingDeclNode):
            return self.lower_using_decl(decl)
        elif isinstance(decl, vl_ast.FunctionDeclNode):
            return self.lower_function_decl(decl)
        elif isinstance(
            decl,
            (
                vl_ast.VariableDeclNode,
                vl_ast.ConstantDeclNode,
                vl_ast.ConstexprDeclNode,
            ),
        ):
            return self.lower_data_decl(decl)
        else:
            raise FatalCompileError(f"IE: Unknown decl type '{type(decl)}'")

    def lower_expr(self, expr: vl_ast.ExprNode) -> ExprNode:
        """Only to be called on rvalue exprs"""
        if isinstance(expr, vl_ast.IdentifierNode):
            expr_lowered = self.lower_identifier_expr(expr)
        elif isinstance(expr, vl_ast.ScopedIdentifierNode):
            expr_lowered = self.lower_scoped_identifier_expr(expr)
        elif isinstance(expr, vl_ast.ArrayLiteralExprNode):
            expr_lowered = self.lower_array_literal_expr(expr)
        elif isinstance(expr, vl_ast.MemberAccessExprNode):
            expr_lowered = self.lower_rvalue_member_access_expr(expr)
        elif isinstance(expr, vl_ast.IndexExprNode):
            expr_lowered = self.lower_rvalue_index_expr(expr)
        elif isinstance(expr, vl_ast.FunctionCallExprNode):
            expr_lowered = self.lower_function_call_expr(expr)
        elif isinstance(expr, vl_ast.CastExprNode):
            expr_lowered = self.lower_cast_expr(expr)
        elif isinstance(expr, vl_ast.BinaryOperationExprNode):
            expr_lowered = self.lower_binary_operation_expr(expr)
        elif isinstance(expr, vl_ast.UnaryOperatorExprNode):
            expr_lowered = self.lower_unary_operation_expr(expr)
        elif isinstance(expr, vl_ast.ConstantExprNode):
            expr_lowered = self.lower_constant_expr(expr)
        else:
            raise FatalCompileError(f"IE: Unknown expr type '{type(expr)}'")

        # apply constant folding
        if expr_lowered.constexpr_value:
            return ConstantExprNode(
                expr_lowered.vl_type,
                expr_lowered.constexpr_value,
                expr_lowered.ast_position_info,
            )
        return expr_lowered


def lower(
    ast_node: vl_ast.ProgramNode, compiler_flags: CompilerFlags
) -> tuple[ProgramNode | None, list[Diagnostic]]:
    """
    Lowers an AST to a HIR, returning a tuple of:
    - a HIR ProgramNode or None
    - a list[Diagnostic]
    """
    lowerer = Lowerer(compiler_flags)
    return lowerer.lower(ast_node)
