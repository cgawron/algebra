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
    
    @property
    def precedence(self):
        return 100

@dataclass
class Number(ASTNode):
    value: float
    def __str__(self):
        if isinstance(self.value, float) and self.value.is_integer():
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
    
    @property
    def precedence(self):
        if self.op in (Op.ADD, Op.SUB): return 10
        if self.op in (Op.MUL, Op.DIV): return 20
        if self.op == Op.POW: return 40
        return 100

    def __str__(self):
        left_str = str(self.left)
        right_str = str(self.right)
        
        # Check Left Child
        if self.left.precedence < self.precedence:
            left_str = f"({left_str})"
        elif self.left.precedence == self.precedence:
             # If right-associative operator (POW) and we are the left child -> wrap
             if self.op == Op.POW:
                 left_str = f"({left_str})"
             # Else (Left associative operators ADD, SUB, MUL, DIV) -> No wrap needed
        
        # Check Right Child
        if self.right.precedence < self.precedence:
            right_str = f"({right_str})"
        elif self.right.precedence == self.precedence:
             # If left-associative operators (SUB, DIV) and we are right child -> wrap
             # ADD and MUL are associative, so x+(y+z) can be x+y+z usually, 
             # but keeping strict parser structure (left-assoc) implies we might want to wrap right?
             # Parser: a+b+c -> (a+b)+c. Output: a+b+c.
             # Parser: a+(b+c). Output: a+(b+c).
             # So if right child has same op, and it's ADD/MUL, we technically don't need parens for value, 
             # but for SUB/DIV we DO. 
             # For ADD/MUL being explicit `a + (b + c)` is also fine.
             # Let's enforce parens for right child if equal precedence for SUB and DIV.
             # For ADD and MUL? 
             # If I have x + (y + z). -> Right child matches. Wrap. `x + (y + z)`.
             # If I have (x + y) + z. -> Left child matches. No wrap. `x + y + z`.
             # This distinguishes the structure well.
             
             if self.op in (Op.SUB, Op.DIV):
                 right_str = f"({right_str})"
             elif self.op in (Op.ADD, Op.MUL):
                 # Optional: wrap right if same op? 
                 # Let's assume standard formatting where a+b+c is Left associative.
                 # So right associative tree `a+(b+c)` should have parens.
                 right_str = f"({right_str})"

        return f"{left_str} {self.op.value} {right_str}"

@dataclass
class UnaryOp(ASTNode):
    op: Op
    operand: ASTNode
    
    @property
    def precedence(self):
        return 30
        
    def __str__(self):
        operand_str = str(self.operand)
        if self.operand.precedence < self.precedence:
            operand_str = f"({operand_str})"
        return f"{self.op.value}{operand_str}"

@dataclass
class FunctionCall(ASTNode):
    name: str
    args: List[ASTNode]
    def __str__(self):
        args_str = ", ".join(map(str, self.args))
        return f"{self.name}({args_str})"
