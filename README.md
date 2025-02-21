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
