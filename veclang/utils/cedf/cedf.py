import abc
import dataclasses
import json
import struct
import typing


CEDF_MAGIC = b"CEDF"
CEDF_VERSION = 0x00_00_01_00
CEDF_HEADER_FORMAT = "<4sIIIQQ"
CEDF_HEADER_SIZE = struct.calcsize(CEDF_HEADER_FORMAT)

CEDF_HEADER_FIELDS = [
    ("magic", 4),
    ("version", 4),
    ("sedf_id", 4),
    ("flags", 4),
    ("json_length", 8),
    ("data_length", 8),
]


@dataclasses.dataclass
class CEDFHeader:
    magic: str
    version: int
    sedf_id: int
    flags: int
    json_length: int
    data_length: int


def encode_cedf_to_bytes(
    json_header: dict, binary_payload: bytes, sedf_id: int
) -> bytes:
    json_bytes = json.dumps(
        json_header, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    json_len = len(json_bytes)
    data_len = len(binary_payload)

    flags = 0x_00_00_00_00
    header = struct.pack(
        CEDF_HEADER_FORMAT,
        CEDF_MAGIC,
        CEDF_VERSION,
        sedf_id,
        flags,
        json_len,
        data_len,
    )
    return header + json_bytes + binary_payload


def decode_cedf_from_bytes(blob: bytes) -> tuple[CEDFHeader, dict, bytes]:
    """
    Decodes a CEDF file from bytes, returning a tuple of:
    - CEDFHeader
    - JSON header (dict)
    - Binary payload (bytes)
    """
    if len(blob) < CEDF_HEADER_SIZE:
        raise ValueError("File too short to contain valid CEDF header")

    header = blob[:CEDF_HEADER_SIZE]
    magic, version, sedf_id, flags, json_len, data_len = struct.unpack(
        CEDF_HEADER_FORMAT, header
    )
    cedf_header = CEDFHeader(magic, version, sedf_id, flags, json_len, data_len)

    if magic != CEDF_MAGIC:
        raise ValueError("Invalid CEDF magic")
    if version != CEDF_VERSION:
        raise ValueError(f"Unsupported CEDF version: {version:#08x}")
    if not isinstance(sedf_id, int):
        raise NotImplementedError

    json_start = CEDF_HEADER_SIZE
    json_end = json_start + json_len
    data_end = json_end + data_len

    if len(blob) != data_end:
        raise ValueError(
            f"Mismatched file length: expected {data_end}, got {len(blob)}"
        )

    json_bytes = blob[json_start:json_end]
    binary_payload = blob[json_end:data_end]

    json_header = json.loads(json_bytes.decode("utf-8"))
    if not isinstance(json_header, dict):
        raise ValueError("CEDF JSON header must be a top-level object")

    return cedf_header, json_header, binary_payload


T = typing.TypeVar("T")


class SEDF(abc.ABC, typing.Generic[T]):
    """
    A Specialised Everything Data Format (SEDF) class is a concrete
    implementation of a CEDF.

    The generic type T represents the Python type that the SEDF data represents.
    """

    @staticmethod
    @abc.abstractmethod
    def get_sedf_id() -> int:
        """Returns the SEDF ID as an integer"""

    @staticmethod
    @abc.abstractmethod
    def check_header(header: dict) -> None:
        """Checks the header, raising an exception if incorrectly formatted"""

    @classmethod
    @abc.abstractmethod
    def serialise(cls, instance: T) -> tuple[dict, bytes]:
        """
        Serialises an instance of T, returning a tuple of:
        - the JSON header data (dict)
        - the binary payload (bytes)
        """

    @classmethod
    @abc.abstractmethod
    def deserialise(cls, header: dict, payload: bytes) -> T:
        """
        Deserialises given an input of:
        - the JSON header data (dict)
        - the binary payload (bytes)
        Returning an instance of T.
        """

    @classmethod
    def dumpb(cls, instance: T) -> bytes:
        json_header, binary_payload = cls.serialise(instance)
        sedf_id = cls.get_sedf_id()
        return encode_cedf_to_bytes(json_header, binary_payload, sedf_id)

    @classmethod
    def loadb(cls, blob: bytes) -> T:
        cedf_header, json_header, binary_payload = decode_cedf_from_bytes(blob)
        if cedf_header.sedf_id != cls.get_sedf_id():
            raise ValueError(
                f"Expected SEDF ID '{cls.get_sedf_id()}', got '{cedf_header.sedf_id}'"
            )
        return cls.deserialise(json_header, binary_payload)

    @classmethod
    def dump(cls, fp: str, instance: T) -> None:
        blob = cls.dumpb(instance)
        with open(fp, "wb") as f:
            f.write(blob)

    @classmethod
    def load(cls, fp: str) -> T:
        with open(fp, "rb") as f:
            blob = f.read()
            return cls.loadb(blob)
