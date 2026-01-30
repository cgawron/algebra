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

    def test_negative_simplification(self):
        # 2 * (-sin(x) * cos(x)) + 2 * (cos(x) * sin(x)) -> 0
        
        # term1: 2 * (-1 * (sin * cos))
        # -sin(x)
        neg_sin = UnaryOp(Op.SUB, FunctionCall("sin", [Variable("x")]))
        # neg_sin * cos
        prod1 = BinaryOp(neg_sin, Op.MUL, FunctionCall("cos", [Variable("x")]))
        # 2 * prod1
        term1 = BinaryOp(Number(2), Op.MUL, prod1)
        
        # term2: 2 * (cos * sin)
        prod2 = BinaryOp(FunctionCall("cos", [Variable("x")]), Op.MUL, FunctionCall("sin", [Variable("x")]))
        term2 = BinaryOp(Number(2), Op.MUL, prod2)
        
        node = BinaryOp(term1, Op.ADD, term2)
        
        simplified = simplify(node)
        self.assertIsInstance(simplified, Number)
        self.assertEqual(simplified.value, 0)
        
    def test_negative_propagation(self):
        # (-a) * b -> -(a * b)
        node = BinaryOp(UnaryOp(Op.SUB, Variable("a")), Op.MUL, Variable("b"))
        simplified = simplify(node)
        self.assertIsInstance(simplified, UnaryOp)
        self.assertEqual(simplified.op, Op.SUB)
        self.assertIsInstance(simplified.operand, BinaryOp)
        self.assertEqual(simplified.operand.op, Op.MUL)
        
        # a * (-b) -> -(a * b)
        node = BinaryOp(Variable("a"), Op.MUL, UnaryOp(Op.SUB, Variable("b")))
        simplified = simplify(node)
        self.assertIsInstance(simplified, UnaryOp)
        self.assertEqual(simplified.op, Op.SUB)

        # (-a) * (-b) -> a * b
        node = BinaryOp(UnaryOp(Op.SUB, Variable("a")), Op.MUL, UnaryOp(Op.SUB, Variable("b")))
        simplified = simplify(node)
        self.assertIsInstance(simplified, BinaryOp)
        self.assertEqual(simplified.op, Op.MUL)

    def test_pythagorean_identity(self):
        # sin(x)^2 + cos(x)^2 -> 1
        term1 = BinaryOp(FunctionCall("sin", [Variable("x")]), Op.POW, Number(2))
        term2 = BinaryOp(FunctionCall("cos", [Variable("x")]), Op.POW, Number(2))
        node = BinaryOp(term1, Op.ADD, term2)
        
        simplified = simplify(node)
        self.assertIsInstance(simplified, Number)
        self.assertEqual(simplified.value, 1)

    def test_double_angle_identity(self):
        # cos(x)^2 - sin(x)^2 -> cos(2x)
        # 1 * cos^2 + (-1) * sin^2
        term1 = BinaryOp(FunctionCall("cos", [Variable("x")]), Op.POW, Number(2))
        term2 = UnaryOp(Op.SUB, BinaryOp(FunctionCall("sin", [Variable("x")]), Op.POW, Number(2)))
        # Or BinaryOp(cos^2, ADD, Unary(SUB, sin^2))
        # Simplify handles ADD.
        # But parser produces SUB(cos^2, sin^2).
        # My simplify handles SUB?
        # Let's test ADD(cos^2, Unary(SUB, sin^2)).
        # As well as SUB(cos^2, sin^2).
        
        # Case 1: SUB node
        node = BinaryOp(term1, Op.SUB, BinaryOp(FunctionCall("sin", [Variable("x")]), Op.POW, Number(2)))
        simplified = simplify(node)
        self.assertIsInstance(simplified, FunctionCall)
        self.assertEqual(simplified.name, "cos")
        # Arg 2x
        self.assertIsInstance(simplified.args[0], BinaryOp)
        self.assertEqual(simplified.args[0].left.value, 2)
        
    def test_double_angle_identity_canonical(self):
        # -sin(x)^2 + cos(x)^2 -> cos(2x)
        term1 = UnaryOp(Op.SUB, BinaryOp(FunctionCall("sin", [Variable("x")]), Op.POW, Number(2)))
        term2 = BinaryOp(FunctionCall("cos", [Variable("x")]), Op.POW, Number(2))
        node = BinaryOp(term1, Op.ADD, term2)
        
        simplified = simplify(node)
        self.assertIsInstance(simplified, FunctionCall)
        self.assertEqual(simplified.name, "cos")

    def test_division_combination(self):
        # 2 * (x / 4) -> 0.5 * x
        node = BinaryOp(Number(2), Op.MUL, BinaryOp(Variable("x"), Op.DIV, Number(4)))
        simplified = simplify(node)
        self.assertEqual(simplified.op, Op.MUL)
        self.assertEqual(simplified.left.value, 0.5)
        self.assertEqual(simplified.right.name, "x")
        
        # 2 * (x / 2) -> 1 * x -> x
        node = BinaryOp(Number(2), Op.MUL, BinaryOp(Variable("x"), Op.DIV, Number(2)))
        simplified = simplify(node)
        self.assertIsInstance(simplified, Variable)
        self.assertEqual(simplified.name, "x")

    def test_distribution_add(self):
        # 2 * (x + 1) -> 2x + 2
        # Note: 2x + 2 might be simplified further or just (2x + 2) depending on canonical ordering.
        # 1: 2*x + 2*1 -> 2x + 2.
        # Canonical: Number(2) vs BinaryOp(2x). Number is rank 0. BinaryOp is rank 3.
        # So 2 + 2x.
        
        node = BinaryOp(Number(2), Op.MUL, BinaryOp(Variable("x"), Op.ADD, Number(1)))
        simplified = simplify(node)
        
        self.assertEqual(simplified.op, Op.ADD)
        # Check canonical order: 2 + 2x
        self.assertIsInstance(simplified.left, Number)
        self.assertEqual(simplified.left.value, 2)
        self.assertEqual(simplified.right.op, Op.MUL)
        self.assertEqual(simplified.right.left.value, 2)
        self.assertEqual(simplified.right.right.name, "x")

    def test_distribution_sub(self):
        # 2 * (x - 1) -> 2x - 2
        
        node = BinaryOp(Number(2), Op.MUL, BinaryOp(Variable("x"), Op.SUB, Number(1)))
        simplified = simplify(node)
        
        self.assertEqual(simplified.op, Op.SUB)
        # 2x - 2
        self.assertEqual(simplified.left.op, Op.MUL)
        self.assertEqual(simplified.left.left.value, 2)
        self.assertEqual(simplified.right.value, 2)

    def test_associativity_sub(self):
        # (x + 2x^2) - 4x^2 -> x + (2x^2 - 4x^2) -> x - 2x^2
        
        term_x = Variable("x")
        term_2x2 = BinaryOp(Number(2), Op.MUL, BinaryOp(Variable("x"), Op.POW, Number(2)))
        term_4x2 = BinaryOp(Number(4), Op.MUL, BinaryOp(Variable("x"), Op.POW, Number(2)))
        
        # (x + 2x^2)
        sum_term = BinaryOp(term_x, Op.ADD, term_2x2)
        
        # (x + 2x^2) - 4x^2
        node = BinaryOp(sum_term, Op.SUB, term_4x2)
        
        simplified = simplify(node)
        
        # Expected: x + (-2x^2)  OR  x - 2x^2 depending on how -2x^2 is represented.
        # simplify(2x^2 - 4x^2) -> -2x^2 (BinaryOp(-2, MUL, x^2)) OR UnaryOp(SUB, 2x^2)?
        # 2x^2 - 4x^2 uses subtraction rule "Combine Like Terms".
        # c1=2, c2=4. new_coeff = -2. 
        # Returns BinaryOp(-2, MUL, x^2).
        
        # So we expect A + (-2x^2).
        # But wait, A + B. Does A+B simplify A=x, B=-2x^2? No like terms.
        # Expected: x - 2x^2
        self.assertEqual(simplified.op, Op.SUB)
        self.assertEqual(simplified.left.name, "x")
        self.assertEqual(simplified.right.op, Op.MUL)
        self.assertEqual(simplified.right.left.value, 2)

    def test_reported_issue_logic(self):
        # 2 * (1 + x^2) - 4x^2 -> 2 - 2x^2
        
        t1 = BinaryOp(Number(2), Op.MUL, BinaryOp(Number(1), Op.ADD, BinaryOp(Variable("x"), Op.POW, Number(2))))
        t2 = BinaryOp(Number(4), Op.MUL, BinaryOp(Variable("x"), Op.POW, Number(2)))
        node = BinaryOp(t1, Op.SUB, t2)
        
        simplified = simplify(node)
        
        # 2 - 2x^2
        self.assertEqual(simplified.op, Op.SUB)
        self.assertEqual(simplified.left.value, 2)
        self.assertEqual(simplified.right.op, Op.MUL)
        self.assertEqual(simplified.right.left.value, 2)

if __name__ == '__main__':
    unittest.main()
