import unittest
from src.ast_nodes import Number, Variable, BinaryOp, UnaryOp, FunctionCall, Op
from src.differentiation import diff

class TestDifferentiation(unittest.TestCase):
    def test_number(self):
        node = Number(42)
        derivative = diff(node, "x")
        self.assertIsInstance(derivative, Number)
        self.assertEqual(derivative.value, 0)

    def test_variable_match(self):
        node = Variable("x")
        derivative = diff(node, "x")
        self.assertIsInstance(derivative, Number)
        self.assertEqual(derivative.value, 1)

    def test_variable_mismatch(self):
        node = Variable("y")
        derivative = diff(node, "x")
        self.assertIsInstance(derivative, Number)
        self.assertEqual(derivative.value, 0)

    def test_add(self):
        # d/dx (x + 1) = 1 + 0 = 1
        node = BinaryOp(Variable("x"), Op.ADD, Number(1))
        derivative = diff(node, "x")
        self.assertIsInstance(derivative, Number)
        self.assertEqual(derivative.value, 1)

    def test_mul(self):
        # d/dx (2 * x) = 0*x + 2*1 = 0 + 2 = 2
        node = BinaryOp(Number(2), Op.MUL, Variable("x"))
        derivative = diff(node, "x")
        # u'v + uv' -> 0*x + 2*1 -> 0 + 2 -> 2
        self.assertIsInstance(derivative, Number)
        self.assertEqual(derivative.value, 2)

    def test_pow(self):
        # d/dx (x^2) = 2 * x^(2-1) * 1 = 2 * x^1 = 2 * x
        node = BinaryOp(Variable("x"), Op.POW, Number(2))
        derivative = diff(node, "x")
        # n * u^(n-1) * u' -> 2 * x^1 * 1 -> 2 * x
        self.assertEqual(derivative.op, Op.MUL)
        self.assertEqual(derivative.left.value, 2)
        self.assertEqual(derivative.right.name, "x")

    def test_sin(self):
        # d/dx sin(x) = cos(x) * 1 = cos(x)
        node = FunctionCall("sin", [Variable("x")])
        derivative = diff(node, "x")
        self.assertIsInstance(derivative, FunctionCall)
        self.assertEqual(derivative.name, "cos")
        self.assertEqual(derivative.args[0].name, "x")

    def test_cos(self):
        # d/dx cos(x) = -sin(x) * 1 = -sin(x)
        node = FunctionCall("cos", [Variable("x")])
        derivative = diff(node, "x")
        self.assertIsInstance(derivative, UnaryOp)
        self.assertEqual(derivative.op, Op.SUB)
        self.assertEqual(derivative.operand.name, "sin")

    def test_exp(self):
        # d/dx exp(x) = exp(x) * 1 = exp(x)
        node = FunctionCall("exp", [Variable("x")])
        derivative = diff(node, "x")
        self.assertIsInstance(derivative, FunctionCall)
        self.assertEqual(derivative.name, "exp")
        self.assertEqual(derivative.args[0].name, "x")

if __name__ == '__main__':
    unittest.main()
