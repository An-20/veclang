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

    def overload_profile(self) -> tuple:
        return tuple([self.fn_name] + [x.vl_type for x in self.fn_params])


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
        used_overload_profiles = set()

        for fn in self.functions:
            used_identifiers.add(fn.fn_name)
            if fn.overload_profile() in used_overload_profiles:
                raise ValueError(
                    f"IE: Function with overload profile '{fn.overload_profile()}' already declared"
                )
            used_overload_profiles.add(fn.overload_profile())

        for ce in self.constexprs:
            if ce.constexpr_name in used_identifiers:
                raise ValueError(
                    f"IE: identifier '{ce.constexpr_name}' already declared"
                )
            used_identifiers.add(ce.constexpr_name)

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

    def generate_docs(self) -> str:
        out_lines = []
        for ns, namespace in self.namespaces.items():
            out_lines.append(f"## {ns}")
            out_lines.append(f"{namespace.description}")

            if namespace.constexprs:
                out_lines.append(f"#### Constants")
                for constexpr in namespace.constexprs:
                    out_lines.append(
                        f"###### `{constexpr.constexpr_name}` (`{ns}::{constexpr.constexpr_name}`)"
                    )
                    out_lines.append(
                        f"`{constexpr.constexpr_name}: {constexpr.constexpr_value.to_vl_type_str()}`"
                    )
                    out_lines.append(f"`value: {constexpr.constexpr_value.underlying}`")
                    out_lines.append(f"{constexpr.constexpr_doc}\n")

            if namespace.functions:
                out_lines.append(f"#### Functions")
                for function in namespace.functions:
                    out_lines.append(
                        f"###### `{function.fn_name}` (`{ns}::{function.fn_name}`)"
                    )
                    # form function signature
                    out_lines.append(
                        f"`{function.fn_name}({', '.join([f'{x.name}: {x.vl_type}' for x in function.fn_params])})"
                        f" -> {function.fn_return_type}`"
                    )
                    out_lines.append(f"`builtin_idx: 0x{function.fn_id:02x}`")
                    out_lines.append(f"{function.fn_doc}\n")

        return "\n".join(out_lines)
