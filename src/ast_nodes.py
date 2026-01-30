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
    pass

@dataclass
class Number(ASTNode):
    value: float

@dataclass
class Variable(ASTNode):
    name: str

@dataclass
class BinaryOp(ASTNode):
    left: ASTNode
    op: Op
    right: ASTNode

@dataclass
class UnaryOp(ASTNode):
    op: Op
    operand: ASTNode

@dataclass
class FunctionCall(ASTNode):
    name: str
    args: List[ASTNode]
