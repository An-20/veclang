## Pipeline

There are three stages to the Veclang compilation pipeline:

- The **frontend**, where a Veclang program is lexed and parsed into an **abstract syntax tree** (AST).
- The **midend**, where the AST is lowered into a **high-level intermediate representation** (HIR). Additional checks are run at this stage, including code linting, analysis, and compiler plugins.
- The **backend**, where the HIR is compiled into a Veclang bytecode, which can then be interpreted.

###### Frontend

The Veclang compiler frontend uses a custom version of PLY (Python Lex-Yacc) to parse a Veclang program based on the Veclang grammar. The frontend parses the input into an AST.

###### Midend

The midend first lowers the AST to a tree-based HIR by recursively 'collapsing' parts of the AST. At the lowering stage, information on types, functions, imports, and identifiers is fully resolved. Then, the compiler performs pre-compilation checks with the linter. Compiler plugins run at the midend layer. A plugin is a stateful piece of code that is allowed to recursively process the HIR.

###### Backend

The backend compiles the HIR to bytecode, a linear instruction-based representation of a Veclang program that is run by the Veclang Interpreter.

# Veclang Interpreter

## Values and Objects

A Veclang program is capable of running with 32-bit or 64-bit integers and floating-point numbers. The **runtime precision** can thus be 32 or 64 bits.

A **value** is an `int`, `real`, `bool`, or `null`. A value takes up 4 or 8 bytes, depending on runtime precision.
An **object** is a `complex`, `matN`, or `vecN`, where $n \in \{2,3,4\}$. An object takes up 64 or 128 bytes, depending on runtime precision, when stored on the intermediate-value stack. An object only takes up as much memory as necessary when stored in the main stack memory, with no padding.

There are two intermediate-value stacks:

- The **value stack**, which has fixed offsets of either 4 or 8 bytes.
- The **object stack**, which has fixed offsets of either 64 or 128 bytes.

All values and objects stored in variables are in the stack memory.

All Veclang types have an associated **type code**, which are used in some object instructions for dynamic dispatch:

- VlInt=0x00
- VlBool=0x01
- VlReal=0x02
- VlComplex=0x03
- VlVec2=0x04
- VlVec3=0x05
- VlVec4=0x06
- VlMat2=0x07
- VlMat3=0x08
- VlMat4=0x09

The **canonical size** of a Veclang type is the number of bytes needed to represent it in its bytecode form.

## Lvalues and rvalues

In Veclang, all **expressions** can be treated as `rvalues`, which can be on the right-hand side of an assignment statement. However, only bare identifiers and some member access / index operations can be treated as `lvalues`, which are expressions on the left-hand side of an assignment statement that can actually be assigned to.

# Execution

Each stack frame can have a maximum of 65,536 bytes allocated for local stack variables (values and objects).

# Opcodes

## Overvew

There are three main types of instructions, classified by how they take operands:

- 0 operand instructions e.g. `OP_POP`.
- 1 operand instructions e.g. `OP_CONSTANT_VAL_TABLE`, that take 1 16-bit operand.
- 2 operand instructions e.g. `OP_VECTOR_ADD`, that take 1 8-bit operand and 1 16-bit operand.
  Each instruction consisting of opcode and operand(s) is stored as 4 bytes.

## 0x00 - 0x2F - Basic variable and constant manipulations

#### Constant loading

##### `0x00: OP_CONSTANT_VAL_DIRECT`

`OP_CONSTANT_VAL_DIRECT value_16b`
Loads a constant value directly, by directly pushing the operand `value` onto the value stack. This instruction only works for `int`s and `bool`s, interpreting `value` as the last 2 bytes of an otherwise zeroed 4 or 8 byte value.

##### `0x01: OP_CONSTANT_OBJ_DIRECT`

`OP_CONSTANT_OBJ_DIRECT type_8b value_16b`
Reserved instruction.
Constant objects are too large to store in `value`.

##### `0x02: OP_CONSTANT_VAL_TABLE`

`OP_CONSTANT_VAL_TABLE offset_16b`
Loads a constant value from the constant table at the given offset, by pushing the value at `offset` onto the value stack.

##### `0x03: OP_CONSTANT_OBJ_TABLE`

`OP_CONSTANT_OBJ_TABLE type_8b offset_16b`
Loads a constant object from the constant table at the given offset, by pushing the object at `offset` onto the object stack.

#### Stack manipulation

##### `0x04: OP_POP_VAL`

`OP_POP_VAL`
Pops a value off the top of the value stack.

##### `0x05: OP_POP_OBJ`

`OP_POP_OBJ`
Pops a value off the top of the object stack.

#### Function calls

##### `0x06: OP_CALL_BUILTIN`

`OP_CALL_BUILTIN builtin_id_16b`
Calls a builtin function. All arguments in Veclang must be evaluated in left-to-right order, therfore this operation will pop arguments off the value and object stacks in

##### `0x07: OP_CALL`

`OP_CALL_BUILTIN function_id_16b`
Calls a function. Unimplemented.

##### `0x08: OP_RETURN`

`OP_RETURN`
Returns from a function. Before this instruction is executed, the return value should be at the top of the object or value stacks.

#### Getting and setting values

##### `0x10: OP_GET_LOCAL_VAL`

`OP_GET_LOCAL_VAL offset_16b`
Gets the local value variable at `offset` and pushes the value onto the value stack.

##### `0x11: OP_SET_LOCAL_VAL`

`OP_SET_LOCAL_VAL offset_16b`
Pops a value off the top of the value stack and sets the local variable at `offset` to that value.

##### `0x12: OP_GET_GLOBAL_VAL`

`OP_GET_GLOBAL_VAL offset_16b`
Gets the global value variable at `offset` and pushes the value onto the value stack.

##### `0x13: OP_SET_GLOBAL_VAL`

`OP_SET_GLOBAL_VAL offset_16b`
Pops a value off the top of the value stack and sets the global variable at `offset` to that value.

##### `0x14: OP_GET_LOCAL_OBJ`

`OP_GET_LOCAL_OBJ type_8b offset_16b`
Gets the local object variable at `offset` with type `type` and pushes the object onto the object stack.

##### `0x15: OP_SET_LOCAL_OBJ`

`OP_SET_LOCAL_OBJ type_8b offset_16b`
Pops a value off the top of the object stack and sets the local variable at `offset` with type `type` to that object.

##### `0x16: OP_GET_GLOBAL_OBJ`

`OP_GET_GLOBAL_OBJ type_8b offset_16b`
Gets the global object variable at `offset` with type `type` and pushes the object onto the object stack.

##### `0x17: OP_SET_GLOBAL_OBJ`

`OP_SET_GLOBAL_OBJ type_8b offset_16b`
Pops a value off the top of the object stack and sets the global variable at `offset` with type `type` to that object.

#### Jumps

##### `0x20: OP_JMP`

`OP_JMP offset_16b`
Unconditionally jumps to the instruction at `offset`.

##### `0x21: OP_JMP_IF_TRUE`

`OP_JMP_IF_TRUE offset_16b`
Pops the top value off the value stack, and jumps to the instruction at `offset` if the value is non-zero.

##### `0x22: OP_JMP_IF_FALSE`

`OP_JMP_IF_FALSE offset_16b`
Pops the top value off the value stack, and jumps to the instruction at `offset` if the value is zero.

### 0x80 - 0x9F - Integer and Boolean Operations

​

```
enum VlOpcode : uint8 {
    OP_CONSTANT_VAL_DIRECT=0x00,
    OP_CONSTANT_OBJ_DIRECT=0x01,
    OP_CONSTANT_VAL_TABLE=0x02,
    OP_CONSTANT_OBJ_TABLE=0x03,
    OP_POP_VAL=0x04,
    OP_POP_OBJ=0x05,
    OP_CALL_BUILTIN=0x06,
    OP_CALL=0x07,
    OP_RETURN=0x08,

    OP_GET_LOCAL_VAL=0x10,
    OP_SET_LOCAL_VAL=0x11,
    OP_GET_GLOBAL_VAL=0x12,
    OP_SET_GLOBAL_VAL=0x13,
    OP_GET_LOCAL_OBJ=0x14,
    OP_SET_LOCAL_OBJ=0x15,
    OP_GET_GLOBAL_OBJ=0x16,
    OP_SET_GLOBAL_OBJ=0x17,

    OP_JMP=0x20,
    OP_JMP_IF_TRUE=0x20,
    OP_JMP_IF_FALSE=0x21,

    OP_INT_EQUAL=0x80,
    OP_INT_NOT_EQUAL=0x81,
    OP_INT_GREATER=0x82,
    OP_INT_GREATER_OR_EQUAL=0x83,
    OP_INT_LESS=0x84,
    OP_INT_LESS_OR_EQUAL=0x85,
    OP_INT_ADD=0x86,
    OP_INT_SUB=0x87,
    OP_INT_MUL=0x88,
    OP_INT_DIV=0x89,
    OP_INT_MOD=0x8A,
    OP_INT_EXP=0x8B,
    OP_INT_NEG=0x8C,
    OP_INT_AND=0x8D,
    OP_INT_OR=0x8E,
    OP_INT_XOR=0x8F,

    OP_INT_NOT=0x90,
    OP_INT_LEFT_SHIFT=0x91,
    OP_INT_RIGHT_SHIFT=0x92,
    OP_BOOLEAN_AND=0x9C,
    OP_BOOLEAN_OR=0x9D,
    OP_BOOLEAN_NOT=0x9E,

    OP_REAL_EQUAL=0xA0,
    OP_REAL_NOT_EQUAL=0xA1,
    OP_REAL_GREATER=0xA2,
    OP_REAL_GREATER_OR_EQUAL=0xA3,
    OP_REAL_LESS=0xA4,
    OP_REAL_LESS_OR_EQUAL=0xA5,
    OP_REAL_ADD=0xA6,
    OP_REAL_SUB=0xA7,
    OP_REAL_MUL=0xA8,
    OP_REAL_DIV=0xA9,
    OP_REAL_MOD=0xAA,
    OP_REAL_EXP=0xAB,
    OP_REAL_NEG=0xAC,

    OP_COMPLEX_EQUAL=0xB0,
    OP_COMPLEX_NOT_EQUAL=0xB1,
    OP_COMPLEX_ADD=0xB2,
    OP_COMPLEX_SUB=0xB3,
    OP_COMPLEX_MUL=0xB4,
    OP_COMPLEX_DIV=0xB5,
    OP_COMPLEX_EXP=0xB6,
    OP_COMPLEX_NEG=0xB7,

    OP_VECTOR_ADD=0xC0,
    OP_VECTOR_SUB=0xC1,
    OP_VECTOR_MUL=0xC2,
    OP_VECTOR_DIV=0xC3,
    OP_VECTOR_NEG=0xC4,
    OP_VECTOR_SCL=0xC5,
    OP_VECTOR_DOT=0xC6,
    OP_VECTOR_CRS=0xC7,
    OP_MATRIX_ADD=0xC8,
    OP_MATRIX_SUB=0xC9,
    OP_MATRIX_MUL=0xCA,
    OP_MATRIX_NEG=0xCB,
    OP_MATRIX_SCL=0xCC,
    OP_MATRIX_TRA=0xCD,
    OP_MATRIX_DET=0xCE,
    OP_MATRIX_INV=0xCF,
}
```

## Builtin Function ID Codes

Various elements of Veclang functionality are implemented by calling **builtin functions** (functions implemented in the interpreter's native language), either explicitly or implicitly:

- Builtin functions, e.g. `print`, `math::sin`
- Type casts, e.g. casting an `int` to a `real`, either explicit or implicit
- Type methods, e.g. constructing a `vec2` from 2 `real`s
- Type properties, e.g. the expr `complex_var.imag`

When the AST is lowered to a HIR, type casts, methods, and property calls are all converted into function call HIR nodes to simplify the compilation process.

`0x0000 - 0x0FFF` is used for builtin functions
`0x1000 - 0x1FFF` is used for builtin type methods and properties.

#### 0x1000 - 0x10FF: int methods and properties

`0x1000`: Cast an int to a real
`0x1001`: Cast an int to a complex

#### 0x1100 - 0x11FF: real methods and properties

`0x1100`: Cast a real to a complex

#### 0x1200 - 0x12FF: complex methods and properties

`0x1200`: Get the real part of a complex, returning a real.
`0x1200`: Get the real part of a complex, returning a real.

#### 0x1300 - 0x13FF: vec methods and properties

`0x1300`: Construct a vec2 from 2 reals
`0x1301`: Construct a vec3 from 3 reals
`0x1302`: Construct a vec4 from 4 reals

#### 0x1400 - 0x14FF: mat methods and properties

`python setup.py build_ext --inplace`
