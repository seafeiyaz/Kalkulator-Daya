"""
Custom dialogs for circuit component property editing.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import Optional, Tuple


class CustomSourceDialog(simpledialog.Dialog):
    """Custom modal dialog to edit the properties (Voltage and Current) of a voltage source."""

    def __init__(self, parent: tk.Widget, title: str, initial_voltage: float, initial_current: float):
        self.initial_voltage = initial_voltage
        self.initial_current = initial_current
        self.voltage_var = tk.StringVar(parent)
        self.current_var = tk.StringVar(parent)
        self.result: Optional[Tuple[float, float]] = None
        super().__init__(parent, title)

    def body(self, master: tk.Widget) -> ttk.Entry:
        ttk.Label(master, text="Voltage Value (V):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.voltage_entry = ttk.Entry(master, textvariable=self.voltage_var, width=15)
        self.voltage_entry.grid(row=0, column=1, padx=5, pady=5)
        self.voltage_var.set(str(self.initial_voltage))

        ttk.Label(master, text="Associated Current (A):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.current_entry = ttk.Entry(master, textvariable=self.current_var, width=15)
        self.current_entry.grid(row=1, column=1, padx=5, pady=5)
        self.current_var.set(str(self.initial_current))

        return self.voltage_entry

    def apply(self) -> None:
        try:
            voltage = float(self.voltage_var.get())
            current = float(self.current_var.get())
            if voltage <= 0:
                messagebox.showerror("Invalid Value", "Voltage must be a positive number.", parent=self)
                self.result = None
                return
            self.result = (voltage, current)
        except ValueError:
            messagebox.showerror("Invalid Value", "Voltage and current must be valid numeric values.", parent=self)
            self.result = None
