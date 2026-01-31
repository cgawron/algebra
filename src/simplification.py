from .ast_nodes import ASTNode, Number, Variable, BinaryOp, UnaryOp, FunctionCall, Op, Rational
from typing import Tuple, Optional, Union
import math

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
    if isinstance(node, Rational):
        return 0
    return 100

def _gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return abs(a)

def _simplify_rational(n: int, d: int) -> ASTNode:
    if d == 0:
        raise ValueError("Division by zero")
    if d < 0:
        n, d = -n, -d
    common = _gcd(n, d)
    n //= common
    d //= common
    if d == 1:
        return Number(n)
    return Rational(n, d)

def to_fraction(n: Union[Number, Rational]) -> Tuple[int, int]:
    if isinstance(n, Rational):
        return n.numerator, n.denominator
    if isinstance(n, Number):
        if isinstance(n.value, int):
            return n.value, 1
        # Float case - avoiding for now in this path if possible, or raising error?
        # For now, let's assume we don't mix float and rational to produce rational unless float is integer.
        if n.value.is_integer():
            return int(n.value), 1
    raise ValueError(f"Cannot convert {n} to fraction")

def add_scalars(n1: ASTNode, n2: ASTNode) -> ASTNode:
    if isinstance(n1, Number) and isinstance(n1.value, float): return Number(n1.value + n2.value if isinstance(n2, Number) else n1.value + n2.value) # Fallback to float
    if isinstance(n2, Number) and isinstance(n2.value, float): return Number(n1.value + n2.value if isinstance(n1, Number) else n1.value + n2.value)
    
    # Both are int-like (Number(int) or Rational)
    try:
        num1, den1 = to_fraction(n1)
        num2, den2 = to_fraction(n2)
        return _simplify_rational(num1 * den2 + num2 * den1, den1 * den2)
    except ValueError:
        pass
    
    # Fallback
    v1 = n1.value
    v2 = n2.value
    return Number(v1 + v2)

def sub_scalars(n1: ASTNode, n2: ASTNode) -> ASTNode:
    if isinstance(n1, Number) and isinstance(n1.value, float): return Number(n1.value - n2.value if isinstance(n2, Number) else n1.value - n2.value)
    if isinstance(n2, Number) and isinstance(n2.value, float): return Number(n1.value - n2.value if isinstance(n1, Number) else n1.value - n2.value)
    
    try:
        num1, den1 = to_fraction(n1)
        num2, den2 = to_fraction(n2)
        return _simplify_rational(num1 * den2 - num2 * den1, den1 * den2)
    except ValueError:
        pass
        
    v1 = n1.value
    v2 = n2.value
    return Number(v1 - v2)

def mul_scalars(n1: ASTNode, n2: ASTNode) -> ASTNode:
    if isinstance(n1, Number) and isinstance(n1.value, float): return Number(n1.value * n2.value if isinstance(n2, Number) else n1.value * n2.value)
    if isinstance(n2, Number) and isinstance(n2.value, float): return Number(n1.value * n2.value if isinstance(n1, Number) else n1.value * n2.value)
    
    try:
        num1, den1 = to_fraction(n1)
        num2, den2 = to_fraction(n2)
        return _simplify_rational(num1 * num2, den1 * den2)
    except ValueError:
        pass

    v1 = n1.value
    v2 = n2.value
    return Number(v1 * v2)

def div_scalars(n1: ASTNode, n2: ASTNode) -> ASTNode:
    # If any float, return float
    if (isinstance(n1, Number) and isinstance(n1.value, float)) or \
       (isinstance(n2, Number) and isinstance(n2.value, float)):
        v1 = n1.value
        v2 = n2.value
        return Number(v1 / v2)
        
    # Try exact rational division
    try:
        num1, den1 = to_fraction(n1)
        num2, den2 = to_fraction(n2)
        return _simplify_rational(num1 * den2, den1 * num2)
    except ValueError:
        pass
        
    v1 = n1.value
    v2 = n2.value
    return Number(v1 / v2)

def pow_scalars(n1: ASTNode, n2: ASTNode) -> ASTNode:
    # Powers are tricky with rationals. For now, if exponent is integer, we can try.
    # (a/b)^n -> a^n / b^n
    if isinstance(n2, Number) and isinstance(n2.value, int):
        try:
             num1, den1 = to_fraction(n1)
             return _simplify_rational(num1 ** n2.value, den1 ** n2.value)
        except ValueError:
             pass
    
    v1 = n1.value
    v2 = n2.value
    return Number(v1 ** v2)

def get_term(node: ASTNode) -> Tuple[ASTNode, ASTNode]:
    """Returns (coefficient, base_node) for addition."""
    # 2 * x -> (2, x)
    # x -> (1, x)
    if isinstance(node, BinaryOp) and node.op == Op.MUL:
        if isinstance(node.left, (Number, Rational)):
            return (node.left, node.right)
    # Unary -x -> (-1, x)
    if isinstance(node, UnaryOp) and node.op == Op.SUB:
         # Handle -(2 * x) -> (-2, x)
         if isinstance(node.operand, BinaryOp) and node.operand.op == Op.MUL:
             if isinstance(node.operand.left, (Number, Rational)):
                 return (simplify(UnaryOp(Op.SUB, node.operand.left)), node.operand.right)
         return (Number(-1), node.operand)
    return (Number(1), node)

def get_power(node: ASTNode) -> Tuple[ASTNode, ASTNode]:
    """Returns (base, exponent) for multiplication."""
    # x ^ 2 -> (x, 2)
    # sqrt(x) -> (x, 0.5)
    # x -> (x, 1)
    if isinstance(node, BinaryOp) and node.op == Op.POW:
        if isinstance(node.right, (Number, Rational)):
            return (node.left, node.right)
    if isinstance(node, FunctionCall) and node.name == "sqrt" and len(node.args) == 1:
        return (node.args[0], Rational(1, 2))
    return (node, Number(1))

def get_trig_arg(node: ASTNode, func_name: str, target_exponent: float) -> Optional[ASTNode]:
    """
    Checks if node is func_name(arg) ^ target_exponent.
    Returns arg if match, None otherwise.
    target_exponent kept as float for convenience in pattern matching integers 1, 2 etc.
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

def extract_negative(node: ASTNode) -> Optional[ASTNode]:
    """
    Checks if a node represents a negative value.
    Returns the positive counterpart if true, else None.
    -3 -> 3
    -x -> x
    -2 * x -> 2 * x
    """
    if isinstance(node, (Number, Rational)) and node.value < 0:
        if isinstance(node, Number): return Number(-node.value)
        if isinstance(node, Rational): return Rational(-node.numerator, node.denominator)
    if isinstance(node, UnaryOp) and node.op == Op.SUB:
        return node.operand
    if isinstance(node, BinaryOp) and node.op == Op.MUL:
        if isinstance(node.left, (Number, Rational)) and node.left.value < 0:
             return BinaryOp(simplify(UnaryOp(Op.SUB, node.left)), Op.MUL, node.right)
    return None

def _apply_rule(rule_name: str, result: ASTNode, original: ASTNode, depth: int) -> ASTNode:
    """Helper to log rule application and recursively simplify the result."""
    import os
    debug = os.environ.get('DEBUG_SIMPLIFY', '0') == '1'
    if debug:
        indent = "  " * depth
        print(f"{indent}  [RULE: {rule_name}] {original} → {result}")
    return simplify(result, depth)

def simplify(node: ASTNode, _depth: int = 0) -> ASTNode:
    import os
    debug = os.environ.get('DEBUG_SIMPLIFY', '0') == '1'
    indent = "  " * _depth
    
    if debug:
        print(f"{indent}→ simplify({node})")
    
    original_node = node
    
    if isinstance(node, BinaryOp):
        # Simplify children first (bottom-up) - create new node to avoid mutation
        left_simplified = simplify(node.left, _depth + 1)
        right_simplified = simplify(node.right, _depth + 1)
        # Create new node instead of mutating
        node = BinaryOp(left_simplified, node.op, right_simplified)
        
        if debug:
            print(f"{indent}  After simplifying children: {node}")
        
        # 1. Canonical Ordering for Commutative Operations
        if node.op in (Op.ADD, Op.MUL):
             rank_left = get_rank(node.left)
             rank_right = get_rank(node.right)
             
             if rank_right < rank_left:
                 node = BinaryOp(node.right, node.op, node.left)
             elif rank_right == rank_left:
                 if str(node.right) < str(node.left):
                      node = BinaryOp(node.right, node.op, node.left)
        
        # 2. Simplification Rules
        
        # Addition Rules
        if node.op == Op.ADD:
            # Identity
            if isinstance(node.left, Number) and node.left.value == 0:
                return node.right 
            if isinstance(node.right, Number) and node.right.value == 0:
                return node.left
            if isinstance(node.left, (Number, Rational)) and isinstance(node.right, (Number, Rational)):
                return add_scalars(node.left, node.right)
            
            # Combine Like Terms: c1*x + c2*x
            c1, t1 = get_term(node.left)
            c2, t2 = get_term(node.right)
            if are_terms_equal(t1, t2):
                new_coeff = add_scalars(c1, c2)
                if isinstance(new_coeff, Number) and new_coeff.value == 0: return Number(0)
                if isinstance(new_coeff, Number) and new_coeff.value == 1: return t1
                return simplify(BinaryOp(new_coeff, Op.MUL, t1))
            
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
            # Need to check if c1 == -c2. Use scalar addition to 0? Or compare values.
            # Ideally Rational compare.
            sum_coeffs = add_scalars(c1, c2)
            if isinstance(sum_coeffs, Number) and sum_coeffs.value == 0:
                # Case 1: t1=cos^2, t2=sin^2 -> c1 * (cos^2 - sin^2)
                cos_arg = get_trig_arg(t1, "cos", 2)
                sin_arg = get_trig_arg(t2, "sin", 2)
                if cos_arg and sin_arg and are_terms_equal(cos_arg, sin_arg):
                     double_arg = simplify(BinaryOp(Number(2), Op.MUL, cos_arg))
                     return simplify(BinaryOp(c1, Op.MUL, FunctionCall("cos", [double_arg])))
                
                # Case 2: t1=sin^2, t2=cos^2 -> c2 * (cos^2 - sin^2)
                sin_arg_l = get_trig_arg(t1, "sin", 2)
                cos_arg_r = get_trig_arg(t2, "cos", 2)
                if sin_arg_l and cos_arg_r and are_terms_equal(sin_arg_l, cos_arg_r):
                     double_arg = simplify(BinaryOp(Number(2), Op.MUL, cos_arg_r))
                     return simplify(BinaryOp(c2, Op.MUL, FunctionCall("cos", [double_arg])))

            # Associative Constant Folding
            if isinstance(node.left, Number) and isinstance(node.right, BinaryOp) and node.right.op == Op.ADD:
                 if isinstance(node.right.left, Number):
                      new_value = node.left.value + node.right.left.value
                      return simplify(BinaryOp(Number(new_value), Op.ADD, node.right.right))

            # Simplification: A + (-B) -> A - B
            negative_right = extract_negative(node.right)
            if negative_right:
                 return simplify(BinaryOp(node.left, Op.SUB, negative_right))

        # Subtraction Rules
        if node.op == Op.SUB:
            if isinstance(node.right, Number) and node.right.value == 0:
                return node.left 
            if isinstance(node.left, Number) and node.left.value == 0:
                return simplify(UnaryOp(Op.SUB, node.right))
            if isinstance(node.left, (Number, Rational)) and isinstance(node.right, (Number, Rational)):
                return sub_scalars(node.left, node.right)
            
            # Combine Like Terms: c1*x - c2*x
            c1, t1 = get_term(node.left)
            c2, t2 = get_term(node.right)
            if are_terms_equal(t1, t2):
                new_coeff = sub_scalars(c1, c2)
                if isinstance(new_coeff, Number) and new_coeff.value == 0: return Number(0)
                if isinstance(new_coeff, Number) and new_coeff.value == 1: return t1
                return simplify(BinaryOp(new_coeff, Op.MUL, t1))
            
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
                 if are_terms_equal(c1, c2): # Need robust equality for ASTNode coefficients
                      # c * (cos^2 - sin^2) -> c * cos(2u)
                      double_arg = simplify(BinaryOp(Number(2), Op.MUL, cos_arg))
                      result = FunctionCall("cos", [double_arg])
                      if isinstance(c1, Number) and c1.value == 1: return result
                      return simplify(BinaryOp(c1, Op.MUL, result))

            # Associativity: (A + B) - C -> A + (B - C)
            # This allows combining terms like (x + 2x^2) - 4x^2 -> x + (2x^2 - 4x^2)
            if isinstance(node.left, BinaryOp) and node.left.op == Op.ADD:
                 A = node.left.left
                 B = node.left.right
                 C = node.right
                 # Attempt to simplify B - C
                 new_sub = simplify(BinaryOp(B, Op.SUB, C))
                 return simplify(BinaryOp(A, Op.ADD, new_sub))


        # Multiplication Rules
        if node.op == Op.MUL:
            if isinstance(node.left, Number) and node.left.value == 0: return Number(0)
            if isinstance(node.right, Number) and node.right.value == 0: return Number(0)
            if isinstance(node.left, Number) and node.left.value == 1: return node.right
            if isinstance(node.right, Number) and node.right.value == 1: return node.left
            if isinstance(node.left, (Number, Rational)) and isinstance(node.right, (Number, Rational)):
                return mul_scalars(node.left, node.right)
            
            # Associative Constant Folding: c1 * (c2 * x) -> (c1 * c2) * x
            if isinstance(node.left, (Number, Rational)) and isinstance(node.right, BinaryOp) and node.right.op == Op.MUL:
                 if isinstance(node.right.left, (Number, Rational)):
                      new_value = mul_scalars(node.left, node.right.left)
                      return simplify(BinaryOp(new_value, Op.MUL, node.right.right))
            
            # Constant Combination: c * (x / d) -> (c/d) * x
            if isinstance(node.left, (Number, Rational)) and isinstance(node.right, BinaryOp) and node.right.op == Op.DIV:
                if isinstance(node.right.right, (Number, Rational)) and node.right.right.value != 0:
                     new_val = div_scalars(node.left, node.right.right)
                     return simplify(BinaryOp(new_val, Op.MUL, node.right.left))

            # Combine Fraction Multiplication: x * (y / z) -> (x * y) / z
            if isinstance(node.right, BinaryOp) and node.right.op == Op.DIV:
                # x * (y / z)
                new_num = simplify(BinaryOp(node.left, Op.MUL, node.right.left))
                return simplify(BinaryOp(new_num, Op.DIV, node.right.right))

            # Combine Fraction Multiplication: (x / y) * z -> (x * z) / y
            if isinstance(node.left, BinaryOp) and node.left.op == Op.DIV:
                # (x / y) * z
                new_num = simplify(BinaryOp(node.left.left, Op.MUL, node.right))
                return simplify(BinaryOp(new_num, Op.DIV, node.left.right))

            # Distribute Constant: c * (a + b) -> c*a + c*b
            if isinstance(node.left, (Number, Rational)) and isinstance(node.right, BinaryOp) and node.right.op == Op.ADD:
                 # c * (a + b)
                 c = node.left
                 a = node.right.left
                 b = node.right.right
                 new_left = simplify(BinaryOp(c, Op.MUL, a))
                 new_right = simplify(BinaryOp(c, Op.MUL, b))
                 return simplify(BinaryOp(new_left, Op.ADD, new_right))
            
            # Distribute Constant: c * (a - b) -> c*a - c*b
            if isinstance(node.left, (Number, Rational)) and isinstance(node.right, BinaryOp) and node.right.op == Op.SUB:
                 # c * (a - b)
                 c = node.left
                 a = node.right.left
                 b = node.right.right
                 new_left = simplify(BinaryOp(c, Op.MUL, a))
                 new_right = simplify(BinaryOp(c, Op.MUL, b))
                 return simplify(BinaryOp(new_left, Op.SUB, new_right))
            
            # Pull constant from right child: x * (c * y) -> c * (x * y)
            if isinstance(node.right, BinaryOp) and node.right.op == Op.MUL and isinstance(node.right.left, (Number, Rational)):
                 c = node.right.left
                 y = node.right.right
                 return simplify(BinaryOp(c, Op.MUL, BinaryOp(node.left, Op.MUL, y)))
            
            # Pull constant from left child: (c * x) * y -> c * (x * y)
            if isinstance(node.left, BinaryOp) and node.left.op == Op.MUL and isinstance(node.left.left, (Number, Rational)):
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
                    new_exp = add_scalars(e1, e2)
                    if isinstance(new_exp, Number) and new_exp.value == 0: return Number(1)
                    if isinstance(new_exp, Number) and new_exp.value == 1: return b1
                    return simplify(BinaryOp(b1, Op.POW, new_exp))

        # Division Rules
        if node.op == Op.DIV:
            # 0 / x -> 0
            if isinstance(node.left, Number) and node.left.value == 0:
                 if isinstance(node.right, Number) and node.right.value == 0:
                      raise ValueError("Division by zero")
                 return Number(0)

            # Cancellation: x / (c * x) -> 1/c
            if isinstance(node.right, BinaryOp) and node.right.op == Op.MUL:
                 if are_terms_equal(node.left, node.right.right) and isinstance(node.right.left, (Number, Rational)): # x / (c*x)
                     return simplify(BinaryOp(Number(1), Op.DIV, node.right.left))
                 if are_terms_equal(node.left, node.right.left) and isinstance(node.right.right, (Number, Rational)): # x / (x*c)
                     return simplify(BinaryOp(Number(1), Op.DIV, node.right.right))

            # Cancellation: x / -x -> -1
            if isinstance(node.right, UnaryOp) and node.right.op == Op.SUB:
                 if are_terms_equal(node.left, node.right.operand):
                     return Number(-1)
            
            # Cancellation: -x / x -> -1
            if isinstance(node.left, UnaryOp) and node.left.op == Op.SUB:
                 if are_terms_equal(node.left.operand, node.right):
                     return Number(-1)
            
            # Cancellation: (-a) / (-b) -> a / b
            if isinstance(node.left, UnaryOp) and node.left.op == Op.SUB:
                if isinstance(node.right, UnaryOp) and node.right.op == Op.SUB:
                    # Both negative - cancel them out
                    return simplify(BinaryOp(node.left.operand, Op.DIV, node.right.operand))


            
            if isinstance(node.right, Number) and node.right.value == 1:
                 return node.left
            if isinstance(node.left, (Number, Rational)) and isinstance(node.right, (Number, Rational)) and node.right.value != 0:
                 return div_scalars(node.left, node.right)
             
            # (c * x^a) / x^b -> c * x^(a-b) or c / x^(b-a)
            if isinstance(node.left, BinaryOp) and node.left.op == Op.MUL:
                if isinstance(node.left.left, (Number, Rational)):
                    c = node.left.left
                    numerator_power_part = node.left.right
                    b1, e1 = get_power(numerator_power_part)
                    b2, e2 = get_power(node.right)
                    if are_terms_equal(b1, b2):
                        new_exp = sub_scalars(e1, e2)
                        if isinstance(new_exp, Number) and new_exp.value == 0:
                            return c
                        # Check positive logic? scalar arithmetic returns a value.
                        # We need to know if new_exp > 0.
                        is_pos = False
                        if isinstance(new_exp, Number) and new_exp.value > 0: is_pos = True
                        if isinstance(new_exp, Rational) and new_exp.numerator * new_exp.denominator > 0: is_pos = True
                        
                        if is_pos:
                            return simplify(BinaryOp(c, Op.MUL, BinaryOp(b1, Op.POW, new_exp)))
                        else:
                            # c / x^|new_exp|
                            neg_exp = simplify(UnaryOp(Op.SUB, new_exp)) # Actually need absolute value logic or just negate
                            # Better: c / x^(-new_exp)
                            # But we want positive exponent in denominator?
                            # If new_exp is negative, -new_exp is positive.
                            
                            # extract_negative might help but scalar sub_scalars returns a simplified node.
                            # Just use UnaryOp(Op.SUB, new_exp) and let simplification handle -(-1/2) -> 1/2?
                            # Or helper neg_scalar(n).
                            
                            if isinstance(new_exp, Number): neg_exp = Number(-new_exp.value)
                            elif isinstance(new_exp, Rational): neg_exp = Rational(-new_exp.numerator, new_exp.denominator)
                            else: neg_exp = UnaryOp(Op.SUB, new_exp)
                            
                            return simplify(BinaryOp(c, Op.DIV, BinaryOp(b1, Op.POW, neg_exp)))
            
            # x^a / (c * x^b) → (1/c) * x^(a-b) or 1/(c * x^(b-a))
            if isinstance(node.right, BinaryOp) and node.right.op == Op.MUL:
                if isinstance(node.right.left, (Number, Rational)):
                    c = node.right.left
                    denominator_power_part = node.right.right
                    b1, e1 = get_power(node.left)
                    b2, e2 = get_power(denominator_power_part)
                    if are_terms_equal(b1, b2):
                        new_exp = sub_scalars(e1, e2)
                        one_over_c = BinaryOp(Number(1), Op.DIV, c)
                        if isinstance(new_exp, Number) and new_exp.value == 0:
                            return one_over_c
                            
                        is_pos = False
                        if isinstance(new_exp, Number) and new_exp.value > 0: is_pos = True
                        if isinstance(new_exp, Rational) and new_exp.numerator * new_exp.denominator > 0: is_pos = True

                        if is_pos:
                            # (1/c) * x^(a-b)
                            return simplify(BinaryOp(one_over_c, Op.MUL, BinaryOp(b1, Op.POW, new_exp)))
                        else:
                            # 1 / (c * x^|new_exp|)
                            if isinstance(new_exp, Number): neg_exp = Number(-new_exp.value)
                            elif isinstance(new_exp, Rational): neg_exp = Rational(-new_exp.numerator, new_exp.denominator)
                            else: neg_exp = UnaryOp(Op.SUB, new_exp)
                            return simplify(BinaryOp(Number(1), Op.DIV, BinaryOp(c, Op.MUL, BinaryOp(b1, Op.POW, neg_exp))))
            
            # Combine Powers: x^a / x^b -> x^(a-b)
            b1, e1 = get_power(node.left)
            b2, e2 = get_power(node.right)
            if are_terms_equal(b1, b2):
                 new_exp = sub_scalars(e1, e2)
                 if isinstance(new_exp, Number) and new_exp.value == 0: return Number(1)
                 if isinstance(new_exp, Number) and new_exp.value == 1: return b1
                 return simplify(BinaryOp(b1, Op.POW, new_exp))


        # Exponentiation Rules
        if node.op == Op.POW:
            if isinstance(node.right, Number):
                if node.right.value == 0: return Number(1)
                if node.right.value == 1: return node.left
                if isinstance(node.left, (Number, Rational)):
                     return pow_scalars(node.left, node.right)
                # (x^a)^b -> x^(a*b)
                if isinstance(node.left, BinaryOp) and node.left.op == Op.POW:
                    if isinstance(node.left.right, (Number, Rational)):
                         b1 = node.left.left
                         e1 = node.left.right
                         e2 = node.right
                         new_exp = mul_scalars(e1, e2)
                         return simplify(BinaryOp(b1, Op.POW, new_exp))
                
                # (-a)^(even) -> a^(even)
                if isinstance(node.left, UnaryOp) and node.left.op == Op.SUB:
                    exponent = node.right.value
                    if exponent == int(exponent) and int(exponent) % 2 == 0:
                        # Even exponent - remove the negative
                        return simplify(BinaryOp(node.left.operand, Op.POW, node.right))

    elif isinstance(node, UnaryOp):
        operand_simplified = simplify(node.operand)
        node = UnaryOp(node.op, operand_simplified)
        if isinstance(node.operand, (Number, Rational)):
            if node.op == Op.ADD: return node.operand
            if node.op == Op.SUB:
                 if isinstance(node.operand, Number): return Number(-node.operand.value)
                 if isinstance(node.operand, Rational): return Rational(-node.operand.numerator, node.operand.denominator)
        # Simplify -(-x) -> x
        if node.op == Op.SUB and isinstance(node.operand, UnaryOp) and node.operand.op == Op.SUB:
             return node.operand.operand
    
    elif isinstance(node, FunctionCall):
        new_args = [simplify(arg) for arg in node.args]
        node = FunctionCall(node.name, new_args)
        
        # Normalize sqrt to power notation for better simplification
        if node.name == "sqrt" and len(node.args) == 1:
            return BinaryOp(node.args[0], Op.POW, Rational(1, 2))

    if debug:
        print(f"{indent}← {node}")
    return node
