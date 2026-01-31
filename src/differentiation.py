from .ast_nodes import ASTNode, Number, Variable, BinaryOp, UnaryOp, FunctionCall, Op, Rational
from .simplification import simplify, sub_scalars, mul_scalars, div_scalars

def diff(node: ASTNode, var: str) -> ASTNode:
    result = _diff(node, var)
    return simplify(result)

def _diff(node: ASTNode, var: str) -> ASTNode:
    if isinstance(node, Number):
        return Number(0)
    
    if isinstance(node, Variable):
        if node.name == var:
            return Number(1)
        else:
            return Number(0)
            
    if isinstance(node, UnaryOp):
        if node.op == Op.SUB:
            return UnaryOp(Op.SUB, diff(node.operand, var))
        if node.op == Op.ADD: # Unary +
            return diff(node.operand, var)

    if isinstance(node, BinaryOp):
        if node.op == Op.ADD:
            return BinaryOp(diff(node.left, var), Op.ADD, diff(node.right, var))
        elif node.op == Op.SUB:
            return BinaryOp(diff(node.left, var), Op.SUB, diff(node.right, var))
        elif node.op == Op.MUL:
            # (u*v)' = u'v + uv'
            left_diff = diff(node.left, var)
            right_diff = diff(node.right, var)
            term1 = BinaryOp(left_diff, Op.MUL, node.right)
            term2 = BinaryOp(node.left, Op.MUL, right_diff)
            return BinaryOp(term1, Op.ADD, term2)
        elif node.op == Op.DIV:
            # (u/v)' = (u'v - uv') / v^2
            left_diff = diff(node.left, var)
            right_diff = diff(node.right, var)
            numerator_term1 = BinaryOp(left_diff, Op.MUL, node.right)
            numerator_term2 = BinaryOp(node.left, Op.MUL, right_diff)
            numerator = BinaryOp(numerator_term1, Op.SUB, numerator_term2)
            denominator = BinaryOp(node.right, Op.POW, Number(2))
            return BinaryOp(numerator, Op.DIV, denominator)
        elif node.op == Op.POW:
            # Check for x^n case (variable base, constant exp)
            if isinstance(node.right, (Number, Rational)):
                exponent = node.right
                # n * u^(n-1) * u'
                new_exponent = simplify(sub_scalars(exponent, Number(1)))
                base_pow = BinaryOp(node.left, Op.POW, new_exponent)
                term = BinaryOp(exponent, Op.MUL, base_pow)
                return BinaryOp(term, Op.MUL, diff(node.left, var))
            # Check for b^u case (constant base, variable exp)
            elif isinstance(node.left, (Number, Rational)):
                # b^u * ln(b) * u'
                base = node.left
                exponent = node.right
                ln_base = FunctionCall("ln", [base])
                term = BinaryOp(node, Op.MUL, ln_base)
                return BinaryOp(term, Op.MUL, diff(exponent, var))
            else:
                # General case: u^v -> u^v * (v' * ln(u) + v * u' / u)
                base = node.left
                exponent = node.right
                base_diff = diff(base, var)
                exponent_diff = diff(exponent, var)
                
                ln_base = FunctionCall("ln", [base])
                term1 = BinaryOp(exponent_diff, Op.MUL, ln_base)
                
                term2_num = BinaryOp(exponent, Op.MUL, base_diff)
                term2 = BinaryOp(term2_num, Op.DIV, base)
                
                sum_terms = BinaryOp(term1, Op.ADD, term2)
                return BinaryOp(node, Op.MUL, sum_terms)

    if isinstance(node, FunctionCall):
        if len(node.args) != 1:
             raise NotImplementedError(f"Differentiation for functions with {len(node.args)} arguments not implemented.")
        
        arg = node.args[0]
        arg_diff = diff(node.args[0], var)
        
        if node.name == "sin":
            # cos(u) * u'
            func_derivative = FunctionCall("cos", [arg])
            return BinaryOp(func_derivative, Op.MUL, arg_diff)
        elif node.name == "cos":
            # -sin(u) * u'
            # -sin(u) is UnaryOp(-, sin(u))
            func_derivative = UnaryOp(Op.SUB, FunctionCall("sin", [arg]))
            return BinaryOp(func_derivative, Op.MUL, arg_diff)
        elif node.name == "exp":
            # exp(u) * u'
            return BinaryOp(FunctionCall("exp", [arg]), Op.MUL, arg_diff)
        elif node.name == "ln":
            # (1/u) * u' = u' / u
            return BinaryOp(arg_diff, Op.DIV, arg) # Direct (u'/u) is simpler than (1/u)*u'
        elif node.name == "sqrt":
            # d/dx[sqrt(u)] = u' / (2*sqrt(u)) -> (1/2) * u' * u^(-1/2)
            # Actually standard form: u' / (2 * u^(1/2)) = 0.5 * u' * u^(-0.5)
            # using Rational: 1/2 * u' * u^(-1/2)
            # But let's keep structure similar: u' / (2 * sqrt(u))
            two_sqrt_u = BinaryOp(Number(2), Op.MUL, FunctionCall("sqrt", [arg]))
            return BinaryOp(arg_diff, Op.DIV, two_sqrt_u)
        else:
             raise NotImplementedError(f"Differentiation for function '{node.name}' not implemented.")
    
    raise NotImplementedError(f"Differentiation not implemented for node: {node}")
