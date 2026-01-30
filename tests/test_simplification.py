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

    def test_collect_like_terms(self):
        # x + x -> 2x
        node = BinaryOp(Variable("x"), Op.ADD, Variable("x"))
        simplified = simplify(node)
        self.assertEqual(simplified.op, Op.MUL)
        self.assertEqual(simplified.left.value, 2)
        self.assertEqual(simplified.right.name, "x")
        
        # 2x + 3x -> 5x
        term1 = BinaryOp(Number(2), Op.MUL, Variable("x"))
        term2 = BinaryOp(Number(3), Op.MUL, Variable("x"))
        node = BinaryOp(term1, Op.ADD, term2)
        simplified = simplify(node)
        self.assertEqual(simplified.left.value, 5)
        self.assertEqual(simplified.right.name, "x")

    def test_combine_products(self):
        # x * x -> x^2
        node = BinaryOp(Variable("x"), Op.MUL, Variable("x"))
        simplified = simplify(node)
        self.assertEqual(simplified.op, Op.POW)
        self.assertEqual(simplified.left.name, "x")
        self.assertEqual(simplified.right.value, 2)

    def test_combine_products_advanced(self):
        # x * (x * x) -> x^3
        # x * x^2 -> x^3
        inner = BinaryOp(Variable("x"), Op.MUL, Variable("x"))
        outer = BinaryOp(Variable("x"), Op.MUL, inner)
        simplified = simplify(outer)
        # simplify(outer) -> simplify(x, x^2) -> x^3
        self.assertEqual(simplified.op, Op.POW)
        self.assertEqual(simplified.left.name, "x")
        self.assertEqual(simplified.right.value, 3)

    def test_complex_simplification(self):
        # x * (x + x) + x * x
        # x * (2x) + x^2 -> 2x^2 + x^2 -> 3x^2
        
        # Construct: x * (x + x)
        term1 = BinaryOp(Variable("x"), Op.MUL, BinaryOp(Variable("x"), Op.ADD, Variable("x")))
        # Construct: x * x
        term2 = BinaryOp(Variable("x"), Op.MUL, Variable("x"))
        # Total
        node = BinaryOp(term1, Op.ADD, term2)
        
        simplified = simplify(node)
        # Should be 3 * x^2
        self.assertEqual(simplified.op, Op.MUL)
        self.assertEqual(simplified.left.value, 3)
        self.assertEqual(simplified.right.op, Op.POW)
        self.assertEqual(simplified.right.left.name, "x")
        self.assertEqual(simplified.right.right.value, 2)

    def test_user_requested_simplification(self):
        # x * (2 * x) + x ^ 2 -> 3 * x^2
        term1 = BinaryOp(Variable("x"), Op.MUL, BinaryOp(Number(2), Op.MUL, Variable("x")))
        term2 = BinaryOp(Variable("x"), Op.POW, Number(2))
        node = BinaryOp(term1, Op.ADD, term2)
        
        simplified = simplify(node)
        self.assertEqual(simplified.op, Op.MUL)
        self.assertEqual(simplified.left.value, 3)
        self.assertEqual(simplified.right.op, Op.POW)
        self.assertEqual(simplified.right.left.name, "x")
        self.assertEqual(simplified.right.right.value, 2)

if __name__ == '__main__':
    unittest.main()
