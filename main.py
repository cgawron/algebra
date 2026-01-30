from src.lexer import Lexer
from src.parser import Parser
from src.differentiation import diff

def parse_expression(text: str):    
    lexer = Lexer(text)
    parser = Parser(lexer)
    return parser.parse()

def main():
    expressions = [
        "x + 1",
        "x + x",
        "x * x * x",
        "sin(30 * x)",
        "exp(x^2 + 1)",
        "ln(x^2 + 1)"
    ]
    
    for expr in expressions:
        try:
            ast = parse_expression(expr)
            print(f"Expression: {expr}")
            print(f"AST: {ast.__repr__()}")
            print(f"Derivative: {diff(ast, 'x')}")
        except Exception as e:
            print(f"Error parsing '{expr}': {e}")

if __name__ == "__main__":
    main()
