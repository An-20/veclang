def int_to_1_byte(x: int) -> bytes:
    if x not in range(0x100):
        raise ValueError("Int must be in range(0x100)")
    return x.to_bytes(length=1)


def int_to_2_bytes(x: int) -> bytes:
    if x not in range(0x10000):
        raise ValueError("Int must be in range(0x10000)")
    return x.to_bytes(length=2).rjust(2, bytes(1))
