from .ast_nodes import ASTNode, Number, Variable, BinaryOp, UnaryOp, FunctionCall, Op
from .simplification import simplify

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
            if isinstance(node.right, Number):
                exponent = node.right.value
                # n * u^(n-1) * u'
                new_exponent = Number(exponent - 1)
                base_pow = BinaryOp(node.left, Op.POW, new_exponent)
                term = BinaryOp(Number(exponent), Op.MUL, base_pow)
                return BinaryOp(term, Op.MUL, diff(node.left, var))
            else:
                raise NotImplementedError("Differentiation for non-constant exponent not implemented yet.")

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
            # d/dx[sqrt(u)] = u' / (2*sqrt(u))
            two_sqrt_u = BinaryOp(Number(2), Op.MUL, FunctionCall("sqrt", [arg]))
            return BinaryOp(arg_diff, Op.DIV, two_sqrt_u)
        else:
             raise NotImplementedError(f"Differentiation for function '{node.name}' not implemented.")
    
    raise NotImplementedError(f"Differentiation not implemented for node: {node}")
