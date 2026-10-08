"""
Core mathematical and circuit network analysis algorithms.
"""

from circuit_calculator.core.calculator import (
    calculate_resistance_from_expression,
    solve_vipr,
)
from circuit_calculator.core.circuit_analyzer import (
    CircuitAnalyzer,
)

# Alias for convenience
calculate_vipr = solve_vipr

__all__ = [
    "calculate_resistance_from_expression",
    "solve_vipr",
    "calculate_vipr",
    "CircuitAnalyzer",
]
