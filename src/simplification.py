from .ast_nodes import ASTNode, Number, Variable, BinaryOp, UnaryOp, FunctionCall, Op

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
                 # Swap
                 node.left, node.right = node.right, node.left
                 rank_left, rank_right = rank_right, rank_left
             elif rank_right == rank_left:
                 # Tie-break lexicographically (e.g. x vs y, or 2 vs 3 if both numbers)
                 # Actually Numbers are usually simplified to single number if possible,
                 # but for Variables x vs y -> x first.
                 str_left = str(node.left)
                 str_right = str(node.right)
                 if str_right < str_left:
                      node.left, node.right = node.right, node.left
        
        # 2. Simplification Rules (re-apply after potential swap)
        
        # Addition Rules
        if node.op == Op.ADD:
            if isinstance(node.left, Number) and node.left.value == 0:
                return node.right # 0 + x = x
            if isinstance(node.right, Number) and node.right.value == 0:
                return node.left # x + 0 = x
            if isinstance(node.left, Number) and isinstance(node.right, Number):
                return Number(node.left.value + node.right.value) # Constant folding
            
            # Associative Constant Folding: (Num + (Num + Node)) -> (Num+Num) + Node
            # Since we reordered, Numbers should bubble to the left.
            # But structure might be right-associative `Num + BindaryOp(ADD, Num, Node)`?
            # Or left-associative `BinaryOp(ADD, Num, Num) + Node`.
            # If structure is (Num + (Num + Node)): Right child is BinaryOp(ADD).
            if isinstance(node.left, Number) and isinstance(node.right, BinaryOp) and node.right.op == Op.ADD:
                 if isinstance(node.right.left, Number):
                      new_value = node.left.value + node.right.left.value
                      return simplify(BinaryOp(Number(new_value), Op.ADD, node.right.right))

        # Subtraction Rules
        if node.op == Op.SUB:
            if isinstance(node.right, Number) and node.right.value == 0:
                return node.left # x - 0 = x
            if isinstance(node.left, Number) and node.left.value == 0:
                return simplify(UnaryOp(Op.SUB, node.right)) # 0 - x = -x
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
            
            # Associative Constant Folding for MUL
            if isinstance(node.left, Number) and isinstance(node.right, BinaryOp) and node.right.op == Op.MUL:
                 if isinstance(node.right.left, Number):
                      new_value = node.left.value * node.right.left.value
                      return simplify(BinaryOp(Number(new_value), Op.MUL, node.right.right))

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

    return node
