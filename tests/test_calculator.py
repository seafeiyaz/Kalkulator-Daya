"""
Unit tests for mathematical calculations and expression evaluation.
"""

import math
import unittest

from circuit_calculator.core.calculator import (
    calculate_resistance_from_expression,
    solve_vipr,
)


class TestCalculator(unittest.TestCase):

    def test_series_resistance(self):
        self.assertAlmostEqual(calculate_resistance_from_expression("10 + 20 + 30"), 60.0)

    def test_parallel_resistance(self):
        # 10 || 10 = 5
        self.assertAlmostEqual(calculate_resistance_from_expression("10 | 10"), 5.0)
        # 20 || 30 = 12
        self.assertAlmostEqual(calculate_resistance_from_expression("20 | 30"), 12.0)

    def test_mixed_expression(self):
        # 10 + (20 | 30) = 10 + 12 = 22
        self.assertAlmostEqual(calculate_resistance_from_expression("10 + (20 | 30)"), 22.0)
        # (10 + 10) | (10 + 10) = 20 | 20 = 10
        self.assertAlmostEqual(calculate_resistance_from_expression("(10 + 10) | (10 + 10)"), 10.0)

    def test_invalid_expression(self):
        with self.assertRaises(ValueError):
            calculate_resistance_from_expression("")
        with self.assertRaises(ValueError):
            calculate_resistance_from_expression("10 + abc")
        with self.assertRaises(ValueError):
            calculate_resistance_from_expression("10 + ")

    def test_solve_vipr_three_known(self):
        # Given V=12, I=2, P=24 -> Solve R = 6
        res = solve_vipr(v=12.0, i=2.0, p=24.0)
        self.assertFalse(res.is_error)
        self.assertAlmostEqual(res.r, 6.0)

        # Given I=3, R=4, P=36 -> Solve V = 12
        res = solve_vipr(i=3.0, r=4.0, p=36.0)
        self.assertFalse(res.is_error)
        self.assertAlmostEqual(res.v, 12.0)

        # Given V=10, R=5, P=20 -> Solve I = 2
        res = solve_vipr(v=10.0, r=5.0, p=20.0)
        self.assertFalse(res.is_error)
        self.assertAlmostEqual(res.i, 2.0)

        # Given V=10, I=2, R=5 -> Solve P = 20
        res = solve_vipr(v=10.0, i=2.0, r=5.0)
        self.assertFalse(res.is_error)
        self.assertAlmostEqual(res.p, 20.0)

    def test_solve_vipr_v_and_i_only(self):
        # Given V=24, I=2 -> R=12, P=48
        res = solve_vipr(v=24.0, i=2.0)
        self.assertFalse(res.is_error)
        self.assertAlmostEqual(res.r, 12.0)
        self.assertAlmostEqual(res.p, 48.0)

    def test_solve_vipr_four_known_consistent(self):
        res = solve_vipr(v=10.0, i=2.0, r=5.0, p=20.0)
        self.assertFalse(res.is_error)

    def test_solve_vipr_four_known_inconsistent(self):
        res = solve_vipr(v=10.0, i=2.0, r=10.0, p=20.0)
        self.assertTrue(res.is_error)


if __name__ == '__main__':
    unittest.main()
