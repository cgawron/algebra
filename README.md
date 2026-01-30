# Math Expression Parser & Differentiator

A robust mathematical expression parser, simplifier, and symbolic differentiator written in Python.

## Features

- **Expression Parsing**: Converts mathematical strings into an Abstract Syntax Tree (AST) using a Recursive Descent Parser.
  - Supports basic arithmetic (`+`, `-`, `*`, `/`, `^`).
  - Supports functions (`sin`, `cos`, `exp`, `ln`).
  - Supports variables (`x`, `y`, etc.).
- **Symbolic Differentiation**: Computes the derivative of an expression with respect to a variable.
- **Advanced Simplification**:
  - **Algebraic**: Identity rules (`x+0=x`), constant folding, collecting like terms (`2x+3x=5x`), and combining powers (`x*x=x^2`).
  - **Trigonometric**: Applies identities like `sin(x)^2 + cos(x)^2 = 1` and `cos(x)^2 - sin(x)^2 = cos(2x)`.
  - **Negative Handling**: Smartly handles negative signs to maximize cancellation (`2*(-sin*cos) + 2*(cos*sin) = 0`).
- **Canonical Output**: Expressions are printed in a clean, standard mathematical format.

## Usage

### Prerequisites
- Python 3.8+ (Verified on 3.13)
- `uv` (optional, for running scripts easily)

### Running the Example
The `main.py` script demonstrates parsing, simplification, and differentiation of various expressions.

```bash
uv run main.py
```

**Example Output:**
```
Expression: sin(x)^2 + cos(x)^2
AST: 1
Derivative: 0

Expression: sin(x) * cos(x) * 2
AST: 2 * (cos(x) * sin(x))
Derivative: 2 * cos(2 * x)
```

### Library Usage
You can use the core modules in your own code:

```python
from src.parser import parse_expression
from src.differentiation import diff
from src.simplification import simplify

expr = "x^2 + 2*x + 1"
ast = parse_expression(expr)
print(f"AST: {ast}")

derivative = diff(ast, "x")
print(f"Derivative: {derivative}")
# Output: 2 * (1 + x)  (Simplified form)
```

## Project Structure

- `src/`
  - `lexer.py`: Tokenizes input strings.
  - `parser.py`: recurses descent parser to build AST.
  - `ast_nodes.py`: Dataclasses for AST nodes (Number, Variable, BinaryOp, etc.).
  - `differentiation.py`: Logic for symbolic differentiation.
  - `simplification.py`: Comprehensive simplification rules.
- `tests/`: Unit tests for all modules.
- `main.py`: Demo script.

## Testing
Run the comprehensive test suite using `unittest`:

```bash
python3 -m unittest discover tests
```
