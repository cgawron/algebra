from .ast_nodes import ASTNode, BinaryOp, UnaryOp, Number, Op, FunctionCall, Variable
from .lexer import Lexer, TokenType, Token

class Parser:
    def __init__(self, lexer: Lexer):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()

    def error(self):
        raise Exception('Invalid syntax')

    def eat(self, token_type: TokenType):
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error()

    def factor(self) -> ASTNode:
        token = self.current_token
        if token.type == TokenType.PLUS:
            self.eat(TokenType.PLUS)
            node = UnaryOp(op=Op.ADD, operand=self.factor())
            return node
        elif token.type == TokenType.MINUS:
            self.eat(TokenType.MINUS)
            node = UnaryOp(op=Op.SUB, operand=self.factor())
            return node
        return self.power()

    def power(self) -> ASTNode:
        node = self.atom()
        if self.current_token.type == TokenType.POW:
            self.eat(TokenType.POW)
            node = BinaryOp(left=node, op=Op.POW, right=self.factor())
        return node

    def atom(self) -> ASTNode:
        token = self.current_token
        if token.type == TokenType.NUMBER:
            self.eat(TokenType.NUMBER)
            return Number(value=token.value)
        elif token.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            node = self.expr()
            self.eat(TokenType.RPAREN)
            return node
        elif token.type == TokenType.IDENTIFIER:
            self.eat(TokenType.IDENTIFIER)
            name = token.value
            if self.current_token.type == TokenType.LPAREN:
                 return self.parse_function_call(name)
            else:
                 return Variable(name=name)
        else:
            self.error()

    def parse_function_call(self, name: str) -> ASTNode:
        self.eat(TokenType.LPAREN)
        args = []
        if self.current_token.type != TokenType.RPAREN:
            args.append(self.expr())
            while self.current_token.type == TokenType.COMMA:
                self.eat(TokenType.COMMA)
                args.append(self.expr())
        self.eat(TokenType.RPAREN)
        
        return FunctionCall(name=name, args=args)

    def term(self) -> ASTNode:
        node = self.factor()

        while self.current_token.type in (TokenType.MUL, TokenType.DIV):
            token = self.current_token
            if token.type == TokenType.MUL:
                self.eat(TokenType.MUL)
                node = BinaryOp(left=node, op=Op.MUL, right=self.factor())
            elif token.type == TokenType.DIV:
                self.eat(TokenType.DIV)
                node = BinaryOp(left=node, op=Op.DIV, right=self.factor())

        return node

    def expr(self) -> ASTNode:
        node = self.term()

        while self.current_token.type in (TokenType.PLUS, TokenType.MINUS):
            token = self.current_token
            if token.type == TokenType.PLUS:
                self.eat(TokenType.PLUS)
                node = BinaryOp(left=node, op=Op.ADD, right=self.term())
            elif token.type == TokenType.MINUS:
                self.eat(TokenType.MINUS)
                node = BinaryOp(left=node, op=Op.SUB, right=self.term())

        return node

    def parse(self) -> ASTNode:
        return self.expr()

def parse_expression(text: str) -> ASTNode:
    lexer = Lexer(text)
    parser = Parser(lexer)
    return parser.parse()
