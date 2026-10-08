"""
Main application window for Circuit Calculator.
Provides dual-mode functionality: Manual VIPR Solving and Interactive Schematic Analysis.
"""

import math
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Tuple

from circuit_calculator.core.calculator import (
    calculate_resistance_from_expression,
    solve_vipr,
)
from circuit_calculator.core.circuit_analyzer import CircuitAnalyzer
from circuit_calculator.ui.canvas import CircuitCanvasManager


class CircuitCalculatorApp:
    """Tkinter Desktop UI for Circuit and Power Calculations."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Electrical Circuit & Power Calculator")
        self.root.geometry("1150x880")
        self.root.minsize(950, 700)

        self._configure_styles()
        self._build_layout()

    def _configure_styles(self) -> None:
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TLabel", padding=4, font=('Helvetica', 10))
        style.configure("TButton", padding=5, font=('Helvetica', 10))
        style.configure("TEntry", padding=4, font=('Helvetica', 10))
        style.configure("TRadiobutton", padding=4, font=('Helvetica', 10))
        style.configure("Title.TLabel", font=('Helvetica', 11, 'bold'))
        style.configure("Result.TLabel", font=('Helvetica', 10, 'bold'), foreground="#0d47a1")
        style.configure("Error.TLabel", font=('Helvetica', 10, 'bold'), foreground="#b71c1c")
        style.configure("Note.TLabel", font=('Helvetica', 9), foreground="#555555")

    def _build_layout(self) -> None:
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)
        main_frame.columnconfigure(0, weight=4)  # Left panel
        main_frame.columnconfigure(1, weight=6)  # Right panel
        main_frame.rowconfigure(0, weight=1)

        self._build_left_panel(main_frame)
        self._build_right_panel(main_frame)

    def _build_left_panel(self, parent: ttk.Frame) -> None:
        left_panel = ttk.Frame(parent, padding="8")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        header_label = ttk.Label(
            left_panel,
            text="Solve V, I, R, P (Ohm's Law & Power)\nEnter any 3 variables (1 blank) OR enter V & I only.",
            style="Title.TLabel",
            wraplength=420
        )
        header_label.pack(pady=(0, 10), anchor="w")

        # --- Section 1: Resistor Network Expression ---
        expr_frame = ttk.LabelFrame(left_panel, text="Resistor Network Expression (Manual)", padding="10")
        expr_frame.pack(pady=6, fill=tk.X)
        expr_frame.columnconfigure(0, weight=1)

        ttk.Label(expr_frame, text="Resistance Expression (Ω):").grid(row=0, column=0, sticky="w")
        self.resistors_str_var = tk.StringVar()
        self.resistors_entry = ttk.Entry(expr_frame, textvariable=self.resistors_str_var)
        self.resistors_entry.grid(row=1, column=0, sticky="ew", padx=2, pady=(2, 4))

        syntax_hint = ttk.Label(
            expr_frame,
            text="Syntax: + (series), | (parallel), () (grouping). E.g.: 10 + (20 | 30)",
            style="Note.TLabel",
            wraplength=380
        )
        syntax_hint.grid(row=2, column=0, sticky="w")

        # --- Section 2: VIPR Variables ---
        vipr_frame = ttk.LabelFrame(left_panel, text="Circuit Variables (V, I, R, P)", padding="10")
        vipr_frame.pack(pady=6, fill=tk.X)
        vipr_frame.columnconfigure(1, weight=1)

        variable_defs = [
            ("Voltage (V):", "V"),
            ("Current (I) (A):", "I"),
            ("Total Resistance (R) (Ω):", "R"),
            ("Power (P) (W):", "P")
        ]
        self.entries: Dict[str, ttk.Entry] = {}
        self.entry_vars: Dict[str, tk.StringVar] = {}

        for row_idx, (label_text, key) in enumerate(variable_defs):
            ttk.Label(vipr_frame, text=label_text).grid(row=row_idx, column=0, sticky="w", pady=3)
            var = tk.StringVar()
            entry = ttk.Entry(vipr_frame, textvariable=var)
            entry.grid(row=row_idx, column=1, sticky="ew", padx=5, pady=3)
            self.entries[key] = entry
            self.entry_vars[key] = var

        # Buttons
        btn_frame = ttk.Frame(left_panel)
        btn_frame.pack(pady=8, fill=tk.X)

        self.calc_btn = ttk.Button(btn_frame, text="Calculate (Manual)", command=self.calculate_manual)
        self.calc_btn.pack(side=tk.LEFT, padx=4, expand=True, fill=tk.X)

        self.reset_btn = ttk.Button(btn_frame, text="Reset All", command=self.reset_all_fields)
        self.reset_btn.pack(side=tk.LEFT, padx=4, expand=True, fill=tk.X)

        # --- Section 3: Calculation Results ---
        results_frame = ttk.LabelFrame(left_panel, text="Manual Calculation Results", padding="10")
        results_frame.pack(pady=6, fill=tk.X)

        self.lbl_res_comp = ttk.Label(results_frame, text="Expression Resistance (R_comp): -", style="Result.TLabel")
        self.lbl_res_comp.pack(anchor="w", pady=2)

        self.lbl_res_v = ttk.Label(results_frame, text="Voltage (V): -", style="Result.TLabel")
        self.lbl_res_v.pack(anchor="w", pady=2)

        self.lbl_res_i = ttk.Label(results_frame, text="Current (I): -", style="Result.TLabel")
        self.lbl_res_i.pack(anchor="w", pady=2)

        self.lbl_res_r_total = ttk.Label(results_frame, text="Total Circuit Resistance (R_total): -", style="Result.TLabel")
        self.lbl_res_r_total.pack(anchor="w", pady=2)

        self.lbl_res_p = ttk.Label(results_frame, text="Power (P): -", style="Result.TLabel")
        self.lbl_res_p.pack(anchor="w", pady=2)

        self.lbl_status = ttk.Label(left_panel, text="", style="Result.TLabel", wraplength=420)
        self.lbl_status.pack(pady=(6, 2), fill=tk.X)

        self.lbl_note = ttk.Label(left_panel, text="", style="Note.TLabel", wraplength=420)
        self.lbl_note.pack(pady=(2, 6), fill=tk.X)

    def _build_right_panel(self, parent: ttk.Frame) -> None:
        right_panel = ttk.Frame(parent, padding="8")
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        right_panel.rowconfigure(1, weight=1)
        right_panel.columnconfigure(0, weight=1)

        # Toolbox bar
        toolbox_frame = ttk.LabelFrame(right_panel, text="Schematic Drafting Tools", padding="8")
        toolbox_frame.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        tool_select_frame = ttk.Frame(toolbox_frame)
        tool_select_frame.pack(side=tk.LEFT, padx=5)

        ttk.Label(tool_select_frame, text="Tool:", font=('Helvetica', 10, 'bold')).pack(anchor="w")
        self.selected_tool = tk.StringVar(value="resistor")

        for tool_name, tool_val in [("Resistor", "resistor"), ("Voltage Source", "voltage_source"), ("Wire", "wire")]:
            rb = ttk.Radiobutton(
                tool_select_frame,
                text=tool_name,
                variable=self.selected_tool,
                value=tool_val,
                command=self._update_tool_input_visibility
            )
            rb.pack(anchor="w")

        # Values input frame for active tool
        self.tool_val_frame = ttk.Frame(toolbox_frame)
        self.tool_val_frame.pack(side=tk.LEFT, padx=20)

        self.resistor_val_label = ttk.Label(self.tool_val_frame, text="Resistance (Ω):")
        self.resistor_val_var = tk.StringVar(value="10")
        self.resistor_val_entry = ttk.Entry(self.tool_val_frame, textvariable=self.resistor_val_var, width=12)

        self.voltage_val_label = ttk.Label(self.tool_val_frame, text="Voltage (V):")
        self.voltage_val_var = tk.StringVar(value="5")
        self.voltage_val_entry = ttk.Entry(self.tool_val_frame, textvariable=self.voltage_val_var, width=12)

        self._update_tool_input_visibility()

        # Canvas
        self.circuit_canvas = tk.Canvas(right_panel, bg="white", relief=tk.SUNKEN, borderwidth=1)
        self.circuit_canvas.grid(row=1, column=0, sticky="nsew", pady=4)

        # Setup Canvas Manager
        self.canvas_mgr = CircuitCanvasManager(
            canvas=self.circuit_canvas,
            parent_window=self.root,
            status_callback=self._set_status,
            get_selected_tool=lambda: self.selected_tool.get(),
            get_tool_values=self._get_tool_values
        )

        # Action Buttons
        canvas_actions_frame = ttk.Frame(right_panel)
        canvas_actions_frame.grid(row=2, column=0, sticky="ew", pady=4)

        ttk.Button(canvas_actions_frame, text="Clear Canvas", command=self.clear_canvas).pack(
            side=tk.LEFT, padx=3, expand=True, fill=tk.X
        )
        ttk.Button(canvas_actions_frame, text="Analyze Circuit", command=self.analyze_visual_circuit).pack(
            side=tk.LEFT, padx=3, expand=True, fill=tk.X
        )
        ttk.Button(canvas_actions_frame, text="Transfer to Manual", command=self.transfer_visual_to_manual).pack(
            side=tk.LEFT, padx=3, expand=True, fill=tk.X
        )

        controls_tip = (
            "Controls: Left-click to place/select. Drag to reposition. "
            "Press 'R' to rotate component. Double-click to edit value. "
            "Right-click to delete/cancel."
        )
        ttk.Label(right_panel, text=controls_tip, style="Note.TLabel", wraplength=600).grid(
            row=3, column=0, sticky="w", pady=(3, 0)
        )

    def _update_tool_input_visibility(self) -> None:
        tool = self.selected_tool.get()
        self.resistor_val_label.pack_forget()
        self.resistor_val_entry.pack_forget()
        self.voltage_val_label.pack_forget()
        self.voltage_val_entry.pack_forget()

        if tool == "resistor":
            self.resistor_val_label.pack(anchor="w")
            self.resistor_val_entry.pack(anchor="w", pady=(2, 0))
        elif tool == "voltage_source":
            self.voltage_val_label.pack(anchor="w")
            self.voltage_val_entry.pack(anchor="w", pady=(2, 0))

    def _get_tool_values(self) -> Tuple[float, float]:
        r_val = 10.0
        v_val = 5.0
        try:
            r_val = float(self.resistor_val_var.get())
        except ValueError:
            pass
        try:
            v_val = float(self.voltage_val_var.get())
        except ValueError:
            pass
        return r_val, v_val

    def _set_status(self, message: str, is_error: bool = False) -> None:
        style_name = "Error.TLabel" if is_error else "Result.TLabel"
        self.lbl_status.config(text=message, style=style_name)

    # --- Actions & Logic ---
    def calculate_manual(self) -> None:
        self.clear_manual_results()
        self.lbl_note.config(text="")

        # 1. Parse resistor expression if provided
        r_comp = None
        expr = self.resistors_str_var.get().strip()
        if expr:
            try:
                r_comp = calculate_resistance_from_expression(expr)
                self.lbl_res_comp.config(text=f"Expression Resistance (R_comp): {r_comp:.2f} Ω")
            except Exception as exc:
                self._set_status(f"Resistor Expression Error: {exc}", is_error=True)
                return
        else:
            self.lbl_res_comp.config(text="Expression Resistance (R_comp): - (none)")

        # 2. Extract VIPR entries
        parsed_inputs = {}
        for key, var in self.entry_vars.items():
            val_str = var.get().strip()
            if not val_str:
                parsed_inputs[key] = None
            else:
                try:
                    parsed_inputs[key] = float(val_str)
                except ValueError:
                    self._set_status(f"Input Error: Value for '{key}' is not a valid number.", is_error=True)
                    return

        # 3. Solve VIPR
        result = solve_vipr(
            v=parsed_inputs.get('V'),
            i=parsed_inputs.get('I'),
            r=parsed_inputs.get('R'),
            p=parsed_inputs.get('P'),
        )

        if result.is_error:
            self._set_status(result.status, is_error=True)
            if result.note:
                self.lbl_note.config(text=result.note)
            return

        # 4. Update display
        self.lbl_res_v.config(text=f"Voltage (V): {result.v:.2f} V" if result.v is not None else "Voltage (V): -")
        self.lbl_res_i.config(text=f"Current (I): {result.i:.2f} A" if result.i is not None else "Current (I): -")
        self.lbl_res_r_total.config(
            text=f"Total Circuit Resistance (R_total): {result.r:.2f} Ω" if result.r is not None else "Total Circuit Resistance (R_total): -"
        )
        self.lbl_res_p.config(text=f"Power (P): {result.p:.2f} W" if result.p is not None else "Power (P): -")

        self._set_status(result.status, is_error=False)

        # 5. Check compatibility between R_total and R_comp
        if r_comp is not None and result.r is not None:
            if not math.isclose(r_comp, result.r, rel_tol=1e-2):
                existing = self.lbl_note.cget("text")
                sep = "\n" if existing else ""
                self.lbl_note.config(
                    text=f"{existing}{sep}Note: Total Resistance R_total ({result.r:.2f} Ω) differs from R_comp ({r_comp:.2f} Ω)."
                )
        elif r_comp is not None and parsed_inputs.get('R') is None and self.entry_vars['R'].get().strip() == "":
            self.entry_vars['R'].set(f"{r_comp:.2f}")
            self.lbl_res_r_total.config(text=f"Total Circuit Resistance (R_total): {r_comp:.2f} Ω (from R_comp)")
            existing = self.lbl_note.cget("text")
            sep = "\n" if existing else ""
            self.lbl_note.config(text=f"{existing}{sep}Note: R_total populated from expression R_comp ({r_comp:.2f} Ω).")

    def analyze_visual_circuit(self) -> Tuple[str, float]:
        status_msg, r_eq = CircuitAnalyzer.analyze_circuit(self.canvas_mgr.elements)
        if r_eq is not None:
            self._set_status(f"Visual Analysis: {status_msg} (R_eq = {r_eq:.2f} Ω)", is_error=False)
        else:
            self._set_status(f"Visual Analysis: {status_msg}", is_error=True)
        return status_msg, r_eq

    def transfer_visual_to_manual(self) -> None:
        if not self.canvas_mgr.elements:
            self._set_status("No elements on canvas to transfer.", is_error=True)
            return

        expr_status, r_expr = CircuitAnalyzer.generate_resistor_expression(self.canvas_mgr.elements)
        _, r_total = CircuitAnalyzer.analyze_circuit(self.canvas_mgr.elements)

        visual_v = None
        visual_i = None
        v_sources = [el for el in self.canvas_mgr.elements if el.get('type') == 'voltage_source']
        if v_sources:
            src = v_sources[0]
            visual_v = src.get('value')
            visual_i = src.get('current_value')
            if len(v_sources) > 1:
                self._set_status("Warning: Multiple voltage sources found; only the first was transferred.", is_error=True)

        note_lines = ["Transferred from schematic:"]
        has_transfer = False

        if r_expr:
            self.resistors_str_var.set(r_expr)
            note_lines.append(f"• Resistor Expression: {r_expr}")
            has_transfer = True
        else:
            resistors = [el['value'] for el in self.canvas_mgr.elements if el.get('type') == 'resistor']
            if resistors:
                self.resistors_str_var.set(", ".join(map(str, resistors)))
                note_lines.append(f"• Raw Resistors (non-reducible): {', '.join(map(str, resistors))} Ω")
                note_lines.append(f"  ({expr_status})")
                has_transfer = True

        if r_total is not None:
            self.entry_vars['R'].set(f"{r_total:.2f}")
            note_lines.append(f"• R_total (from network reduction): {r_total:.2f} Ω")
            has_transfer = True

        if visual_v is not None:
            self.entry_vars['V'].set(f"{visual_v:.2f}")
            note_lines.append(f"• Voltage: {visual_v:.2f} V")
            has_transfer = True

        if visual_i is not None and visual_i != 0.0:
            self.entry_vars['I'].set(f"{visual_i:.2f}")
            note_lines.append(f"• Current: {visual_i:.2f} A")
            has_transfer = True

        if has_transfer:
            note_lines.append("Complete any remaining fields and click 'Calculate (Manual)'.")
            self.lbl_note.config(text="\n".join(note_lines))
            self._set_status("Visual schematic data transferred to manual input.", is_error=False)
        else:
            self.lbl_note.config(text="No valid components to transfer.")
            self._set_status("No valid schematic data found to transfer.", is_error=True)

    def clear_manual_results(self) -> None:
        self.lbl_res_comp.config(text="Expression Resistance (R_comp): -")
        self.lbl_res_v.config(text="Voltage (V): -")
        self.lbl_res_i.config(text="Current (I): -")
        self.lbl_res_r_total.config(text="Total Circuit Resistance (R_total): -")
        self.lbl_res_p.config(text="Power (P): -")

    def reset_all_fields(self) -> None:
        self.resistors_str_var.set("")
        for var in self.entry_vars.values():
            var.set("")
        self.clear_manual_results()
        self.clear_canvas()
        self._set_status("All inputs, results, and schematic reset.", is_error=False)
        self.lbl_note.config(text="")

    def clear_canvas(self) -> None:
        self.canvas_mgr.clear_canvas()


def main() -> None:
    root = tk.Tk()
    app = CircuitCalculatorApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
