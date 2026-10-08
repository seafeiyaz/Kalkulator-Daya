#!/usr/bin/env python3
"""
Legacy Entrypoint for Backward Compatibility.

Redirects execution to the refactored modern package:
circuit_calculator.ui.app.main()
"""

import os
import sys

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from circuit_calculator.ui.app import main

if __name__ == '__main__':
    main()
