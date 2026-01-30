from dataclasses import dataclass
from enum import Enum, auto
from typing import Union, List

class Op(Enum):
    ADD = "+"
    SUB = "-"
    MUL = "*"
    DIV = "/"
    POW = "^"

@dataclass
class ASTNode:
    def __str__(self):
        return self.__repr__()

@dataclass
class Number(ASTNode):
    value: float
    def __str__(self):
        if self.value.is_integer():
             return str(int(self.value))
        return str(self.value)

@dataclass
class Variable(ASTNode):
    name: str
    def __str__(self):
        return self.name

@dataclass
class BinaryOp(ASTNode):
    left: ASTNode
    op: Op
    right: ASTNode
    def __str__(self):
        return f"({self.left} {self.op.value} {self.right})"

@dataclass
class UnaryOp(ASTNode):
    op: Op
    operand: ASTNode
    def __str__(self):
        return f"{self.op.value}{self.operand}"

@dataclass
class FunctionCall(ASTNode):
    name: str
    args: List[ASTNode]
    def __str__(self):
        args_str = ", ".join(map(str, self.args))
        return f"{self.name}({args_str})"
