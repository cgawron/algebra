import unittest
from src.lexer import Lexer
from src.parser import Parser
from src.ast_nodes import Number, BinaryOp, UnaryOp, FunctionCall, Variable, Op

class TestParser(unittest.TestCase):
    def parse(self, text):
        return Parser(Lexer(text)).parse()

    def test_number(self):
        ast = self.parse("42")
        self.assertIsInstance(ast, Number)
        self.assertEqual(ast.value, 42.0)

    def test_variable(self):
        ast = self.parse("x")
        self.assertIsInstance(ast, Variable)
        self.assertEqual(ast.name, "x")

    def test_variable_expression(self):
        ast = self.parse("x + 1")
        self.assertIsInstance(ast, BinaryOp)
        self.assertEqual(ast.op, Op.ADD)
        self.assertIsInstance(ast.left, Variable)
        self.assertEqual(ast.left.name, "x")
        self.assertEqual(ast.right.value, 1.0)

    def test_addition(self):
        ast = self.parse("1 + 2")
        self.assertIsInstance(ast, BinaryOp)
        self.assertEqual(ast.op, Op.ADD)
        self.assertEqual(ast.left.value, 1.0)
        self.assertEqual(ast.right.value, 2.0)

    def test_precedence(self):
        ast = self.parse("2 + 3 * 4")
        self.assertIsInstance(ast, BinaryOp)
        self.assertEqual(ast.op, Op.ADD)
        self.assertEqual(ast.left.value, 2.0)
        self.assertIsInstance(ast.right, BinaryOp) # 3 * 4
        self.assertEqual(ast.right.op, Op.MUL)

    def test_parentheses(self):
        ast = self.parse("(2 + 3) * 4")
        self.assertIsInstance(ast, BinaryOp)
        self.assertEqual(ast.op, Op.MUL)
        self.assertIsInstance(ast.left, BinaryOp) # 2 + 3
        self.assertEqual(ast.right.value, 4.0)

    def test_unary(self):
        ast = self.parse("-5")
        self.assertIsInstance(ast, UnaryOp)
        self.assertEqual(ast.op, Op.SUB)
        self.assertEqual(ast.operand.value, 5.0)

    def test_exponentiation(self):
        ast = self.parse("2 ^ 3")
        self.assertIsInstance(ast, BinaryOp)
        self.assertEqual(ast.op, Op.POW)
        self.assertEqual(ast.left.value, 2.0)
        self.assertEqual(ast.right.value, 3.0)

    def test_exponentiation_right_associative(self):
        # 2 ^ 3 ^ 4 should be 2 ^ (3 ^ 4)
        ast = self.parse("2 ^ 3 ^ 4")
        self.assertIsInstance(ast, BinaryOp)
        self.assertEqual(ast.op, Op.POW)
        self.assertEqual(ast.left.value, 2.0)
        self.assertIsInstance(ast.right, BinaryOp) # 3 ^ 4
        self.assertEqual(ast.right.left.value, 3.0)
        self.assertEqual(ast.right.right.value, 4.0)

    def test_exponentiation_precedence(self):
        # 4 * 2 ^ 3 should be 4 * (2 ^ 3)
        ast = self.parse("4 * 2 ^ 3")
        self.assertIsInstance(ast, BinaryOp)
        self.assertEqual(ast.op, Op.MUL)
        self.assertEqual(ast.left.value, 4.0)
        self.assertIsInstance(ast.right, BinaryOp)
        self.assertEqual(ast.right.op, Op.POW)

    def test_function_call(self):
        ast = self.parse("sin(30)")
        self.assertIsInstance(ast, FunctionCall)
        self.assertEqual(ast.name, "sin")
        self.assertEqual(len(ast.args), 1)
        self.assertEqual(ast.args[0].value, 30.0)

    def test_function_call_multiple_args(self):
        ast = self.parse("max(1, 2, 3)")
        self.assertIsInstance(ast, FunctionCall)
        self.assertEqual(ast.name, "max")
        self.assertEqual(len(ast.args), 3)
        self.assertEqual(ast.args[0].value, 1.0)
        self.assertEqual(ast.args[1].value, 2.0)
        self.assertEqual(ast.args[2].value, 3.0)

    def test_nested_function_call(self):
        ast = self.parse("sin(max(2, 3))")
        self.assertIsInstance(ast, FunctionCall)
        self.assertEqual(ast.name, "sin")
        self.assertEqual(len(ast.args), 1)
        arg = ast.args[0]
        self.assertIsInstance(arg, FunctionCall)
        self.assertEqual(arg.name, "max")

if __name__ == '__main__':
    unittest.main()
