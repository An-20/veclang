import dataclasses

from veclang.frontend.parser.vl_ast import ASTPositionInfo
from veclang.midend.vl_core import VlType, VlTypeABC


@dataclasses.dataclass
class Scope:
    fn_name: str | None
    ast_position_info: ASTPositionInfo

    # Tuple of [type_or_value, is_variable
    data: dict[str, tuple[VlType | VlTypeABC, bool]]
    ref_counts: dict[str, int]


class ScopeTracker:

    def __init__(self):
        # TODO: TRACK LOOP SCOPE (useful for tracking if break / continue used in loop)
        self.scopes: list[Scope] = [
            self.create_scope("vl::global", ASTPositionInfo(0, 0))
        ]

    @staticmethod
    def create_scope(
        scope_fn_name: str | None, ast_position_info: ASTPositionInfo
    ) -> Scope:
        return Scope(scope_fn_name, ast_position_info, {}, {})

    def scope_in(self, fn_name: str | None, ast_position_info: ASTPositionInfo) -> None:
        self.scopes.append(self.create_scope(fn_name, ast_position_info))

    def scope_out(self) -> None:
        if len(self.scopes) == 1:
            raise ValueError("Cannot scope out of global scope!")
        self.scopes.pop()

    def resolve(self, identifier: str) -> tuple[VlType | VlTypeABC, bool]:
        """
        Resolves a variable / constant, returning a tuple of:
        - VlType of the class of the variable / constant
        - VlTypeABC of the actual constant value, or None if is a variable
        :return:
        """
        for scope in reversed(self.scopes):
            if identifier in scope.data:
                scope.ref_counts[identifier] += 1
                type_or_value, is_variable = scope.data[identifier]
                return type_or_value, is_variable
        # FIXME
        raise ValueError(f"Could not resolve identifier `{identifier}`")

    def raise_if_identifier_declared(self, identifier: str):
        for parent_scope in reversed(self.scopes[:-1]):
            if identifier in parent_scope.data:
                type_or_value, is_variable = parent_scope.data[identifier]
                raise ValueError(
                    f"{'Variable' if is_variable else 'Constant'} `{identifier}` "
                    f"already declared in parent scope with ASTPositionInfo {parent_scope.ast_position_info}"
                )

        scope = self.scopes[-1]
        if identifier in scope.data:
            type_or_value, is_variable = scope.data[identifier]
            raise ValueError(
                f"{'Variable' if is_variable else 'Constant'} `{identifier}` already declared in this scope"
            )

    def init_variable(self, identifier: str, vl_type: VlType):
        self.raise_if_identifier_declared(identifier)
        scope = self.scopes[-1]
        scope.data[identifier] = (vl_type, True)
        scope.ref_counts[identifier] = 0

    def init_constant(self, identifier: str, vl_val: VlTypeABC):
        self.raise_if_identifier_declared(identifier)
        scope = self.scopes[-1]
        scope.data[identifier] = (vl_val, False)
        scope.ref_counts[identifier] = 0
