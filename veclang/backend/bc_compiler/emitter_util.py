import struct

from veclang.frontend.parser.vl_ast import ConstantValue


def int_to_1_byte(x: int) -> bytes:
    if x not in range(256):
        raise ValueError("Int must be in range(256)")
    return x.to_bytes()


def int_to_2_bytes(x: int) -> bytes:
    if x not in range(65536):
        raise ValueError("Int must be in range(65536)")
    return x.to_bytes()


def constant_value_to_bytes(x: ConstantValue) -> bytes:
    # TODO: fix for 32 / 64 bit
    if isinstance(x, int):
        if 0 <= x <= 65535:
            return x.to_bytes()
        else:
            return x.to_bytes().rjust(4)
    elif isinstance(x, float):
        return bytes(struct.pack("!f", x))
    else:
        raise ValueError()
