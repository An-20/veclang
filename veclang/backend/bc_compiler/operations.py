import abc
import dataclasses
import typing

UnaryOperationType = typing.Literal["BOOLEAN_NOT, BITWISE_NOT"]
UnaryOperationTypes = ["BOOLEAN_NOT, BITWISE_NOT"]

BinaryOperationType = typing.Literal["PLUS", "MINUS", "TIMES", "DIVIDE", "MODULUS"]


class OperationABC(abc.ABC):

    def __init__(self):
        pass
