"""
Unit tests for circuit topological analysis and network reduction.
"""

import unittest

from circuit_calculator.core.circuit_analyzer import CircuitAnalyzer


class TestCircuitAnalyzer(unittest.TestCase):

    def test_single_resistor_circuit(self):
        # A source and 1 resistor connected by 2 wires
        elements = [
            {
                'type': 'voltage_source', 'group_tag': 'src_1', 'value': 12.0,
                'connection_points': [{'id': 1}, {'id': 2}]
            },
            {
                'type': 'resistor', 'group_tag': 'res_1', 'value': 100.0,
                'connection_points': [{'id': 3}, {'id': 4}]
            },
            {
                'type': 'wire', 'group_tag': 'w_1',
                'start_cp_info': {'component_group_tag': 'src_1', 'cp_index': 0},
                'end_cp_info': {'component_group_tag': 'res_1', 'cp_index': 0}
            },
            {
                'type': 'wire', 'group_tag': 'w_2',
                'start_cp_info': {'component_group_tag': 'res_1', 'cp_index': 1},
                'end_cp_info': {'component_group_tag': 'src_1', 'cp_index': 1}
            }
        ]

        status, r_eq = CircuitAnalyzer.analyze_circuit(elements)
        self.assertIsNotNone(r_eq)
        self.assertAlmostEqual(r_eq, 100.0)

        expr_status, expr = CircuitAnalyzer.generate_resistor_expression(elements)
        self.assertIsNotNone(expr)
        self.assertEqual(expr, "100")

    def test_series_resistors_circuit(self):
        # A source and 2 series resistors: 20 ohm + 30 ohm = 50 ohm
        elements = [
            {
                'type': 'voltage_source', 'group_tag': 'src', 'value': 10.0,
                'connection_points': [{'id': 1}, {'id': 2}]
            },
            {
                'type': 'resistor', 'group_tag': 'r1', 'value': 20.0,
                'connection_points': [{'id': 3}, {'id': 4}]
            },
            {
                'type': 'resistor', 'group_tag': 'r2', 'value': 30.0,
                'connection_points': [{'id': 5}, {'id': 6}]
            },
            # Wire 1: src pin 0 -> r1 pin 0
            {
                'type': 'wire',
                'start_cp_info': {'component_group_tag': 'src', 'cp_index': 0},
                'end_cp_info': {'component_group_tag': 'r1', 'cp_index': 0}
            },
            # Wire 2: r1 pin 1 -> r2 pin 0
            {
                'type': 'wire',
                'start_cp_info': {'component_group_tag': 'r1', 'cp_index': 1},
                'end_cp_info': {'component_group_tag': 'r2', 'cp_index': 0}
            },
            # Wire 3: r2 pin 1 -> src pin 1
            {
                'type': 'wire',
                'start_cp_info': {'component_group_tag': 'r2', 'cp_index': 1},
                'end_cp_info': {'component_group_tag': 'src', 'cp_index': 1}
            }
        ]

        status, r_eq = CircuitAnalyzer.analyze_circuit(elements)
        self.assertIsNotNone(r_eq)
        self.assertAlmostEqual(r_eq, 50.0)

        expr_status, expr = CircuitAnalyzer.generate_resistor_expression(elements)
        self.assertIsNotNone(expr)
        self.assertIn("+", expr)

    def test_parallel_resistors_circuit(self):
        # A source and 2 parallel resistors: 40 ohm || 40 ohm = 20 ohm
        elements = [
            {
                'type': 'voltage_source', 'group_tag': 'src', 'value': 5.0,
                'connection_points': [{'id': 1}, {'id': 2}]
            },
            {
                'type': 'resistor', 'group_tag': 'r1', 'value': 40.0,
                'connection_points': [{'id': 3}, {'id': 4}]
            },
            {
                'type': 'resistor', 'group_tag': 'r2', 'value': 40.0,
                'connection_points': [{'id': 5}, {'id': 6}]
            },
            # Wire src[0] -> r1[0]
            {
                'type': 'wire',
                'start_cp_info': {'component_group_tag': 'src', 'cp_index': 0},
                'end_cp_info': {'component_group_tag': 'r1', 'cp_index': 0}
            },
            # Wire r1[0] -> r2[0] (common node)
            {
                'type': 'wire',
                'start_cp_info': {'component_group_tag': 'r1', 'cp_index': 0},
                'end_cp_info': {'component_group_tag': 'r2', 'cp_index': 0}
            },
            # Wire src[1] -> r1[1]
            {
                'type': 'wire',
                'start_cp_info': {'component_group_tag': 'src', 'cp_index': 1},
                'end_cp_info': {'component_group_tag': 'r1', 'cp_index': 1}
            },
            # Wire r1[1] -> r2[1] (common node)
            {
                'type': 'wire',
                'start_cp_info': {'component_group_tag': 'r1', 'cp_index': 1},
                'end_cp_info': {'component_group_tag': 'r2', 'cp_index': 1}
            }
        ]

        status, r_eq = CircuitAnalyzer.analyze_circuit(elements)
        self.assertIsNotNone(r_eq)
        self.assertAlmostEqual(r_eq, 20.0)

        expr_status, expr = CircuitAnalyzer.generate_resistor_expression(elements)
        self.assertIsNotNone(expr)
        self.assertIn("|", expr)


if __name__ == '__main__':
    unittest.main()
