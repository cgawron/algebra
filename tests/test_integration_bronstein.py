import unittest
from src.ast_nodes import Variable, Number, BinaryOp, FunctionCall, Op
from src.integration import integrate
from src.simplification import simplify

class TestBronsteinIntegration(unittest.TestCase):
    def setUp(self):
        self.x = Variable('x')

    def test_logarithmic_derivative_simple(self):
        # int(2x / (x^2 + 1)) -> ln(x^2 + 1)
        # u = x^2 + 1, du = 2x
        numerator = BinaryOp(Number(2), Op.MUL, self.x)
        denominator = BinaryOp(BinaryOp(self.x, Op.POW, Number(2)), Op.ADD, Number(1))
        expr = BinaryOp(numerator, Op.DIV, denominator)
        
        result = integrate(expr, 'x')
        expected = FunctionCall("ln", [denominator])
        
        # We might get ln(x^2+1) directly or some equivalent. 
        # Check if result structure matches expected roughly or string match.
        self.assertEqual(str(result), str(expected))

    def test_tangent(self):
        # int(sin(x)/cos(x)) -> -ln(cos(x)) (integral of tan(x) is -ln|cos(x)|)
        # u = cos(x), du = -sin(x).
        # sin(x)/cos(x) = - (-sin(x))/cos(x) = - du/u
        expr = BinaryOp(FunctionCall("sin", [self.x]), Op.DIV, FunctionCall("cos", [self.x]))
        
        result = integrate(expr, 'x')
        # Expect -1 * ln(cos(x))
        ln_cos = FunctionCall("ln", [FunctionCall("cos", [self.x])])
        expected = BinaryOp(Number(-1), Op.MUL, ln_cos)
        
        # Simplification might handle -1 * ... or UnaryOp subtraction. 
        # Let's see what simplify returns.
        self.assertEqual(str(result), str(simplify(expected)))

if __name__ == '__main__':
    unittest.main()
