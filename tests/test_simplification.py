import unittest
from src.ast_nodes import Number, Variable, BinaryOp, UnaryOp, FunctionCall, Op
from src.simplification import simplify

class TestSimplification(unittest.TestCase):
    def test_canonical_add(self):
        # x + 1 -> 1 + x
        node = BinaryOp(Variable("x"), Op.ADD, Number(1))
        simplified = simplify(node)
        self.assertIsInstance(simplified, BinaryOp)
        self.assertEqual(simplified.op, Op.ADD)
        self.assertIsInstance(simplified.left, Number)
        self.assertEqual(simplified.left.value, 1)
        self.assertIsInstance(simplified.right, Variable)
        self.assertEqual(simplified.right.name, "x")

    def test_canonical_mul(self):
        # x * 2 -> 2 * x
        node = BinaryOp(Variable("x"), Op.MUL, Number(2))
        simplified = simplify(node)
        self.assertIsInstance(simplified, BinaryOp)
        self.assertEqual(simplified.op, Op.MUL)
        self.assertIsInstance(simplified.left, Number)
        self.assertEqual(simplified.left.value, 2)
        self.assertIsInstance(simplified.right, Variable)
        self.assertEqual(simplified.right.name, "x")
    
    def test_var_vs_function(self):
        # sin(x) + x -> x + sin(x)
        # Variable rank (1) < FunctionCall rank (4)
        node = BinaryOp(FunctionCall("sin", [Variable("x")]), Op.ADD, Variable("x"))
        simplified = simplify(node)
        self.assertEqual(simplified.op, Op.ADD)
        self.assertIsInstance(simplified.left, Variable)
        self.assertIsInstance(simplified.right, FunctionCall)

    def test_associative_folding_add(self):
        # 1 + (2 + x) -> 3 + x
        inner = BinaryOp(Number(2), Op.ADD, Variable("x"))
        outer = BinaryOp(Number(1), Op.ADD, inner)
        simplified = simplify(outer)
        self.assertEqual(simplified.left.value, 3)
        self.assertEqual(simplified.right.name, "x")

    def test_associative_folding_mul(self):
        # 2 * (3 * x) -> 6 * x
        inner = BinaryOp(Number(3), Op.MUL, Variable("x"))
        outer = BinaryOp(Number(2), Op.MUL, inner)
        simplified = simplify(outer)
        self.assertEqual(simplified.left.value, 6)
        self.assertEqual(simplified.right.name, "x")

    def test_associative_folding_with_reordering(self):
        # (x + 2) + 1 -> 1 + (2 + x) -> 3 + x
        inner = BinaryOp(Variable("x"), Op.ADD, Number(2)) # -> 2 + x (canonical)
        outer = BinaryOp(inner, Op.ADD, Number(1)) # -> 1 + (2 + x) (canonical) -> 3 + x (folding)
        simplified = simplify(outer)
        # inner: simplify(x+2) -> 2+x
        # outer: BinaryOp(2+x, ADD, 1). 
        # simplify(outer):
        #   left=2+x, right=1.
        #   rank(right) < rank(left)? 0 < 3. Swap.
        #   left=1, right=2+x.
        #   Associative check: right is ADD. right.left is Number(2).
        #   1 + 2 = 3.
        #   Return 3 + x.
        self.assertEqual(simplified.left.value, 3)
        self.assertEqual(simplified.right.name, "x")

    def test_simplify_add_zero(self):
        # x + 0 -> x
        node = BinaryOp(Variable("x"), Op.ADD, Number(0))
        simplified = simplify(node)
        self.assertIsInstance(simplified, Variable)
        self.assertEqual(simplified.name, "x")
        
        # 0 + x -> x
        node = BinaryOp(Number(0), Op.ADD, Variable("x"))
        simplified = simplify(node)
        self.assertIsInstance(simplified, Variable)
        self.assertEqual(simplified.name, "x")

    def test_simplify_mul_one(self):
        # x * 1 -> x
        node = BinaryOp(Variable("x"), Op.MUL, Number(1))
        simplified = simplify(node)
        self.assertIsInstance(simplified, Variable)
        self.assertEqual(simplified.name, "x")

    def test_simplify_mul_zero(self):
        # x * 0 -> 0
        node = BinaryOp(Variable("x"), Op.MUL, Number(0))
        simplified = simplify(node)
        self.assertIsInstance(simplified, Number)
        self.assertEqual(simplified.value, 0)
    
    def test_nested_canonical(self):
        # (x * 2) * 3 -> (2 * x) * 3 -> 3 * (2 * x) -> 6 * x
        inner = BinaryOp(Variable("x"), Op.MUL, Number(2))
        outer = BinaryOp(inner, Op.MUL, Number(3))
        simplified = simplify(outer)
        self.assertEqual(simplified.left.value, 6)
        self.assertEqual(simplified.right.name, "x")

if __name__ == '__main__':
    unittest.main()
