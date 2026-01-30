import unittest
from src.ast_nodes import Number, Variable, BinaryOp, UnaryOp, FunctionCall, Op
from src.simplification import simplify

class TestSimplification(unittest.TestCase):
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
        
        # 1 * x -> x
        node = BinaryOp(Number(1), Op.MUL, Variable("x"))
        simplified = simplify(node)
        self.assertIsInstance(simplified, Variable)
        self.assertEqual(simplified.name, "x")

    def test_simplify_mul_zero(self):
        # x * 0 -> 0
        node = BinaryOp(Variable("x"), Op.MUL, Number(0))
        simplified = simplify(node)
        self.assertIsInstance(simplified, Number)
        self.assertEqual(simplified.value, 0)

    def test_simplify_pow_zero(self):
        # x ^ 0 -> 1
        node = BinaryOp(Variable("x"), Op.POW, Number(0))
        simplified = simplify(node)
        self.assertIsInstance(simplified, Number)
        self.assertEqual(simplified.value, 1)

    def test_simplify_pow_one(self):
        # x ^ 1 -> x
        node = BinaryOp(Variable("x"), Op.POW, Number(1))
        simplified = simplify(node)
        self.assertIsInstance(simplified, Variable)
        self.assertEqual(simplified.name, "x")

    def test_simplify_sub_zero(self):
        # x - 0 -> x
        node = BinaryOp(Variable("x"), Op.SUB, Number(0))
        simplified = simplify(node)
        self.assertIsInstance(simplified, Variable)
        self.assertEqual(simplified.name, "x")

    def test_simplify_nested(self):
        # (x + 0) * 1 -> x
        inner = BinaryOp(Variable("x"), Op.ADD, Number(0))
        outer = BinaryOp(inner, Op.MUL, Number(1))
        simplified = simplify(outer)
        self.assertIsInstance(simplified, Variable)
        self.assertEqual(simplified.name, "x")

    def test_constant_folding(self):
        # 1 + 2 -> 3
        node = BinaryOp(Number(1), Op.ADD, Number(2))
        simplified = simplify(node)
        self.assertIsInstance(simplified, Number)
        self.assertEqual(simplified.value, 3)

if __name__ == '__main__':
    unittest.main()
