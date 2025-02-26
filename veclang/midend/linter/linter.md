# Linter

## E0xx errors - Core program error

### E000
E000: No `main` function in program.  

### E010
E010: Usage of forbidden functions  
This error is only shown when the `-strict` flag is passed to the transpiler.
With the `-strict` flag, the linter will not allow usage of the following functions:
* `print`


### E011
E011: Usage of forbidden language features  
This error is only shown when the `-strict` flag is passed to the transpiler.
With the `-strict` flag, the linter will not allow usage of the following features:
* Slicing (`x[:5]`, `x[3:2]`, `x[3:]`, etc.)
* Initializing constants in program body outside of function


## E1xx errors - Type errors

### E100
E100: Variable `<>` is type `<>`, got type `<>`

### E101
E100: Constant `<>` is type `<>`, got type `<>`

### E102
E102: Assignment of non-constant expression to constant `<>`

### E103
E103: Assignment to `constant` object `<>`after initialization

### E104
E104: Operator `<>` not supported between instances of `<>` and `<>`

### E110
E110: Expected return type of `<>`, got type `<>`

### E120
E120: `if` statement condition should be type `boolean`, got type `<>`

### E121
E121: `elseif` statement condition should be type `boolean`, got type `<>`

### E123
E122: `while` statement condition should be type `boolean`, got type `<>`

### E124
E123: `for` statement condition should be type `boolean`, got type `<>`


## E2xx errors - Identifiers

### E200
E200: Unresolved identifier `<>`

### E201
E201: Identifier `<>` has already been initialized

### E210
E210: Function `<>` expects `<>` arguments, not `<>` arguments

### E211
E211: Function `<>` expects parameter #`<>` to be type `<>`, not type `<>`

### E220
E202: Illegal use of namespace in initialization

## E3xx errors - Program structure errors

### E300
E300: Function definition within function definition  

### E301
E301: Potential for recursion

### E310
E310: Use of `break` statement outside of loop

### E311
E311: Use of `continue` statement outside of loop

### E312
E312: More than one `break` or `continue` statement in statement list

### E320
E320: More than one `return` statement in statement list

### E321
E321: No `return` statement at end of statement list in function 

### E330
E330: Use of `elseif` statement not in an `if-elseif-else` stack

### E331
E331: Use of `else` statement not in an `if-elseif-else` stack


## E4xx errors - Import errors

### E400
E400: Unknown namespace `<>`

### E401
E401: Unknown name `<>` in namespace `<>`

### E410
E410: Name `<>` has already been imported from namespace `<>`


## E5xx errors - Linter / transpiler internal error

### E400
E400: Unknown AST node type `<>`


## W0xx strong warnings - Optimization warnings

### W001
W001: Unused identifier `<>`

### W010
W010: Unreachable code after `return` statement   

### W011
W011: Unreachable code after `break` statement   

### W012
W012: Unreachable code after `continue` statement   

### W020
W020: Identifier `<>` is never used

### W021
W021: Function `<>` is never used

### W900
W900: `constant` identifier `<>` should be uppercase snake_case

### W901
W901: `variable` identifier `<>` should be lowercase snake_case

### W902
W902: Function name `<>` should be lowercase snake_case
