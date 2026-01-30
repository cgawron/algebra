# Math Expression Parser, Differentiator & Integrator

A robust mathematical expression parser, simplifier, symbolic differentiator, and integrator written in Python.

## Features

- **Expression Parsing**: Converts mathematical strings into an Abstract Syntax Tree (AST) using a Recursive Descent Parser.
  - Supports basic arithmetic (`+`, `-`, `*`, `/`, `^`).
  - Supports functions (`sin`, `cos`, `exp`, `ln`).
  - Supports variables (`x`, `y`, etc.).
- **Symbolic Differentiation**: Computes the derivative of an expression with respect to a variable.
- **Symbolic Integration**: Computes the anti-derivative of an expression.
  - **Standard Rules**: Power rule, constants, linearity, standard functions.
  - **Substitution Rules**:
    - Linear: `int(f(ax+b))`.
    - Reverse Chain Rule: `int(u^n * du)`.
    - Generalized Substitution: `int(f(u) * du)`.
- **Advanced Simplification**:
  - **Algebraic**: Identity rules (`x+0=x`), constant folding, collecting like terms (`2x+3x=5x`), and combining powers (`x*x=x^2`).
  - **Trigonometric**: Applies identities like `sin(x)^2 + cos(x)^2 = 1` and `cos(x)^2 - sin(x)^2 = cos(2x)`.
  - **Negative Handling**: Smartly handles negative signs to maximize cancellation.
  - **Division Simplification**: `x / (c*x) -> 1/c`, `0 / x -> 0`.
- **Canonical Output**: Expressions are printed in a clean, standard mathematical format.

## Usage

### Prerequisites
- Python 3.8+ (Verified on 3.13)
- `uv` (optional, for running scripts easily)

### Running the Example
The `main.py` script demonstrates parsing, simplification, differentiation, and integration.

```bash
uv run main.py
```

**Example Output:**
```
Expression: sin(x)^2 + cos(x)^2
AST: 1
Derivative: 0
Integral: x

Expression: x * exp(x^2 + 1)
AST: x * exp(1 + x^2)
Derivative: exp(1 + x^2) + 2 * x^2 * exp(1 + x^2)
Integral: 0.5 * exp(1 + x^2)
```

### Library Usage
You can use the core modules in your own code:

```python
from src.parser import parse_expression
from src.differentiation import diff
from src.integration import integrate
from src.simplification import simplify

expr = "x^2 + 2*x + 1"
ast = parse_expression(expr)
print(f"AST: {ast}")

derivative = diff(ast, "x")
print(f"Derivative: {derivative}")

integral = integrate(ast, "x")
print(f"Integral: {integral}")
```

## Project Structure

- `src/`
  - `lexer.py`: Tokenizes input strings.
  - `parser.py`: recurses descent parser to build AST.
  - `ast_nodes.py`: Dataclasses for AST nodes (Number, Variable, BinaryOp, etc.).
  - `differentiation.py`: Logic for symbolic differentiation.
  - `integration.py`: Logic for symbolic integration.
  - `simplification.py`: Comprehensive simplification rules.
- `tests/`: Unit tests for all modules.
- `main.py`: Demo script.

## Testing
Run the comprehensive test suite using `unittest`:


```bash
python3 -m unittest discover tests
```
