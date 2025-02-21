import dataclasses

from veclang.backend.bc_interpreter.instruction import OpcodeHRMap

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


@dataclasses.dataclass
class FunctionProfile:
    instruction_offset: int
    stack_frame_locals_offset: int


class BytecodeEmitter:

    def __init__(self):
        self.instructions: list[bytes] = []
        self.constants: bytearray = bytearray()

        self.functions: dict[str, FunctionProfile] = {}
        self.ctx_loop_offsets: list[int] = []

    def add_constant(self, constant_as_bytes: bytes) -> int:
        """Adds a constant to the constant table, returning the offset."""
        constant_offset = len(self.constants)
        self.constants.extend(constant_as_bytes)
        return constant_offset

    def add_instruction(self, opcode_hr: str, *operands: bytes) -> None:
        if opcode_hr not in OpcodeHRMap:
            raise ValueError(f"Unknown opcode '{opcode_hr}'")
        self.instructions.append(OpcodeHRMap[opcode_hr].pack(operands))

    def emit_stmts(self, stmts: list[StmtNode]):
        pass

    def emit_function_decl_node(self, node: FunctionDeclNode):
        pass
