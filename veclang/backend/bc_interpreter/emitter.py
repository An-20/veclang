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
from veclang.midend.vl_types import VlInt, VlReal


@dataclasses.dataclass
class FunctionProfile:
    instruction_offset: int
    stack_frame_locals_offset: int


class BytecodeEmitter:

    def __init__(self):
        self.instructions: list[bytes] = []
        self.constants: bytearray = bytearray()

        self.globals: dict[str, ConstantExprNode] = {}
        self.functions: dict[str, FunctionProfile] = {}
        self.ctx_loop_offsets: list[int] = []
        self.ctx_stack_frame_locals: dict[str, int] = {}
        self.ctx_stack_frame_locals_offset = 0

    def add_constant(self, constant_as_bytes: bytes) -> int:
        """Adds a constant to the constant table, returning the offset."""
        constant_offset = len(self.constants)
        self.constants.extend(constant_as_bytes)
        return constant_offset

    def add_instruction(self, opcode_hr: str, *operands: bytes) -> None:
        if opcode_hr not in OpcodeHRMap:
            raise ValueError(f"Unknown opcode '{opcode_hr}'")
        self.instructions.append(OpcodeHRMap[opcode_hr].pack(operands))

    def emit_stmt(self, node: StmtNode):
        pass

    def emit_expr(self, node: ExprNode):
        if isinstance(node, IdentifierExprNode):
            pass
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
        pass

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
            self.ctx_stack_frame_locals_offset += parameter._type.get_size()
            if parameter._type in [VlInt, VlReal]:
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
