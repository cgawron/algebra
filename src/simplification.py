from .ast_nodes import ASTNode, Number, Variable, BinaryOp, UnaryOp, FunctionCall, Op
from typing import Tuple, Optional

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
         # Handle -(2 * x) -> (-2, x)
         if isinstance(node.operand, BinaryOp) and node.operand.op == Op.MUL:
             if isinstance(node.operand.left, Number):
                 return (-1 * node.operand.left.value, node.operand.right)
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

def get_trig_arg(node: ASTNode, func_name: str, target_exponent: float) -> Optional[ASTNode]:
    """
    Checks if node is func_name(arg) ^ target_exponent.
    Returns arg if match, None otherwise.
    """
    # Check for direct function call if exponent is 1
    if target_exponent == 1:
        if isinstance(node, FunctionCall) and node.name == func_name and len(node.args) == 1:
            return node.args[0]
        return None

    # Check for Power
    if isinstance(node, BinaryOp) and node.op == Op.POW:
        if isinstance(node.right, Number) and node.right.value == target_exponent:
            base = node.left
            if isinstance(base, FunctionCall) and base.name == func_name and len(base.args) == 1:
                return base.args[0]
    return None

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
            
            # Trigonometric Identities
            # sin(u)^2 + cos(u)^2 = 1
            # We need to handle c * sin^2 + c * cos^2 -> c * 1 -> c
            # Only if coefficients match.
            if c1 == c2:
                sin_arg = get_trig_arg(t1, "sin", 2)
                cos_arg = get_trig_arg(t2, "cos", 2)
                if sin_arg and cos_arg and are_terms_equal(sin_arg, cos_arg):
                     # c * (sin^2 + cos^2) -> c * 1 -> c
                     return Number(c1)
                
                # Check reverse order (cos^2 + sin^2) - dealt with by canonical order?
                # Canonical: cos (4) vs sin (4). "cos" < "sin". So cos usually first.
                # So we should check t1=cos, t2=sin too.
                sin_arg_r = get_trig_arg(t2, "sin", 2)
                cos_arg_l = get_trig_arg(t1, "cos", 2)
                if sin_arg_r and cos_arg_l and are_terms_equal(sin_arg_r, cos_arg_l):
                     return Number(c1)
            
            # Double Angle Cosine: cos(u)^2 - sin(u)^2 = cos(2u)
            if c1 == -c2:
                # Case 1: t1=cos^2, t2=sin^2 -> c1 * (cos^2 - sin^2)
                cos_arg = get_trig_arg(t1, "cos", 2)
                sin_arg = get_trig_arg(t2, "sin", 2)
                if cos_arg and sin_arg and are_terms_equal(cos_arg, sin_arg):
                     double_arg = simplify(BinaryOp(Number(2), Op.MUL, cos_arg))
                     return simplify(BinaryOp(Number(c1), Op.MUL, FunctionCall("cos", [double_arg])))
                
                # Case 2: t1=sin^2, t2=cos^2 -> c2 * (cos^2 - sin^2)
                sin_arg_l = get_trig_arg(t1, "sin", 2)
                cos_arg_r = get_trig_arg(t2, "cos", 2)
                if sin_arg_l and cos_arg_r and are_terms_equal(sin_arg_l, cos_arg_r):
                     double_arg = simplify(BinaryOp(Number(2), Op.MUL, cos_arg_r))
                     return simplify(BinaryOp(Number(c2), Op.MUL, FunctionCall("cos", [double_arg])))

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
            
            # Trig Identities for Subtraction?
            # cos^2 - sin^2.
            # If canonical ordering is Off, we might see this in SUB.
            # But simplify(SUB) is usually kept unless we convert SUB to ADD(-)?
            # My parser creates SUB.
            # cos^2 - sin^2 matches here.
            # c1=1, t1=cos^2. c2=1, t2=sin^2. (get_term handles coeff 1).
            cos_arg = get_trig_arg(t1, "cos", 2)
            sin_arg = get_trig_arg(t2, "sin", 2)
            if cos_arg and sin_arg and are_terms_equal(cos_arg, sin_arg):
                 if c1 == c2:
                      # c * (cos^2 - sin^2) -> c * cos(2u)
                      double_arg = simplify(BinaryOp(Number(2), Op.MUL, cos_arg))
                      result = FunctionCall("cos", [double_arg])
                      if c1 == 1: return result
                      return simplify(BinaryOp(Number(c1), Op.MUL, result))


        # Multiplication Rules
        if node.op == Op.MUL:
            if isinstance(node.left, Number) and node.left.value == 0: return Number(0)
            if isinstance(node.right, Number) and node.right.value == 0: return Number(0)
            if isinstance(node.left, Number) and node.left.value == 1: return node.right
            if isinstance(node.right, Number) and node.right.value == 1: return node.left
            if isinstance(node.left, Number) and isinstance(node.right, Number):
                return Number(node.left.value * node.right.value)
            
            # Constant Combination: c * (x / d) -> (c/d) * x
            if isinstance(node.left, Number) and isinstance(node.right, BinaryOp) and node.right.op == Op.DIV:
                if isinstance(node.right.right, Number) and node.right.right.value != 0:
                     new_val = node.left.value / node.right.right.value
                     return simplify(BinaryOp(Number(new_val), Op.MUL, node.right.left))


            


            # Cancellation: (c * x) / x -> c
            if isinstance(node.left, BinaryOp) and node.left.op == Op.MUL:
                 if are_terms_equal(node.left.right, node.right) and isinstance(node.left.left, Number): # (c*x) / x
                     return node.left.left
                 if are_terms_equal(node.left.left, node.right) and isinstance(node.left.right, Number): # (x*c) / x
                     return node.left.right
            

            
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
            
            # Handle Negatives: (-a) * b -> -(a * b)
            is_left_neg = isinstance(node.left, UnaryOp) and node.left.op == Op.SUB
            is_right_neg = isinstance(node.right, UnaryOp) and node.right.op == Op.SUB
            
            if is_left_neg and is_right_neg:
                # (-a) * (-b) -> a * b
                return simplify(BinaryOp(node.left.operand, Op.MUL, node.right.operand))
            elif is_left_neg:
                # (-a) * b -> -(a * b)
                return simplify(UnaryOp(Op.SUB, BinaryOp(node.left.operand, Op.MUL, node.right)))
            elif is_right_neg:
                # a * (-b) -> -(a * b)
                return simplify(UnaryOp(Op.SUB, BinaryOp(node.left, Op.MUL, node.right.operand)))

            # Combine Powers: x^a * x^b -> x^(a+b)
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
            # 0 / x -> 0
            if isinstance(node.left, Number) and node.left.value == 0:
                 if isinstance(node.right, Number) and node.right.value == 0:
                      raise ValueError("Division by zero")
                 return Number(0)

            # Cancellation: x / (c * x) -> 1/c
            if isinstance(node.right, BinaryOp) and node.right.op == Op.MUL:
                 if are_terms_equal(node.left, node.right.right) and isinstance(node.right.left, Number): # x / (c*x)
                     return simplify(BinaryOp(Number(1), Op.DIV, node.right.left))
                 if are_terms_equal(node.left, node.right.left) and isinstance(node.right.right, Number): # x / (x*c)
                     return simplify(BinaryOp(Number(1), Op.DIV, node.right.right))


            
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
        # Simplify -(-x) -> x
        if node.op == Op.SUB and isinstance(node.operand, UnaryOp) and node.operand.op == Op.SUB:
             return node.operand.operand
    
    elif isinstance(node, FunctionCall):
        new_args = [simplify(arg) for arg in node.args]
        node.args = new_args

    return node
