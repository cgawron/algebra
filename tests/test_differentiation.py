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
        self.assertIsInstance(derivative, BinaryOp)
        self.assertEqual(derivative.op, Op.ADD)
        self.assertEqual(derivative.left.value, 1)
        self.assertEqual(derivative.right.value, 0)

    def test_mul(self):
        # d/dx (2 * x) = 0*x + 2*1 = 2
        node = BinaryOp(Number(2), Op.MUL, Variable("x"))
        derivative = diff(node, "x")
        # u'v + uv'
        # u=2, v=x => u'=0, v'=1
        # 0*x + 2*1
        self.assertEqual(derivative.op, Op.ADD)
        term1 = derivative.left
        term2 = derivative.right
        self.assertEqual(term1.op, Op.MUL)
        self.assertEqual(term1.left.value, 0)
        self.assertEqual(term1.right.name, "x")
        self.assertEqual(term2.op, Op.MUL)
        self.assertEqual(term2.left.value, 2)
        self.assertEqual(term2.right.value, 1)

    def test_pow(self):
        # d/dx (x^2) = 2 * x^(2-1) * 1 = 2 * x^1
        node = BinaryOp(Variable("x"), Op.POW, Number(2))
        derivative = diff(node, "x")
        # n * u^(n-1) * u'
        self.assertEqual(derivative.op, Op.MUL) # (n * u^(n-1)) * u'
        left_term = derivative.left # n * u^(n-1)
        self.assertEqual(left_term.op, Op.MUL)
        self.assertEqual(left_term.left.value, 2)
        # Check u^(n-1)
        pow_node = left_term.right
        self.assertEqual(pow_node.op, Op.POW)
        self.assertEqual(pow_node.left.name, "x")
        self.assertEqual(pow_node.right.value, 1)

    def test_sin(self):
        # d/dx sin(x) = cos(x) * 1
        node = FunctionCall("sin", [Variable("x")])
        derivative = diff(node, "x")
        self.assertEqual(derivative.op, Op.MUL)
        self.assertIsInstance(derivative.left, FunctionCall)
        self.assertEqual(derivative.left.name, "cos")
        self.assertEqual(derivative.right.value, 1)

    def test_cos(self):
        # d/dx cos(x) = -sin(x) * 1
        node = FunctionCall("cos", [Variable("x")])
        derivative = diff(node, "x")
        # -sin(u) * u'
        self.assertEqual(derivative.op, Op.MUL)
        neg_sin = derivative.left
        self.assertEqual(neg_sin.op, Op.SUB)
        self.assertIsInstance(neg_sin.operand, FunctionCall)
        self.assertEqual(neg_sin.operand.name, "sin")

    def test_exp(self):
        # d/dx exp(x) = exp(x) * 1
        node = FunctionCall("exp", [Variable("x")])
        derivative = diff(node, "x")
        self.assertEqual(derivative.op, Op.MUL)
        self.assertIsInstance(derivative.left, FunctionCall)
        self.assertEqual(derivative.left.name, "exp")
        self.assertEqual(derivative.right.value, 1)

if __name__ == '__main__':
    unittest.main()
