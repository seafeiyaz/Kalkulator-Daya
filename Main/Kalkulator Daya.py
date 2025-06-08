import tkinter as tk
from tkinter import ttk, messagebox, colorchooser, simpledialog
import math
import re

class CustomSourceDialog(simpledialog.Dialog):
    """A custom dialog to edit the properties of a voltage source."""
    def __init__(self, parent, title, initial_voltage, initial_current):
        self.initial_voltage = initial_voltage
        self.initial_current = initial_current
        self.voltage_var = tk.StringVar(parent)
        self.current_var = tk.StringVar(parent)
        super().__init__(parent, title)

    def body(self, master):
        ttk.Label(master, text="Nilai Tegangan (V):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.voltage_entry = ttk.Entry(master, textvariable=self.voltage_var, width=15)
        self.voltage_entry.grid(row=0, column=1, padx=5, pady=5)
        self.voltage_var.set(str(self.initial_voltage))

        ttk.Label(master, text="Nilai Arus (A):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.current_entry = ttk.Entry(master, textvariable=self.current_var, width=15)
        self.current_entry.grid(row=1, column=1, padx=5, pady=5)
        self.current_var.set(str(self.initial_current))
        
        return self.voltage_entry # initial focus

    def apply(self):
        try:
            voltage = float(self.voltage_var.get())
            current = float(self.current_var.get())
            if voltage <= 0:
                messagebox.showerror("Error Nilai", "Nilai tegangan harus positif.", parent=self)
                self.result = None
                return
            self.result = (voltage, current)
        except ValueError:
            messagebox.showerror("Error Nilai", "Nilai tegangan/arus tidak valid.", parent=self)
            self.result = None


class CircuitCalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Kalkulator Rangkaian Listrik")
        self.root.geometry("1100x850")

        # --- Styling & Constants ---
        style = ttk.Style()
        style.theme_use('clam') 
        style.configure("TLabel", padding=5, font=('Helvetica', 10))
        style.configure("TButton", padding=5, font=('Helvetica', 10))
        style.configure("TEntry", padding=5, font=('Helvetica', 10))
        style.configure("TRadiobutton", padding=5, font=('Helvetica', 10))
        style.configure("Title.TLabel", font=('Helvetica', 12, 'bold'))
        style.configure("Result.TLabel", font=('Helvetica', 10, 'bold'), foreground="blue")
        style.configure("Error.TLabel", font=('Helvetica', 10, 'bold'), foreground="red")
        style.configure("Note.TLabel", font=('Helvetica', 9), foreground="gray")

        # --- Grid and Component Constants ---
        self.GRID_SIZE = 20  
        self.CP_RADIUS = 3   
        self.SELECTED_OUTLINE_COLOR = "green"
        self.DEFAULT_OUTLINE_COLOR = "black"
        self.SELECTED_OUTLINE_WIDTH = 2
        self.DEFAULT_OUTLINE_WIDTH = 1
        self.RESISTOR_WIDTH = 2 * self.GRID_SIZE
        self.RESISTOR_HEIGHT = 1 * self.GRID_SIZE
        self.VOLTAGE_SOURCE_RADIUS = 1.0 * self.GRID_SIZE

        # --- Main Application Frame ---
        app_frame = ttk.Frame(root, padding="10")
        app_frame.pack(expand=True, fill=tk.BOTH)
        app_frame.columnconfigure(0, weight=1) 
        app_frame.columnconfigure(1, weight=3)
        app_frame.rowconfigure(0, weight=1)   

        # --- Left Panel (Manual Inputs and Results) ---
        left_panel = ttk.Frame(app_frame, padding="10")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        title_label = ttk.Label(left_panel, text="Isi variabel V,I,R,P: 3 nilai (1 kosong) ATAU isi V dan I saja (R,P kosong)", style="Title.TLabel", wraplength=480)
        title_label.pack(pady=(0,10), anchor="w")
        
        # --- UPDATED: Manual Input for Mixed Circuits ---
        components_frame = ttk.LabelFrame(left_panel, text="Konfigurasi Komponen Resistor (Input Manual)", padding="10")
        components_frame.pack(pady=10, fill=tk.X, expand=False)
        components_frame.columnconfigure(0, weight=1)

        ttk.Label(components_frame, text="Ekspresi Resistor (Ω):", wraplength=300).grid(row=0, column=0, sticky="w")
        self.resistors_str_var = tk.StringVar()
        self.resistors_entry = ttk.Entry(components_frame, textvariable=self.resistors_str_var)
        self.resistors_entry.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))
        ttk.Label(components_frame, text="Gunakan + (seri), | (paralel), dan () untuk grup. Cth: 10 + (20|30)", style="Note.TLabel").grid(row=2, column=0, sticky="w", padx=5)

        vipr_frame = ttk.LabelFrame(left_panel, text="Variabel Rangkaian Utama (Input Manual)", padding="10")
        vipr_frame.pack(pady=10, fill=tk.X, expand=False)
        vipr_frame.columnconfigure(1, weight=1)
        
        labels_texts = ["Tegangan (V):", "Arus (I) (A):", "Hambatan Total (R) (Ω):", "Daya (P) (W):"]
        self.entries = {}
        self.entry_vars = {}

        for i, text in enumerate(labels_texts):
            ttk.Label(vipr_frame, text=text).grid(row=i, column=0, sticky="w", pady=2)
            var = tk.StringVar()
            entry = ttk.Entry(vipr_frame, textvariable=var)
            entry.grid(row=i, column=1, sticky="ew", padx=5, pady=2)
            try:
                key_char_index = text.find('(') + 1
                key = text[key_char_index]
            except IndexError: 
                key = f"UNKNOWN_{i}"
            self.entries[key] = entry
            self.entry_vars[key] = var
        
        buttons_frame = ttk.Frame(left_panel)
        buttons_frame.pack(pady=10)

        self.calculate_button = ttk.Button(buttons_frame, text="Hitung (Manual)", command=self.calculate_manual)
        self.calculate_button.pack(side=tk.LEFT, padx=5)

        self.reset_button = ttk.Button(buttons_frame, text="Reset Semua", command=self.reset_all_fields)
        self.reset_button.pack(side=tk.LEFT, padx=5)

        results_frame = ttk.LabelFrame(left_panel, text="Hasil Perhitungan (Input Manual)", padding="10")
        results_frame.pack(pady=10, fill=tk.X, expand=False)

        self.label_res_components = ttk.Label(results_frame, text="Hambatan dari ekspresi (R_comp): -", style="Result.TLabel")
        self.label_res_components.pack(anchor="w")
        self.label_res_v = ttk.Label(results_frame, text="Tegangan (V): -", style="Result.TLabel")
        self.label_res_v.pack(anchor="w")
        self.label_res_i = ttk.Label(results_frame, text="Arus (I): -", style="Result.TLabel")
        self.label_res_i.pack(anchor="w")
        self.label_res_r_total = ttk.Label(results_frame, text="Hambatan Total Rangkaian (R_total): -", style="Result.TLabel")
        self.label_res_r_total.pack(anchor="w")
        self.label_res_p = ttk.Label(results_frame, text="Daya (P): -", style="Result.TLabel")
        self.label_res_p.pack(anchor="w")

        self.label_status = ttk.Label(left_panel, text="", style="Error.TLabel", wraplength=350)
        self.label_status.pack(pady=(5,0), fill=tk.X)
        
        self.label_note = ttk.Label(left_panel, text="", style="Note.TLabel", wraplength=350)
        self.label_note.pack(pady=(0,5), fill=tk.X)

        # --- Right Panel (Visual Design) ---
        right_panel = ttk.Frame(app_frame, padding="10")
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        right_panel.rowconfigure(1, weight=1) 
        right_panel.columnconfigure(0, weight=1) 

        visual_tool_controls_frame = ttk.LabelFrame(right_panel, text="Input dengan Gambar", padding="10")
        visual_tool_controls_frame.grid(row=0, column=0, sticky="ew", pady=(0,5))

        ttk.Label(visual_tool_controls_frame, text="Pilih Alat (untuk menambah):").grid(row=0, column=0, sticky="w") 
        self.selected_tool = tk.StringVar(value="resistor") 
        
        resistor_tool_rb = ttk.Radiobutton(visual_tool_controls_frame, text="Resistor", variable=self.selected_tool, value="resistor", command=self.update_visual_input_visibility)
        resistor_tool_rb.grid(row=1, column=0, sticky="w")
        
        voltage_tool_rb = ttk.Radiobutton(visual_tool_controls_frame, text="Sumber Tegangan", variable=self.selected_tool, value="voltage_source", command=self.update_visual_input_visibility)
        voltage_tool_rb.grid(row=2, column=0, sticky="w")

        wire_tool_rb = ttk.Radiobutton(visual_tool_controls_frame, text="Kabel", variable=self.selected_tool, value="wire", command=self.update_visual_input_visibility)
        wire_tool_rb.grid(row=3, column=0, sticky="w")
        
        self.visual_value_input_frame = ttk.Frame(visual_tool_controls_frame)
        self.visual_value_input_frame.grid(row=0, column=1, rowspan=4, sticky="ns", padx=10)

        self.visual_resistor_label = ttk.Label(self.visual_value_input_frame, text="Nilai Resistor (Ω):")
        self.visual_resistor_value_var = tk.StringVar(value="10")
        self.visual_resistor_entry = ttk.Entry(self.visual_value_input_frame, textvariable=self.visual_resistor_value_var, width=10)

        self.visual_voltage_label = ttk.Label(self.visual_value_input_frame, text="Nilai Tegangan (V):")
        self.visual_voltage_value_var = tk.StringVar(value="5")
        self.visual_voltage_entry = ttk.Entry(self.visual_value_input_frame, textvariable=self.visual_voltage_value_var, width=10)
        
        self.update_visual_input_visibility() 

        self.circuit_canvas = tk.Canvas(right_panel, bg="white", relief=tk.SUNKEN, borderwidth=1) 
        self.circuit_canvas.grid(row=1, column=0, sticky="nsew", pady=5)
        
        # --- State variables for visual design ---
        self.canvas_elements = [] 
        self.drag_data = {"item": None, "group_tag": None, "offset_x": 0, "offset_y": 0} 
        self.selected_canvas_item_group_tag = None 
        self.is_wiring = False
        self.current_wire_points = []
        self.current_wire_c_points_info = [] # Stores start/end CP info
        self.temp_wire_id = None

        self._draw_grid()

        # --- Event Bindings ---
        self.circuit_canvas.bind("<Button-1>", self.on_canvas_left_click)
        self.circuit_canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.circuit_canvas.bind("<ButtonRelease-1>", self.on_canvas_left_release)
        self.circuit_canvas.bind("<Button-3>", self.on_canvas_right_click) 
        self.circuit_canvas.bind("<Double-Button-1>", self.on_canvas_double_click)
        self.circuit_canvas.bind("<Motion>", self.on_canvas_motion)
        self.root.bind("<KeyPress-r>", self.on_keypress_r) 
        self.root.bind("<KeyPress-R>", self.on_keypress_r)

        visual_canvas_buttons_frame = ttk.Frame(right_panel)
        visual_canvas_buttons_frame.grid(row=2, column=0, sticky="ew", pady=(5,0))

        self.clear_canvas_button = ttk.Button(visual_canvas_buttons_frame, text="Bersihkan Kanvas", command=self.clear_canvas)
        self.clear_canvas_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        self.analyze_circuit_button = ttk.Button(visual_canvas_buttons_frame, text="Analisis Rangkaian Visual", command=self.analyze_visual_circuit_and_display)
        self.analyze_circuit_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self.transfer_visual_button = ttk.Button(visual_canvas_buttons_frame, text="Transfer Visual ke Input Manual", command=self.transfer_visual_to_manual)
        self.transfer_visual_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        ttk.Label(right_panel, text="Pilih Alat. Klik kiri: Tambah/Pilih. Tahan & Geser: Pindahkan Komponen.\nKabel: Klik untuk mulai, klik lagi untuk belok, Dobel-klik/klik di titik koneksi untuk selesai. Klik kanan: Hapus/Batal.", font=('Helvetica', 8)).grid(row=3, column=0, sticky="w", pady=(5,0))

    def _draw_grid(self):
        """Draws a grid on the canvas."""
        for i in range(0, 2000, self.GRID_SIZE):
            self.circuit_canvas.create_line(i, 0, i, 2000, fill="#f0f0f0", tags="grid_line")
        for i in range(0, 2000, self.GRID_SIZE):
            self.circuit_canvas.create_line(0, i, 2000, i, fill="#f0f0f0", tags="grid_line")
        self.circuit_canvas.tag_lower("grid_line") 

    def _snap_to_grid(self, x, y):
        """Snaps x, y coordinates to the nearest grid point."""
        snapped_x = round(x / self.GRID_SIZE) * self.GRID_SIZE
        snapped_y = round(y / self.GRID_SIZE) * self.GRID_SIZE
        return int(snapped_x), int(snapped_y)

    def _update_wire_path(self, wire_data):
        """Recalculates and redraws a wire's path when a connected component moves."""
        if not wire_data or wire_data['type'] != 'wire':
            return
            
        # Update start point if connected
        if 'start_cp_info' in wire_data and wire_data['start_cp_info']:
            start_info = wire_data['start_cp_info']
            _, start_comp_data = self.find_element_by_group_tag(start_info['component_group_tag'])
            if start_comp_data:
                new_start_coords = (
                    start_comp_data['connection_points'][start_info['cp_index']]['abs_x'],
                    start_comp_data['connection_points'][start_info['cp_index']]['abs_y']
                )
                wire_data['path'][0] = new_start_coords

        # Update end point if connected
        if 'end_cp_info' in wire_data and wire_data['end_cp_info']:
            end_info = wire_data['end_cp_info']
            _, end_comp_data = self.find_element_by_group_tag(end_info['component_group_tag'])
            if end_comp_data:
                new_end_coords = (
                    end_comp_data['connection_points'][end_info['cp_index']]['abs_x'],
                    end_comp_data['connection_points'][end_info['cp_index']]['abs_y']
                )
                wire_data['path'][-1] = new_end_coords

        # Redraw the wire on canvas
        if len(wire_data['path']) > 1:
            flat_path = [coord for point in wire_data['path'] for coord in point]
            self.circuit_canvas.coords(wire_data['main_id'], *flat_path)

    # --- Electrical Node Analysis & Circuit Simplification ---

    def _get_cp_tuple_from_wire_info(self, cp_info):
        if not cp_info: return None
        return (cp_info['component_group_tag'], cp_info['cp_index'])

    def _build_electrical_nodes(self, components_to_include, wires):
        all_component_cps = []
        for comp_data in components_to_include:
            for i in range(len(comp_data.get('connection_points', []))):
                all_component_cps.append((comp_data['group_tag'], i))

        if not all_component_cps:
            return []

        node_map = {cp_tuple: frozenset([cp_tuple]) for cp_tuple in all_component_cps}
        
        for wire_data in wires:
            connected_cps_on_wire = []
            if wire_data.get('start_cp_info'):
                connected_cps_on_wire.append(self._get_cp_tuple_from_wire_info(wire_data['start_cp_info']))
            if wire_data.get('end_cp_info'):
                connected_cps_on_wire.append(self._get_cp_tuple_from_wire_info(wire_data['end_cp_info']))
            
            connected_cps_on_wire = [cp for cp in connected_cps_on_wire if cp and cp in node_map]
            if len(connected_cps_on_wire) < 2:
                continue

            base_node_set = node_map[connected_cps_on_wire[0]]
            nodes_to_merge = [base_node_set]
            for i in range(1, len(connected_cps_on_wire)):
                node_to_add = node_map[connected_cps_on_wire[i]]
                if node_to_add not in nodes_to_merge:
                    nodes_to_merge.append(node_to_add)
            
            if len(nodes_to_merge) > 1:
                merged_node = frozenset().union(*nodes_to_merge)
                for cp_in_merged in merged_node:
                    node_map[cp_in_merged] = merged_node
        
        final_nodes = list(dict.fromkeys(node_map.values()))
        return final_nodes
        
    def analyze_visual_circuit(self):
        """
        Analyzes the visual circuit using graph reduction to find the equivalent resistance.
        Returns a tuple: (string_result, numeric_value_or_None)
        """
        resistors_data = [elem for elem in self.canvas_elements if elem['type'] == 'resistor']
        sources_data = [elem for elem in self.canvas_elements if elem['type'] == 'voltage_source']
        wires_data = [elem for elem in self.canvas_elements if elem['type'] == 'wire']

        if not sources_data: return "Tidak ada sumber tegangan.", None
        if len(sources_data) > 1: return "Analisis hanya mendukung 1 sumber tegangan.", None
        if not resistors_data: return "Tidak ada resistor untuk dianalisis.", None

        source = sources_data[0]
        components_for_node_building = resistors_data + sources_data
        
        # Build node sets
        electrical_nodes = self._build_electrical_nodes(components_for_node_building, wires_data)
        if not electrical_nodes: return "Tidak dapat membangun node listrik.", None

        # Map nodes to integer IDs for easier processing
        node_map = {node_set: i for i, node_set in enumerate(electrical_nodes)}
        
        # Represent resistors as [value, node1_id, node2_id]
        resistors = []
        for r_data in resistors_data:
            cp1_tuple = (r_data['group_tag'], 0)
            cp2_tuple = (r_data['group_tag'], 1)
            
            node1 = next((node_set for node_set in electrical_nodes if cp1_tuple in node_set), None)
            node2 = next((node_set for node_set in electrical_nodes if cp2_tuple in node_set), None)

            if node1 is None or node2 is None or node1 == node2:
                return f"Resistor {r_data['value']}Ω terhubung singkat atau tidak terhubung.", None
            
            resistors.append([r_data['value'], node_map[node1], node_map[node2]])
            
        # Identify source nodes
        src_cp1_tuple = (source['group_tag'], 0)
        src_cp2_tuple = (source['group_tag'], 1)
        src_node1_set = next((node_set for node_set in electrical_nodes if src_cp1_tuple in node_set), None)
        src_node2_set = next((node_set for node_set in electrical_nodes if src_cp2_tuple in node_set), None)
        
        if src_node1_set is None or src_node2_set is None: return "Sumber tegangan tidak terhubung.", None
        if src_node1_set == src_node2_set: return "Sumber tegangan terhubung singkat.", None
        
        source_node_id1 = node_map[src_node1_set]
        source_node_id2 = node_map[src_node2_set]
        
        # Simplification loop
        while True:
            simplified_in_pass = False
            
            # 1. Find and combine series resistors
            node_connections = {}
            for i, r in enumerate(resistors):
                n1, n2 = r[1], r[2]
                node_connections.setdefault(n1, []).append(i)
                node_connections.setdefault(n2, []).append(i)

            for node_id, conn_indices in node_connections.items():
                # A series connection node has exactly two connections and is not a source terminal
                if len(conn_indices) == 2 and node_id not in [source_node_id1, source_node_id2]:
                    r_idx1, r_idx2 = conn_indices[0], conn_indices[1]
                    r1_val, r1_n1, r1_n2 = resistors[r_idx1]
                    r2_val, r2_n1, r2_n2 = resistors[r_idx2]
                    
                    # New resistor value
                    new_r_val = r1_val + r2_val
                    
                    # Find the two outer nodes
                    new_n1 = r1_n1 if r1_n2 == node_id else r1_n2
                    new_n2 = r2_n1 if r2_n2 == node_id else r2_n2
                    
                    # Remove old resistors, add new one
                    resistors.append([new_r_val, new_n1, new_n2])
                    # Mark old ones for deletion by setting value to -1
                    resistors[r_idx1][0] = -1
                    resistors[r_idx2][0] = -1
                    
                    simplified_in_pass = True
                    break # Restart search
            
            resistors = [r for r in resistors if r[0] != -1]
            if simplified_in_pass:
                continue

            # 2. Find and combine parallel resistors
            resistor_pairs = {}
            for i, r in enumerate(resistors):
                # Use a sorted tuple of nodes as a key to identify parallel components
                key = tuple(sorted((r[1], r[2])))
                resistor_pairs.setdefault(key, []).append(i)

            for key, indices in resistor_pairs.items():
                if len(indices) > 1:
                    r_parallel_val = 0
                    try:
                        r_parallel_val = 1 / sum(1 / resistors[i][0] for i in indices)
                    except ZeroDivisionError:
                        r_parallel_val = 0 # Short circuit
                    
                    n1, n2 = key
                    resistors.append([r_parallel_val, n1, n2])
                    for i in indices:
                        resistors[i][0] = -1 # Mark for deletion
                        
                    simplified_in_pass = True
                    break # Restart search
            
            resistors = [r for r in resistors if r[0] != -1]
            if simplified_in_pass:
                continue

            # If no simplification was made in a full pass, exit the loop
            if not simplified_in_pass:
                break
                
        # Final check
        if len(resistors) == 1:
            r_final, n1, n2 = resistors[0]
            if tuple(sorted((n1,n2))) == tuple(sorted((source_node_id1, source_node_id2))):
                return "Rangkaian Campuran Teranalisis", r_final
            else:
                return "Rangkaian tidak terhubung dengan benar ke sumber.", None
        elif len(resistors) == 0:
             return "Tidak ada resistor di jalur sumber tegangan.", None
        else:
            return "Rangkaian terlalu kompleks (cth: jembatan Wheatstone).", None
            
    def _generate_resistor_expression_from_visual(self):
        """
        Analyzes the visual circuit to generate a series/parallel string expression.
        Returns a tuple: (status_string, expression_string_or_None)
        """
        resistors_data = [elem for elem in self.canvas_elements if elem['type'] == 'resistor']
        sources_data = [elem for elem in self.canvas_elements if elem['type'] == 'voltage_source']
        wires_data = [elem for elem in self.canvas_elements if elem['type'] == 'wire']

        if not sources_data or not resistors_data:
            return "Butuh 1 sumber tegangan dan min 1 resistor.", None

        if len(sources_data) > 1:
            return "Hanya mendukung 1 sumber tegangan.", None

        source = sources_data[0]
        components_for_node_building = resistors_data + sources_data
        
        electrical_nodes = self._build_electrical_nodes(components_for_node_building, wires_data)
        if not electrical_nodes:
            return "Tidak dapat membangun node listrik.", None

        node_map = {node_set: i for i, node_set in enumerate(electrical_nodes)}
        
        # Represent resistors as [expression_str, value, node1_id, node2_id]
        resistors = []
        for r_data in resistors_data:
            cp1_tuple = (r_data['group_tag'], 0)
            cp2_tuple = (r_data['group_tag'], 1)
            node1 = next((n for n in electrical_nodes if cp1_tuple in n), None)
            node2 = next((n for n in electrical_nodes if cp2_tuple in n), None)

            if node1 is None or node2 is None or node1 == node2:
                return f"Resistor {r_data['value']}Ω terhubung singkat/tidak terhubung.", None
            
            resistors.append([str(r_data['value']), r_data['value'], node_map[node1], node_map[node2]])
            
        # Identify source nodes
        src_cp1_tuple = (source['group_tag'], 0)
        src_cp2_tuple = (source['group_tag'], 1)
        src_node1_set = next((n for n in electrical_nodes if src_cp1_tuple in n), None)
        src_node2_set = next((n for n in electrical_nodes if src_cp2_tuple in n), None)
        
        if src_node1_set is None or src_node2_set is None or src_node1_set == src_node2_set:
            return "Sumber tegangan tidak terhubung dengan benar.", None
        
        source_node_id1 = node_map[src_node1_set]
        source_node_id2 = node_map[src_node2_set]

        # Simplification loop
        while True:
            simplified_in_pass = False
            
            # 1. Series reduction
            node_connections = {}
            for i, r in enumerate(resistors):
                n1, n2 = r[2], r[3]
                node_connections.setdefault(n1, []).append(i)
                node_connections.setdefault(n2, []).append(i)

            for node_id, conn_indices in node_connections.items():
                if len(conn_indices) == 2 and node_id not in [source_node_id1, source_node_id2]:
                    r_idx1, r_idx2 = conn_indices
                    r1_expr, r1_val, r1_n1, r1_n2 = resistors[r_idx1]
                    r2_expr, r2_val, r2_n1, r2_n2 = resistors[r_idx2]
                    
                    new_expr = f"({r1_expr} + {r2_expr})"
                    new_val = r1_val + r2_val
                    new_n1 = r1_n1 if r1_n2 == node_id else r1_n2
                    new_n2 = r2_n1 if r2_n2 == node_id else r2_n2
                    
                    resistors.append([new_expr, new_val, new_n1, new_n2])
                    resistors[r_idx1][1] = -1 # Mark for deletion
                    resistors[r_idx2][1] = -1
                    simplified_in_pass = True
                    break
            
            resistors = [r for r in resistors if r[1] != -1]
            if simplified_in_pass: continue

            # 2. Parallel reduction
            resistor_pairs = {}
            for i, r in enumerate(resistors):
                key = tuple(sorted((r[2], r[3])))
                resistor_pairs.setdefault(key, []).append(i)

            for key, indices in resistor_pairs.items():
                if len(indices) > 1:
                    parallel_exprs = [resistors[i][0] for i in indices]
                    parallel_vals = [resistors[i][1] for i in indices]

                    new_expr = f"({' | '.join(parallel_exprs)})"
                    try:
                        new_val = 1 / sum(1 / v for v in parallel_vals if v != 0)
                    except ZeroDivisionError:
                        new_val = 0
                    
                    n1, n2 = key
                    resistors.append([new_expr, new_val, n1, n2])
                    for i in indices:
                        resistors[i][1] = -1 # Mark for deletion
                    simplified_in_pass = True
                    break
            
            resistors = [r for r in resistors if r[1] != -1]
            if simplified_in_pass: continue

            if not simplified_in_pass:
                break
        
        if len(resistors) == 1:
            final_expr, _, n1, n2 = resistors[0]
            if tuple(sorted((n1, n2))) == tuple(sorted((source_node_id1, source_node_id2))):
                # Clean up expression: remove outer parenthesis if it's the whole expression
                if final_expr.startswith('(') and final_expr.endswith(')'):
                    final_expr = final_expr[1:-1]
                return "Ekspresi berhasil dibuat.", final_expr
            else:
                return "Rangkaian tidak terhubung ke sumber.", None
        elif len(resistors) == 0:
            return "Tidak ada resistor di jalur sumber.", None
        else:
            return "Rangkaian terlalu kompleks (tidak bisa disederhanakan ke seri/paralel).", None

    def analyze_visual_circuit_and_display(self):
        analysis_result, value = self.analyze_visual_circuit()
        if value is not None:
             self.label_status.config(text=f"Analisis Visual: {analysis_result} (R_eq = {value:.2f} Ω)", style="Result.TLabel")
        else:
             self.label_status.config(text=f"Analisis Visual: {analysis_result}", style="Error.TLabel")
        return analysis_result, value

    def _draw_connection_point(self, x, y, group_tag):
        cp_id = self.circuit_canvas.create_oval(x - self.CP_RADIUS, y - self.CP_RADIUS,
                                                  x + self.CP_RADIUS, y + self.CP_RADIUS,
                                                  fill="red", outline="darkred", tags=(group_tag, "connection_point"))
        return cp_id
    
    def update_visual_input_visibility(self):
        """Hides or shows the correct value input fields based on the selected tool."""
        tool = self.selected_tool.get()
        if hasattr(self, 'visual_value_input_frame') and self.visual_value_input_frame.winfo_exists():
            self.visual_resistor_label.pack_forget()
            self.visual_resistor_entry.pack_forget()
            self.visual_voltage_label.pack_forget()
            self.visual_voltage_entry.pack_forget()

            if tool == "resistor":
                self.visual_resistor_label.pack(anchor="w") 
                self.visual_resistor_entry.pack(anchor="w", pady=(0,5))
            elif tool == "voltage_source":
                self.visual_voltage_label.pack(anchor="w") 
                self.visual_voltage_entry.pack(anchor="w", pady=(0,5))

    def find_element_by_group_tag(self, group_tag):
        for i, elem_data in enumerate(self.canvas_elements):
            if elem_data.get('group_tag') == group_tag:
                return i, elem_data
        return None, None
        
    def get_nearest_connection_point(self, x, y, exclude_group_tag=None):
        nearest_cp_info = None
        min_dist_sq = (self.GRID_SIZE)**2 
        for elem_idx, elem_data in enumerate(self.canvas_elements):
            if exclude_group_tag and elem_data.get('group_tag') == exclude_group_tag: continue
            if 'connection_points' in elem_data:
                for cp_idx_in_comp, cp_visual_data in enumerate(elem_data['connection_points']): 
                    dist_sq = (cp_visual_data['abs_x'] - x)**2 + (cp_visual_data['abs_y'] - y)**2
                    if dist_sq < min_dist_sq:
                        min_dist_sq = dist_sq
                        nearest_cp_info = {'x': cp_visual_data['abs_x'], 'y': cp_visual_data['abs_y'], 
                                           'component_group_tag': elem_data['group_tag'], 
                                           'cp_index': cp_idx_in_comp, 
                                           'cp_canvas_id': cp_visual_data['id']} 
        return nearest_cp_info

    def _select_canvas_item(self, group_tag):
        # Deselect old item
        if self.selected_canvas_item_group_tag:
            idx, old_data = self.find_element_by_group_tag(self.selected_canvas_item_group_tag)
            if old_data and old_data['type'] != 'wire': 
                self.circuit_canvas.itemconfig(old_data['main_id'], outline=self.DEFAULT_OUTLINE_COLOR, width=self.DEFAULT_OUTLINE_WIDTH)
        
        # Select new item
        idx, new_data = self.find_element_by_group_tag(group_tag)
        if new_data and new_data['type'] != 'wire':
            self.circuit_canvas.itemconfig(new_data['main_id'], outline=self.SELECTED_OUTLINE_COLOR, width=self.SELECTED_OUTLINE_WIDTH)
            self.selected_canvas_item_group_tag = group_tag
        else:
            self.selected_canvas_item_group_tag = None

    def _deselect_all_canvas_items(self):
        if self.selected_canvas_item_group_tag:
            idx, data = self.find_element_by_group_tag(self.selected_canvas_item_group_tag)
            if data and data['type'] != 'wire':
                self.circuit_canvas.itemconfig(data['main_id'], outline=self.DEFAULT_OUTLINE_COLOR, width=self.DEFAULT_OUTLINE_WIDTH)
        self.selected_canvas_item_group_tag = None

    def on_canvas_left_click(self, event):
        tool = self.selected_tool.get()
        if tool != "wire" and self.is_wiring:
            self.cancel_wiring()

        if tool == "wire":
            self.handle_wire_click(event)
        else:
            self.handle_component_click(event)

    def on_canvas_motion(self, event):
        if not self.is_wiring:
            return

        snapped_x, snapped_y = self._snap_to_grid(event.x, event.y)
        
        cp_info = self.get_nearest_connection_point(event.x, event.y)
        if cp_info:
            start_cp_info = self.current_wire_c_points_info[0] if self.current_wire_c_points_info else None
            if not start_cp_info or cp_info['component_group_tag'] != start_cp_info['component_group_tag']:
                 snapped_x, snapped_y = cp_info['x'], cp_info['y']

        path_for_preview = self.current_wire_points + [(snapped_x, snapped_y)]
        flat_path = [coord for point in path_for_preview for coord in point]
        
        if self.temp_wire_id is None:
             self.temp_wire_id = self.circuit_canvas.create_line(
                 *flat_path, fill="gray", width=2, dash=(2, 2), tags="temp_wire_line"
             )
        else:
             self.circuit_canvas.coords(self.temp_wire_id, *flat_path)
    
    def on_keypress_r(self, event):
        if self.selected_canvas_item_group_tag:
            idx, data = self.find_element_by_group_tag(self.selected_canvas_item_group_tag)
            if not data or data['type'] == 'wire': return 

            self.circuit_canvas.delete(data['group_tag']) 
            
            if data['type'] == 'resistor':
                current_width = data.get('width', self.RESISTOR_WIDTH)
                current_height = data.get('height', self.RESISTOR_HEIGHT)
                new_width, new_height = current_height, current_width 
                data['width'] = new_width
                data['height'] = new_height
                new_orientation = 'vertical' if data['orientation'] == 'horizontal' else 'horizontal'
                data['orientation'] = new_orientation

                data['main_id'] = self.circuit_canvas.create_rectangle(
                    data['x'] - new_width/2, data['y'] - new_height/2, 
                    data['x'] + new_width/2, data['y'] + new_height/2, 
                    fill="lightblue", outline=self.SELECTED_OUTLINE_COLOR, width=self.SELECTED_OUTLINE_WIDTH)
                self.circuit_canvas.addtag_withtag(data['group_tag'], data['main_id']) 

                data['text_id'] = self.circuit_canvas.create_text(data['x'], data['y'], text=f"{data['value']}Ω", tags=(data['group_tag'], "component_text"))
                
                new_rel_cps = []
                if new_orientation == 'horizontal': 
                    new_rel_cps = [{'rel_x': -new_width/2, 'rel_y': 0}, {'rel_x': new_width/2, 'rel_y': 0}]
                else: 
                    new_rel_cps = [{'rel_x': 0, 'rel_y': -new_height/2}, {'rel_x': 0, 'rel_y': new_height/2}]
                
                updated_cps_list = []
                for i, rel_cp_info in enumerate(new_rel_cps):
                    abs_x = data['x'] + rel_cp_info['rel_x']
                    abs_y = data['y'] + rel_cp_info['rel_y']
                    new_cp_canvas_id = self._draw_connection_point(abs_x, abs_y, data['group_tag'])
                    updated_cps_list.append({
                        'id': new_cp_canvas_id, 
                        'rel_x': rel_cp_info['rel_x'], 'rel_y': rel_cp_info['rel_y'],
                        'abs_x': abs_x, 'abs_y': abs_y
                    })
                data['connection_points'] = updated_cps_list

            elif data['type'] == 'voltage_source':
                new_orientation = 'vertical' if data['orientation'] == 'horizontal' else 'horizontal' 
                data['orientation'] = new_orientation
                radius = data['radius']

                data['main_id'] = self.circuit_canvas.create_oval(
                    data['x'] - radius, data['y'] - radius, 
                    data['x'] + radius, data['y'] + radius, 
                    fill="lightgreen", 
                    outline=self.SELECTED_OUTLINE_COLOR, width=self.SELECTED_OUTLINE_WIDTH)
                self.circuit_canvas.addtag_withtag(data['group_tag'], data['main_id'])
                
                plus_rel_y, minus_rel_y = (-radius*0.4, radius*0.4) if new_orientation == 'vertical' else (0,0)
                plus_rel_x, minus_rel_x = (0,0) if new_orientation == 'vertical' else (-radius*0.4, radius*0.4) 
                data['plus_id'] = self.circuit_canvas.create_text(data['x']+plus_rel_x, data['y']+plus_rel_y, text="+", font=('Helvetica', 10, 'bold'), tags=(data['group_tag'],"component_text")) 
                data['minus_id'] = self.circuit_canvas.create_text(data['x']+minus_rel_x, data['y']+minus_rel_y, text="-", font=('Helvetica', 12, 'bold'), tags=(data['group_tag'],"component_text")) 
                
                val_text_x, val_text_y = data['x'], data['y'] + radius + 8
                if new_orientation == 'horizontal':
                    val_text_x, val_text_y = data['x'] + radius + 12, data['y'] 

                data['value_text_id'] = self.circuit_canvas.create_text(val_text_x, val_text_y, text=f"{data['value']}V", tags=(data['group_tag'],"component_text")) 
                
                new_rel_cps = []
                if new_orientation == 'vertical': 
                    new_rel_cps = [{'rel_x': 0, 'rel_y': -radius}, {'rel_x': 0, 'rel_y': radius}]
                else: 
                    new_rel_cps = [{'rel_x': -radius, 'rel_y': 0}, {'rel_x': radius, 'rel_y': 0}]

                updated_cps_list = []
                for i, rel_cp_info in enumerate(new_rel_cps): 
                    abs_x = data['x'] + rel_cp_info['rel_x']
                    abs_y = data['y'] + rel_cp_info['rel_y']
                    new_cp_canvas_id = self._draw_connection_point(abs_x, abs_y, data['group_tag'])
                    updated_cps_list.append({
                        'id': new_cp_canvas_id,
                        'rel_x': rel_cp_info['rel_x'], 'rel_y': rel_cp_info['rel_y'],
                        'abs_x': abs_x, 'abs_y': abs_y
                    })
                data['connection_points'] = updated_cps_list
            
            self.canvas_elements[idx] = data 
            
            # Update paths of connected wires
            wires_to_update = [el for el in self.canvas_elements if el['type'] == 'wire' and 
                               (el.get('start_cp_info', {}).get('component_group_tag') == data['group_tag'] or 
                                el.get('end_cp_info', {}).get('component_group_tag') == data['group_tag'])]

            for wire_data in wires_to_update:
                self._update_wire_path(wire_data)

            self.label_status.config(text=f"{data['type'].capitalize()} dirotasi.", style="Result.TLabel")

    def on_canvas_double_click(self, event):
        tool = self.selected_tool.get()
        if tool == "wire" and self.is_wiring:
            self.finalize_wire(event)
            return

        item_ids_under_cursor = self.circuit_canvas.find_withtag(tk.CURRENT)
        if not item_ids_under_cursor: return

        group_tag_to_edit = None
        for item_id_uc in item_ids_under_cursor:
            tags = self.circuit_canvas.gettags(item_id_uc)
            for tag in tags:
                if tag.startswith("group_"):
                    idx_test, data_test = self.find_element_by_group_tag(tag)
                    if data_test and data_test['type'] != 'wire': 
                        group_tag_to_edit = tag
                        break
            if group_tag_to_edit: break
        
        if group_tag_to_edit:
            idx, elem_data = self.find_element_by_group_tag(group_tag_to_edit)
            if not elem_data: return

            if elem_data['type'] == 'resistor':
                new_value = simpledialog.askfloat("Edit Nilai Resistor", 
                                                 "Masukkan nilai resistor baru (Ω):", 
                                                 parent=self.root, 
                                                 initialvalue=elem_data['value'], 
                                                 minvalue=0.000001) 
                if new_value is not None:
                    elem_data['value'] = new_value
                    text_item_id_to_update = elem_data.get('text_id') 
                    if text_item_id_to_update:
                        self.circuit_canvas.itemconfig(text_item_id_to_update, text=f"{new_value}Ω")
                    self.canvas_elements[idx] = elem_data
                    self.label_status.config(text=f"Nilai resistor diperbarui menjadi {new_value}Ω.", style="Result.TLabel")
            
            elif elem_data['type'] == 'voltage_source':
                dialog = CustomSourceDialog(self.root, 
                                            "Edit Sumber Tegangan", 
                                            elem_data.get('value', 0.0), 
                                            elem_data.get('current_value', 0.0))
                if dialog.result:
                    new_voltage, new_current = dialog.result
                    elem_data['value'] = new_voltage
                    elem_data['current_value'] = new_current 
                    
                    text_item_id_to_update = elem_data.get('value_text_id') 
                    if text_item_id_to_update:
                        self.circuit_canvas.itemconfig(text_item_id_to_update, text=f"{new_voltage}V")
                    self.canvas_elements[idx] = elem_data
                    self.label_status.config(text=f"Sumber Tegangan: {new_voltage}V, Arus terkait: {new_current}A.", style="Result.TLabel")

    def on_canvas_right_click(self, event):
        if self.is_wiring:
            self.cancel_wiring()
            return

        item_ids_under_cursor = self.circuit_canvas.find_withtag(tk.CURRENT)
        if not item_ids_under_cursor:
            self.label_status.config(text="Tidak ada elemen yang dipilih untuk dihapus.", style="Error.TLabel")
            return

        group_tag_to_delete = None
        
        # Prioritize deleting components over wires
        for item_id_uc in item_ids_under_cursor:
            tags = self.circuit_canvas.gettags(item_id_uc)
            is_cp_visual = "connection_point" in tags 
            if is_cp_visual: continue

            for tag in tags:
                if tag.startswith("group_"):
                    _, data_test = self.find_element_by_group_tag(tag)
                    if data_test and data_test['type'] != 'wire':
                        group_tag_to_delete = tag
                        break
            if group_tag_to_delete: break
        
        # If no component, find a wire to delete
        if not group_tag_to_delete:
            for item_id_uc in item_ids_under_cursor:
                tags = self.circuit_canvas.gettags(item_id_uc)
                is_cp_visual = "connection_point" in tags
                if is_cp_visual: continue
                for tag in tags:
                    if tag.startswith("group_"):
                        _, data_test = self.find_element_by_group_tag(tag)
                        if data_test and data_test['type'] == 'wire':
                            group_tag_to_delete = tag
                            break
                if group_tag_to_delete: break
        
        if group_tag_to_delete:
            idx_del, data_del = self.find_element_by_group_tag(group_tag_to_delete)
            
            if data_del:
                element_type_for_status = data_del.get('type', 'Elemen').capitalize()
                # If deleting a component, also delete connected wires
                if data_del['type'] != 'wire':
                    wires_to_remove_indices = []
                    for i, el in enumerate(self.canvas_elements):
                        if el['type'] == 'wire':
                            start_info = el.get('start_cp_info', {})
                            end_info = el.get('end_cp_info', {})
                            if (start_info and start_info.get('component_group_tag') == group_tag_to_delete or 
                                end_info and end_info.get('component_group_tag') == group_tag_to_delete):
                                self.circuit_canvas.delete(el['group_tag']) 
                                wires_to_remove_indices.append(i)
                    
                    for i_wire in sorted(wires_to_remove_indices, reverse=True):
                        del self.canvas_elements[i_wire]

                # Delete the main element (component or wire)
                self.circuit_canvas.delete(group_tag_to_delete) 
                del self.canvas_elements[idx_del]

                if self.selected_canvas_item_group_tag == group_tag_to_delete: 
                    self.selected_canvas_item_group_tag = None
                
                if data_del['type'] != 'wire':
                    text_to_display = f"{element_type_for_status} dan kabel terhubung dihapus."
                else:
                    text_to_display = f"{element_type_for_status} dihapus."
                self.label_status.config(text=text_to_display, style="Result.TLabel")

            else: 
                self.label_status.config(text="Gagal menghapus: elemen tidak ditemukan di data.", style="Error.TLabel")
        else:
            self.label_status.config(text="Klik pada komponen atau kabel yang valid untuk menghapus.", style="Error.TLabel")

    def on_canvas_drag(self, event):
        if self.drag_data["item"] and self.drag_data["group_tag"]: 
            idx_drag, data_drag = self.find_element_by_group_tag(self.drag_data["group_tag"])
            if not data_drag or data_drag['type'] == 'wire': 
                self.drag_data = {"item": None, "group_tag": None, "offset_x": 0, "offset_y": 0}
                return

            new_x_unmapped = event.x - self.drag_data["offset_x"]
            new_y_unmapped = event.y - self.drag_data["offset_y"]
            new_center_x, new_center_y = self._snap_to_grid(new_x_unmapped, new_y_unmapped)

            dx = new_center_x - data_drag['x']
            dy = new_center_y - data_drag['y']

            if dx != 0 or dy != 0:
                self.circuit_canvas.move(self.drag_data["group_tag"], dx, dy)
                
                data_drag['x'] = new_center_x 
                data_drag['y'] = new_center_y
                if 'connection_points' in data_drag:
                    for cp_storage in data_drag['connection_points']:
                        cp_storage['abs_x'] = new_center_x + cp_storage['rel_x']
                        cp_storage['abs_y'] = new_center_y + cp_storage['rel_y']
                self.canvas_elements[idx_drag] = data_drag

                wires_affected = [el for el in self.canvas_elements if el['type'] == 'wire' and 
                                  (el.get('start_cp_info',{}).get('component_group_tag') == self.drag_data["group_tag"] or 
                                   el.get('end_cp_info',{}).get('component_group_tag') == self.drag_data["group_tag"])]
                
                for wire_data in wires_affected:
                    self._update_wire_path(wire_data)

    def on_canvas_left_release(self, event):
        if self.drag_data["item"] and self.drag_data["group_tag"]: 
            idx, data = self.find_element_by_group_tag(self.drag_data["group_tag"])
            if data:
                self.label_status.config(text=f"{data['type'].capitalize()} dipindahkan.", style="Result.TLabel")
            self.drag_data["item"] = None
            self.drag_data["group_tag"] = None

    def is_already_connected(self, cp_info1, cp_info2):
        """Checks if a wire already exists between the two specified CPs."""
        tag1, idx1 = cp_info1['component_group_tag'], cp_info1['cp_index']
        tag2, idx2 = cp_info2['component_group_tag'], cp_info2['cp_index']

        for elem in self.canvas_elements:
            if elem['type'] == 'wire':
                s_info = elem.get('start_cp_info')
                e_info = elem.get('end_cp_info')
                if s_info and e_info:
                    s_tag, s_idx = s_info['component_group_tag'], s_info['cp_index']
                    e_tag, e_idx = e_info['component_group_tag'], e_info['cp_index']
                    
                    if (s_tag == tag1 and s_idx == idx1 and e_tag == tag2 and e_idx == idx2) or \
                       (s_tag == tag2 and s_idx == idx2 and e_tag == tag1 and e_idx == idx1):
                        return True
        return False

    def handle_wire_click(self, event):
        snapped_x, snapped_y = self._snap_to_grid(event.x, event.y)
        cp_info = self.get_nearest_connection_point(event.x, event.y)

        if cp_info:
             snapped_x, snapped_y = cp_info['x'], cp_info['y']

        if not self.is_wiring:
            self.is_wiring = True
            self.current_wire_points.append((snapped_x, snapped_y))
            if cp_info:
                self.current_wire_c_points_info.append(cp_info)
            else:
                self.current_wire_c_points_info.append(None)
            self.label_status.config(text="Mulai menggambar kabel. Klik untuk menambah titik, Dobel-klik/klik di titik koneksi untuk selesai.", style="Result.TLabel")
        else:
            if (snapped_x, snapped_y) != self.current_wire_points[-1]:
                self.current_wire_points.append((snapped_x, snapped_y))
            
            if cp_info:
                start_cp_info = self.current_wire_c_points_info[0]
                if not start_cp_info or cp_info['component_group_tag'] != start_cp_info['component_group_tag']:
                    self.finalize_wire(event)

    def finalize_wire(self, event):
        if not self.is_wiring or len(self.current_wire_points) < 1:
            self.cancel_wiring()
            return
        
        snapped_x, snapped_y = self._snap_to_grid(event.x, event.y)
        end_cp_info = self.get_nearest_connection_point(event.x, event.y)
        if end_cp_info:
            snapped_x, snapped_y = end_cp_info['x'], end_cp_info['y']

        if len(self.current_wire_points) == 0 or (snapped_x, snapped_y) != self.current_wire_points[-1]:
            self.current_wire_points.append((snapped_x, snapped_y))
        
        if len(self.current_wire_points) < 2:
             self.cancel_wiring()
             return

        start_cp_info = self.current_wire_c_points_info[0]

        if start_cp_info and end_cp_info and start_cp_info['component_group_tag'] == end_cp_info['component_group_tag']:
            self.label_status.config(text="Tidak dapat menghubungkan komponen ke dirinya sendiri.", style="Error.TLabel")
            self.cancel_wiring()
            return

        if start_cp_info and end_cp_info and self.is_already_connected(start_cp_info, end_cp_info):
            self.label_status.config(text="Koneksi antara titik-titik ini sudah ada.", style="Error.TLabel")
            self.cancel_wiring()
            return

        flat_path = [coord for point in self.current_wire_points for coord in point]
        item_id = self.circuit_canvas.create_line(*flat_path, fill="black", width=2)
        group_tag = f"group_{item_id}"
        self.circuit_canvas.addtag_withtag(group_tag, item_id)
        
        self.canvas_elements.append({
            'group_tag': group_tag, 'type': 'wire', 
            'path': self.current_wire_points, 
            'main_id': item_id,
            'start_cp_info': start_cp_info, 
            'end_cp_info': end_cp_info 
        })
        self.label_status.config(text="Kabel ditambahkan.", style="Result.TLabel")
        
        self.cancel_wiring()

    def cancel_wiring(self):
        if self.temp_wire_id:
            self.circuit_canvas.delete(self.temp_wire_id)
        self.is_wiring = False
        self.current_wire_points = []
        self.current_wire_c_points_info = []
        self.temp_wire_id = None

    def handle_component_click(self, event):
        x, y = self._snap_to_grid(event.x, event.y)
        
        item_ids_under_cursor = self.circuit_canvas.find_withtag(tk.CURRENT)
        clicked_component_group_tag = None
        if item_ids_under_cursor:
            for item_id_uc in item_ids_under_cursor:
                tags = self.circuit_canvas.gettags(item_id_uc)
                for tag in tags:
                    if tag.startswith("group_"):
                        idx, data = self.find_element_by_group_tag(tag)
                        if data and data['type'] != 'wire': 
                            clicked_component_group_tag = tag
                            break
                if clicked_component_group_tag: break
        
        if clicked_component_group_tag: 
            self._select_canvas_item(clicked_component_group_tag)
            idx, data = self.find_element_by_group_tag(clicked_component_group_tag)
            if data: 
                self.drag_data["item"] = data['main_id'] 
                self.drag_data["group_tag"] = clicked_component_group_tag
                self.drag_data["offset_x"] = event.x - data['x'] 
                self.drag_data["offset_y"] = event.y - data['y']
            return 
        else: 
            self._deselect_all_canvas_items()

        tool = self.selected_tool.get()
        if tool == "resistor":
            try: value = float(self.visual_resistor_value_var.get())
            except ValueError: messagebox.showerror("Error Nilai", "Nilai resistor tidak valid."); return
            if value <= 0: messagebox.showerror("Error Nilai", "Nilai resistor harus positif."); return
            
            width, height = self.RESISTOR_WIDTH, self.RESISTOR_HEIGHT
            item_id = self.circuit_canvas.create_rectangle(x - width/2, y - height/2, x + width/2, y + height/2, fill="lightblue", outline=self.DEFAULT_OUTLINE_COLOR, width=self.DEFAULT_OUTLINE_WIDTH)
            group_tag = f"group_{item_id}" 
            self.circuit_canvas.addtag_withtag(group_tag, item_id)
            
            text_id = self.circuit_canvas.create_text(x, y, text=f"{value}Ω", tags=(group_tag, "component_text"))
            
            cps_data_for_storage = [
                {'rel_x': -width/2, 'rel_y': 0}, 
                {'rel_x': width/2, 'rel_y': 0} 
            ]
            stored_cps_with_ids = []
            for cp_rel_info in cps_data_for_storage:
                abs_x, abs_y = x + cp_rel_info['rel_x'], y + cp_rel_info['rel_y']
                cp_canvas_id = self._draw_connection_point(abs_x, abs_y, group_tag)
                stored_cps_with_ids.append({
                    'id': cp_canvas_id, 
                    'rel_x': cp_rel_info['rel_x'], 'rel_y': cp_rel_info['rel_y'],
                    'abs_x': abs_x, 'abs_y': abs_y
                })

            self.canvas_elements.append({
                'group_tag': group_tag, 'type': 'resistor', 'value': value, 'orientation': 'horizontal',
                'x': x, 'y': y, 'main_id': item_id, 'text_id': text_id, 
                'width': width, 'height': height, 
                'connection_points': stored_cps_with_ids 
            })
            self.label_status.config(text=f"Resistor {value}Ω ditambahkan.", style="Result.TLabel")
            self._select_canvas_item(group_tag)

        elif tool == "voltage_source":
            try: value = float(self.visual_voltage_value_var.get())
            except ValueError: messagebox.showerror("Error Nilai", "Nilai tegangan tidak valid."); return
            if value <= 0: messagebox.showerror("Error Nilai", "Nilai tegangan harus positif."); return

            radius = self.VOLTAGE_SOURCE_RADIUS
            item_id = self.circuit_canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill="lightgreen", outline=self.DEFAULT_OUTLINE_COLOR, width=self.DEFAULT_OUTLINE_WIDTH)
            group_tag = f"group_{item_id}"
            self.circuit_canvas.addtag_withtag(group_tag, item_id)

            plus_id = self.circuit_canvas.create_text(x, y - radius*0.4, text="+", font=('Helvetica', 10, 'bold'), tags=(group_tag,"component_text")) 
            minus_id = self.circuit_canvas.create_text(x, y + radius*0.4, text="-", font=('Helvetica', 12, 'bold'), tags=(group_tag,"component_text")) 
            value_text_id = self.circuit_canvas.create_text(x, y + radius + 8, text=f"{value}V", tags=(group_tag,"component_text")) 
            
            cps_data_for_storage = [
                {'rel_x': 0, 'rel_y': -radius}, 
                {'rel_x': 0, 'rel_y': radius}   
            ]
            stored_cps_with_ids = []
            for cp_rel_info in cps_data_for_storage:
                abs_x, abs_y = x + cp_rel_info['rel_x'], y + cp_rel_info['rel_y']
                cp_canvas_id = self._draw_connection_point(abs_x, abs_y, group_tag)
                stored_cps_with_ids.append({
                    'id': cp_canvas_id,
                    'rel_x': cp_rel_info['rel_x'], 'rel_y': cp_rel_info['rel_y'],
                    'abs_x': abs_x, 'abs_y': abs_y
                })
            
            self.canvas_elements.append({
                'group_tag': group_tag, 'type': 'voltage_source', 
                'value': value, 'current_value': 0.0, 
                'orientation': 'vertical', 
                'x': x, 'y': y, 'main_id': item_id, 'radius': radius,
                'plus_id': plus_id, 'minus_id': minus_id, 'value_text_id': value_text_id, 
                'connection_points': stored_cps_with_ids
            })
            self.label_status.config(text=f"Sumber Tegangan {value}V ditambahkan.", style="Result.TLabel")
            self._select_canvas_item(group_tag)

    # --- Canvas & Manual Input Interaction ---
    def clear_canvas(self):
        self.cancel_wiring()
        self.circuit_canvas.delete("all") 
        self._draw_grid()
        self.canvas_elements = []
        self.selected_canvas_item_group_tag = None
        self.label_status.config(text="Kanvas dibersihkan.", style="Result.TLabel")
        self.label_note.config(text="")

    def transfer_visual_to_manual(self):
        if not self.canvas_elements:
            self.label_status.config(text="Tidak ada elemen di kanvas untuk ditransfer.", style="Error.TLabel")
            return

        # NEW: Generate expression first
        expr_status, r_expr_visual = self._generate_resistor_expression_from_visual()
        
        # Then, get the numeric total resistance
        _, r_total_visual = self.analyze_visual_circuit()
        
        visual_voltage = None
        visual_current_from_vsource = None 
        found_voltage_source = False
        
        for elem in self.canvas_elements:
            if elem['type'] == 'voltage_source':
                if not found_voltage_source: 
                    visual_voltage = elem['value']
                    visual_current_from_vsource = elem.get('current_value', 0.0) 
                    found_voltage_source = True
                else: 
                    self.label_status.config(text="Peringatan: >1 sumber tegangan di kanvas. Hanya yang pertama digunakan.", style="Error.TLabel")
        
        note_parts = ["Data dari visual ditransfer:"]
        transferred_something = False

        # Set resistor expression field
        if r_expr_visual:
            self.resistors_str_var.set(r_expr_visual)
            note_parts.append(f"Ekspresi Resistor: {r_expr_visual}")
            transferred_something = True
        else:
            # Fallback to listing individual resistors if expression fails
            resistor_values_visual = [elem['value'] for elem in self.canvas_elements if elem['type'] == 'resistor']
            if resistor_values_visual:
                self.resistors_str_var.set(", ".join(map(str, resistor_values_visual)))
                note_parts.append(f"Resistor individual (tidak dapat membuat ekspresi): {', '.join(map(str, resistor_values_visual))} Ω")
                note_parts.append(f"({expr_status})") # Add reason for failure
                transferred_something = True
            else:
                self.resistors_str_var.set("") 

        # Set total resistance field from numeric analysis
        if r_total_visual is not None:
            self.entry_vars['R'].set(f"{r_total_visual:.2f}") 
            note_parts.append(f"R_total (dari analisis visual): {r_total_visual:.2f} Ω")
            transferred_something = True 
        else: 
            self.entry_vars['R'].set("")

        if found_voltage_source:
            if visual_voltage is not None:
                self.entry_vars['V'].set(f"{visual_voltage:.2f}")
                note_parts.append(f"Tegangan (sumber visual): {visual_voltage:.2f} V")
                transferred_something = True
            if visual_current_from_vsource is not None: 
                self.entry_vars['I'].set(f"{visual_current_from_vsource:.2f}")
                note_parts.append(f"Arus (sumber tegangan visual): {visual_current_from_vsource:.2f} A")
                transferred_something = True 
        
        if transferred_something:
            note_parts.append("Lengkapi input manual lain jika perlu & tekan 'Hitung (Manual)'.")
            self.label_note.config(text="\n".join(note_parts))
            self.label_status.config(text="Data visual ditransfer. Lengkapi & hitung.", style="Result.TLabel")
        else:
            self.label_note.config(text="Tidak ada resistor atau sumber tegangan valid di kanvas untuk ditransfer.")
            self.label_status.config(text="Tidak ada data visual untuk ditransfer.", style="Error.TLabel")


    def clear_manual_results_and_status(self):
        self.label_res_components.config(text="Hambatan dari ekspresi (R_comp): -")
        self.label_res_v.config(text="Tegangan (V): -")
        self.label_res_i.config(text="Arus (I): -")
        self.label_res_r_total.config(text="Hambatan Total Rangkaian (R_total): -")
        self.label_res_p.config(text="Daya (P): -")

    def reset_all_fields(self): 
        self.resistors_str_var.set("")
        for key in self.entry_vars:
            self.entry_vars[key].set("")
        self.clear_manual_results_and_status()
        self.clear_canvas() 
        self.label_status.config(text="Semua input dan kanvas direset.")
        self.label_note.config(text="")

    def _calculate_r_from_expression(self, expr):
        """Recursively calculates resistance from a string expression."""
        expr = expr.strip()
        
        # Innermost parenthesis
        match = re.search(r'\(([^()]+)\)', expr)
        if match:
            sub_expr = match.group(1)
            result = self._calculate_r_from_expression(sub_expr)
            new_expr = expr.replace(match.group(0), str(result), 1)
            return self._calculate_r_from_expression(new_expr)
            
        # Series calculation (addition)
        series_parts = [p.strip() for p in expr.split('+')]
        series_totals = []
        for part in series_parts:
            # Parallel calculation (pipe)
            parallel_parts_str = [val.strip() for val in part.split('|')]
            if not all(s for s in parallel_parts_str): raise ValueError("Ekspresi paralel tidak lengkap.")
            parallel_parts = [float(s) for s in parallel_parts_str]

            if len(parallel_parts) == 1:
                series_totals.append(parallel_parts[0])
            else:
                if any(r == 0 for r in parallel_parts):
                    series_totals.append(0)
                else:
                    try:
                        parallel_total = 1 / sum(1/r for r in parallel_parts)
                        series_totals.append(parallel_total)
                    except ZeroDivisionError:
                        raise ValueError("Resistor dalam paralel tidak boleh nol.")

        return sum(series_totals)

    def calculate_manual(self):
        self.clear_manual_results_and_status()
        self.label_note.config(text="") 

        r_components = None 
        res_expr = self.resistors_str_var.get()
        if res_expr.strip():
            try:
                # Validate input to prevent eval-like vulnerabilities
                if not re.match(r'^[0-9\.\s()|+-]+$', res_expr):
                    raise ValueError("Ekspresi mengandung karakter tidak valid.")
                
                r_components = self._calculate_r_from_expression(res_expr)
                if r_components < 0:
                    raise ValueError("Hasil resistansi tidak boleh negatif.")
                self.label_res_components.config(text=f"Hambatan dari ekspresi (R_comp): {r_components:.2f} Ω")
            except Exception as e:
                self.label_status.config(text=f"Error ekspresi R: {str(e)}", style="Error.TLabel")
                return
        else: 
            self.label_res_components.config(text="Hambatan dari ekspresi (R_comp): - (tidak ada)")

        # --- VIPR Calculation Logic ---
        inputs_vipr = {}
        unknown_keys = []
        known_values_count = 0
        for key_char, var_str_obj in self.entry_vars.items():
            val_str = var_str_obj.get().strip()
            if not val_str:
                unknown_keys.append(key_char)
                inputs_vipr[key_char] = None
            else:
                try:
                    inputs_vipr[key_char] = float(val_str)
                    known_values_count +=1
                except ValueError:
                    self.label_status.config(text=f"Error: Nilai input manual '{key_char}' tidak valid.", style="Error.TLabel")
                    return
        
        v_in, i_in, r_in, p_in = inputs_vipr.get('V'), inputs_vipr.get('I'), inputs_vipr.get('R'), inputs_vipr.get('P')
        v_calc, i_calc, r_calc, p_calc = v_in, i_in, r_in, p_in 

        try:
            # Case 1: Exactly 3 known values, calculate the 4th
            if known_values_count == 3 and len(unknown_keys) == 1:
                var_to_calc = unknown_keys[0]
                if var_to_calc == 'R':
                    if v_in is not None and i_in is not None:
                        if i_in == 0: 
                            if v_in == 0: r_calc = None 
                            else: raise ValueError("Arus (I) nol, V non-nol -> R tak hingga.")
                        else: r_calc = v_in / i_in
                    elif v_in is not None and p_in is not None:
                        if p_in == 0:
                            if v_in == 0: r_calc = None 
                            else: raise ValueError("Daya (P) nol, V non-nol -> R tak hingga.")
                        else: r_calc = v_in**2 / p_in
                    elif i_in is not None and p_in is not None:
                        if i_in == 0:
                            if p_in == 0: r_calc = None 
                            else: raise ValueError("Arus (I) nol, P non-nol -> R tak hingga.")
                        else: r_calc = p_in / i_in**2
                    else: self.label_status.config(text="Kombinasi tidak cukup untuk hitung R.", style="Error.TLabel"); return
                
                elif var_to_calc == 'V':
                    if i_in is not None and r_in is not None: v_calc = i_in * r_in
                    elif i_in is not None and p_in is not None:
                        if i_in == 0:
                            if p_in == 0: v_calc = 0.0 
                            else: raise ValueError("Arus (I) nol, P non-nol -> V tak hingga.")
                        else: v_calc = p_in / i_in
                    elif r_in is not None and p_in is not None:
                        if p_in * r_in < 0 and not (math.isclose(p_in,0) or math.isclose(r_in,0)): 
                            raise ValueError("P*R negatif, V tidak real.")
                        v_calc = math.sqrt(abs(p_in * r_in)) 
                        if p_in < 0 and r_in > 0 and not math.isclose(p_in * r_in, 0): v_calc = -v_calc 
                    else: self.label_status.config(text="Kombinasi tidak cukup untuk hitung V.", style="Error.TLabel"); return

                elif var_to_calc == 'I':
                    if v_in is not None and r_in is not None:
                        if r_in == 0:
                            if v_in == 0: i_calc = None 
                            else: raise ValueError("Hambatan (R) nol, V non-nol -> I tak hingga.")
                        else: i_calc = v_in / r_in
                    elif v_in is not None and p_in is not None:
                        if v_in == 0:
                            if p_in == 0: i_calc = None 
                            else: raise ValueError("Tegangan (V) nol, P non-nol -> I tak hingga.")
                        else: i_calc = p_in / v_in
                    elif r_in is not None and p_in is not None:
                        if r_in == 0:
                            if p_in == 0: i_calc = None 
                            else: raise ValueError("Hambatan (R) nol, P non-nol -> I tak hingga.")
                        else:
                            if (p_in / r_in) < 0 and not (math.isclose(p_in,0) or math.isclose(r_in,0)): 
                                raise ValueError("P/R negatif, I tidak real.")
                            i_calc = math.sqrt(abs(p_in / r_in))
                            if p_in <0 and not math.isclose(p_in,0): i_calc = -i_calc 
                    else: self.label_status.config(text="Kombinasi tidak cukup untuk hitung I.", style="Error.TLabel"); return

                elif var_to_calc == 'P':
                    if v_in is not None and i_in is not None: p_calc = v_in * i_in
                    elif v_in is not None and r_in is not None:
                        if r_in == 0:
                            if v_in != 0: raise ValueError("Hambatan (R) nol, V non-nol -> P tak hingga.")
                            else: p_calc = 0.0 
                        else: p_calc = v_in**2 / r_in
                    elif i_in is not None and r_in is not None: p_calc = i_in**2 * r_in
                    else: self.label_status.config(text="Kombinasi tidak cukup untuk hitung P.", style="Error.TLabel"); return
            
            # Case 2: Exactly V and I are known, calculate R and P
            elif known_values_count == 2 and v_in is not None and i_in is not None and r_in is None and p_in is None:
                if i_in == 0:
                    if v_in != 0: raise ValueError("Arus (I) nol, V non-nol -> R & P tak terdefinisi.")
                    else: r_calc, p_calc = None, 0.0 
                else: r_calc, p_calc = v_in / i_in, v_in * i_in
            
            # Case 3: All 4 values are provided, just verify them
            elif known_values_count == 4:
                if not (math.isclose(v_in, i_in * r_in, rel_tol=1e-2) and \
                        math.isclose(p_in, v_in * i_in, rel_tol=1e-2)):
                    self.label_status.config(text="Input V,I,R,P tidak konsisten.", style="Error.TLabel")
                    self.label_note.config(text="Nilai V,I,R,P yang diinput tidak konsisten secara matematis (V=IR, P=VI).")
                    return
                else:
                    self.label_status.config(text="Semua nilai VIPR diisi & konsisten.", style="Result.TLabel")

            # Case 4: Invalid number of inputs
            else: 
                self.label_status.config(text="Error: Pola input manual tidak valid. Isi 3 nilai (1 kosong) ATAU V dan I saja.", style="Error.TLabel")
                return

        except ValueError as e: self.label_status.config(text=f"Error perhitungan: {str(e)}", style="Error.TLabel"); return
        except ZeroDivisionError: self.label_status.config(text="Error perhitungan: Pembagian dengan nol.", style="Error.TLabel"); return
        except Exception as e: self.label_status.config(text=f"Error tak terduga (perhitungan): {str(e)}", style="Error.TLabel"); return

        # --- Display Results ---
        self.label_res_v.config(text=f"Tegangan (V): {v_calc:.2f} V" if v_calc is not None else "Tegangan (V): -")
        self.label_res_i.config(text=f"Arus (I): {i_calc:.2f} A" if i_calc is not None else "Arus (I): -")
        self.label_res_r_total.config(text=f"Hambatan Total Rangkaian (R_total): {r_calc:.2f} Ω" if r_calc is not None else "Hambatan Total Rangkaian (R_total): -")
        self.label_res_p.config(text=f"Daya (P): {p_calc:.2f} W" if p_calc is not None else "Daya (P): -")
        
        current_status_text = self.label_status.cget("text")
        if not current_status_text.startswith("Error"):
            self.label_status.config(text="Perhitungan Manual Selesai.", style="Result.TLabel")

        # --- Post-calculation notes and checks ---
        if r_components is not None and r_calc is not None:
            if not math.isclose(r_components, r_calc, rel_tol=1e-2): 
                existing_note = self.label_note.cget("text")
                separator = "\n" if existing_note else ""
                new_note_part = f"Catatan: R_total ({r_calc:.2f} Ω) berbeda dengan R_comp dari ekspresi ({r_components:.2f} Ω)."
                self.label_note.config(text=existing_note + separator + new_note_part)
        elif r_components is not None and r_in is None and self.entry_vars['R'].get().strip() == "": 
            self.entry_vars['R'].set(f"{r_components:.2f}") 
            self.label_res_r_total.config(text=f"Hambatan Total Rangkaian (R_total): {r_components:.2f} Ω (dari R_comp)")
            existing_note = self.label_note.cget("text")
            separator = "\n" if existing_note else ""
            self.label_note.config(text=existing_note + separator + f"Catatan: R_total diisi dari R_comp ({r_components:.2f} Ω).")

if __name__ == '__main__':
    root = tk.Tk()
    app = CircuitCalculatorApp(root)
    root.mainloop()
