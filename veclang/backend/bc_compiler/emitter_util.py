def int_to_1_byte(x: int) -> bytes:
    if x not in range(256):
        raise ValueError("Int must be in range(256)")
    return x.to_bytes()


def int_to_2_bytes(x: int) -> bytes:
    if x not in range(65536):
        raise ValueError("Int must be in range(65536)")
    return x.to_bytes()
