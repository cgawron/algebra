from .ast_nodes import ASTNode, Number, Variable, BinaryOp, UnaryOp, FunctionCall, Op
from typing import Tuple

def get_rank(node: ASTNode) -> int:
    """
    Rank nodes for canonical ordering.
    0: Number
    1: Variable
    2: UnaryOp
    3: BinaryOp
    4: FunctionCall
    """
    if isinstance(node, Number):
        return 0
    if isinstance(node, Variable):
        return 1
    if isinstance(node, UnaryOp):
        return 2
    if isinstance(node, BinaryOp):
        return 3
    if isinstance(node, FunctionCall):
        return 4
    return 100

def get_term(node: ASTNode) -> Tuple[float, ASTNode]:
    """Returns (coefficient, base_node) for addition."""
    # 2 * x -> (2, x)
    # x -> (1, x)
    if isinstance(node, BinaryOp) and node.op == Op.MUL:
        if isinstance(node.left, Number):
            return (node.left.value, node.right)
    # Unary -x -> (-1, x)
    if isinstance(node, UnaryOp) and node.op == Op.SUB:
         return (-1, node.operand)
    return (1, node)

def get_power(node: ASTNode) -> Tuple[ASTNode, float]:
    """Returns (base, exponent) for multiplication."""
    # x ^ 2 -> (x, 2)
    # x -> (x, 1)
    if isinstance(node, BinaryOp) and node.op == Op.POW:
        if isinstance(node.right, Number):
            return (node.left, node.right.value)
    return (node, 1)

def are_terms_equal(term1: ASTNode, term2: ASTNode) -> bool:
    """Check if two terms are identical (structurally)."""
    return str(term1) == str(term2) # Simple string comparison for now as canonical order should make them consistent.

def simplify(node: ASTNode) -> ASTNode:
    if isinstance(node, BinaryOp):
        # Simplify children first (bottom-up)
        node.left = simplify(node.left)
        node.right = simplify(node.right)
        
        # 1. Canonical Ordering for Commutative Operations
        if node.op in (Op.ADD, Op.MUL):
             rank_left = get_rank(node.left)
             rank_right = get_rank(node.right)
             
             if rank_right < rank_left:
                 node.left, node.right = node.right, node.left
             elif rank_right == rank_left:
                 if str(node.right) < str(node.left):
                      node.left, node.right = node.right, node.left
        
        # 2. Simplification Rules
        
        # Addition Rules
        if node.op == Op.ADD:
            # Identity
            if isinstance(node.left, Number) and node.left.value == 0:
                return node.right 
            if isinstance(node.right, Number) and node.right.value == 0:
                return node.left
            if isinstance(node.left, Number) and isinstance(node.right, Number):
                return Number(node.left.value + node.right.value)
            
            # Combine Like Terms: c1*x + c2*x
            c1, t1 = get_term(node.left)
            c2, t2 = get_term(node.right)
            if are_terms_equal(t1, t2):
                new_coeff = c1 + c2
                if new_coeff == 0: return Number(0)
                if new_coeff == 1: return t1
                return simplify(BinaryOp(Number(new_coeff), Op.MUL, t1))
            
            # Associative Constant Folding
            if isinstance(node.left, Number) and isinstance(node.right, BinaryOp) and node.right.op == Op.ADD:
                 if isinstance(node.right.left, Number):
                      new_value = node.left.value + node.right.left.value
                      return simplify(BinaryOp(Number(new_value), Op.ADD, node.right.right))

        # Subtraction Rules
        if node.op == Op.SUB:
            if isinstance(node.right, Number) and node.right.value == 0:
                return node.left 
            if isinstance(node.left, Number) and node.left.value == 0:
                return simplify(UnaryOp(Op.SUB, node.right))
            if isinstance(node.left, Number) and isinstance(node.right, Number):
                return Number(node.left.value - node.right.value)
            
            # Combine Like Terms: c1*x - c2*x
            c1, t1 = get_term(node.left)
            c2, t2 = get_term(node.right)
            if are_terms_equal(t1, t2):
                new_coeff = c1 - c2
                if new_coeff == 0: return Number(0)
                if new_coeff == 1: return t1
                return simplify(BinaryOp(Number(new_coeff), Op.MUL, t1))

        # Multiplication Rules
        if node.op == Op.MUL:
            if isinstance(node.left, Number) and node.left.value == 0: return Number(0)
            if isinstance(node.right, Number) and node.right.value == 0: return Number(0)
            if isinstance(node.left, Number) and node.left.value == 1: return node.right
            if isinstance(node.right, Number) and node.right.value == 1: return node.left
            if isinstance(node.left, Number) and isinstance(node.right, Number):
                return Number(node.left.value * node.right.value)
            
            # Pull constant from right child: x * (c * y) -> c * (x * y)
            if isinstance(node.right, BinaryOp) and node.right.op == Op.MUL and isinstance(node.right.left, Number):
                 c = node.right.left
                 y = node.right.right
                 return simplify(BinaryOp(c, Op.MUL, BinaryOp(node.left, Op.MUL, y)))
            
            # Pull constant from left child: (c * x) * y -> c * (x * y)
            if isinstance(node.left, BinaryOp) and node.left.op == Op.MUL and isinstance(node.left.left, Number):
                 c = node.left.left
                 x = node.left.right
                 return simplify(BinaryOp(c, Op.MUL, BinaryOp(x, Op.MUL, node.right)))
            
            # Combine Powers: x^a * x^b -> x^(a+b)
            # This needs to handle cases where x is Base (not Coeff*Base).
            # But get_term handles Coeff*Base.
            # get_power handles Base^Exp.
            # If left is Number, we bubbled it.
            # If both are variables/powers/functions (Rank > 0).
            if get_rank(node.left) > 0 and get_rank(node.right) > 0:
                b1, e1 = get_power(node.left)
                b2, e2 = get_power(node.right)
                if are_terms_equal(b1, b2):
                    new_exp = e1 + e2
                    if new_exp == 0: return Number(1)
                    if new_exp == 1: return b1
                    return simplify(BinaryOp(b1, Op.POW, Number(new_exp)))

        # Division Rules
        if node.op == Op.DIV:
             if isinstance(node.right, Number) and node.right.value == 1:
                 return node.left
             if isinstance(node.left, Number) and isinstance(node.right, Number) and node.right.value != 0:
                 return Number(node.left.value / node.right.value)
             
             # Combine Powers: x^a / x^b -> x^(a-b)
             b1, e1 = get_power(node.left)
             b2, e2 = get_power(node.right)
             if are_terms_equal(b1, b2):
                 new_exp = e1 - e2
                 if new_exp == 0: return Number(1)
                 if new_exp == 1: return b1
                 return simplify(BinaryOp(b1, Op.POW, Number(new_exp)))


        # Exponentiation Rules
        if node.op == Op.POW:
            if isinstance(node.right, Number):
                if node.right.value == 0: return Number(1)
                if node.right.value == 1: return node.left
                if isinstance(node.left, Number):
                     return Number(node.left.value ** node.right.value)
                # (x^a)^b -> x^(a*b)
                if isinstance(node.left, BinaryOp) and node.left.op == Op.POW:
                    if isinstance(node.left.right, Number):
                         b1 = node.left.left
                         e1 = node.left.right.value
                         e2 = node.right.value
                         return simplify(BinaryOp(b1, Op.POW, Number(e1 * e2)))

    elif isinstance(node, UnaryOp):
        node.operand = simplify(node.operand)
        if isinstance(node.operand, Number):
            if node.op == Op.ADD: return node.operand
            if node.op == Op.SUB: return Number(-node.operand.value)
    
    elif isinstance(node, FunctionCall):
        new_args = [simplify(arg) for arg in node.args]
        node.args = new_args

    return node
