from src.parser import parse_expression
from src.differentiation import diff
from src.ast_nodes import ASTNode, Op
from src.integration import integrate

def main():
    expressions = [
        "x / (2 * x)",
        "x + 1",
        "x + x",
        "x * x * x",
        "x^2 + 2*x + 1",
        "cos(30 * x)",
        "exp(x^2 + 1)*x",
        "ln(x^2 + 1)*x",
        "sin(x)^2 + cos(x)^2",
        "sin(x) * cos(x) * 2",
        "cos(2*x)",
        "cos(x)^2 - sin(x)^2",
        "2*x / (x^2 + 1)"
    ]
    
    for expr in expressions:
        try:
            ast = parse_expression(expr)
            print(f"Expression: {expr}")
            print(f"AST: {ast}")
            print(f"Derivative: {diff(ast, 'x')}")
            try:
                print(f"Integral: {integrate(ast, 'x')}")
            except NotImplementedError as e:
                print(f"Integral: Not supported ({e})")
            print("-" * 20)
        except Exception as e:
            print(f"Error parsing '{expr}': {e}")

if __name__ == "__main__":
    main()
