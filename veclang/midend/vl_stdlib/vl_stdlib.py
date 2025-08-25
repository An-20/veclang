from veclang.midend.vl_stdlib.core_stdlib import VlCoreStdlib
from veclang.midend.vl_stdlib.math_stdlib import VlMathStdlib
from veclang.midend.vl_stdlib.repl_stdlib import VlReplStdlib
from veclang.midend.vl_stdlib.vl_stdlib_types import Stdlib


VlStdlib = Stdlib([VlCoreStdlib, VlMathStdlib, VlReplStdlib])
