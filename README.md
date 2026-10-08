# Electrical Circuit & Power Calculator

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-Tkinter-green.svg)](https://docs.python.org/3/library/tkinter.html)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](tests/)

A desktop application built with Python and Tkinter for calculating, designing, and analyzing DC electrical circuits. It features dual interactive modes: **Manual VIPR Solving** with symbolic series/parallel expressions and a **Visual Schematic Canvas** with graph-based circuit network reduction.

![Circuit Calculator Screenshot](https://github.com/user-attachments/assets/15adb796-5ad7-471d-b15b-b71fd04405cf)

---

## Key Features

- **Ohm's Law & Electric Power Solver (VIPR)**:
  - Solves the relationship between **Voltage ($V$)**, **Current ($I$)**, **Resistance ($R$)**, and **Power ($P$)**.
  - Enter any 3 variables to compute the 4th, or input only $V$ and $I$ to automatically derive $R$ and $P$.
  - Automatically verifies 4-variable sets for physical consistency ($V = I \cdot R$ and $P = V \cdot I$).
- **Algebraic Resistor Expression Evaluator**:
  - Solves compound resistor configurations using intuitive syntax:
    - `+` for series combinations (e.g., `10 + 20`)
    - `|` for parallel branches (e.g., `20 | 30`)
    - `( )` for nested sub-circuits (e.g., `10 + (20 | 30)`)
- **Interactive Visual Schematic Designer**:
  - Drag-and-drop 2D canvas with grid alignment and pin snapping.
  - Place DC Voltage Sources, Resistors, and interconnecting Wires.
  - Live wire rerouting when components are repositioned.
  - Hotkey rotation (`R`), double-click property editing, and right-click deletion.
- **Topological Network Reduction**:
  - Implements an iterative graph-reduction algorithm to simplify schematics.
  - Computes equivalent resistance ($R_{eq}$) and generates the equivalent algebraic formula directly from the drawn schematic.
- **Visual-to-Manual Bridge**:
  - One-click transfer (`Transfer to Manual`) imports voltages, currents, and equivalent network formulas from your schematic into the calculation engine.

---

## Project Structure

```text
Kalkulator-Daya/
├── circuit_calculator/         # Core application package
│   ├── __init__.py             # Package metadata
│   ├── __main__.py             # Package entrypoint (python -m circuit_calculator)
│   ├── core/                   # Pure business logic & algorithms
│   │   ├── __init__.py
│   │   ├── calculator.py       # VIPR formulas & recursive expression parser
│   │   └── circuit_analyzer.py # Graph reduction & electrical node analysis
│   └── ui/                     # Tkinter user interface
│       ├── __init__.py
│       ├── app.py              # Main application window & layout
│       ├── canvas.py           # Interactive 2D schematic canvas
│       └── dialogs.py          # Component property editing dialogs
├── tests/                      # Automated test suite
│   ├── __init__.py
│   ├── test_calculator.py     # Unit tests for VIPR math & expressions
│   └── test_analyzer.py       # Unit tests for graph reduction
├── Main/                       # Backward compatibility directory
│   └── Kalkulator Daya.py      # Legacy entrypoint stub
├── main.py                     # Primary root runner (python main.py)
├── pyproject.toml              # Modern Python packaging configuration
├── requirements.txt            # Environment & dependency notes
├── LICENSE                     # MIT License
└── README.md                   # Project documentation
```

---

## Installation & Requirements

The application runs on standard Python with **zero external dependencies**. All libraries (`tkinter`, `math`, `re`, `unittest`) are included in Python's standard library.

### Prerequisites

- Python 3.8 or higher.

#### Windows & macOS
Python installers from [python.org](https://www.python.org/downloads/) bundle Tkinter by default.
> **Note for Windows:** During installation, ensure you check **"Add Python to PATH"**.

#### Linux (Debian / Ubuntu / Raspberry Pi OS)
On some Linux distributions, Tkinter must be installed via your system package manager:
```bash
sudo apt update
sudo apt install python3 python3-tk
```

---

## How to Run

Clone the repository and run using any of the following methods:

### Method 1: Root Launcher (Recommended)
```bash
python main.py
```

### Method 2: Python Module
```bash
python -m circuit_calculator
```

### Method 3: Legacy Compatibility
```bash
python "Main/Kalkulator Daya.py"
```

---

## Controls & Shortcuts (Schematic Canvas)

| Action | Control |
| :--- | :--- |
| **Select Tool** | Choose `Resistor`, `Voltage Source`, or `Wire` in the toolbox panel. |
| **Place Component** | Left-click on the canvas grid. |
| **Move Component** | Click and drag the component to the desired grid location. |
| **Rotate Component** | Select a component and press <kbd>R</kbd>. |
| **Edit Value** | Double-click on any component to change its resistance or voltage/current. |
| **Route Wire** | Click a terminal pin to start, click to add elbows, and click the destination pin or double-click to finish. |
| **Cancel Wire / Deselect** | Right-click anywhere on the canvas or press <kbd>Esc</kbd>. |
| **Delete Element** | Right-click directly on any component or wire segment. |

---

## Running Automated Tests

To execute the unit test suite verifying mathematical solvers and topological graph reduction:

```bash
python -m unittest discover tests
```

---

## License

This project is licensed under the [MIT License](LICENSE).
Created and maintained by [seafeiyaz](https://github.com/seafeiyaz) (MuhammadWPA).
