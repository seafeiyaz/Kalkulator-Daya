"""
Graph-based electrical node analysis and network reduction for visual schematics.
Performs series-parallel simplification to compute equivalent resistance
and generate formatted symbolic expressions.
"""

from typing import Any, Dict, List, Optional, Tuple, Set


class CircuitAnalyzer:
    """Performs topological analysis and graph reduction on 2D circuit schematics."""

    @staticmethod
    def get_cp_tuple_from_wire_info(cp_info: Optional[Dict[str, Any]]) -> Optional[Tuple[str, int]]:
        """Converts a connection point info dict into a hashable (group_tag, cp_index) tuple."""
        if not cp_info:
            return None
        return (cp_info['component_group_tag'], cp_info['cp_index'])

    @classmethod
    def build_electrical_nodes(
        cls,
        components_to_include: List[Dict[str, Any]],
        wires: List[Dict[str, Any]]
    ) -> List[Set[Tuple[str, int]]]:
        """Groups component connection points into unified electrical nodes based on wire interconnects."""
        all_component_cps = []
        for comp in components_to_include:
            for i in range(len(comp.get('connection_points', []))):
                all_component_cps.append((comp['group_tag'], i))

        if not all_component_cps:
            return []

        node_map: Dict[Tuple[str, int], frozenset] = {
            cp: frozenset([cp]) for cp in all_component_cps
        }

        for wire in wires:
            connected_cps = []
            if wire.get('start_cp_info'):
                connected_cps.append(cls.get_cp_tuple_from_wire_info(wire['start_cp_info']))
            if wire.get('end_cp_info'):
                connected_cps.append(cls.get_cp_tuple_from_wire_info(wire['end_cp_info']))

            connected_cps = [cp for cp in connected_cps if cp and cp in node_map]
            if len(connected_cps) < 2:
                continue

            base_node = node_map[connected_cps[0]]
            nodes_to_merge = [base_node]
            for i in range(1, len(connected_cps)):
                candidate = node_map[connected_cps[i]]
                if candidate not in nodes_to_merge:
                    nodes_to_merge.append(candidate)

            if len(nodes_to_merge) > 1:
                merged = frozenset().union(*nodes_to_merge)
                for cp in merged:
                    node_map[cp] = merged

        # Return unique node sets
        unique_nodes = list(dict.fromkeys(node_map.values()))
        return [set(node) for node in unique_nodes]

    @classmethod
    def analyze_circuit(cls, canvas_elements: List[Dict[str, Any]]) -> Tuple[str, Optional[float]]:
        """Analyzes the visual circuit using iterative series/parallel reduction

        to find equivalent resistance.

        Returns:
            Tuple of (status_message, equivalent_resistance_or_None)
        """
        resistors_data = [elem for elem in canvas_elements if elem.get('type') == 'resistor']
        sources_data = [elem for elem in canvas_elements if elem.get('type') == 'voltage_source']
        wires_data = [elem for elem in canvas_elements if elem.get('type') == 'wire']

        if not sources_data:
            return "No voltage source detected in schematic.", None
        if len(sources_data) > 1:
            return "Network reduction supports only 1 voltage source at this time.", None
        if not resistors_data:
            return "No resistors detected for analysis.", None

        source = sources_data[0]
        nodes = cls.build_electrical_nodes(resistors_data + sources_data, wires_data)
        if not nodes:
            return "Unable to construct electrical nodes from schematic.", None

        node_map = {frozenset(node_set): i for i, node_set in enumerate(nodes)}

        resistors: List[List[Any]] = []
        for r_data in resistors_data:
            cp1 = (r_data['group_tag'], 0)
            cp2 = (r_data['group_tag'], 1)

            node1 = next((n for n in nodes if cp1 in n), None)
            node2 = next((n for n in nodes if cp2 in n), None)

            if node1 is None or node2 is None or node1 == node2:
                return f"Resistor {r_data['value']}Ω is short-circuited or disconnected.", None

            resistors.append([r_data['value'], node_map[frozenset(node1)], node_map[frozenset(node2)]])

        src_cp1 = (source['group_tag'], 0)
        src_cp2 = (source['group_tag'], 1)
        src_node1 = next((n for n in nodes if src_cp1 in n), None)
        src_node2 = next((n for n in nodes if src_cp2 in n), None)

        if src_node1 is None or src_node2 is None:
            return "Voltage source is not connected.", None
        if src_node1 == src_node2:
            return "Voltage source is short-circuited.", None

        source_n1_id = node_map[frozenset(src_node1)]
        source_n2_id = node_map[frozenset(src_node2)]

        # Iterative reduction
        while True:
            simplified = False

            # 1. Series reduction
            node_connections: Dict[int, List[int]] = {}
            for i, r in enumerate(resistors):
                node_connections.setdefault(r[1], []).append(i)
                node_connections.setdefault(r[2], []).append(i)

            for node_id, indices in node_connections.items():
                if len(indices) == 2 and node_id not in (source_n1_id, source_n2_id):
                    idx1, idx2 = indices[0], indices[1]
                    r1_val, r1_n1, r1_n2 = resistors[idx1]
                    r2_val, r2_n1, r2_n2 = resistors[idx2]

                    new_r = r1_val + r2_val
                    new_n1 = r1_n1 if r1_n2 == node_id else r1_n2
                    new_n2 = r2_n1 if r2_n2 == node_id else r2_n2

                    resistors.append([new_r, new_n1, new_n2])
                    resistors[idx1][0] = -1
                    resistors[idx2][0] = -1
                    simplified = True
                    break

            resistors = [r for r in resistors if r[0] != -1]
            if simplified:
                continue

            # 2. Parallel reduction
            resistor_pairs: Dict[Tuple[int, int], List[int]] = {}
            for i, r in enumerate(resistors):
                key = tuple(sorted((r[1], r[2])))
                resistor_pairs.setdefault(key, []).append(i)

            for key, indices in resistor_pairs.items():
                if len(indices) > 1:
                    try:
                        r_parallel = 1.0 / sum(1.0 / resistors[i][0] for i in indices)
                    except ZeroDivisionError:
                        r_parallel = 0.0

                    n1, n2 = key
                    resistors.append([r_parallel, n1, n2])
                    for i in indices:
                        resistors[i][0] = -1
                    simplified = True
                    break

            resistors = [r for r in resistors if r[0] != -1]
            if simplified:
                continue

            if not simplified:
                break

        if len(resistors) == 1:
            r_final, n1, n2 = resistors[0]
            if tuple(sorted((n1, n2))) == tuple(sorted((source_n1_id, source_n2_id))):
                return "Circuit analyzed successfully.", r_final
            else:
                return "Circuit components are not properly connected across source terminals.", None
        elif len(resistors) == 0:
            return "No resistor load present along the voltage source path.", None
        else:
            return "Circuit is too complex for standard series/parallel reduction (e.g., bridge topology).", None

    @classmethod
    def generate_resistor_expression(cls, canvas_elements: List[Dict[str, Any]]) -> Tuple[str, Optional[str]]:
        """Extracts an equivalent series/parallel algebraic string expression from visual topology."""
        resistors_data = [elem for elem in canvas_elements if elem.get('type') == 'resistor']
        sources_data = [elem for elem in canvas_elements if elem.get('type') == 'voltage_source']
        wires_data = [elem for elem in canvas_elements if elem.get('type') == 'wire']

        if not sources_data or not resistors_data:
            return "Requires 1 voltage source and at least 1 resistor.", None
        if len(sources_data) > 1:
            return "Only 1 voltage source is supported for symbolic expression generation.", None

        source = sources_data[0]
        nodes = cls.build_electrical_nodes(resistors_data + sources_data, wires_data)
        if not nodes:
            return "Unable to construct electrical nodes.", None

        node_map = {frozenset(node_set): i for i, node_set in enumerate(nodes)}

        resistors: List[List[Any]] = []
        for r_data in resistors_data:
            cp1 = (r_data['group_tag'], 0)
            cp2 = (r_data['group_tag'], 1)
            node1 = next((n for n in nodes if cp1 in n), None)
            node2 = next((n for n in nodes if cp2 in n), None)

            if node1 is None or node2 is None or node1 == node2:
                return f"Resistor {r_data['value']}Ω is shorted or disconnected.", None

            val = r_data['value']
            val_str = f"{int(val)}" if float(val).is_integer() else f"{val}"
            resistors.append([val_str, val, node_map[frozenset(node1)], node_map[frozenset(node2)]])

        src_cp1 = (source['group_tag'], 0)
        src_cp2 = (source['group_tag'], 1)
        src_node1 = next((n for n in nodes if src_cp1 in n), None)
        src_node2 = next((n for n in nodes if src_cp2 in n), None)

        if src_node1 is None or src_node2 is None or src_node1 == src_node2:
            return "Voltage source is not properly connected.", None

        source_n1_id = node_map[frozenset(src_node1)]
        source_n2_id = node_map[frozenset(src_node2)]

        while True:
            simplified = False

            # Series reduction
            node_connections: Dict[int, List[int]] = {}
            for i, r in enumerate(resistors):
                node_connections.setdefault(r[2], []).append(i)
                node_connections.setdefault(r[3], []).append(i)

            for node_id, indices in node_connections.items():
                if len(indices) == 2 and node_id not in (source_n1_id, source_n2_id):
                    idx1, idx2 = indices[0], indices[1]
                    r1_expr, r1_val, r1_n1, r1_n2 = resistors[idx1]
                    r2_expr, r2_val, r2_n1, r2_n2 = resistors[idx2]

                    new_expr = f"({r1_expr} + {r2_expr})"
                    new_val = r1_val + r2_val
                    new_n1 = r1_n1 if r1_n2 == node_id else r1_n2
                    new_n2 = r2_n1 if r2_n2 == node_id else r2_n2

                    resistors.append([new_expr, new_val, new_n1, new_n2])
                    resistors[idx1][1] = -1
                    resistors[idx2][1] = -1
                    simplified = True
                    break

            resistors = [r for r in resistors if r[1] != -1]
            if simplified:
                continue

            # Parallel reduction
            resistor_pairs: Dict[Tuple[int, int], List[int]] = {}
            for i, r in enumerate(resistors):
                key = tuple(sorted((r[2], r[3])))
                resistor_pairs.setdefault(key, []).append(i)

            for key, indices in resistor_pairs.items():
                if len(indices) > 1:
                    parallel_exprs = [resistors[i][0] for i in indices]
                    parallel_vals = [resistors[i][1] for i in indices]

                    new_expr = f"({' | '.join(parallel_exprs)})"
                    try:
                        new_val = 1.0 / sum(1.0 / v for v in parallel_vals if v != 0)
                    except ZeroDivisionError:
                        new_val = 0.0

                    n1, n2 = key
                    resistors.append([new_expr, new_val, n1, n2])
                    for i in indices:
                        resistors[i][1] = -1
                    simplified = True
                    break

            resistors = [r for r in resistors if r[1] != -1]
            if simplified:
                continue

            if not simplified:
                break

        if len(resistors) == 1:
            final_expr, _, n1, n2 = resistors[0]
            if tuple(sorted((n1, n2))) == tuple(sorted((source_n1_id, source_n2_id))):
                if final_expr.startswith('(') and final_expr.endswith(')'):
                    final_expr = final_expr[1:-1]
                return "Expression successfully generated.", final_expr
            else:
                return "Circuit is not connected across source terminals.", None
        elif len(resistors) == 0:
            return "No resistors along source path.", None
        else:
            return "Circuit cannot be reduced to simple series/parallel expression.", None
