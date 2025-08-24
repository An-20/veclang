# Veclang Language
**Veclang** is an interpreted scripting language designed for high-performance numerical calculations. Veclang was originally developed for Aureus, but [VKSL LAB](https://lab.vksl.uk) shows how Veclang can be used as a scripting language in other contexts, e.g. for image generation.

Veclang code is compiled to Veclang bytecode by the compiler. Veclang bytecode is then run by the Veclang interpreter. There are different interpreters for different platforms:
- **Veclang for x86**, or `bc_interpreter` is the 'standard' Veclang interpreter implementation in C++, for running on desktop x86 platforms.
- **Veclang for Web** is a variant of `bc_interpreter` compiled to WebAssembly using Emscripten (and is the interpreter used in VKSL LAB).
- **Veclang for CUDA**, or `cu_interpreter` is a interpreter designed for running Veclang code simultaneously across many GPU cores. It has very little code in common with `bc_interpreter`, and is still in development.

## Variables, constants, and constexpr
There are three type qualifiers in Veclang:
- `var`: a variable value
- `const`: a constant value that can not have its value modified after initialisation
- `constexpr`: a constant value that can be evaluated at compile time.
Collectively, `var`s, `const`s, and `constexpr`s are referred to throughout Veclang documentation as 'data'.

**Variables** (`var`) are defined with the `let` keyword, which defines a new variable in the current local or global scope. Variables can only be accessed (read or written to) in the same local scope as their definition; i.e. global variables cannot be read or written to inside a function.

**Constants** (`const`) are defined with the `const` keyword, which creates a new constant in the current local or global scope. Constants cannot be written to after initialisation. When compiling with the `--strict` flag, reading global constants from within a function will raise an error (as constants can't necessarily be evaluated at compile time, only constexprs).

**Constexprs** (`constexpr`) are defined with the `constexpr` keyword, which creates a new constant in the current local or global scope. Constexprs are evaluated at compile-time using constant folding and placed into the bytecode's constant table (or direct loaded). Where a `const` data is actually `constexpr`, the compiler will automatically promote the `const` to a `constexpr`, allowing for constant folding, and also emit a weak warning.

## Types
A Veclang program is capable of running with 32-bit or 64-bit integers and floating-point numbers. The **runtime precision** can thus be 32 or 64 bits (this feature is a carryover from Veclang v1).

All types in Veclang are values or objects.
- A **value** is an `int`, `real`, `bool`, or `null`. A value takes up 4 or 8 bytes, depending on runtime precision.
- An **object** is a `complex`, `matN`, or `vecN`, where $n \in \{2,3,4\}$. An object takes up 64 or 128 bytes, depending on runtime precision, when stored on the intermediate-value stack. An object only takes up as much memory as necessary when stored in stack memory, with no padding.

Veclang types have an associated **type code**, which are used in some object instructions for dynamic dispatch (especially as the vector and matrix instructions are shared across all `vecN` and `matN`s):
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
VlNull does not have a type code as it is an internal compiler-only value. VlNull represents the return value of a function that does not have a useful return output. `null` cannot be assigned to a variable or 

The **canonical size** of a Veclang type is the least number of bytes needed to represent it (like a struct with zero padding). When data is stored in a constant table or in stack memory, it is always arranged contiguously.

All values in Veclang bytecode, including the constant table, and operands for instructions, are stored in little endian order.

#### Casts
Veclang has type casts with the `IntoType(val)` syntax. A type cast can either be a narrowing or widening conversion:
- A **narrowing** conversion causes data loss, e.g. a `real` to an `int`, and must always be performed explicitly.
- A **widening** conversion does not cause data loss (apart from potential floating-point imprecisions), e.g. a `real` to a `complex`. 

The compiler will attempt widening type casts when there are mismatched types in data initialisation, assignment, binary operations, or function arguments. In a binary operation `a OP b` where no suitable operator is found for the two types, the compiler will first try widening the type of `b`, then try widening the type of `a`.

#### Stacks
Veclang is a stack-based interpreted language, with operands and function parameters being pushed onto and popped off intermediate value stacks. There are two intermediate-value stacks:
- The **value stack**, which has elements of either 4 or 8 bytes.
- The **object stack**, which has elements of either 64 or 128 bytes.

**Stack memory** stores all variables used in a Veclang program. In stack memory, objects and values are stored contiguously, in order of definition in each stack frame, and in stack frames. There are two stacks:
- The **global stack**, which stores all global variables
- The **local stack**, which stores all local variables, organised in stack frames

The reason for this separation is so that globals can be easily added when using Veclang in a REPL or similar.

## Functions
Each Veclang function's **stack frame** can have a maximum of 65,536 bytes allocated for local stack variables (values and objects), as a result of the `offset` operand for instructions being 16 bytes. Similarly, a Veclang program can have a maximum of 65,536 bytes used for values in the constant table (across all global and local constexpr values). All Veclang functions must return some data.

When a Veclang function is called:
- The arguments are evaluated and pushed onto their respective stacks in the same order as the function declaration.
- The details of the function are retrieved and a stack frame is constructed with the correct locals size and return instruction pointer.
- The instruction pointer is set to the start of the function's instructions, transferring program flow to the function.
- The function's instructions begin by popping off the function's arguments, in reverse order of the function declaration's parameters.
- The function continues executing.
- The function pushes the return value to the top of the object or value stacks and calls `OP_RETURN`.
- The instruction pointer is set to the return instruction pointer value, and the top stack frame is popped.
- The result of the value is now at the top of the object or value stacks. If the function was called as a bare function (a `ExprStmt`), e.g. `print(42);`, then `OP_POP_VAL` or `OP_POP_OBJ` will be emitted by the compiler to ensure the return value is dealt with.

#### Attribute Tags
Functions in Veclang can be prefixed with attribute tags, and individual parameters can also be prefixed with attribute tags.

The values of attribute tags can only be 'simple literal' expressions. These are:
- Integer literals e.g. 0, 1, 2, 3, etc. Note that negative numbers are not integer literals, as they are actually unary operations.
- Boolean literals e.g. `true`, `false`
- String literals e.g. `"string"`
- Null literals e.g. `null`

#### Builtin Functions
Various elements of Veclang functionality are implemented by calling **builtin functions** (functions implemented in the interpreter's native language), either explicitly or implicitly:
- Builtin functions, e.g. `print`, `math::sin`
- Type casts, e.g. casting an `int` to a `real`, either explicit or implicit
- Type methods, e.g. constructing a `vec2` from 2 `real`s
- Type properties, e.g. the expr `complex_var.imag`

When the AST is lowered to a HIR, type casts, methods, and property calls are all converted into function call HIR nodes to simplify the compilation process.

#### User-defined Functions
User-defined functions are resolved at the HIR lowering stage. Function declarations are hoisted to the top of a Veclang program, and each function is assigned an index in declaration order before the HIR is properly lowered. This allows functions to call other functions which have not yet been declared, or call themselves. When the HIR is lowered, this `userdef_fn_idx` is stored and later emitted.

When a Veclang program is loaded into the interpreter, the interpreter creates a list of functions that acts as a lookup table, mapping a `userdef_fn_idx` to a tuple of `fn_instruction_offset` and `fn_stack_size`.

When a user-defined function is called, the `userdef_fn_idx` is looked up and the instruction offset and stack size are used to create a stack frame and jump to the necessary instructions.

## Veclang Grammar
Veclang has separation between expressions and statements:
- An **expression** evaluates to a value, including operations, function calls, type casts, etc. An expression is a **constexpr** expression if it can be evaluated at compile time; compound expressions are **constexpr** if all their children are also constexpr.
- A **statement** forms part of the program structure and does not evaluate to a value, including selection, loops, and declarations. Declarations are treated in Veclang as a subclass of statements that only belong in certain places.

#### Hoisting
Veclang only has two ways to pass data into a function:
- Through parameters
- Through global `constexpr`s. Global variables and constants cannot be accessed from within functions (for parallelisability).

When a Veclang program is compiled to bytecode, function bytecode is placed at the beginning of the bytecode. The exact order is:
- A JMP instruction to the end of all the function bytecode.
- For each function, the bytecode is emitted with all function bytecode placed contiguously.
- After all the function bytecode, the global bytecode.

Hoisting is where the order of statements in a Veclang program is reorganised during the HIR lowering stage. Statements are considered in the following order:
- 'Lookahead' on `using` and function declarations, in order of declaration. Lookahead on the `using` declarations is where the lowerer runs all imports ahead of actual lowering. Lookahead on function declaration is where the lowerer builds up an internal table of the declared functions and signatures, meaning when actual lowering takes place, functions can refer to other functions defined later in their own body (or refer to themselves). 
- All `using` declarations throughout the program are actually lowered. This results in no effect as all import resolution is done in lookahead.
- All global `constexpr` declarations are actually lowered.
- All function declarations throughout the program are actually lowered.

#### Lvalues and rvalues
In Veclang, all **expressions** can be treated as **rvalues**, which can be on the right-hand side of an assignment statement. However, only specific expressions can be treated as **lvalues**, which are expressions on the left-hand side of an assignment statement that can actually be assigned to:
- Bare identifiers that identify a piece of data (not a function)
- Member access expressions, e.g. `vector.x`
- Index expressions, e.g. `matrix[2, 3]`

Similarly, only certain expressions can be called:
- Bare identifiers that identify a function
- Member access expressions, e.g. `a.dot(b)`

In the HIR lowering process, all expressions must be a VlType. Thus, when lowering function calls (which can involve member access expression callees), there is separate logic, as Veclang does not have first-class functions. With the exception of member access and index operations, all other expression types can only ever be used as rvalues.
##### Member access expressions
A **member access expression** e.g. `a.b` is permitted to be used:  
- In a lvalue for assignment e.g. `vec2Instance.x = 15;`
- In a rvalue expression for calling a property and resolving to a VlType e.g. `complexInstance.real`
- In a rvalue expression for calling a method and resolving to a VlType e.g. `a.dot(b)`
##### Index expressions
An **index expression** e.g. `a[0]` or `b[1, 2]` is permitted to be used:
- In a lvalue for assignment e.g. `vec2Instance[0] = 15;`
- In a rvalue to resolve to a VlType e.g. `printr(a[0]);`

# Veclang Implementation
## Veclang Compiler
There are three stages to the Veclang compilation pipeline:
- The **frontend**, where a Veclang program is lexed and parsed into an **abstract syntax tree** (AST).
- The **midend**, where the AST is lowered into a **high-level intermediate representation** (HIR). Additional checks are run at this stage, including code linting, analysis, and compiler plugins.
- The **backend**, where the HIR is compiled into a Veclang bytecode, which can then be interpreted.

#### Compiler frontend
The Veclang compiler frontend uses a custom version of PLY (Python Lex-Yacc) to parse a Veclang program based on the Veclang grammar. The frontend lexes the input into a stream of tokens, which is parsed into an **AST** (abstract syntax tree), where every language feature has a different AST node class.

#### Compiler midend
The midend first lowers the AST to a tree-based **HIR** by recursively 'collapsing' parts of the AST. At the lowering stage, information on types, functions, imports, and identifiers is fully resolved, and stored in the produced HIR nodes.

Almost all non-syntax errors are typically emitted when the AST is lowered to a HIR. the **lowerer** performs type checking and general linting, producing **diagnostics** of three categories:
- **Errors**, which result in the program not lowering to a HIR, and thus not compiling
- **Warnings**, which do not prevent the program from being lowered
- **Weak warnings**, which are code-style issues that do not affect the program's functionality in any way.

#### Compiler backend
The backend compiles the HIR to bytecode, a linear instruction-based representation of a Veclang program that is run by the Veclang Interpreter. A Python VlProgram object is output, which contains a header, binary constants data, and binary instructions data. More information is below in the bytecode section.

## Bytecode
### Overview
There are three main types of instructions, classified by how they take operands:
- 0 operand instructions e.g. `OP_POP_VAL`.
- 1 operand instructions e.g. `OP_CONSTANT_VAL_TABLE`, that take 1 16-bit operand.
- 2 operand instructions e.g. `OP_VECTOR_ADD`, that take 1 8-bit operand and 1 16-bit operand.
Each instruction consisting of opcode and operand(s) is stored as 4 bytes. The operands are interpreted as unsigned 8 bit and 16 bit integers in little-endian order.

### Binary Representation
A VlProgram object contains:
- A JSON header with information about the program, including the functions, their instruction offsets, stack sizes, the global stack size, runtime flags, and attribute tags.
- Binary data representing the constants table.
- Binary data representing the bytecode instructions.

A VlProgram is serialised and deserialised to binary across language boundaries (e.g. when passed from Python compiler to C++ interpreter) by using the CEDF utility library (part of the Aureus project, found in `veclang/utils`). The CEDF ID for Veclang is `0x0001_0000 = 65536`. A outline of the JSON header is below.

###### VlHeader
- **magic** (`string`, must be `"VECL"`)
  Should always equal `"VECL"`.
- **version** (`integer`)
  Version number, typically `0x0002_0000 = 131072` for Veclang v2.
- **flags** (`object<string, integer>`)
  Dictionary of string keys to integer values.
- **functions** (`array<VlFunction>`)
  List of functions defined in this header.
- **globals_stack_size** (`integer`)
  Size of the global stack.

###### VlFunction
- **name** (`string`)  
  Function name.
- **stack_size** (`integer`)  
  Maximum stack size for this function.
- **instruction_offset** (`integer`)  
  Offset into the bytecode where the function starts.
- **arg_types** (`array<integer>`)  
  List of argument type identifiers.
- **return_type** (`integer`)  
  Return type identifier.
- **attribute_tags** (`object<string, integer>`)  
  Dictionary of string keys to integer values representing tags/attributes for the function.

# Bytecode Reference
### 0x00 - 0x2F - Basic variable and constant manipulations
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
Calls a builtin function.

##### `0x07: OP_CALL_USERDEF`
`OP_CALL_USERDEF function_idx_16b`
Calls a user-defined function. This instruction causes a new stack frame to be pushed and the instruction pointer to be set to the beginning of the function.

##### `0x08: OP_RETURN`
`OP_RETURN`
Returns from a function. Before this instruction is executed, the return value should be at the top of the object or value stacks. This instruction causes the instruction pointer to be set to the return address, and 

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

### 0x24 - 0x3F - Fast instructions
##### `0x24: OP_FAST_LOCAL_INT_INPLACE_ADD`
`OP_FAST_LOCAL_INT_INPLACE_ADD offset_16b`
Performs an inplace addition operation on the int at `offset` in the local stack, popping the top value off the value stack, and adding it to the int at `offset`.

##### `0x25: OP_FAST_LOCAL_INT_INPLACE_ADD_DIRECT`
`OP_FAST_LOCAL_INT_INPLACE_ADD_DIRECT delta_8b offset_16b`
Performs an inplace addition operation on the int at `offset` in the local stack, taking `delta_8b` as a signed 8-bit integer, which is added to the int at `offset`.

##### `0x26: OP_FAST_GLOBAL_INT_INPLACE_ADD`
`OP_FAST_GLOBAL_INT_INPLACE_ADD offset_16b`
Performs an inplace addition operation on the int at `offset` in the global stack, popping the top value off the value stack, and adding it to the int at `offset`.

##### `0x27: OP_FAST_GLOBAL_INT_INPLACE_ADD_DIRECT`
`OP_FAST_GLOBAL_INT_INPLACE_ADD_DIRECT delta_8b offset_16b`
Performs an inplace addition operation on the int at `offset` in the global stack, taking `delta_8b` as a signed 8-bit integer, which is added to the int at `offset`.

##### `0x28: OP_FAST_LOCAL_INT_INPLACE_SUB`
`OP_FAST_LOCAL_INT_INPLACE_SUB offset_16b`
Performs an inplace subtraction operation on the int at `offset` in the local stack, popping the top value off the value stack, and subtracting it from the int at `offset`.

##### `0x29: OP_FAST_GLOBAL_INT_INPLACE_SUB`
`OP_FAST_GLOBAL_INT_INPLACE_SUB offset_16b`
Performs an inplace subtraction operation on the int at `offset` in the global stack, popping the top value off the value stack, and subtracting it from the int at `offset`.


### 0x80 - 0x9F - Integer and Boolean Operations

### Full Opcode Reference
```
enum VlOpcode : uint8 {  
	OP_CONSTANT_VAL_DIRECT = 0x00,
	OP_CONSTANT_OBJ_DIRECT = 0x01,
	OP_CONSTANT_VAL_TABLE = 0x02,
	OP_CONSTANT_OBJ_TABLE = 0x03,
	OP_POP_VAL = 0x04,
	OP_POP_OBJ = 0x05,
	OP_CALL_BUILTIN = 0x06,
	OP_CALL_USERDEF = 0x07,
	OP_RETURN = 0x08,
	
	OP_GET_LOCAL_VAL = 0x10,
	OP_SET_LOCAL_VAL = 0x11,
	OP_GET_GLOBAL_VAL = 0x12,
	OP_SET_GLOBAL_VAL = 0x13,
	OP_GET_LOCAL_OBJ = 0x14,
	OP_SET_LOCAL_OBJ = 0x15,
	OP_GET_GLOBAL_OBJ = 0x16,
	OP_SET_GLOBAL_OBJ = 0x17,

	OP_JMP = 0x20,
	OP_JMP_IF_TRUE = 0x21,
	OP_JMP_IF_FALSE = 0x22,

	OP_FAST_LOCAL_INT_INPLACE_ADD = 0x24,
	OP_FAST_LOCAL_INT_INPLACE_ADD_DIRECT = 0x25,
	OP_FAST_GLOBAL_INT_INPLACE_ADD = 0x26,
	OP_FAST_GLOBAL_INT_INPLACE_ADD_DIRECT = 0x27,
	OP_FAST_LOCAL_INT_INPLACE_SUB = 0x28,
	OP_FAST_GLOBAL_INT_INPLACE_SUB = 0x29,

	OP_INT_EQUAL = 0x80,
	OP_INT_NOT_EQUAL = 0x81,
	OP_INT_GREATER = 0x82,
	OP_INT_GREATER_OR_EQUAL = 0x83,
	OP_INT_LESS = 0x84,
	OP_INT_LESS_OR_EQUAL = 0x85,
	OP_INT_ADD = 0x86,
	OP_INT_SUB = 0x87,
	OP_INT_MUL = 0x88,
	OP_INT_DIV = 0x89,
	OP_INT_MOD = 0x8A,
	OP_INT_POW = 0x8B,
	OP_INT_NEG = 0x8C,
	OP_INT_AND = 0x8D,
	OP_INT_OR = 0x8E,
	OP_INT_XOR = 0x8F,
	OP_INT_NOT = 0x90,
	OP_INT_LEFT_SHIFT = 0x91,
	OP_INT_RIGHT_SHIFT = 0x92,

	OP_BOOLEAN_AND = 0x9C,
	OP_BOOLEAN_OR = 0x9D,
	OP_BOOLEAN_NOT = 0x9E,

	OP_REAL_EQUAL = 0xA0,
	OP_REAL_NOT_EQUAL = 0xA1,
	OP_REAL_GREATER = 0xA2,
	OP_REAL_GREATER_OR_EQUAL = 0xA3,
	OP_REAL_LESS = 0xA4,
	OP_REAL_LESS_OR_EQUAL = 0xA5,
	OP_REAL_ADD = 0xA6,
	OP_REAL_SUB = 0xA7,
	OP_REAL_MUL = 0xA8,
	OP_REAL_DIV = 0xA9,
	OP_REAL_MOD = 0xAA,
	OP_REAL_POW = 0xAB,
	OP_REAL_NEG = 0xAC,

	OP_COMPLEX_EQUAL = 0xB0,
	OP_COMPLEX_NOT_EQUAL = 0xB1,
	OP_COMPLEX_ADD = 0xB2,
	OP_COMPLEX_SUB = 0xB3,
	OP_COMPLEX_MUL = 0xB4,
	OP_COMPLEX_DIV = 0xB5,
	OP_COMPLEX_POW = 0xB6,
	OP_COMPLEX_NEG = 0xB7,

	OP_VECTOR_ADD = 0xC0,
	OP_VECTOR_SUB = 0xC1,
	OP_VECTOR_MUL = 0xC2,
	OP_VECTOR_DIV = 0xC3,
	OP_VECTOR_NEG = 0xC4,
	OP_VECTOR_SCL = 0xC5,
	OP_VECTOR_DOT = 0xC6,
	OP_VECTOR_CRS = 0xC7,
	OP_MATRIX_ADD = 0xC8,
	OP_MATRIX_SUB = 0xC9,
	OP_MATRIX_MUL = 0xCA,
	OP_MATRIX_NEG = 0xCB,
	OP_MATRIX_SCL = 0xCC
}
```

# Builtin Function Reference
`0x0000 - 0x0FFF` is used for builtin functions
`0x1000 - 0x1FFF` is used for builtin type methods and properties.

#### 0x0000 - 0x0FFF: builtin functions
###### 0x0000 - 0x00FF: Basic builtins
`0x0000`: Prints an integer
`0x0001`: Prints a float
#### 0x1000 - 0x10FF: int methods and properties
`0x1000`: Cast an int to a real
`0x1001`: Cast an int to a complex
#### 0x1100 - 0x11FF: real methods and properties
`0x1100`: Cast a real to a complex
#### 0x1200 - 0x12FF: complex methods and properties
`0x1200`: Get the real component of a complex, returning a real.
`0x1201`: Get the imaginary component of a complex, returning a real.
#### 0x1300 - 0x13FF: vec methods and properties
`0x1300`: Construct a vec2 from 2 reals
`0x1301`: Construct a vec3 from 3 reals
`0x1302`: Construct a vec4 from 4 reals
#### 0x1400 - 0x14FF: mat methods and properties


# Compiler Diagnostics Reference
#### E0xx errors - Core program errors
###### E000
E000: Syntax error
#### E1xx errors - Type errors
###### E100
E100: Data `<>` is type `<>`, got type `<>`
###### E101
E102: Assignment of non-constexpr expression to constexpr `<>`
###### E102
E102: Assignment to constant `<>`after initialization
###### E103
E103: Assignment to non-lvalue
###### E104
E104: Operator `<>` not supported between instances of `<>` and `<>`
###### E105
E105: Cannot cast from `<>` to `<>`
###### E106
E106: Member access results in callable; Veclang does not support first-class functions.
###### E110
E110: Function `<>` expects `<>` arguments, not `<>` arguments
###### E111
E111: Function `<>` expects argument #`<>` to be type `<>`, not `<>`
###### E112
E112: Expected return type of `<>`, got type `<>`
###### E113
E113: Calling non-callable expression
###### E120
E120: `if` statement condition should be type `bool`, got type `<>`
###### E121
E121: `elseif` statement condition should be type `bool`, got type `<>` 
###### E122
E122: `while` statement condition should be type `bool`, got type `<>`
###### E123
E123: `for` statement range literal must either be `start:stop:constexpr_step` or `constexpr_start:constexpr_stop:step`

#### E2xx errors - Identifier errors
###### E200
E200: Unresolved identifier `<>`
###### E201
E201: Identifier `<>` has already been initialized
###### E202
E202: Function `<>` has already been declared
###### E210
E210: Duplicate parameter `<>` in declaration for function `<>`
###### E211
E211: Attribute tag parsing error: `<>`

#### E3xx errors - Structure errors
###### E300
E300: Nested function declarations
###### E301
E301: `using` declaration inside function declaration
###### E310
E310: Use of `break` statement outside of loop
###### E311
E311: Use of `continue` statement outside of loop
###### E320
E320: Use of `return` statement outside of function
###### E321
E321: No `return` statement at end of statement list in function
###### E330
E330: Use of `elseif` statement not in an `if-elseif-else` stack
###### E331
E331: Use of `else` statement not in an `if-elseif-else` stack

#### E4xx errors - Import errors

#### E9xx errors - Internal errors
E900: Internal error: `<>`

## Warnings
###### W001 
W001: Unused identifier `<>`
###### W002
W002: Variable `<>` is never written to after initialisation
###### W010
W010: Unreachable code after `return` statement
###### W011
W011: Unreachable code after `break` statement
###### W012
W012: Unreachable code after `continue` statement
###### W013
W013: Expression statement has no effect
###### W014
W014: Statement has no effect
###### W020
W020: Unknown attribute tag key `<>`

## Weak warnings
###### X000
X000: Constant identifier `<>` should be uppercase `SNAKE_CASE`
###### X001
X001: Variable identifier `<>` should be lowercase `snake_case`
###### X002
X002: Function name `<>` should be lowercase `snake_case`
###### X003
X003: Only unused identifiers should be prefixed with '\_'
###### X100
X100: Constant `<>` could be declared as constexpr
