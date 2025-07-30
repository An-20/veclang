from veclang.utils.test_utils import get_test_file_path
from veclang.utils.cedf.cedf import SEDF


class ExampleSEDF(SEDF[str]):
    @staticmethod
    def get_sedf_id() -> int:
        return 0x0000_0001

    @staticmethod
    def check_header(header: dict) -> None:
        if "description" not in header:
            raise ValueError("Missing 'description' in header")

    @classmethod
    def serialise(cls, instance: str) -> tuple[dict, bytes]:
        header = {
            "description": "Test SEDF file",
            "length": len(instance),
        }
        payload = instance.encode("utf-8")
        return header, payload

    @classmethod
    def deserialise(cls, header: dict, payload: bytes) -> str:
        cls.check_header(header)
        return payload.decode("utf-8")


def test():
    test_path = get_test_file_path()

    # Create and write
    test_data = "Hello, world! This is a test."
    ExampleSEDF.dump(test_path, test_data)
    print(f"Wrote test file to {test_path}")

    # Load and verify
    loaded = ExampleSEDF.load(test_path)
    print("Read back:", loaded)

    assert loaded == test_data
    print("Round-trip successful")
