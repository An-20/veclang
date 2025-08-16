import dataclasses

from veclang.midend.vl_core.vl_type import VlTypeStr, VlTypeABC


@dataclasses.dataclass
class StdlibFnParam:
    name: str
    vl_type: VlTypeStr


@dataclasses.dataclass
class StdlibFunction:
    fn_name: str
    fn_doc: str
    fn_params: list[StdlibFnParam]
    fn_return_type: VlTypeStr
    fn_id: int


@dataclasses.dataclass
class StdlibConstexpr:
    constexpr_name: str
    constexpr_doc: str
    constexpr_value: VlTypeABC


class StdlibNamespace:

    def __init__(
        self,
        namespace: str,
        description: str,
        functions: list[StdlibFunction],
        constexprs: list[StdlibConstexpr],
    ):
        self.namespace: str = namespace
        self.description: str = description
        self.functions: list[StdlibFunction] = functions
        self.constexprs: list[StdlibConstexpr] = constexprs
        self.check()

    def check(self) -> None:
        used_identifiers = set()
        identifiers = [x.fn_name for x in self.functions] + [
            x.constexpr_name for x in self.constexprs
        ]
        for identifier in identifiers:
            if identifier in used_identifiers:
                raise ValueError(
                    f"IE: identifier '{identifier}' declared multiple times in stdlib namespace '{self.namespace}'"
                )
            used_identifiers.add(identifier)

    def get_identifier(
        self, identifier: str
    ) -> StdlibFunction | StdlibConstexpr | None:
        for function in self.functions:
            if function.fn_name == identifier:
                return function
        for constexpr in self.constexprs:
            if constexpr.constexpr_name == identifier:
                return constexpr


class Stdlib:

    def __init__(self, namespaces: list[StdlibNamespace]):
        self.namespaces: dict[str, StdlibNamespace] = {
            x.namespace: x for x in namespaces
        }
        self.check()

    def check(self) -> None:
        used_fn_ids = set()
        fn_ids = sum(
            [[y.fn_id for y in x.functions] for x in self.namespaces.values()], []
        )
        for fn_id in fn_ids:
            if fn_id in used_fn_ids:
                raise ValueError(f"IE: fn id '{fn_id}' used multiple times in stdlib")
            used_fn_ids.add(fn_id)
