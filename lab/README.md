# VKSL LAB

VKSL LAB is a frontend application built with React and Goldenlayout to act as a 'web IDE' for Veclang code.
VKSL LAB is now developed here under the `veclang` repo but deployed at [lab.vksl.uk](https://lab.vksl.uk) using Firebase under the `vksl_projects` repo and associated Firebase project.

## How VKSL LAB works

VKSL LAB uses GoldenLayout for the resizable and movable IDE widgets. GoldenLayout is initialised in `main.js` and each GoldenLayout component is a React root, with all the components in separate roots created in `main.jsx`.

`main.js` defines all the important functions for actually running Veclang code. `main.js` interacts with `main.py`, which is built using PyScript, to call the Veclang compiler and generate bytecode, as well as compiler diagnostics and other outputs.

`main.js` also interacts with `veclang.js`, a file created by compiling `veclang/backend/bc_interpreter` using Emscripten to WASM. This allows code to actually be executed.

While in typical Veclang REPL usage the interpreter is called from Python, this is not possible on the web (this would involving compiling a Python extension for WASM, which is doubly complicated compared to the already tedious task of doing both individually). Instead, the bytecode is passed back to JavaScript, and then passed through to the interpreter.

When the user interacts with the UI, the React components will set global variables on `window` and call methods defined in `main.js` on `window` (this is very dodgy but unfortunuately necessary unless we switch to global state management because GoldenLayout is not built for this).

**Summary of files**

- `lab/public/main.js`: Initialises GoldenLayout, defines the methods on `window` for running the compiler and code.
- `lab/public/main.py`: Wrapper over the Veclang interpreter to compile code and generate outputs.
- `lab/public/veclang.zip`: Actual Veclang compiler code (in Python), created by `sutoris` by zipping up the `.py` files in the repo. This runs in the browser using PyScript.
- `lab/public/veclang.js and veclang.wasm`: Veclang `bc_interpreter`, compiled to WASM using emscripten.
- `lab/src/main.jsx`: Creates the various React roots for each IDE component. Only runs once the GoldenLayout is initialised.
