import veclang.backend.bc_common.py as bc
from veclang.backend.bc_compiler.vl_instruction import OpcodeHRMap

from veclang.frontend.parser.vl_ast import ASTPositionInfo
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
    SelectionStackStmt,
    RangedForStmtNode,
    WhileStmtNode,
    ReturnStmtNode,
    BreakStmtNode,
    ContinueStmtNode,
)
from veclang.midend.vl_core import VlType, VlTypeABC, VlInt, VlNull
from veclang.midend.hir.vl_lowerer import GLOBAL_FN_NAME, VlQualifier

from veclang.backend.bc_compiler.vl_emitter_utils import (
    FunctionScope,
    FunctionSubScope,
    IdentifierData,
    int_to_1_byte,
    int_to_2_bytes,
)
from veclang.common import (
    LANGUAGE_VERSION_INT,
    Diagnostic,
    FatalCompileError,
    CompilerFlags,
)


class BytecodeEmitter:

    def __init__(self, compiler_flags: CompilerFlags):
        self.compiler_flags: CompilerFlags = compiler_flags

        self.instructions: list[bytes] = []
        self.constants: bytearray = bytearray()
        self.constant_offsets: dict[bytes, int] = {}

        self.scopes: list[FunctionScope] = [
            FunctionScope(
                GLOBAL_FN_NAME, ASTPositionInfo(0, 0), {}, 0, 0, [], [], VlNull
            )
        ]

        # some context attributes to keep track of state
        self.ctx_selection_block_end_updates: list[int]
        self.ctx_selection_stack_end_updates: list[int]

        self.functions: list[FunctionScope] = []

    def is_global_scope(self):
        return len(self.scopes) == 1

    def scope_in_fn(
        self,
        fn_name: str,
        ast_position_info: ASTPositionInfo,
        arg_types: list[VlType],
        return_type: VlType,
    ) -> None:
        for scope in self.scopes:
            if scope.fn_name != GLOBAL_FN_NAME:
                raise FatalCompileError("Cannot nest function declarations!")
        self.scopes.append(
            FunctionScope(
                fn_name,
                ast_position_info,
                {},
                0,
                self.next_instruction_offset(),
                [],
                arg_types,
                return_type,
            )
        )

    def scope_out_fn(self) -> None:
        if len(self.scopes) == 1:
            raise FatalCompileError("Cannot scope out of global scope!")
        if not self.scopes[-1].fn_name:
            raise FatalCompileError(
                "Mismatched scope: current scope is not a function scope"
            )
        self.functions.append(self.scopes.pop())

    def subscope_add_block_end_update(self, instruction_offset: int):
        self.scopes[-1].sub_scopes[-1].block_end_update_offsets.append(
            instruction_offset
        )

    def subscope_add_stack_end_update(self, instruction_offset: int):
        self.scopes[-1].sub_scopes[-1].stack_end_update_offsets.append(
            instruction_offset
        )

    @staticmethod
    def vl_type_or_val_to_type(vl_type_or_val: VlType | VlTypeABC) -> VlType:
        """Utility to get the Python type from a vl_type_or_val"""
        if isinstance(vl_type_or_val, type):
            # noinspection PyTypeChecker
            return vl_type_or_val
        return type(vl_type_or_val)

    def fn_add_data(
        self, qualifier: VlQualifier, identifier: str, vl_type: VlType
    ) -> int:
        scope = self.scopes[-1]
        data_offset = scope.data_offset_counter
        self.scopes[-1].data[identifier] = IdentifierData(
            qualifier, vl_type, data_offset
        )

        if self.compiler_flags.runtime_precision == 32:
            type_canonical_size = vl_type.get_info()[3][0]
        elif self.compiler_flags.runtime_precision == 64:
            type_canonical_size = vl_type.get_info()[3][1]
        else:
            raise FatalCompileError(
                f"IE: runtime precision set to {self.compiler_flags.runtime_precision}"
            )
        scope.data_offset_counter += type_canonical_size

        if scope.data_offset_counter > 65536:
            raise FatalCompileError(
                "IE: a Veclang function can have a maximum stack frame size of 65536 bytes"
            )

        return data_offset

    def last_instruction_offset(self) -> int:
        return len(self.instructions) - 1

    def next_instruction_offset(self) -> int:
        return len(self.instructions)

    def add_instruction(self, opcode_hr: str, *operands: bytes) -> int:
        if opcode_hr not in OpcodeHRMap:
            raise FatalCompileError(f"Unknown opcode '{opcode_hr}'")
        self.instructions.append(OpcodeHRMap[opcode_hr].pack(operands))
        return len(self.instructions) - 1

    def add_constant(self, constant_as_bytes: bytes) -> int:
        """
        If a constant is not already in the constant table, adds a constant to the constant table, returning the offset.
        Otherwise, returns the offset to the existing constant.
        """
        if constant_as_bytes in self.constant_offsets:
            return self.constant_offsets[constant_as_bytes]
        constant_offset = len(self.constants)
        self.constants.extend(constant_as_bytes)
        self.constant_offsets[constant_as_bytes] = constant_offset

        if len(self.constants) > 65536:
            raise FatalCompileError(
                "IE: a Veclang program can have a maximum constant table size of 65536 bytes"
            )
        return constant_offset

    def modify_instruction_16b(self, instruction_offset: int, arg_16b: int):
        current_instruction = self.instructions[instruction_offset]
        if current_instruction[0] not in [0x20, 0x21, 0x22]:
            raise FatalCompileError(
                "IE: modification of arg_16b for a non-JMP instruction"
            )
        self.instructions[instruction_offset] = current_instruction[
            :2
        ] + int_to_2_bytes(arg_16b)

    def check_instructions(self):
        """
        Performs basic sanity checks on instructions:
        - checks if any instructions have an offset of 0xFFFF
        """
        for instruction in self.instructions:
            opcode = instruction[0]
            if opcode in [0x20, 0x21, 0x22]:
                if instruction[2] == 0xFF and instruction[3] == 0xFF:
                    raise FatalCompileError("IE: instruction with unset offset")

    def emit_stmt(self, node: StmtNode) -> None:
        if isinstance(node, DeclNode):
            self.emit_decl(node)
        elif isinstance(node, AssignmentStmtNode):
            self.emit_assignment_stmt(node)
        elif isinstance(node, SelectionStackStmt):
            self.emit_selection_stack_stmt(node)
        elif isinstance(node, RangedForStmtNode):
            self.emit_ranged_for_stmt(node)
        elif isinstance(node, WhileStmtNode):
            self.emit_while_stmt(node)
        elif isinstance(node, ReturnStmtNode):
            self.emit_return_stmt(node)
        elif isinstance(node, BreakStmtNode):
            self.emit_break_stmt(node)
        elif isinstance(node, ContinueStmtNode):
            self.emit_continue_stmt(node)
        elif isinstance(node, ExprStmtNode):
            self.emit_expr_stmt(node)
        else:
            raise FatalCompileError(f"IE: Unknown stmt type {type(node)}")

    def emit_decl(self, node: DeclNode) -> None:
        if isinstance(node, FunctionDeclNode):
            self.emit_function_decl(node)
        elif isinstance(node, DataDeclNode):
            self.emit_data_decl(node)
        else:
            raise FatalCompileError(f"IE: Unknown decl type {type(node)}")

    def emit_expr(self, node: ExprNode) -> None:
        if isinstance(node, RvalueIdentifierExprNode):
            self.emit_rvalue_identifier_expr(node)
        elif isinstance(node, BuiltinFunctionCallExprNode):
            self.emit_builtin_function_call_expr(node)
        elif isinstance(node, UserdefFunctionCallExprNode):
            self.emit_userdef_function_call_expr(node)
        elif isinstance(node, BinaryOperationExprNode):
            self.emit_binary_operator_expr(node)
        elif isinstance(node, UnaryOperatorExprNode):
            self.emit_unary_operator_expr(node)
        elif isinstance(node, ConstantExprNode):
            self.emit_constant_expr(node)
        else:
            raise FatalCompileError(f"IE: Unknown expr type {type(node)}")

    def emit_rvalue_identifier_expr(self, node: RvalueIdentifierExprNode) -> None:
        identifier = node.identifier
        # it doesn't matter if we check globals or locals first
        # because locals cant shadow globals
        for scope in reversed(self.scopes):
            if identifier not in scope.data:
                continue
            identifier_data = scope.data[identifier]
            data_offset = identifier_data.data_offset
            vl_type = identifier_data.vl_type

            if scope.fn_name == GLOBAL_FN_NAME:
                instruction_prefix = "OP_GET_GLOBAL_"
            else:
                instruction_prefix = "OP_GET_LOCAL_"
            if vl_type.is_val():
                instruction = instruction_prefix + "VAL"
                self.add_instruction(instruction, int_to_2_bytes(data_offset))
            else:
                instruction = instruction_prefix + "OBJ"
                self.add_instruction(
                    instruction,
                    int_to_1_byte(vl_type.to_vl_type_code()),
                    int_to_2_bytes(data_offset),
                )
            return
        raise FatalCompileError(f"Unknown identifier '{identifier}'")

    def emit_builtin_function_call_expr(
        self, node: BuiltinFunctionCallExprNode
    ) -> None:
        # arguments are pushed onto the stack in order
        for argument in node.arguments:
            self.emit_expr(argument)
        self.add_instruction("OP_CALL_BUILTIN", int_to_2_bytes(node.callee_fn_id))

    def emit_userdef_function_call_expr(
        self, node: UserdefFunctionCallExprNode
    ) -> None:
        # arguments are pushed onto the stack in order
        for argument in node.arguments:
            self.emit_expr(argument)
        self.add_instruction("OP_CALL_USERDEF", int_to_2_bytes(node.callee_fn_idx))

    def emit_unary_operator_expr(self, node: UnaryOperatorExprNode) -> None:
        self.emit_expr(node.operand)
        self.add_instruction(node.operation.opcode_hr)

    def emit_binary_operator_expr(self, node: BinaryOperationExprNode) -> None:
        # post-order traversal
        self.emit_expr(node.right)
        self.emit_expr(node.left)
        self.add_instruction(node.operation.opcode_hr)

    def emit_constant_expr(self, node: ConstantExprNode) -> None:
        if self.compiler_flags.runtime_precision == 32:
            as_bytes = node.value.to_bytes_32()
        elif self.compiler_flags.runtime_precision == 64:
            as_bytes = node.value.to_bytes_64()
        else:
            raise FatalCompileError(
                f"IE: runtime precision set to {self.compiler_flags.runtime_precision}"
            )

        if node.value.to_vl_type_str() in {"int", "bool"} and len(as_bytes) == 2:
            # direct loading
            self.add_instruction("OP_CONSTANT_VAL_DIRECT", as_bytes)
            return

        # add to constant table
        constant_offset = self.add_constant(as_bytes)
        if node.vl_type.is_val():
            self.add_instruction(
                "OP_CONSTANT_VAL_TABLE", int_to_2_bytes(constant_offset)
            )
        else:
            self.add_instruction(
                "OP_CONSTANT_OBJ_TABLE",
                int_to_1_byte(node.vl_type.to_vl_type_code()),
                int_to_2_bytes(constant_offset),
            )

    def emit_function_decl(self, node: FunctionDeclNode) -> None:
        fn_identifier = node.identifier

        # pop arguments off the intermediate value stack and onto the call stack
        arg_types = [p.vl_type for p in node.parameters]
        return_type = node.return_type
        self.scope_in_fn(fn_identifier, node.ast_position_info, arg_types, return_type)
        for parameter in node.parameters:
            self.fn_add_data("const", parameter.identifier, parameter.vl_type)

        # arguments are evaluated in left-to-right order, so pop them off in reverse
        for parameter in reversed(node.parameters):
            if parameter.vl_type.is_val():
                self.add_instruction(
                    "OP_SET_LOCAL_VAL",
                    int_to_2_bytes(
                        self.scopes[-1].data[parameter.identifier].data_offset
                    ),
                )
            else:
                self.add_instruction(
                    "OP_SET_LOCAL_OBJ",
                    int_to_1_byte(parameter.vl_type.to_vl_type_code()),
                    int_to_2_bytes(
                        self.scopes[-1].data[parameter.identifier].data_offset
                    ),
                )

        # emit each statement
        for stmt in node.stmts:
            self.emit_stmt(stmt)
        self.scope_out_fn()

    def emit_data_decl(self, node: DataDeclNode):
        self.emit_expr(node.value)
        if node.constant:
            vl_qualifier: VlQualifier = "const"
        else:
            vl_qualifier: VlQualifier = "var"
        self.fn_add_data(vl_qualifier, node.target, node.vl_type)

        data_offset = self.scopes[-1].data[node.target].data_offset
        if len(self.scopes) == 1:
            instruction_pre = "OP_SET_GLOBAL_"
        else:
            instruction_pre = "OP_SET_LOCAL_"
        if node.vl_type.is_val():
            instruction = instruction_pre + "VAL"
            self.add_instruction(instruction, int_to_2_bytes(data_offset))
        else:
            instruction = instruction_pre + "OBJ"
            self.add_instruction(
                instruction,
                int_to_1_byte(node.vl_type.to_vl_type_code()),
                int_to_2_bytes(data_offset),
            )

    def try_emit_fast_inplace(self, node: AssignmentStmtNode) -> bool:
        """
        Emits a fast inplace instructions for statements like:
        - z = z + 1;
        - c = c - 1;
        """
        if not isinstance(node.value, BinaryOperationExprNode):
            return False
        if node.value.vl_type != VlInt:
            return False
        if node.value.operation.op_type not in {"PLUS", "MINUS"}:
            return False

        # find if either left or right is the same as target
        if (
            isinstance(node.value.left, RvalueIdentifierExprNode)
            and node.value.left.identifier == node.target
        ):
            delta = node.value.right
        elif (
            isinstance(node.value.right, RvalueIdentifierExprNode)
            and node.value.right.identifier == node.target
        ):
            delta = node.value.left
        else:
            # there has to be a common identifier
            return False

        if delta.vl_type != VlInt:
            return False

        if len(self.scopes) == 1:
            scope = "GLOBAL"
        else:
            scope = "LOCAL"
        if node.value.operation.op_type == "PLUS":
            op_name = "ADD"
        else:
            op_name = "SUB"

        if (
            delta.constexpr_value
            and isinstance(delta.constexpr_value, VlInt)
            and -128 < delta.constexpr_value.underlying < 127
            and op_name == "ADD"
        ):
            data_offset = self.scopes[-1].data[node.target].data_offset
            delta = delta.constexpr_value.to_byte()
            self.add_instruction(
                f"OP_FAST_{scope}_INT_INPLACE_ADD_DIRECT",
                delta,
                int_to_2_bytes(data_offset),
            )
            return True

        # slightly slower but we can still call the non-direct method
        self.emit_expr(delta)
        data_offset = self.scopes[-1].data[node.target].data_offset
        self.add_instruction(
            f"OP_FAST_{scope}_INT_INPLACE_{op_name}", int_to_2_bytes(data_offset)
        )
        return True

    def emit_assignment_stmt(self, node: AssignmentStmtNode):
        if self.try_emit_fast_inplace(node):
            return

        self.emit_expr(node.value)
        if len(self.scopes) == 1:
            instruction_pre = "OP_SET_GLOBAL_"
        else:
            instruction_pre = "OP_SET_LOCAL_"

        data_offset = self.scopes[-1].data[node.target].data_offset
        if self.scopes[-1].data[node.target].vl_type.is_val():
            instruction = instruction_pre + "VAL"
            self.add_instruction(instruction, int_to_2_bytes(data_offset))
        else:
            instruction = instruction_pre + "OBJ"
            vl_type_code = self.scopes[-1].data[node.target].vl_type.to_vl_type_code()
            self.add_instruction(
                instruction,
                int_to_1_byte(vl_type_code),
                int_to_2_bytes(data_offset),
            )

    def emit_selection_stack_stmt(self, node: SelectionStackStmt):
        block_end_updates = []
        stack_end_updates = []
        for block in node.blocks:
            for block_end_update in block_end_updates:
                self.modify_instruction_16b(
                    block_end_update, self.next_instruction_offset()
                )

            self.scopes[-1].sub_scopes.append(
                FunctionSubScope(
                    None,
                    "selection",
                    node.ast_position_info,
                    self.next_instruction_offset(),
                    [],
                    [],
                )
            )
            self.emit_expr(block.condition)
            self.add_instruction("OP_JMP_IF_FALSE", int_to_2_bytes(0xFFFF))
            self.subscope_add_stack_end_update(self.last_instruction_offset())
            self.emit_stmts(block.stmts)

            # no need to jump if there is just one if statement
            if len(node.blocks) != 1 or node.else_stmts:
                self.add_instruction("OP_JMP", int_to_2_bytes(0xFFFF))
                stack_end_updates.append(self.last_instruction_offset())

            subscope = self.scopes[-1].sub_scopes.pop()
            for stack_end_update in subscope.stack_end_update_offsets:
                self.modify_instruction_16b(
                    stack_end_update, self.next_instruction_offset()
                )

        if node.else_stmts:
            self.scopes[-1].sub_scopes.append(
                FunctionSubScope(
                    None,
                    "selection",
                    node.ast_position_info,
                    self.next_instruction_offset(),
                    [],
                    stack_end_updates,
                )
            )
            self.emit_stmts(node.else_stmts)

            self.scopes[-1].sub_scopes.pop()

        for stack_end_update in stack_end_updates:
            self.modify_instruction_16b(
                stack_end_update, self.next_instruction_offset()
            )

    def emit_ranged_for_stmt(self, node: RangedForStmtNode):
        block_end_updates = []

        self.fn_add_data("var", node.loop_var_identifier, node.loop_var_type)
        self.emit_expr(node.loop_var_start)
        if self.is_global_scope():
            # fortunately this is the only construct outside of initialisation that means
            # we have to find a place for a new variable
            set_val_instruction = "OP_SET_GLOBAL_VAL"
            get_val_instruction = "OP_GET_GLOBAL_VAL"
        else:
            set_val_instruction = "OP_SET_LOCAL_VAL"
            get_val_instruction = "OP_GET_LOCAL_VAL"

        self.add_instruction(
            set_val_instruction,
            int_to_2_bytes(self.scopes[-1].data[node.loop_var_identifier].data_offset),
        )
        loop_start_offset = self.next_instruction_offset()

        self.emit_expr(node.loop_var_end)
        self.add_instruction(
            get_val_instruction,
            int_to_2_bytes(self.scopes[-1].data[node.loop_var_identifier].data_offset),
        )

        if node.loop_var_is_ascending:
            self.add_instruction("OP_INT_LESS")
        else:
            self.add_instruction("OP_INT_GREATER")

        self.add_instruction("OP_JMP_IF_FALSE", int_to_2_bytes(0xFFFF))
        block_end_updates.append(self.last_instruction_offset())

        self.scopes[-1].sub_scopes.append(
            FunctionSubScope(
                "for",
                None,
                node.ast_position_info,
                loop_start_offset,
                block_end_updates,
                [],
            )
        )
        self.emit_stmts(node.stmts)
        self.emit_assignment_stmt(
            AssignmentStmtNode(
                node.loop_var_identifier,
                BinaryOperationExprNode(
                    RvalueIdentifierExprNode(
                        node.loop_var_identifier,
                        node.loop_var_type,
                        None,
                        node.ast_position_info,
                    ),
                    node.loop_var_step,
                    "PLUS",
                    VlInt.get_operations()[6],
                    node.loop_var_type,
                    None,
                    node.ast_position_info,
                ),
                node.ast_position_info,
            )
        )
        self.add_instruction("OP_JMP", int_to_2_bytes(loop_start_offset))

        subscope = self.scopes[-1].sub_scopes.pop()
        for block_end_update in subscope.block_end_update_offsets:
            self.modify_instruction_16b(
                block_end_update, self.next_instruction_offset()
            )

    def emit_while_stmt(self, node: WhileStmtNode):
        block_end_updates = []

        loop_start_offset = self.next_instruction_offset()
        self.emit_expr(node.condition)
        self.add_instruction("OP_JMP_IF_FALSE", int_to_2_bytes(0xFFFF))
        block_end_updates.append(self.last_instruction_offset())

        self.scopes[-1].sub_scopes.append(
            FunctionSubScope(
                "while",
                None,
                node.ast_position_info,
                loop_start_offset,
                block_end_updates,
                [],
            )
        )
        self.emit_stmts(node.stmts)
        self.add_instruction("OP_JMP", int_to_2_bytes(loop_start_offset))

        subscope = self.scopes[-1].sub_scopes.pop()
        for block_end_update in subscope.block_end_update_offsets:
            self.modify_instruction_16b(
                block_end_update, self.next_instruction_offset()
            )

    def emit_return_stmt(self, node: ReturnStmtNode):
        if self.scopes[-1].fn_name == GLOBAL_FN_NAME:
            raise FatalCompileError(
                "IE: Already checked that return was inside function"
            )
        self.emit_expr(node.value)
        self.add_instruction("OP_RETURN")

    def emit_break_stmt(self, _node: BreakStmtNode):
        for subscope in reversed(self.scopes[-1].sub_scopes):
            if subscope.loop_name:
                self.add_instruction("OP_JMP", int_to_2_bytes(0xFFFF))
                subscope.block_end_update_offsets.append(self.last_instruction_offset())
                return
        else:
            raise FatalCompileError("IE: Already checked in loop scope")

    def emit_continue_stmt(self, _node: ContinueStmtNode):
        for subscope in reversed(self.scopes[-1].sub_scopes):
            if subscope.loop_name:
                self.add_instruction(
                    "OP_JMP", int_to_2_bytes(subscope.instruction_offset)
                )
                return
        else:
            raise FatalCompileError("IE: Already checked in loop scope")

    def emit_expr_stmt(self, node: ExprStmtNode):
        if isinstance(
            node.expr, (BuiltinFunctionCallExprNode, UserdefFunctionCallExprNode)
        ):
            self.emit_expr(node.expr)
            if node.expr.vl_type.is_val():
                self.add_instruction("OP_POP_VAL")
            else:
                self.add_instruction("OP_POP_OBJ")
        # dead code elimination: only a function call could produce a result

    def emit_stmts(self, stmts: list[StmtNode]) -> None:
        for stmt in stmts:
            self.emit_stmt(stmt)

    def emit(
        self, hir_node: ProgramNode
    ) -> tuple[bc.VlProgram | None, list[Diagnostic]]:
        """
        Emits bytecode from a HIR, returning a tuple of:
        - a VlProgram or None
        - a list[Diagnostic]
        """
        try:
            function_decls = [
                x for x in hir_node.stmts if isinstance(x, FunctionDeclNode)
            ]
            other_stmts = [
                x for x in hir_node.stmts if not isinstance(x, FunctionDeclNode)
            ]

            if function_decls:
                # add a JMP at the start to skip all the function code
                self.add_instruction("OP_JMP", int_to_2_bytes(0x0000))
                self.emit_stmts(function_decls)
                next_instruction_offset = self.next_instruction_offset()
                self.modify_instruction_16b(0x00, next_instruction_offset)

            self.emit_stmts(other_stmts)

            functions: list[bc.VlFunction] = []
            for function in self.functions:
                functions.append(
                    {
                        "name": function.fn_name if function.fn_name else "",
                        "stack_size": function.data_offset_counter,
                        "instruction_offset": function.instruction_offset,
                        "arg_types": [p.to_vl_type_code() for p in function.arg_types],
                        "return_type": function.return_type.to_vl_type_code(),
                    }
                )
            header: bc.VlHeader = {
                "magic": "VECL",
                "version": LANGUAGE_VERSION_INT,
                "flags": {"runtime_precision": self.compiler_flags.runtime_precision},
                "functions": functions,
                "globals_stack_size": self.scopes[0].data_offset_counter,
            }
            vl_program: bc.VlProgram = {
                "header": header,
                "constants": self.constants,
                "instructions": b"".join(self.instructions),
            }
            return vl_program, []

        except Exception as e:
            return None, [
                Diagnostic(0, 0, "E900", "<vl_global>", f"{e}"),
                Diagnostic(
                    0,
                    0,
                    "E900",
                    "<vl_global>",
                    f"The previous error that occurred during bytecode emission "
                    "was fatal and compilation has terminated.",
                ),
            ]


def emit(
    hir_node: ProgramNode, compiler_flags: CompilerFlags
) -> tuple[bc.VlProgram | None, list[Diagnostic]]:
    """
    Emits bytecode from a HIR, returning a tuple of:
    - a VlProgram or None
    - a list[Diagnostic]
    """
    emitter = BytecodeEmitter(compiler_flags)
    return emitter.emit(hir_node)
