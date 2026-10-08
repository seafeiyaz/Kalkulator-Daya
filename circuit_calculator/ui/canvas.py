"""
Interactive Tkinter canvas for schematic drafting, wiring, and component manipulation.
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
from typing import Any, Callable, Dict, List, Optional, Tuple

from circuit_calculator.ui.dialogs import CustomSourceDialog


class CircuitCanvasManager:
    """Manages 2D schematic drawing, grid alignment, component placement,

    interactive wiring, drag-and-drop movement, and component rotation.
    """

    GRID_SIZE: int = 20
    CP_RADIUS: int = 3
    SELECTED_OUTLINE_COLOR: str = "green"
    DEFAULT_OUTLINE_COLOR: str = "black"
    SELECTED_OUTLINE_WIDTH: int = 2
    DEFAULT_OUTLINE_WIDTH: int = 1
    RESISTOR_WIDTH: int = 2 * 20
    RESISTOR_HEIGHT: int = 1 * 20
    VOLTAGE_SOURCE_RADIUS: float = 1.0 * 20

    def __init__(
        self,
        canvas: tk.Canvas,
        parent_window: tk.Tk,
        status_callback: Optional[Callable[[str, bool], None]] = None,
        get_selected_tool: Optional[Callable[[], str]] = None,
        get_tool_values: Optional[Callable[[], Tuple[float, float]]] = None,
    ):
        self.canvas = canvas
        self.root = parent_window
        self.status_cb = status_callback or (lambda msg, is_err=False: None)
        self.get_tool = get_selected_tool or (lambda: "resistor")
        self.get_tool_vals = get_tool_values or (lambda: (10.0, 5.0))

        # Canvas elements state
        self.elements: List[Dict[str, Any]] = []
        self.drag_data: Dict[str, Any] = {"item": None, "group_tag": None, "offset_x": 0, "offset_y": 0}
        self.selected_group_tag: Optional[str] = None
        self.is_wiring: bool = False
        self.current_wire_points: List[Tuple[int, int]] = []
        self.current_wire_cps_info: List[Optional[Dict[str, Any]]] = []
        self.temp_wire_id: Optional[int] = None

        self._draw_grid()
        self._bind_events()

    def _bind_events(self) -> None:
        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_left_release)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        self.canvas.bind("<Motion>", self.on_mouse_motion)
        self.root.bind("<KeyPress-r>", self.on_rotate_key)
        self.root.bind("<KeyPress-R>", self.on_rotate_key)

    def _draw_grid(self) -> None:
        """Draws subtle background grid lines across the canvas."""
        for i in range(0, 2500, self.GRID_SIZE):
            self.canvas.create_line(i, 0, i, 2500, fill="#f0f0f0", tags="grid_line")
            self.canvas.create_line(0, i, 2500, i, fill="#f0f0f0", tags="grid_line")
        self.canvas.tag_lower("grid_line")

    def snap_to_grid(self, x: float, y: float) -> Tuple[int, int]:
        """Snaps coordinate pair (x, y) to the closest grid node."""
        snapped_x = round(x / self.GRID_SIZE) * self.GRID_SIZE
        snapped_y = round(y / self.GRID_SIZE) * self.GRID_SIZE
        return int(snapped_x), int(snapped_y)

    def draw_connection_point(self, x: int, y: int, group_tag: str) -> int:
        """Renders an interactive circular connection terminal pin."""
        return self.canvas.create_oval(
            x - self.CP_RADIUS, y - self.CP_RADIUS,
            x + self.CP_RADIUS, y + self.CP_RADIUS,
            fill="red", outline="darkred", tags=(group_tag, "connection_point")
        )

    def find_element_by_group_tag(self, group_tag: str) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
        for i, el in enumerate(self.elements):
            if el.get('group_tag') == group_tag:
                return i, el
        return None, None

    def get_nearest_connection_point(
        self, x: float, y: float, exclude_group_tag: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        nearest_cp = None
        min_dist_sq = (self.GRID_SIZE) ** 2
        for el in self.elements:
            if exclude_group_tag and el.get('group_tag') == exclude_group_tag:
                continue
            if 'connection_points' in el:
                for cp_idx, cp_data in enumerate(el['connection_points']):
                    dist_sq = (cp_data['abs_x'] - x) ** 2 + (cp_data['abs_y'] - y) ** 2
                    if dist_sq < min_dist_sq:
                        min_dist_sq = dist_sq
                        nearest_cp = {
                            'x': cp_data['abs_x'],
                            'y': cp_data['abs_y'],
                            'component_group_tag': el['group_tag'],
                            'cp_index': cp_idx,
                            'cp_canvas_id': cp_data['id']
                        }
        return nearest_cp

    def select_item(self, group_tag: str) -> None:
        self.deselect_all()
        _, el = self.find_element_by_group_tag(group_tag)
        if el and el.get('type') != 'wire':
            self.canvas.itemconfig(el['main_id'], outline=self.SELECTED_OUTLINE_COLOR, width=self.SELECTED_OUTLINE_WIDTH)
            self.selected_group_tag = group_tag

    def deselect_all(self) -> None:
        if self.selected_group_tag:
            _, el = self.find_element_by_group_tag(self.selected_group_tag)
            if el and el.get('type') != 'wire':
                self.canvas.itemconfig(el['main_id'], outline=self.DEFAULT_OUTLINE_COLOR, width=self.DEFAULT_OUTLINE_WIDTH)
        self.selected_group_tag = None

    def update_wire_path(self, wire_data: Dict[str, Any]) -> None:
        if not wire_data or wire_data.get('type') != 'wire':
            return

        if wire_data.get('start_cp_info'):
            s_info = wire_data['start_cp_info']
            _, comp = self.find_element_by_group_tag(s_info['component_group_tag'])
            if comp and 'connection_points' in comp:
                wire_data['path'][0] = (
                    comp['connection_points'][s_info['cp_index']]['abs_x'],
                    comp['connection_points'][s_info['cp_index']]['abs_y']
                )

        if wire_data.get('end_cp_info'):
            e_info = wire_data['end_cp_info']
            _, comp = self.find_element_by_group_tag(e_info['component_group_tag'])
            if comp and 'connection_points' in comp:
                wire_data['path'][-1] = (
                    comp['connection_points'][e_info['cp_index']]['abs_x'],
                    comp['connection_points'][e_info['cp_index']]['abs_y']
                )

        if len(wire_data['path']) > 1:
            flat_path = [c for pt in wire_data['path'] for c in pt]
            self.canvas.coords(wire_data['main_id'], *flat_path)

    def is_already_connected(self, cp1: Dict[str, Any], cp2: Dict[str, Any]) -> bool:
        t1, i1 = cp1['component_group_tag'], cp1['cp_index']
        t2, i2 = cp2['component_group_tag'], cp2['cp_index']
        for el in self.elements:
            if el.get('type') == 'wire':
                s_info = el.get('start_cp_info')
                e_info = el.get('end_cp_info')
                if s_info and e_info:
                    st, si = s_info['component_group_tag'], s_info['cp_index']
                    et, ei = e_info['component_group_tag'], e_info['cp_index']
                    if (st == t1 and si == i1 and et == t2 and ei == i2) or \
                       (st == t2 and si == i2 and et == t1 and ei == i1):
                        return True
        return False

    # --- Mouse & Keyboard Event Handlers ---
    def on_left_click(self, event: tk.Event) -> None:
        tool = self.get_tool()
        if tool != "wire" and self.is_wiring:
            self.cancel_wiring()

        if tool == "wire":
            self._handle_wire_click(event)
        else:
            self._handle_component_click(event)

    def on_mouse_motion(self, event: tk.Event) -> None:
        if not self.is_wiring:
            return

        sx, sy = self.snap_to_grid(event.x, event.y)
        cp_info = self.get_nearest_connection_point(event.x, event.y)
        if cp_info:
            start_cp = self.current_wire_cps_info[0] if self.current_wire_cps_info else None
            if not start_cp or cp_info['component_group_tag'] != start_cp['component_group_tag']:
                sx, sy = cp_info['x'], cp_info['y']

        preview_path = self.current_wire_points + [(sx, sy)]
        flat_coords = [c for pt in preview_path for c in pt]

        if self.temp_wire_id is None:
            self.temp_wire_id = self.canvas.create_line(
                *flat_coords, fill="gray", width=2, dash=(2, 2), tags="temp_wire_line"
            )
        else:
            self.canvas.coords(self.temp_wire_id, *flat_coords)

    def on_drag(self, event: tk.Event) -> None:
        if self.drag_data["item"] and self.drag_data["group_tag"]:
            idx, el = self.find_element_by_group_tag(self.drag_data["group_tag"])
            if not el or el.get('type') == 'wire':
                self.drag_data = {"item": None, "group_tag": None, "offset_x": 0, "offset_y": 0}
                return

            new_x = event.x - self.drag_data["offset_x"]
            new_y = event.y - self.drag_data["offset_y"]
            snapped_x, snapped_y = self.snap_to_grid(new_x, new_y)

            dx = snapped_x - el['x']
            dy = snapped_y - el['y']

            if dx != 0 or dy != 0:
                self.canvas.move(self.drag_data["group_tag"], dx, dy)
                el['x'] = snapped_x
                el['y'] = snapped_y
                if 'connection_points' in el:
                    for cp in el['connection_points']:
                        cp['abs_x'] = snapped_x + cp['rel_x']
                        cp['abs_y'] = snapped_y + cp['rel_y']
                self.elements[idx] = el

                for wire in self.elements:
                    if wire.get('type') == 'wire':
                        s_tag = wire.get('start_cp_info', {}).get('component_group_tag')
                        e_tag = wire.get('end_cp_info', {}).get('component_group_tag')
                        if s_tag == self.drag_data["group_tag"] or e_tag == self.drag_data["group_tag"]:
                            self.update_wire_path(wire)

    def on_left_release(self, event: tk.Event) -> None:
        if self.drag_data["item"] and self.drag_data["group_tag"]:
            _, el = self.find_element_by_group_tag(self.drag_data["group_tag"])
            if el:
                comp_type = el.get('type', 'Component').replace('_', ' ').title()
                self.status_cb(f"{comp_type} moved to ({el['x']}, {el['y']}).", False)
            self.drag_data = {"item": None, "group_tag": None, "offset_x": 0, "offset_y": 0}

    def on_right_click(self, event: tk.Event) -> None:
        if self.is_wiring:
            self.cancel_wiring()
            self.status_cb("Wiring canceled.", False)
            return

        items = self.canvas.find_withtag(tk.CURRENT)
        if not items:
            self.status_cb("No element selected to delete.", True)
            return

        target_tag = None
        # Prioritize components over wires
        for it in items:
            tags = self.canvas.gettags(it)
            if "connection_point" in tags:
                continue
            for tag in tags:
                if tag.startswith("group_"):
                    _, el = self.find_element_by_group_tag(tag)
                    if el and el.get('type') != 'wire':
                        target_tag = tag
                        break
            if target_tag:
                break

        if not target_tag:
            for it in items:
                tags = self.canvas.gettags(it)
                if "connection_point" in tags:
                    continue
                for tag in tags:
                    if tag.startswith("group_"):
                        _, el = self.find_element_by_group_tag(tag)
                        if el and el.get('type') == 'wire':
                            target_tag = tag
                            break
                if target_tag:
                    break

        if target_tag:
            idx, el = self.find_element_by_group_tag(target_tag)
            if el:
                comp_type = el.get('type', 'element').replace('_', ' ').title()
                if el['type'] != 'wire':
                    # Remove attached wires
                    wires_to_remove = []
                    for i, w in enumerate(self.elements):
                        if w.get('type') == 'wire':
                            s_tag = w.get('start_cp_info', {}).get('component_group_tag')
                            e_tag = w.get('end_cp_info', {}).get('component_group_tag')
                            if s_tag == target_tag or e_tag == target_tag:
                                self.canvas.delete(w['group_tag'])
                                wires_to_remove.append(i)
                    for wi in sorted(wires_to_remove, reverse=True):
                        del self.elements[wi]

                self.canvas.delete(target_tag)
                del self.elements[idx]

                if self.selected_group_tag == target_tag:
                    self.selected_group_tag = None

                self.status_cb(f"{comp_type} deleted.", False)
        else:
            self.status_cb("Click directly on a valid component or wire to delete.", True)

    def on_double_click(self, event: tk.Event) -> None:
        tool = self.get_tool()
        if tool == "wire" and self.is_wiring:
            self.finalize_wire(event)
            return

        items = self.canvas.find_withtag(tk.CURRENT)
        if not items:
            return

        target_tag = None
        for it in items:
            tags = self.canvas.gettags(it)
            for tag in tags:
                if tag.startswith("group_"):
                    _, el = self.find_element_by_group_tag(tag)
                    if el and el.get('type') != 'wire':
                        target_tag = tag
                        break
            if target_tag:
                break

        if target_tag:
            idx, el = self.find_element_by_group_tag(target_tag)
            if not el:
                return

            if el['type'] == 'resistor':
                new_val = simpledialog.askfloat(
                    "Edit Resistor Value",
                    "Enter new resistance value (Ω):",
                    parent=self.root,
                    initialvalue=el['value'],
                    minvalue=1e-6
                )
                if new_val is not None:
                    el['value'] = new_val
                    text_id = el.get('text_id')
                    if text_id:
                        self.canvas.itemconfig(text_id, text=f"{new_val}Ω")
                    self.elements[idx] = el
                    self.status_cb(f"Resistor updated to {new_val}Ω.", False)

            elif el['type'] == 'voltage_source':
                dialog = CustomSourceDialog(
                    self.root,
                    "Edit Voltage Source",
                    el.get('value', 0.0),
                    el.get('current_value', 0.0)
                )
                if dialog.result:
                    new_v, new_i = dialog.result
                    el['value'] = new_v
                    el['current_value'] = new_i
                    v_text_id = el.get('value_text_id')
                    if v_text_id:
                        self.canvas.itemconfig(v_text_id, text=f"{new_v}V")
                    self.elements[idx] = el
                    self.status_cb(f"Voltage source updated: {new_v}V, {new_i}A.", False)

    def on_rotate_key(self, event: tk.Event) -> None:
        if not self.selected_group_tag:
            return

        idx, el = self.find_element_by_group_tag(self.selected_group_tag)
        if not el or el.get('type') == 'wire':
            return

        self.canvas.delete(el['group_tag'])

        if el['type'] == 'resistor':
            w = el.get('width', self.RESISTOR_WIDTH)
            h = el.get('height', self.RESISTOR_HEIGHT)
            new_w, new_h = h, w
            el['width'] = new_w
            el['height'] = new_h
            el['orientation'] = 'vertical' if el['orientation'] == 'horizontal' else 'horizontal'

            el['main_id'] = self.canvas.create_rectangle(
                el['x'] - new_w / 2, el['y'] - new_h / 2,
                el['x'] + new_w / 2, el['y'] + new_h / 2,
                fill="lightblue",
                outline=self.SELECTED_OUTLINE_COLOR,
                width=self.SELECTED_OUTLINE_WIDTH
            )
            self.canvas.addtag_withtag(el['group_tag'], el['main_id'])

            el['text_id'] = self.canvas.create_text(
                el['x'], el['y'], text=f"{el['value']}Ω", tags=(el['group_tag'], "component_text")
            )

            rel_cps = (
                [{'rel_x': -new_w / 2, 'rel_y': 0}, {'rel_x': new_w / 2, 'rel_y': 0}]
                if el['orientation'] == 'horizontal'
                else [{'rel_x': 0, 'rel_y': -new_h / 2}, {'rel_x': 0, 'rel_y': new_h / 2}]
            )

            updated_cps = []
            for r_cp in rel_cps:
                ax = el['x'] + r_cp['rel_x']
                ay = el['y'] + r_cp['rel_y']
                cp_id = self.draw_connection_point(int(ax), int(ay), el['group_tag'])
                updated_cps.append({
                    'id': cp_id, 'rel_x': r_cp['rel_x'], 'rel_y': r_cp['rel_y'],
                    'abs_x': ax, 'abs_y': ay
                })
            el['connection_points'] = updated_cps

        elif el['type'] == 'voltage_source':
            el['orientation'] = 'vertical' if el['orientation'] == 'horizontal' else 'horizontal'
            r = el['radius']

            el['main_id'] = self.canvas.create_oval(
                el['x'] - r, el['y'] - r, el['x'] + r, el['y'] + r,
                fill="lightgreen",
                outline=self.SELECTED_OUTLINE_COLOR,
                width=self.SELECTED_OUTLINE_WIDTH
            )
            self.canvas.addtag_withtag(el['group_tag'], el['main_id'])

            p_ry, m_ry = (-r * 0.4, r * 0.4) if el['orientation'] == 'vertical' else (0, 0)
            p_rx, m_rx = (0, 0) if el['orientation'] == 'vertical' else (-r * 0.4, r * 0.4)

            el['plus_id'] = self.canvas.create_text(
                el['x'] + p_rx, el['y'] + p_ry, text="+",
                font=('Helvetica', 10, 'bold'), tags=(el['group_tag'], "component_text")
            )
            el['minus_id'] = self.canvas.create_text(
                el['x'] + m_rx, el['y'] + m_ry, text="-",
                font=('Helvetica', 12, 'bold'), tags=(el['group_tag'], "component_text")
            )

            vt_x, vt_y = (el['x'], el['y'] + r + 8) if el['orientation'] == 'vertical' else (el['x'] + r + 12, el['y'])
            el['value_text_id'] = self.canvas.create_text(
                vt_x, vt_y, text=f"{el['value']}V", tags=(el['group_tag'], "component_text")
            )

            rel_cps = (
                [{'rel_x': 0, 'rel_y': -r}, {'rel_x': 0, 'rel_y': r}]
                if el['orientation'] == 'vertical'
                else [{'rel_x': -r, 'rel_y': 0}, {'rel_x': r, 'rel_y': 0}]
            )

            updated_cps = []
            for r_cp in rel_cps:
                ax = el['x'] + r_cp['rel_x']
                ay = el['y'] + r_cp['rel_y']
                cp_id = self.draw_connection_point(int(ax), int(ay), el['group_tag'])
                updated_cps.append({
                    'id': cp_id, 'rel_x': r_cp['rel_x'], 'rel_y': r_cp['rel_y'],
                    'abs_x': ax, 'abs_y': ay
                })
            el['connection_points'] = updated_cps

        self.elements[idx] = el

        for wire in self.elements:
            if wire.get('type') == 'wire':
                s_tag = wire.get('start_cp_info', {}).get('component_group_tag')
                e_tag = wire.get('end_cp_info', {}).get('component_group_tag')
                if s_tag == el['group_tag'] or e_tag == el['group_tag']:
                    self.update_wire_path(wire)

        comp_type = el.get('type', 'Component').replace('_', ' ').title()
        self.status_cb(f"{comp_type} rotated.", False)

    def _handle_component_click(self, event: tk.Event) -> None:
        sx, sy = self.snap_to_grid(event.x, event.y)
        items = self.canvas.find_withtag(tk.CURRENT)
        clicked_tag = None

        if items:
            for it in items:
                tags = self.canvas.gettags(it)
                for tag in tags:
                    if tag.startswith("group_"):
                        _, el = self.find_element_by_group_tag(tag)
                        if el and el.get('type') != 'wire':
                            clicked_tag = tag
                            break
                if clicked_tag:
                    break

        if clicked_tag:
            self.select_item(clicked_tag)
            _, el = self.find_element_by_group_tag(clicked_tag)
            if el:
                self.drag_data["item"] = el['main_id']
                self.drag_data["group_tag"] = clicked_tag
                self.drag_data["offset_x"] = event.x - el['x']
                self.drag_data["offset_y"] = event.y - el['y']
            return
        else:
            self.deselect_all()

        tool = self.get_tool()
        resistor_val, voltage_val = self.get_tool_vals()

        if tool == "resistor":
            if resistor_val <= 0:
                messagebox.showerror("Invalid Value", "Resistor value must be positive.")
                return

            w, h = self.RESISTOR_WIDTH, self.RESISTOR_HEIGHT
            item_id = self.canvas.create_rectangle(
                sx - w / 2, sy - h / 2, sx + w / 2, sy + h / 2,
                fill="lightblue", outline=self.DEFAULT_OUTLINE_COLOR, width=self.DEFAULT_OUTLINE_WIDTH
            )
            group_tag = f"group_{item_id}"
            self.canvas.addtag_withtag(group_tag, item_id)

            val_str = f"{int(resistor_val)}" if float(resistor_val).is_integer() else f"{resistor_val}"
            text_id = self.canvas.create_text(sx, sy, text=f"{val_str}Ω", tags=(group_tag, "component_text"))

            rel_cps = [{'rel_x': -w / 2, 'rel_y': 0}, {'rel_x': w / 2, 'rel_y': 0}]
            stored_cps = []
            for r_cp in rel_cps:
                ax, ay = sx + r_cp['rel_x'], sy + r_cp['rel_y']
                cp_id = self.draw_connection_point(int(ax), int(ay), group_tag)
                stored_cps.append({
                    'id': cp_id, 'rel_x': r_cp['rel_x'], 'rel_y': r_cp['rel_y'],
                    'abs_x': ax, 'abs_y': ay
                })

            self.elements.append({
                'group_tag': group_tag, 'type': 'resistor', 'value': resistor_val,
                'orientation': 'horizontal', 'x': sx, 'y': sy,
                'main_id': item_id, 'text_id': text_id, 'width': w, 'height': h,
                'connection_points': stored_cps
            })
            self.status_cb(f"Resistor ({val_str}Ω) added.", False)
            self.select_item(group_tag)

        elif tool == "voltage_source":
            if voltage_val <= 0:
                messagebox.showerror("Invalid Value", "Voltage value must be positive.")
                return

            radius = self.VOLTAGE_SOURCE_RADIUS
            item_id = self.canvas.create_oval(
                sx - radius, sy - radius, sx + radius, sy + radius,
                fill="lightgreen", outline=self.DEFAULT_OUTLINE_COLOR, width=self.DEFAULT_OUTLINE_WIDTH
            )
            group_tag = f"group_{item_id}"
            self.canvas.addtag_withtag(group_tag, item_id)

            val_str = f"{int(voltage_val)}" if float(voltage_val).is_integer() else f"{voltage_val}"
            plus_id = self.canvas.create_text(
                sx, sy - radius * 0.4, text="+", font=('Helvetica', 10, 'bold'), tags=(group_tag, "component_text")
            )
            minus_id = self.canvas.create_text(
                sx, sy + radius * 0.4, text="-", font=('Helvetica', 12, 'bold'), tags=(group_tag, "component_text")
            )
            val_text_id = self.canvas.create_text(
                sx, sy + radius + 8, text=f"{val_str}V", tags=(group_tag, "component_text")
            )

            rel_cps = [{'rel_x': 0, 'rel_y': -radius}, {'rel_x': 0, 'rel_y': radius}]
            stored_cps = []
            for r_cp in rel_cps:
                ax, ay = sx + r_cp['rel_x'], sy + r_cp['rel_y']
                cp_id = self.draw_connection_point(int(ax), int(ay), group_tag)
                stored_cps.append({
                    'id': cp_id, 'rel_x': r_cp['rel_x'], 'rel_y': r_cp['rel_y'],
                    'abs_x': ax, 'abs_y': ay
                })

            self.elements.append({
                'group_tag': group_tag, 'type': 'voltage_source', 'value': voltage_val,
                'current_value': 0.0, 'orientation': 'vertical', 'x': sx, 'y': sy,
                'main_id': item_id, 'radius': radius,
                'plus_id': plus_id, 'minus_id': minus_id, 'value_text_id': val_text_id,
                'connection_points': stored_cps
            })
            self.status_cb(f"Voltage Source ({val_str}V) added.", False)
            self.select_item(group_tag)

    def _handle_wire_click(self, event: tk.Event) -> None:
        sx, sy = self.snap_to_grid(event.x, event.y)
        cp_info = self.get_nearest_connection_point(event.x, event.y)
        if cp_info:
            sx, sy = cp_info['x'], cp_info['y']

        if not self.is_wiring:
            self.is_wiring = True
            self.current_wire_points.append((sx, sy))
            self.current_wire_cps_info.append(cp_info)
            self.status_cb("Routing wire. Click nodes to add segments; double-click or click terminal to finish.", False)
        else:
            if (sx, sy) != self.current_wire_points[-1]:
                self.current_wire_points.append((sx, sy))

            if cp_info:
                start_cp = self.current_wire_cps_info[0]
                if not start_cp or cp_info['component_group_tag'] != start_cp['component_group_tag']:
                    self.finalize_wire(event)

    def finalize_wire(self, event: tk.Event) -> None:
        if not self.is_wiring or len(self.current_wire_points) < 1:
            self.cancel_wiring()
            return

        sx, sy = self.snap_to_grid(event.x, event.y)
        end_cp = self.get_nearest_connection_point(event.x, event.y)
        if end_cp:
            sx, sy = end_cp['x'], end_cp['y']

        if len(self.current_wire_points) == 0 or (sx, sy) != self.current_wire_points[-1]:
            self.current_wire_points.append((sx, sy))

        if len(self.current_wire_points) < 2:
            self.cancel_wiring()
            return

        start_cp = self.current_wire_cps_info[0]

        if start_cp and end_cp and start_cp['component_group_tag'] == end_cp['component_group_tag']:
            self.status_cb("Cannot connect a component pin directly to itself.", True)
            self.cancel_wiring()
            return

        if start_cp and end_cp and self.is_already_connected(start_cp, end_cp):
            self.status_cb("Connection between these two terminals already exists.", True)
            self.cancel_wiring()
            return

        flat_path = [c for pt in self.current_wire_points for c in pt]
        item_id = self.canvas.create_line(*flat_path, fill="black", width=2)
        group_tag = f"group_{item_id}"
        self.canvas.addtag_withtag(group_tag, item_id)

        self.elements.append({
            'group_tag': group_tag,
            'type': 'wire',
            'path': self.current_wire_points,
            'main_id': item_id,
            'start_cp_info': start_cp,
            'end_cp_info': end_cp
        })
        self.status_cb("Wire segment placed.", False)
        self.cancel_wiring()

    def cancel_wiring(self) -> None:
        if self.temp_wire_id:
            self.canvas.delete(self.temp_wire_id)
        self.is_wiring = False
        self.current_wire_points = []
        self.current_wire_cps_info = []
        self.temp_wire_id = None

    def clear_canvas(self) -> None:
        self.cancel_wiring()
        self.canvas.delete("all")
        self._draw_grid()
        self.elements = []
        self.selected_group_tag = None
        self.status_cb("Canvas cleared.", False)
