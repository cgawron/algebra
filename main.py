from src.lexer import Lexer
from src.parser import Parser

def parse_expression(text: str):
    lexer = Lexer(text)
    parser = Parser(lexer)
    return parser.parse()

def main():
    expressions = [
        "x + 1",
        "3 * (x + 5)",
        "-5 + 2",
        "10 / 2 * 3",
        "sin(30)",
        "max(1, 2, 3)",
        "sin(max(2, 3))"
    ]
    
    for expr in expressions:
        try:
            ast = parse_expression(expr)
            print(f"Expression: {expr}")
            print(f"AST: {ast}")
        except Exception as e:
            print(f"Error parsing '{expr}': {e}")

if __name__ == "__main__":
    main()
