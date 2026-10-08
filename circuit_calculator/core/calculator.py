"""
Electrical calculations: VIPR relations (Ohm's law & electric power)
and recursive series/parallel resistance expression parsing.
"""

from dataclasses import dataclass
import math
import re
from typing import Optional


@dataclass
class VIPRResult:
    """Represents the outcome of a VIPR manual calculation."""
    v: Optional[float] = None
    i: Optional[float] = None
    r: Optional[float] = None
    p: Optional[float] = None
    status: str = ""
    is_error: bool = False
    note: str = ""


def calculate_resistance_from_expression(expr: str) -> float:
    """Recursively calculates equivalent resistance from a string expression.

    Syntax:
        +  : Series connection (e.g., 10 + 20)
        |  : Parallel connection (e.g., 20 | 30)
        () : Grouping (e.g., 10 + (20 | 30))

    Args:
        expr: The resistance expression string.

    Returns:
        The total equivalent resistance in Ohms.

    Raises:
        ValueError: If the expression has invalid syntax, missing operands,
                    or resolves to negative resistance.
    """
    cleaned = expr.strip()
    if not cleaned:
        raise ValueError("Expression is empty.")

    if not re.match(r'^[0-9\.\s()|+-]+$', cleaned):
        raise ValueError("Expression contains invalid characters. Only numbers, +, |, -, and () are allowed.")

    # Process innermost parentheses first
    match = re.search(r'\(([^()]+)\)', cleaned)
    if match:
        sub_expr = match.group(1)
        sub_result = calculate_resistance_from_expression(sub_expr)
        replaced = cleaned[:match.start()] + f" {sub_result} " + cleaned[match.end():]
        return calculate_resistance_from_expression(replaced)

    # Series combination (split by +)
    series_parts = [p.strip() for p in cleaned.split('+')]
    if not all(p for p in series_parts):
        raise ValueError("Incomplete series (+) expression.")

    series_totals = []
    for part in series_parts:
        # Parallel combination (split by |)
        parallel_parts_str = [val.strip() for val in part.split('|')]
        if not all(s for s in parallel_parts_str):
            raise ValueError("Incomplete parallel (|) expression.")

        try:
            parallel_parts = [float(s) for s in parallel_parts_str]
        except ValueError as exc:
            raise ValueError(f"Invalid numeric value in expression: {exc}") from exc

        if len(parallel_parts) == 1:
            series_totals.append(parallel_parts[0])
        else:
            if any(r == 0 for r in parallel_parts):
                # A 0-ohm branch shorts the parallel group to 0 ohms
                series_totals.append(0.0)
            else:
                try:
                    parallel_total = 1.0 / sum(1.0 / r for r in parallel_parts)
                    series_totals.append(parallel_total)
                except ZeroDivisionError:
                    series_totals.append(0.0)

    total_r = sum(series_totals)
    if total_r < 0:
        raise ValueError("Total calculated resistance cannot be negative.")

    return total_r


def solve_vipr(
    v: Optional[float] = None,
    i: Optional[float] = None,
    r: Optional[float] = None,
    p: Optional[float] = None,
) -> VIPRResult:
    """Solves for missing electrical variables among Voltage (V), Current (I),

    Resistance (R), and Power (P).

    Rules:
      - Exactly 3 known values: Solves for the 4th value.
      - Exactly V and I known: Solves for R (V/I) and P (V*I).
      - All 4 values known: Verifies consistency with Ohm's Law and Power equations.

    Returns:
        VIPRResult object containing computed/verified values and status messages.
    """
    inputs = {'V': v, 'I': i, 'R': r, 'P': p}
    known_keys = [k for k, val in inputs.items() if val is not None]
    unknown_keys = [k for k, val in inputs.items() if val is None]
    known_count = len(known_keys)

    v_calc, i_calc, r_calc, p_calc = v, i, r, p

    try:
        # Case 1: Exactly 3 values known, solve the 1 missing value
        if known_count == 3 and len(unknown_keys) == 1:
            target = unknown_keys[0]

            if target == 'R':
                if v is not None and i is not None:
                    if i == 0:
                        if v == 0:
                            r_calc = None
                        else:
                            raise ValueError("Current is zero with non-zero Voltage (infinite Resistance).")
                    else:
                        r_calc = v / i
                elif v is not None and p is not None:
                    if p == 0:
                        if v == 0:
                            r_calc = None
                        else:
                            raise ValueError("Power is zero with non-zero Voltage (infinite Resistance).")
                    else:
                        r_calc = (v ** 2) / p
                elif i is not None and p is not None:
                    if i == 0:
                        if p == 0:
                            r_calc = None
                        else:
                            raise ValueError("Current is zero with non-zero Power (infinite Resistance).")
                    else:
                        r_calc = p / (i ** 2)
                else:
                    return VIPRResult(is_error=True, status="Insufficient variable combination to solve for R.")

            elif target == 'V':
                if i is not None and r is not None:
                    v_calc = i * r
                elif i is not None and p is not None:
                    if i == 0:
                        if p == 0:
                            v_calc = 0.0
                        else:
                            raise ValueError("Current is zero with non-zero Power (infinite Voltage).")
                    else:
                        v_calc = p / i
                elif r is not None and p is not None:
                    prod = p * r
                    if prod < 0 and not math.isclose(prod, 0.0):
                        raise ValueError("Product of P * R is negative; Voltage is not real.")
                    v_calc = math.sqrt(abs(prod))
                    if p < 0 and r > 0 and not math.isclose(prod, 0.0):
                        v_calc = -v_calc
                else:
                    return VIPRResult(is_error=True, status="Insufficient variable combination to solve for V.")

            elif target == 'I':
                if v is not None and r is not None:
                    if r == 0:
                        if v == 0:
                            i_calc = None
                        else:
                            raise ValueError("Resistance is zero with non-zero Voltage (infinite Current).")
                    else:
                        i_calc = v / r
                elif v is not None and p is not None:
                    if v == 0:
                        if p == 0:
                            i_calc = None
                        else:
                            raise ValueError("Voltage is zero with non-zero Power (infinite Current).")
                    else:
                        i_calc = p / v
                elif r is not None and p is not None:
                    if r == 0:
                        if p == 0:
                            i_calc = None
                        else:
                            raise ValueError("Resistance is zero with non-zero Power (infinite Current).")
                    else:
                        quot = p / r
                        if quot < 0 and not math.isclose(quot, 0.0):
                            raise ValueError("Quotient P / R is negative; Current is not real.")
                        i_calc = math.sqrt(abs(quot))
                        if p < 0 and not math.isclose(p, 0.0):
                            i_calc = -i_calc
                else:
                    return VIPRResult(is_error=True, status="Insufficient variable combination to solve for I.")

            elif target == 'P':
                if v is not None and i is not None:
                    p_calc = v * i
                elif v is not None and r is not None:
                    if r == 0:
                        if v != 0:
                            raise ValueError("Resistance is zero with non-zero Voltage (infinite Power).")
                        p_calc = 0.0
                    else:
                        p_calc = (v ** 2) / r
                elif i is not None and r is not None:
                    p_calc = (i ** 2) * r
                else:
                    return VIPRResult(is_error=True, status="Insufficient variable combination to solve for P.")

            return VIPRResult(
                v=v_calc, i=i_calc, r=r_calc, p=p_calc,
                status="Calculation completed successfully.", is_error=False
            )

        # Case 2: Only V and I are known -> solve R and P
        elif known_count == 2 and v is not None and i is not None and r is None and p is None:
            if i == 0:
                if v != 0:
                    raise ValueError("Current is zero with non-zero Voltage (R and P undefined).")
                r_calc, p_calc = None, 0.0
            else:
                r_calc = v / i
                p_calc = v * i

            return VIPRResult(
                v=v, i=i, r=r_calc, p=p_calc,
                status="Calculation completed (R and P derived from V and I).", is_error=False
            )

        # Case 3: All 4 values provided -> consistency check
        elif known_count == 4:
            consistent_ohm = math.isclose(v, i * r, rel_tol=1e-2, abs_tol=1e-5)
            consistent_power = math.isclose(p, v * i, rel_tol=1e-2, abs_tol=1e-5)
            if not (consistent_ohm and consistent_power):
                return VIPRResult(
                    v=v, i=i, r=r, p=p,
                    status="Input values are mathematically inconsistent (V=IR, P=VI).",
                    is_error=True,
                    note=f"Verification: V ({v}V) vs I*R ({i*r:.2f}V), P ({p}W) vs V*I ({v*i:.2f}W)."
                )

            return VIPRResult(
                v=v, i=i, r=r, p=p,
                status="All 4 values are consistent with electrical laws.",
                is_error=False
            )

        # Case 4: Invalid input configuration
        else:
            return VIPRResult(
                is_error=True,
                status="Invalid input pattern. Provide 3 values (1 blank) OR Voltage (V) and Current (I) only."
            )

    except ValueError as exc:
        return VIPRResult(is_error=True, status=f"Calculation Error: {str(exc)}")
    except ZeroDivisionError:
        return VIPRResult(is_error=True, status="Calculation Error: Division by zero.")
    except Exception as exc:
        return VIPRResult(is_error=True, status=f"Unexpected Error: {str(exc)}")
