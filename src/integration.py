from .ast_nodes import ASTNode, Number, Variable, BinaryOp, UnaryOp, FunctionCall, Op
from .simplification import simplify, are_terms_equal
from .differentiation import diff
from typing import Tuple, Optional

def is_constant(node: ASTNode, var: str) -> bool:
    """Check if node is free of variable `var`."""
    if isinstance(node, Number):
        return True
    if isinstance(node, Variable):
        return node.name != var
    if isinstance(node, BinaryOp):
        return is_constant(node.left, var) and is_constant(node.right, var)
    if isinstance(node, UnaryOp):
        return is_constant(node.operand, var)
    if isinstance(node, FunctionCall):
        return all(is_constant(arg, var) for arg in node.args)
    return False

def get_linear_coeffs(node: ASTNode, var: str) -> Optional[Tuple[ASTNode, ASTNode]]:
    """
    Analyzes node to find 'a' and 'b' such that node = a * var + b.
    Returns (a, b) if linear, None otherwise.
    a and b are ASTNodes (constants).
    """
    if is_constant(node, var):
        return (Number(0), node)
    
    if isinstance(node, Variable) and node.name == var:
        return (Number(1), Number(0))
        
    if isinstance(node, BinaryOp):
        if node.op == Op.ADD:
            left_coeffs = get_linear_coeffs(node.left, var)
            right_coeffs = get_linear_coeffs(node.right, var)
            if left_coeffs and right_coeffs:
                # (a1 x + b1) + (a2 x + b2) = (a1+a2)x + (b1+b2)
                new_a = simplify(BinaryOp(left_coeffs[0], Op.ADD, right_coeffs[0]))
                new_b = simplify(BinaryOp(left_coeffs[1], Op.ADD, right_coeffs[1]))
                return (new_a, new_b)
                
        if node.op == Op.SUB:
            left_coeffs = get_linear_coeffs(node.left, var)
            right_coeffs = get_linear_coeffs(node.right, var)
            if left_coeffs and right_coeffs:
                # (a1 x + b1) - (a2 x + b2) = (a1-a2)x + (b1-b2)
                new_a = simplify(BinaryOp(left_coeffs[0], Op.SUB, right_coeffs[0]))
                new_b = simplify(BinaryOp(left_coeffs[1], Op.SUB, right_coeffs[1]))
                return (new_a, new_b)
                
        if node.op == Op.MUL:
            # c * (ax + b) = (ca)x + (cb)
            if is_constant(node.left, var):
                right_coeffs = get_linear_coeffs(node.right, var)
                if right_coeffs:
                    new_a = simplify(BinaryOp(node.left, Op.MUL, right_coeffs[0]))
                    new_b = simplify(BinaryOp(node.left, Op.MUL, right_coeffs[1]))
                    return (new_a, new_b)
            elif is_constant(node.right, var):
                left_coeffs = get_linear_coeffs(node.left, var)
                if left_coeffs:
                    new_a = simplify(BinaryOp(node.right, Op.MUL, left_coeffs[0]))
                    new_b = simplify(BinaryOp(node.right, Op.MUL, left_coeffs[1]))
                    return (new_a, new_b)
    
    # UnaryOps
    if isinstance(node, UnaryOp):
        if node.op == Op.SUB:
             coeffs = get_linear_coeffs(node.operand, var)
             if coeffs:
                 return (simplify(UnaryOp(Op.SUB, coeffs[0])), simplify(UnaryOp(Op.SUB, coeffs[1])))
    
    return None

def integrate(node: ASTNode, var: str) -> ASTNode:
    # Simplify the expression before integrating
    simplified_node = simplify(node)
    result = _integrate(simplified_node, var)
    return simplify(result)

def _integrate(node: ASTNode, var: str) -> ASTNode:
    # Constant rule: int(c) -> c * x
    if is_constant(node, var):
        return BinaryOp(node, Op.MUL, Variable(var))
    
    # Variable rule: int(x) -> x^2 / 2
    if isinstance(node, Variable) and node.name == var:
        return BinaryOp(BinaryOp(node, Op.POW, Number(2)), Op.DIV, Number(2))
    
    # Linearity rules: ADD / SUB
    if isinstance(node, BinaryOp):
        if node.op == Op.ADD:
            return BinaryOp(_integrate(node.left, var), Op.ADD, _integrate(node.right, var))
        if node.op == Op.SUB:
            return BinaryOp(_integrate(node.left, var), Op.SUB, _integrate(node.right, var))
            
        if node.op == Op.MUL:
            # Check for constant factor: int(c * f) -> c * int(f)
            if is_constant(node.left, var):
                return BinaryOp(node.left, Op.MUL, _integrate(node.right, var))
            if is_constant(node.right, var):
                return BinaryOp(node.right, Op.MUL, _integrate(node.left, var))
            
            # Reverse Chain Rule: int(u^n * du) -> u^(n+1)/(n+1)
            # Candidates for u:
            # 1. Base of Power: (g(x)^n) * h(x). u=g(x), du=h(x).
            # 2. Function itself: g(x) * h(x). u=g(x), du=h(x) (n=1).

            candidates = []
            # Check left as potential u^n or u
            if isinstance(node.left, BinaryOp) and node.left.op == Op.POW and is_constant(node.left.right, var):
                 candidates.append((node.left.left, node.left.right, node.right)) # (u, n, potential_du)
            elif not is_constant(node.left, var):
                 candidates.append((node.left, Number(1), node.right)) # (u, 1, potential_du)
            
            # Check right as potential u^n or u
            if isinstance(node.right, BinaryOp) and node.right.op == Op.POW and is_constant(node.right.right, var):
                 candidates.append((node.right.left, node.right.right, node.left))
            elif not is_constant(node.right, var):
                 candidates.append((node.right, Number(1), node.left))
            
            for u, n, potential_du in candidates:
                # Calculate exact du
                target_du = simplify(diff(u, var))
                # Check if potential_du is proportional to target_du
                
                # Handling 0 derivative
                if isinstance(target_du, Number) and target_du.value == 0:
                    continue
                    
                ratio = simplify(BinaryOp(potential_du, Op.DIV, target_du))
                #print(f"DEBUG: u={u}, du={potential_du}, target_du={target_du}, ratio={ratio}")
                
                if is_constant(ratio, var):
                    # Found match! int(u^n * k * du) = k * int(u^n du) = k * u^(n+1)/(n+1)
                    k = ratio
                    
                    # Handle n=-1 -> k * ln(u)
                    if isinstance(n, Number) and n.value == -1:
                        integral = BinaryOp(k, Op.MUL, FunctionCall("ln", [u]))
                        return integral
                    
                    new_n = simplify(BinaryOp(n, Op.ADD, Number(1)))
                    # u^(n+1) / (n+1)
                    term = BinaryOp(BinaryOp(u, Op.POW, new_n), Op.DIV, new_n)
                    return BinaryOp(k, Op.MUL, term)

            # Generalized Substitution: f(u) * du
            func_candidates = []
            if isinstance(node.left, FunctionCall) and len(node.left.args) == 1:
                func_candidates.append((node.left, node.right)) # (f(u), potential_du)
            
            if isinstance(node.right, FunctionCall) and len(node.right.args) == 1:
                func_candidates.append((node.right, node.left))

            for func_node, potential_du in func_candidates:
                u = func_node.args[0]
                # Skip if u is just x (already handled by basic rules or handled here trivially)
                # although if u=x, du=1. potential_du must be 1 (or constant).
                # int(f(x)*c) -> c*F(x). This overlaps with constant factor rule but is fine.
                
                target_du = simplify(diff(u, var))
                
                if isinstance(target_du, Number) and target_du.value == 0:
                    continue
                    
                ratio = simplify(BinaryOp(potential_du, Op.DIV, target_du))
                
                if is_constant(ratio, var):
                     k = ratio
                     # Result = k * Primitive(f)(u)
                     primitive = None
                     if func_node.name == "sin": # int(sin(u)du) -> -cos(u)
                         primitive = UnaryOp(Op.SUB, FunctionCall("cos", [u]))
                     elif func_node.name == "cos": # int(cos(u)du) -> sin(u)
                         primitive = FunctionCall("sin", [u])
                     elif func_node.name == "exp": # int(exp(u)du) -> exp(u)
                         primitive = FunctionCall("exp", [u])
                     elif func_node.name == "sqrt": # int(sqrt(u)du) -> (2/3) * u^(3/2)
                         u_to_three_halves = BinaryOp(u, Op.POW, Number(1.5))
                         primitive = BinaryOp(BinaryOp(Number(2), Op.DIV, Number(3)), Op.MUL, u_to_three_halves)
                     elif func_node.name == "ln": # int(ln(u)du) -> u*ln(u) - u
                         # u * ln(u) - u
                         term1 = BinaryOp(u, Op.MUL, FunctionCall("ln", [u]))
                         primitive = BinaryOp(term1, Op.SUB, u)
                     
                     if primitive:
                         return BinaryOp(k, Op.MUL, primitive)

            raise NotImplementedError(f"Integration of product '{node}' not implemented (unless constant factor).")
            
        if node.op == Op.DIV:
            # int(f / c) -> (1/c) * int(f)
            if is_constant(node.right, var):
                return BinaryOp(_integrate(node.left, var), Op.DIV, node.right)
            
            # Quotient Rule: int(u' / u) -> ln(u)
            # node.left = numerator (potential u' or k*u')
            # node.right = denominator (u)
            
            u = node.right
            target_du = simplify(diff(u, var))
            
            # If du is 0, u is constant, handled by is_constant above or caught here
            if isinstance(target_du, Number) and target_du.value == 0:
                 pass # Division by constant handled above
            else:
                 potential_du = node.left
                 ratio = simplify(BinaryOp(potential_du, Op.DIV, target_du))
                 
                 if is_constant(ratio, var):
                     # int(k * du / u) = k * ln(u)
                     k = ratio
                     ln_u = FunctionCall("ln", [u])
                     return simplify(BinaryOp(k, Op.MUL, ln_u))

            raise NotImplementedError(f"Integration of division '{node}' not implemented.")

        if node.op == Op.POW:
            # Power rule: int(x^n)
            if isinstance(node.left, Variable) and node.left.name == var and is_constant(node.right, var):
                exponent = node.right
                if isinstance(exponent, Number) and exponent.value == -1:
                    return FunctionCall("ln", [node.left])
                
                new_exponent = simplify(BinaryOp(exponent, Op.ADD, Number(1)))
                return BinaryOp(BinaryOp(node.left, Op.POW, new_exponent), Op.DIV, new_exponent)
            
            # Generalized Power Rule: int((ax+b)^n)
            coeffs = get_linear_coeffs(node.left, var)
            if coeffs and is_constant(node.right, var):
                a, b = coeffs
                # Check if a!=0
                if isinstance(a, Number) and a.value == 0:
                     # Then base is constant b. int(b^n) -> b^n * x
                     return BinaryOp(node, Op.MUL, Variable(var))
                
                exponent = node.right
                # u = ax+b, du = a dx => dx = du/a
                # int(u^n du/a) = (1/a) * u^(n+1)/(n+1)
                
                if isinstance(exponent, Number) and exponent.value == -1:
                     # (1/a) * ln(u)
                     ln_node = FunctionCall("ln", [node.left])
                     return BinaryOp(ln_node, Op.DIV, a)

                new_exponent = simplify(BinaryOp(exponent, Op.ADD, Number(1)))
                # u^(n+1) / (n+1)
                integral_u = BinaryOp(BinaryOp(node.left, Op.POW, new_exponent), Op.DIV, new_exponent)
                # Apply 1/a
                return BinaryOp(integral_u, Op.DIV, a)

            raise NotImplementedError(f"Integration of power '{node}' not implemented.")

    if isinstance(node, UnaryOp):
        if node.op == Op.SUB:
             return UnaryOp(Op.SUB, _integrate(node.operand, var))
        if node.op == Op.ADD:
             return _integrate(node.operand, var)

    if isinstance(node, FunctionCall):
        if len(node.args) == 1:
            arg = node.args[0]
            coeffs = get_linear_coeffs(arg, var)
            
            if coeffs:
                a, b = coeffs
                # Check for zero slope a=0 (constant arg)
                if isinstance(a, Number) and a.value == 0:
                     # Function is constant. int(C) -> C * x
                     return BinaryOp(node, Op.MUL, Variable(var))
                
                # int(f(ax+b))dx = (1/a) * F(ax+b)
                # Compute F(arg) treating arg as 'x'
                # Just construct the antiderivative F(arg)
                
                primitive = None
                if node.name == "sin": # int(sin) -> -cos
                     primitive = UnaryOp(Op.SUB, FunctionCall("cos", [arg]))
                elif node.name == "cos": # int(cos) -> sin
                     primitive = FunctionCall("sin", [arg])
                elif node.name == "exp": # int(exp) -> exp
                     primitive = FunctionCall("exp", [arg])
                elif node.name == "sqrt": # int(sqrt(u)) -> (2/3) * u^(3/2)
                     # sqrt(u) = u^(1/2), integral is u^(3/2) / (3/2) = (2/3) * u^(3/2)
                     u_to_three_halves = BinaryOp(arg, Op.POW, Number(1.5))
                     primitive = BinaryOp(BinaryOp(Number(2), Op.DIV, Number(3)), Op.MUL, u_to_three_halves)
                elif node.name == "ln": # int(ln(x)) -> x*ln(x) - x
                     # int(ln(u)) -> u*ln(u) - u.
                     term1 = BinaryOp(arg, Op.MUL, FunctionCall("ln", [arg]))
                     primitive = BinaryOp(term1, Op.SUB, arg)
                
                if primitive:
                     # Result = (1/a) * primitive
                     # -> primitive / a
                     # Only if a != 1
                     if isinstance(a, Number) and a.value == 1:
                          return primitive
                     return BinaryOp(primitive, Op.DIV, a)

            
            raise NotImplementedError(f"Integration of function '{node.name}' with arg '{arg}' not implemented.")

    raise NotImplementedError(f"Integration not implemented for node: {node}")
