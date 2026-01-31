from enum import Enum, auto
from dataclasses import dataclass
from typing import Iterator, Optional, Union

class TokenType(Enum):
    NUMBER = auto()
    PLUS = auto()
    MINUS = auto()
    MUL = auto()
    DIV = auto()
    POW = auto()
    LPAREN = auto()
    RPAREN = auto()
    COMMA = auto()
    IDENTIFIER = auto()
    EOF = auto()

@dataclass
class Token:
    type: TokenType
    value: Union[float, int, str, None] = None

class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.current_char = self.text[0] if self.text else None

    def advance(self):
        self.pos += 1
        if self.pos < len(self.text):
            self.current_char = self.text[self.pos]
        else:
            self.current_char = None

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def number(self) -> Token:
        result = ''
        is_float = False
        while self.current_char is not None and (self.current_char.isdigit() or self.current_char == '.'):
            if self.current_char == '.':
                if is_float:
                    break # Simple error handling
                is_float = True
            result += self.current_char
            self.advance()
        
        if is_float:
            return Token(TokenType.NUMBER, float(result))
        else:
            return Token(TokenType.NUMBER, int(result))

    def identifier(self) -> Token:
        result = ''
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()
        return Token(TokenType.IDENTIFIER, result)

    def get_next_token(self) -> Token:
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char.isdigit() or self.current_char == '.':
                return self.number()

            if self.current_char.isalpha():
                return self.identifier()

            if self.current_char == '+':
                self.advance()
                return Token(TokenType.PLUS)
            
            if self.current_char == '-':
                self.advance()
                return Token(TokenType.MINUS)

            if self.current_char == '*':
                self.advance()
                return Token(TokenType.MUL)

            if self.current_char == '/':
                self.advance()
                return Token(TokenType.DIV)

            if self.current_char == '^':
                self.advance()
                return Token(TokenType.POW)

            if self.current_char == '(':
                self.advance()
                return Token(TokenType.LPAREN)

            if self.current_char == ')':
                self.advance()
                return Token(TokenType.RPAREN)

            if self.current_char == ',':
                self.advance()
                return Token(TokenType.COMMA)

            raise Exception(f'Invalid character: {self.current_char}')

        return Token(TokenType.EOF)

    def tokenize(self) -> Iterator[Token]:
        token = self.get_next_token()
        while token.type != TokenType.EOF:
            yield token
            token = self.get_next_token()
        yield token
