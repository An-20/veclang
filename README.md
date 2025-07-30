# Veclang

### A high-level high-performance programming language transpiled for CUDA targets

Veclang 2.0, a redesign of closed-source Veclang V1, is currently a work in progress.
Some of this codebase has been copied line-for-line from Veclang V1; there ain't no technical debt
like technical debt you wrote when you were 14.

### Overview

The Veclang compiler has three main components:

- The frontend parses a Veclang program to an Abstract Syntax Tree (AST).
- The midend (middle-end) converts the AST to a tree-based High-level Intermediate Representation (HIR).
  The midend then checks the HIR with the linter, before optionally converting to a 'flat' Mid-level Intermediate
  Representation (MIR).
- The backend takes a HIR or MIR and emits bytecode or LLVM IR respectively.

## Values and Objects

A value is an `int`, `real`, `bool`, or `null`. A value takes up 4 or 8 bytes.
An object is a `complex`, `matN`, or `vecN`. An object takes up 64 or 128 bytes.

There are two intermediate-value stacks:

- The value stack, which has fixed offsets of either 4 or 8 bytes.
- The object stacks, which has fixed offsets of either 64 or 128 bytes.

All objects stored in variables are in the call stack.

# Opcodes

## Overview

There are three types of instructions, classified by how they take operands:

- 0 operand instructions e.g. `OP_POP`.
- 1 operand instructions e.g. `OP_CONSTANT_VAL_TABLE`, that take 1 16-bit operand.
- 2 operand instructions e.g. `OP_VECTOR_ADD`, that take 1 8-bit operand and 1 16-bit operand.
  Each instruction consisting of opcode and operand(s) is stored as 4 bytes.

## 0x00 - 0x2F - Basic variable and constant manipulations

### Constant loading

##### `0x00: OP_CONSTANT_VAL_DIRECT`

`OP_CONSTANT_VAL_DIRECT value_16b`
Loads a constant value directly, by directly pushing the operand `value` onto the value stack. This instruction only works for `int`s and `bool`s, interpreting `value` as the last 2 bytes of an otherwise zeroed 4 or 8 byte value.

##### `0x01: OP_CONSTANT_OBJ_DIRECT`

`OP_CONSTANT_OBJ_DIRECT type_8b value_16b`
Reserved instruction.

##### `0x02: OP_CONSTANT_VAL_TABLE`

`OP_CONSTANT_VAL_TABLE offset_16b`
Loads a constant value from the constant table at the given offset, by pushing the value at `offset` onto the value stack.

##### `0x03: OP_CONSTANT_OBJ_TABLE`

`OP_CONSTANT_OBJ_TABLE type_8b offset_16b`
Loads a constant object from the constant table at the given offset, by pushing the value at `offset` onto the object stack.

`0x04: OP_POP`
`0x10: OP_GET_LOCAL_VAL`
`0x11: OP_SET_LOCAL_VAL`
`0x12: OP_GET_GLOBAL_VAL`
`0x13: OP_SET_GLOBAL_VAL`
`0x14: OP_GET_LOCAL_OBJ`
`0x15: OP_SET_LOCAL_OBJ`
`0x16: OP_GET_GLOBAL_OBJ`
`0x17: OP_SET_GLOBAL_OBJ`

`cmake -G "MinGW Makefiles" -DCMAKE_CXX_COMPILER=C:\msys64\ucrt64\bin\g++.exe ..`
