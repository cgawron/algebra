from .ast_nodes import ASTNode, Number, Variable, BinaryOp, UnaryOp, FunctionCall, Op

def simplify(node: ASTNode) -> ASTNode:
    if isinstance(node, BinaryOp):
        # Simplify children first (bottom-up)
        node.left = simplify(node.left)
        node.right = simplify(node.right)

        # Addition Rules
        if node.op == Op.ADD:
            if isinstance(node.left, Number) and node.left.value == 0:
                return node.right # 0 + x = x
            if isinstance(node.right, Number) and node.right.value == 0:
                return node.left # x + 0 = x
            if isinstance(node.left, Number) and isinstance(node.right, Number):
                return Number(node.left.value + node.right.value) # Constant folding

        # Subtraction Rules (Optional but good)
        if node.op == Op.SUB:
            if isinstance(node.right, Number) and node.right.value == 0:
                return node.left # x - 0 = x
            if isinstance(node.left, Number) and node.left.value == 0:
                return UnaryOp(Op.SUB, node.right) # 0 - x = -x
            if isinstance(node.left, Number) and isinstance(node.right, Number):
                return Number(node.left.value - node.right.value)

        # Multiplication Rules
        if node.op == Op.MUL:
            if isinstance(node.left, Number) and node.left.value == 0:
                return Number(0) # 0 * x = 0
            if isinstance(node.right, Number) and node.right.value == 0:
                return Number(0) # x * 0 = 0
            if isinstance(node.left, Number) and node.left.value == 1:
                return node.right # 1 * x = x
            if isinstance(node.right, Number) and node.right.value == 1:
                return node.left # x * 1 = x
            if isinstance(node.left, Number) and isinstance(node.right, Number):
                return Number(node.left.value * node.right.value)

        # Division Rules
        if node.op == Op.DIV:
             if isinstance(node.right, Number) and node.right.value == 1:
                 return node.left # x / 1 = x
             if isinstance(node.left, Number) and isinstance(node.right, Number) and node.right.value != 0:
                 return Number(node.left.value / node.right.value)

        # Exponentiation Rules
        if node.op == Op.POW:
            if isinstance(node.right, Number):
                if node.right.value == 0:
                    return Number(1) # x ^ 0 = 1
                if node.right.value == 1:
                    return node.left # x ^ 1 = x
            if isinstance(node.left, Number) and isinstance(node.right, Number):
                 return Number(node.left.value ** node.right.value)

    elif isinstance(node, UnaryOp):
        node.operand = simplify(node.operand)
        if isinstance(node.operand, Number):
            if node.op == Op.ADD:
                return node.operand
            if node.op == Op.SUB:
                return Number(-node.operand.value)
    
    elif isinstance(node, FunctionCall):
        new_args = [simplify(arg) for arg in node.args]
        node.args = new_args
        # Could add constant folding for functions here if desired

    return node
