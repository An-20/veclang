import dataclasses

from veclang.backend.bc_compiler.instruction import OpcodeHRMap

from veclang.midend.vl_hir import (
    ExprNode,
    StmtNode,
    DeclNode,
    ProgramNode,
    IdentifierExprNode,
    ArrayLiteralExprNode,
    MemberAccessExprNode,
    IndexExprNode,
    FunctionCallExprNode,
    BinaryOperationExprNode,
    UnaryOperatorExprNode,
    ConstantExprNode,
    AttributeTagsNode,
    FunctionDeclNode,
    DataDeclNode,
    UsingDeclNode,
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
from veclang.midend.vl_types import VlType, VlInt, VlReal

from veclang.backend.bc_compiler.emitter_util import int_to_1_byte, int_to_2_bytes


@dataclasses.dataclass
class VariableProfile:
    variable_offset: int
    vl_type: VlType


@dataclasses.dataclass
class FunctionProfile:
    instruction_offset: int
    stack_frame_locals_offset: int


class BytecodeEmitter:

    def __init__(self):
        self.instructions: list[bytes] = []
        self.constants: bytearray = bytearray()
        self.constant_offsets: dict[bytes, int] = {}

        self.global_variables: dict[str, VariableProfile] = {}
        self.global_constants: dict[str, ConstantExprNode] = {}
        self.functions: dict[str, FunctionProfile] = {}
        self.ctx_loop_offsets: list[int] = []
        self.ctx_stack_frame_local_variables: dict[str, VariableProfile] = {}
        self.ctx_stack_frame_local_constants: dict[str, ConstantExprNode] = {}
        self.ctx_stack_frame_locals_offset = 0

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

    def add_instruction(self, opcode_hr: str, *operands: bytes) -> None:
        if opcode_hr not in OpcodeHRMap:
            raise ValueError(f"Unknown opcode '{opcode_hr}'")
        self.instructions.append(OpcodeHRMap[opcode_hr].pack(operands))

    def emit_stmt(self, node: StmtNode) -> None:
        pass

    def emit_expr(self, node: ExprNode) -> None:
        if isinstance(node, IdentifierExprNode):
            self.emit_identifier_expr(node)
        elif isinstance(node, ArrayLiteralExprNode):
            pass
        elif isinstance(node, MemberAccessExprNode):
            pass
        elif isinstance(node, IndexExprNode):
            pass
        elif isinstance(node, FunctionCallExprNode):
            pass
        elif isinstance(node, BinaryOperationExprNode):
            pass
        elif isinstance(node, UnaryOperatorExprNode):
            pass
        elif isinstance(node, ConstantExprNode):
            pass

    def emit_identifier_expr(self, node: IdentifierExprNode) -> None:
        identifier = node.name
        # check global constants
        if identifier in self.global_constants:
            self.emit_constant_expr(self.global_constants[identifier])
            return

        # check global variables
        if identifier in self.global_variables:
            var_profile = self.global_variables[identifier]
            if var_profile.vl_type.is_val():
                instruction = "OP_GET_GLOBAL_VAL"
            else:
                instruction = "OP_GET_GLOBAL_OBJ"
            self.add_instruction(
                instruction, int_to_2_bytes(var_profile.variable_offset)
            )
            return

        # check local constants
        if identifier in self.ctx_stack_frame_local_constants:
            self.emit_constant_expr(self.ctx_stack_frame_local_constants[identifier])
            return

        # check local variables
        if identifier in self.ctx_stack_frame_local_variables:
            var_profile = self.ctx_stack_frame_local_variables[identifier]
            if var_profile.vl_type.is_val():
                instruction = "OP_GET_LOCAL_VAL"
            else:
                instruction = "OP_GET_LOCAL_OBJ"
            self.add_instruction(
                instruction, int_to_2_bytes(var_profile.variable_offset)
            )
            return
        raise ValueError(f"Unknown identifier '{identifier}'")

    def emit_constant_expr(self, node: ConstantExprNode) -> None:
        as_bytes = node.to_bytes()
        if len(as_bytes) <= 2:
            # direct loading
            self.add_instruction("OP_CONSTANT_VAL_DIRECT", as_bytes)

        # TODO: implement

    def emit_function_decl_node(self, node: FunctionDeclNode) -> None:
        fn_identifier = node.identifier
        fn_instruction_offset = len(self.instructions)
        self.ctx_stack_frame_locals = {}
        self.ctx_stack_frame_locals_offset = 0

        # pop arguments off the intermediate value stack and onto the call stack
        for parameter in node.parameters:
            self.ctx_stack_frame_locals[parameter.name] = (
                self.ctx_stack_frame_locals_offset
            )
            self.ctx_stack_frame_locals_offset += parameter.vl_type.get_size()
            if parameter.vl_type in [VlInt, VlReal]:
                self.add_instruction(
                    "OP_SET_LOCAL_VAL",
                    self.ctx_stack_frame_locals[parameter.name].to_bytes().rjust(2),
                )

        # emit each statement
        for stmt in node.stmts:
            self.emit_stmt(stmt)

        fn_profile = FunctionProfile(
            fn_instruction_offset, self.ctx_stack_frame_locals_offset
        )
        self.functions[fn_identifier] = fn_profile
