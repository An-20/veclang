import dataclasses

from veclang.frontend.parser.vl_ast import ASTPositionInfo
from veclang.midend.vl_core import VlType
from veclang.midend.hir.vl_lowerer import VlQualifier


@dataclasses.dataclass
class FunctionSubScope:
    loop_name: str | None
    selection_name: str | None
    ast_position_info: ASTPositionInfo

    instruction_offset: int
    block_end_update_offsets: list[int]
    stack_end_update_offsets: list[int]


@dataclasses.dataclass
class IdentifierData:
    """
    We don't store constexprs because they've already been constant-folded.
    """

    vl_qualifier: VlQualifier
    vl_type: VlType
    data_offset: int


@dataclasses.dataclass
class FunctionScope:
    """
    Scope for a single function. Note how data can be tracked at a function level
    because unbound locals have already been checked at the HIR lowering stage.
    """

    fn_name: str | None
    ast_position_info: ASTPositionInfo

    data: dict[str, IdentifierData]
    data_offset_counter: int
    instruction_offset: int
    sub_scopes: list[FunctionSubScope]

    arg_types: list[VlType]
    return_type: VlType


def int_to_1_byte(x: int) -> bytes:
    if x not in range(0x100):
        raise ValueError("Int must be in range(0x100)")
    return x.to_bytes(length=1)


def int_to_2_bytes(x: int) -> bytes:
    if x not in range(0x10000):
        raise ValueError("Int must be in range(0x10000)")
    return x.to_bytes(length=2).rjust(2, bytes(1))
