import dataclasses

from veclang.backend.bc_compiler.vl_instruction import OpcodeHRMap

from veclang.frontend.parser.vl_ast import ASTPositionInfo
from veclang.midend.hir.vl_hir import (
    HIRNode,
    ExprNode,
    StmtNode,
    DeclNode,
    ProgramNode,
    RvalueIdentifierExprNode,
    FunctionCallExprNode,
    BinaryOperationExprNode,
    UnaryOperatorExprNode,
    ConstantExprNode,
    FunctionDeclNode,
    DataDeclNode,
    AssignmentStmtNode,
    AugmentedAssignmentStmtNode,
    ExprStmtNode,
    SelectionStackStmt,
    RangedForStmtNode,
    WhileStmtNode,
    ReturnStmtNode,
    BreakStmtNode,
    ContinueStmtNode,
)
from veclang.midend.vl_core import VlType, VlTypeABC, VlNull, VlInt, VlReal, VlBool

from veclang.backend.bc_compiler.vl_emitter_utils import (
    int_to_1_byte,
    int_to_2_bytes,
)


@dataclasses.dataclass
class VariableProfile:
    variable_offset: int
    vl_type: VlType


@dataclasses.dataclass
class FunctionSubScope:
    loop_name: str | None
    selection_name: str | None
    ast_position_info: ASTPositionInfo

    instruction_offset: int


@dataclasses.dataclass
class FunctionScope:
    fn_name: str | None
    ast_position_info: ASTPositionInfo

    # Tuple of (type_or_value, is_variable, data_offset)
    data: dict[str, tuple[VlType | VlTypeABC, bool, int | None]]
    data_offset_counter: int
    instruction_offset: int

    sub_scopes: list[FunctionSubScope]


class BytecodeEmitter:

    def __init__(self):
        # TODO: add some function that checks the integrity of instructions
        # because by default we will set instruction pointers to 0xFFFF

        self.instructions: list[bytes] = []
        self.constants: bytearray = bytearray()
        self.constant_offsets: dict[bytes, int] = {}

        self.scopes: list[FunctionScope] = [
            FunctionScope("vl::global", ASTPositionInfo(0, 0), {}, 0, 0, [])
        ]

    def scope_in_fn(self, fn_name: str, ast_position_info: ASTPositionInfo) -> None:
        for scope in self.scopes:
            if scope.fn_name != "vl::global":
                raise ValueError("Cannot nest function declarations!")
        self.scopes.append(
            FunctionScope(fn_name, ast_position_info, {}, 0, len(self.instructions), [])
        )

    def scope_out_fn(self) -> None:
        if len(self.scopes) == 1:
            raise ValueError("Cannot scope out of global scope!")
        if not self.scopes[-1].fn_name:
            raise ValueError("Mismatched scope: current scope is not a function scope")
        self.scopes.pop()

    def fn_add_data(
        self, identifier: str, type_or_value: VlType | VlTypeABC, is_variable: bool
    ) -> int:
        scope = self.scopes[-1]
        data_offset = scope.data_offset_counter
        self.scopes[-1].data[identifier] = (type_or_value, is_variable, data_offset)
        # TODO: FIXME FOR 32 / 64
        scope.data_offset_counter += type_or_value.get_info()[3][0]
        return data_offset

    def add_instruction(self, opcode_hr: str, *operands: bytes) -> int:
        if opcode_hr not in OpcodeHRMap:
            raise ValueError(f"Unknown opcode '{opcode_hr}'")
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
        return constant_offset

    def modify_instruction_16b(self, instruction_offset: int, arg_16b: int):
        # TODO: loads more checking
        current_instruction = self.instructions[instruction_offset]
        self.instructions[instruction_offset] = (
            current_instruction[:2] + arg_16b.to_bytes()
        )

    def emit_stmt(self, node: StmtNode) -> None:
        if isinstance(node, DeclNode):
            self.emit_decl(node)
        elif isinstance(node, AssignmentStmtNode):
            self.emit_assignment_stmt(node)
        elif isinstance(node, AugmentedAssignmentStmtNode):
            self.emit_augmented_assignment_stmt(node)
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
            if isinstance(node.expr, FunctionCallExprNode):
                self.emit_expr(node.expr)
            # dead code elimination: only a function call could produce a result

    def emit_decl(self, node: DeclNode) -> None:
        if isinstance(node, FunctionDeclNode):
            self.emit_function_decl(node)
        elif isinstance(node, DataDeclNode):
            self.emit_data_decl(node)
        else:
            raise ValueError("TODO: Unknown decl type")

    def emit_expr(self, node: ExprNode) -> None:
        if isinstance(node, RvalueIdentifierExprNode):
            self.emit_rvalue_identifier_expr(node)
        elif isinstance(node, FunctionCallExprNode):
            self.emit_function_call_expr(node)
        elif isinstance(node, BinaryOperationExprNode):
            self.emit_binary_operator_expr(node)
        elif isinstance(node, UnaryOperatorExprNode):
            self.emit_unary_operator_expr(node)
        elif isinstance(node, ConstantExprNode):
            self.emit_constant_expr(node)
        else:
            raise ValueError

    def emit_rvalue_identifier_expr(self, node: RvalueIdentifierExprNode) -> None:
        identifier = node.identifier
        # it doesn't matter if we check globals or locals first
        # check globals
        for scope in reversed(self.scopes):
            if identifier not in scope.data:
                continue
            vl_type_or_val, is_variable, data_offset = scope.data[identifier]
            if not is_variable:
                self.emit_constant_expr(
                    ConstantExprNode(
                        vl_type_or_val,
                        True,
                        type(vl_type_or_val),
                        node.ast_position_info,
                    )
                )
                return

            # now process if is variable
            vl_type = vl_type_or_val
            if scope.fn_name == "vl::global":
                if vl_type.is_val():
                    instruction = "OP_GET_GLOBAL_VAL"
                else:
                    instruction = "OP_GET_GLOBAL_OBJ"
            else:
                if vl_type.is_val():
                    instruction = "OP_GET_LOCAL_VAL"
                else:
                    instruction = "OP_GET_LOCAL_OBJ"
            self.add_instruction(instruction, int_to_2_bytes(data_offset))
            return
        raise ValueError(f"Unknown identifier '{identifier}'")

    def emit_function_call_expr(self, node: FunctionCallExprNode) -> None:
        # arguments are pushed onto the stack in reverse order
        for argument in reversed(node.arguments):
            self.emit_expr(argument)
        self.add_instruction("OP_CALL", int_to_2_bytes(node.callee_fn_id))

    def emit_unary_operator_expr(self, node: UnaryOperatorExprNode) -> None:
        self.emit_expr(node.operand)
        self.add_instruction(node.operation.opcode_hr)

    def emit_binary_operator_expr(self, node: BinaryOperationExprNode) -> None:
        # post-order traversal
        self.emit_expr(node.right)
        self.emit_expr(node.left)
        self.add_instruction(node.operation.opcode_hr)

    def emit_constant_expr(self, node: ConstantExprNode) -> None:
        as_bytes = node.value.to_bytes_32()
        if node.value.to_vl_type_str() in {"int", "bool"} and len(as_bytes) <= 2:
            # direct loading
            self.add_instruction("OP_CONSTANT_VAL_DIRECT", as_bytes.rjust(2, bytes(1)))
            return

        # add to constant table
        constant_offset = self.add_constant(as_bytes)
        self.add_instruction("OP_CONSTANT_VAL_TABLE", int_to_2_bytes(constant_offset))

    def emit_function_decl(self, node: FunctionDeclNode) -> None:
        fn_identifier = node.identifier

        # pop arguments off the intermediate value stack and onto the call stack
        self.scope_in_fn(fn_identifier, node.ast_position_info)
        for parameter in node.parameters:
            self.fn_add_data(parameter.identifier, parameter.vl_type, True)

        # arguments are evaluated in left-to-right order, so pop them off in reverse
        for parameter in reversed(node.parameters):
            if parameter.vl_type.is_val():
                self.add_instruction(
                    "OP_SET_LOCAL_VAL",
                    int_to_2_bytes(self.scopes[-1].data[parameter.identifier][2]),
                )
            else:
                self.add_instruction(
                    "OP_SET_LOCAL_OBJ",
                    int_to_1_byte(parameter.vl_type.to_vl_type_code()),
                    int_to_2_bytes(self.scopes[-1].data[parameter.identifier][2]),
                )

        # emit each statement
        for stmt in node.stmts:
            self.emit_stmt(stmt)
        self.scope_out_fn()

    def emit_data_decl(self, node: DataDeclNode):
        is_variable = not node.constant
        self.emit_expr(node.value)
        self.fn_add_data(node.target, node.vl_type, is_variable)

        # TODO: bodge?
        data_offset = self.scopes[-1].data[node.target][2]
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

    def emit_assignment_stmt(self, node: AssignmentStmtNode):
        self.emit_expr(node.value)
        if len(self.scopes) == 1:
            instruction_pre = "OP_SET_GLOBAL_"
        else:
            instruction_pre = "OP_SET_LOCAL_"

        data_offset = self.scopes[-1].data[node.target][2]
        if self.scopes[-1].data[node.target][0].is_val():
            instruction = instruction_pre + "VAL"
            self.add_instruction(instruction, int_to_2_bytes(data_offset))
        else:
            instruction = instruction_pre + "OBJ"
            vl_type_code = self.scopes[-1].data[node.target][0].to_vl_type_code()
            self.add_instruction(
                instruction,
                int_to_1_byte(vl_type_code),
                int_to_2_bytes(data_offset),
            )

    def emit_augmented_assignment_stmt(self, node: AugmentedAssignmentStmtNode):
        pass

    def emit_selection_stack_stmt(self, node: SelectionStackStmt):
        pass

    def emit_ranged_for_stmt(self, node: RangedForStmtNode):
        pass

    def emit_while_stmt(self, node: WhileStmtNode):
        pass

    def emit_return_stmt(self, node: ReturnStmtNode):
        if self.scopes[-1].fn_name == "vl::global":
            raise ValueError("TODO: Can't return outside of function")
        self.emit_expr(node.value)
        self.add_instruction("OP_RETURN")

    def emit_break_stmt(self, node: BreakStmtNode):
        pass

    def emit_continue_stmt(self, node: ContinueStmtNode):
        pass

    def emit(self, hir_node: ProgramNode) -> list[bytes]:
        for stmt in hir_node.stmts:
            self.emit_stmt(stmt)
        return self.instructions
