"""
===============================================================================
APPLICATION: Core OS Simulation Suite
ENGINEERING SPEC: Asynchronous Event-Driven Architecture (Tkinter GUI Backend)
TARGET RUNTIME: Python 3.8+ 
===============================================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox
import random
import time
import threading
from collections import deque, OrderedDict
from copy import deepcopy

class VisualAestheticConfig:
    """Encapsulates system-wide palettes, typography metrics, and spatial constants."""
    # Color Workspace Map
    CANVAS_HEX = "#fff4f8"
    DOCK_HEX = "#ffdbe8"
    SURFACE_HEX = "#fffafc"
    PRIMARY_HEX = "#ff5da2"
    MUTED_HEX = "#ffc2de"
    HIGHLIGHT_HEX = "#ff8fc1"
    CRITICAL_HEX = "#ff6f91"
    BODY_HEX = "#5c1636"
    CAPTION_HEX = "#8a4f68"
    OUTLINE_HEX = "#f2b6cd"
    SUCCESS_HEX = "#ff69b4"

    # Type Specifications
    HEADER_MATRICES = ("Segoe Print", 24, "bold")
    SECTION_MATRICES = ("Comic Sans MS", 13, "bold")
    SUBHEADER_MATRICES = ("Segoe Print", 12, "bold")
    REGULAR_MATRICES = ("Candara", 10)
    MONOSPACE_MATRICES = ("Consolas", 10)
    COMPACT_MATRICES = ("Candara", 9)

    PADDING_UNIT = 10


class ElementFactory:
    """Procedural factory generating uniform, stylized graphic components."""
    
    @staticmethod
    def craft_action_trigger(master_node, display_string, execution_callback, accent_hex=VisualAestheticConfig.PRIMARY_HEX, **kwargs):
        return tk.Button(
            master_node, text=display_string, command=execution_callback,
            bg=accent_hex, fg=VisualAestheticConfig.BODY_HEX, relief="flat",
            activebackground=VisualAestheticConfig.MUTED_HEX, activeforeground=VisualAestheticConfig.BODY_HEX,
            font=VisualAestheticConfig.REGULAR_MATRICES, padx=12, pady=6, cursor="hand2",
            bd=0, **kwargs
        )

    @staticmethod
    def craft_header_text(master_node, text_content, **kwargs):
        return tk.Label(master_node, text=text_content, bg=VisualAestheticConfig.DOCK_HEX, fg=VisualAestheticConfig.BODY_HEX, font=VisualAestheticConfig.SECTION_MATRICES, **kwargs)

    @staticmethod
    def craft_description_block(master_node, text_content, explicit_hex=VisualAestheticConfig.CAPTION_HEX, **kwargs):
        return tk.Label(master_node, text=text_content, bg=VisualAestheticConfig.DOCK_HEX, fg=explicit_hex, font=VisualAestheticConfig.COMPACT_MATRICES, wraplength=520, justify="left", **kwargs)

    @staticmethod
    def craft_input_composite(master_node, title_token, fallback_val="", field_width=8):
        boundary_frame = tk.Frame(master_node, bg=VisualAestheticConfig.DOCK_HEX)
        tk.Label(boundary_frame, text=title_token, bg=VisualAestheticConfig.DOCK_HEX, fg=VisualAestheticConfig.CAPTION_HEX, font=VisualAestheticConfig.COMPACT_MATRICES).pack(side="left", padx=(0, 4))
        reactive_string = tk.StringVar(value=fallback_val)
        input_field = tk.Entry(boundary_frame, textvariable=reactive_string, width=field_width, bg=VisualAestheticConfig.SURFACE_HEX, fg=VisualAestheticConfig.BODY_HEX, insertbackground=VisualAestheticConfig.BODY_HEX,
                               relief="flat", font=VisualAestheticConfig.MONOSPACE_MATRICES, highlightthickness=1, highlightbackground=VisualAestheticConfig.OUTLINE_HEX)
        input_field.pack(side="left")
        return boundary_frame, reactive_string


class CPUSchedulingTab(tk.Frame):
    STRATEGIES = ["FCFS", "SJF (Non-Preemptive)", "SJF (Preemptive)", "Priority (Non-Preemptive)", "Priority (Preemptive)", "Round Robin"]

    def __init__(self, master_canvas):
        super().__init__(master_canvas, bg=VisualAestheticConfig.CANVAS_HEX)
        self.simulation_active = False
        self.cached_metrics = []
        self.active_chronology = []
        self._initialize_layout()

    def _initialize_layout(self):
        upper_dock = tk.Frame(self, bg=VisualAestheticConfig.DOCK_HEX)
        upper_dock.pack(fill="x", padx=VisualAestheticConfig.PADDING_UNIT, pady=(VisualAestheticConfig.PADDING_UNIT, 4))

        dock_west = tk.Frame(upper_dock, bg=VisualAestheticConfig.DOCK_HEX)
        dock_west.pack(side="left", fill="x", expand=True)

        ElementFactory.craft_header_text(dock_west, "CPU Scheduling").pack(anchor="w", padx=VisualAestheticConfig.PADDING_UNIT, pady=(VisualAestheticConfig.PADDING_UNIT // 2, 6))
        strategy_row = tk.Frame(dock_west, bg=VisualAestheticConfig.DOCK_HEX)
        strategy_row.pack(fill="x", padx=VisualAestheticConfig.PADDING_UNIT, pady=(0, 6))
        tk.Label(strategy_row, text="Algorithm", bg=VisualAestheticConfig.DOCK_HEX, fg=VisualAestheticConfig.CAPTION_HEX, font=VisualAestheticConfig.COMPACT_MATRICES).pack(side="left")
        self.selected_strategy = tk.StringVar(value=self.STRATEGIES[0])
        dropdown_selector = ttk.Combobox(strategy_row, textvariable=self.selected_strategy, values=self.STRATEGIES, state="readonly", font=VisualAestheticConfig.REGULAR_MATRICES, width=24)
        dropdown_selector.pack(side="left", padx=(8, 0))
        dropdown_selector.bind("<<ComboboxSelected>>", self._handle_strategy_toggle)

        self.quantum_wrapper = tk.Frame(dock_west, bg=VisualAestheticConfig.DOCK_HEX)
        self.quantum_wrapper.pack(fill="x", padx=VisualAestheticConfig.PADDING_UNIT, pady=(0, 4))
        tk.Label(self.quantum_wrapper, text="Time Quantum", bg=VisualAestheticConfig.DOCK_HEX, fg=VisualAestheticConfig.CAPTION_HEX, font=VisualAestheticConfig.COMPACT_MATRICES).pack(side="left")
        self.quantum_state = tk.StringVar(value="2")
        tk.Entry(self.quantum_wrapper, textvariable=self.quantum_state, width=6,
                 bg=VisualAestheticConfig.SURFACE_HEX, fg=VisualAestheticConfig.BODY_HEX, insertbackground=VisualAestheticConfig.BODY_HEX, relief="flat", font=VisualAestheticConfig.MONOSPACE_MATRICES,
                 highlightthickness=1, highlightbackground=VisualAestheticConfig.OUTLINE_HEX).pack(side="left", padx=(8, 0))
        self.quantum_wrapper.pack_forget()

        dock_east = tk.Frame(upper_dock, bg=VisualAestheticConfig.DOCK_HEX)
        dock_east.pack(side="right", padx=VisualAestheticConfig.PADDING_UNIT)
        ElementFactory.craft_action_trigger(dock_east, "+ Row", self._append_process_row, VisualAestheticConfig.MUTED_HEX).pack(side="left", padx=2)
        ElementFactory.craft_action_trigger(dock_east, "Random", self._scramble_process_values, VisualAestheticConfig.HIGHLIGHT_HEX).pack(side="left", padx=2)
        self.trigger_execution_btn = ElementFactory.craft_action_trigger(dock_east, "▶  Run Animation", self._invoke_simulation, VisualAestheticConfig.PRIMARY_HEX)
        self.trigger_execution_btn.pack(side="left", padx=2)

        data_grid_panel = tk.Frame(self, bg=VisualAestheticConfig.DOCK_HEX)
        data_grid_panel.pack(fill="x", padx=VisualAestheticConfig.PADDING_UNIT, pady=(0, VisualAestheticConfig.PADDING_UNIT))
        tk.Label(data_grid_panel, text="Processes", bg=VisualAestheticConfig.DOCK_HEX, fg=VisualAestheticConfig.CAPTION_HEX, font=VisualAestheticConfig.COMPACT_MATRICES).pack(anchor="w", padx=VisualAestheticConfig.PADDING_UNIT, pady=(0, 4))

        self.grid_header_subnode = tk.Frame(data_grid_panel, bg=VisualAestheticConfig.DOCK_HEX)
        self.grid_header_subnode.pack(fill="x", padx=VisualAestheticConfig.PADDING_UNIT)
        self.grid_records_subnode = tk.Frame(data_grid_panel, bg=VisualAestheticConfig.DOCK_HEX)
        self.grid_records_subnode.pack(fill="x", padx=VisualAestheticConfig.PADDING_UNIT)
        self.header_elements_list = []
        self.interactive_matrix_rows = []
        for baseline_index in range(5):
            self._generate_matrix_row(baseline_index)

        workspace_viewport = tk.Frame(self, bg=VisualAestheticConfig.CANVAS_HEX)
        workspace_viewport.pack(fill="both", expand=True, padx=VisualAestheticConfig.PADDING_UNIT, pady=(0, VisualAestheticConfig.PADDING_UNIT))

        self.telemetry_banner = tk.Label(workspace_viewport, text="System Idle", bg=VisualAestheticConfig.DOCK_HEX, fg=VisualAestheticConfig.CAPTION_HEX, font=VisualAestheticConfig.REGULAR_MATRICES, anchor="w", padx=10, pady=4)
        self.telemetry_banner.pack(fill="x", pady=(0, 4))

        self.graphic_render_surface = tk.Canvas(workspace_viewport, bg=VisualAestheticConfig.SURFACE_HEX, bd=0, highlightthickness=0)
        self.graphic_render_surface.pack(fill="both", expand=True)

    def _generate_matrix_row(self, identity_index):
        target_column = len(self.interactive_matrix_rows) // 5
        target_row = len(self.interactive_matrix_rows) % 5
        while target_column >= len(self.header_elements_list):
            header_sub_container = tk.Frame(self.grid_header_subnode, bg=VisualAestheticConfig.DOCK_HEX)
            header_sub_container.grid(row=0, column=len(self.header_elements_list), padx=6, sticky="nw")
            for label_string, dimension in [("PID", 4), ("Arrival", 6), ("Burst", 5), ("Priority", 7)]:
                tk.Label(header_sub_container, text=label_string, bg=VisualAestheticConfig.DOCK_HEX, fg=VisualAestheticConfig.CAPTION_HEX, font=VisualAestheticConfig.COMPACT_MATRICES, width=dimension).pack(side="left", padx=(0, 2))
            self.header_elements_list.append(header_sub_container)

        if not hasattr(self, 'columnar_layout_frames'):
            self.columnar_layout_frames = []
        while target_column >= len(self.columnar_layout_frames):
            structural_col_frame = tk.Frame(self.grid_records_subnode, bg=VisualAestheticConfig.DOCK_HEX)
            structural_col_frame.grid(row=0, column=len(self.columnar_layout_frames), padx=6, sticky="nw")
            self.columnar_layout_frames.append(structural_col_frame)

        record_row_strip = tk.Frame(self.columnar_layout_frames[target_column], bg=VisualAestheticConfig.DOCK_HEX)
        record_row_strip.grid(row=target_row, column=0, pady=1, sticky="nw")
        reactive_pid = tk.StringVar(value=f"P{identity_index+1}")
        reactive_arrival = tk.StringVar(value=str(identity_index if identity_index < 3 else random.randint(0,4)))
        reactive_burst = tk.StringVar(value=str(random.randint(2, 6)))
        reactive_priority = tk.StringVar(value=str(random.randint(1, 5)))
        for targeted_var, field_size in [(reactive_pid, 4), (reactive_arrival, 6), (reactive_burst, 5), (reactive_priority, 7)]:
            tk.Entry(record_row_strip, textvariable=targeted_var, width=field_size, bg=VisualAestheticConfig.SURFACE_HEX, fg=VisualAestheticConfig.BODY_HEX,
                     insertbackground=VisualAestheticConfig.BODY_HEX, relief="flat", font=VisualAestheticConfig.MONOSPACE_MATRICES,
                     highlightthickness=1, highlightbackground=VisualAestheticConfig.OUTLINE_HEX).pack(side="left", padx=1)
        self.interactive_matrix_rows.append((reactive_pid, reactive_arrival, reactive_burst, reactive_priority))

    def _append_process_row(self):
        self._generate_matrix_row(len(self.interactive_matrix_rows))

    def _scramble_process_values(self):
        for pv, av, bv, prv in self.interactive_matrix_rows:
            av.set(str(random.randint(0, 5)))
            bv.set(str(random.randint(1, 8)))
            prv.set(str(random.randint(1, 5)))

    def _handle_strategy_toggle(self, *_):
        if "Round Robin" in self.selected_strategy.get():
            self.quantum_wrapper.pack(fill="x", padx=VisualAestheticConfig.PADDING_UNIT)
        else:
            self.quantum_wrapper.pack_forget()

    def _harvest_compiled_dataset(self):
        extracted_records = []
        for pv, av, bv, prv in self.interactive_matrix_rows:
            try:
                extracted_records.append({
                    "pid": pv.get(), "arrival": int(av.get()),
                    "burst": int(bv.get()), "priority": int(prv.get()),
                })
            except ValueError: continue
        return extracted_records

    HEX_ARRAY_PALETTE = ["#7c6af7", "#38c9b0", "#f7c26a", "#f76a6a", "#6af7a1", "#f7a26a", "#a26af7", "#6ab8f7"]

    def _invoke_simulation(self):
        if self.simulation_active: return
        target_process_data = self._harvest_compiled_dataset()
        if not target_process_data:
            messagebox.showwarning("No Data", "Add at least one process.")
            return

        self.simulation_active = True
        self.trigger_execution_btn.config(state="disabled", bg=VisualAestheticConfig.OUTLINE_HEX, text="⏳ Running...")
        
        computed_burst_sum = sum(node["burst"] for node in target_process_data)
        maximal_arrival_stamp = max(node["arrival"] for node in target_process_data)
        self.timeline_ceiling_limit = maximal_arrival_stamp + computed_burst_sum + 5 

        threading.Thread(target=self._core_calculation_thread, args=(target_process_data,), daemon=True).start()

    def _core_calculation_thread(self, dataset):
        chosen_algo = self.selected_strategy.get()
        working_timeline, calculated_stats = [], []
        self.active_chronology = working_timeline

        if chosen_algo == "FCFS":
            self._compute_fcfs_profile(dataset, working_timeline, calculated_stats)
        elif chosen_algo == "SJF (Non-Preemptive)":
            self._compute_sjf_nonpreemptive_profile(dataset, working_timeline, calculated_stats)
        elif chosen_algo == "SJF (Preemptive)":
            self._compute_sjf_preemptive_profile(dataset, working_timeline, calculated_stats)
        elif chosen_algo == "Priority (Non-Preemptive)":
            self._compute_priority_nonpreemptive_profile(dataset, working_timeline, calculated_stats)
        elif chosen_algo == "Priority (Preemptive)":
            self._compute_priority_preemptive_profile(dataset, working_timeline, calculated_stats)
        else:
            try: quantum_val = int(self.quantum_state.get())
            except ValueError: quantum_val = 2
            self._compute_round_robin_profile(dataset, quantum_val, working_timeline, calculated_stats)

        self.simulation_active = False
        self.trigger_execution_btn.config(state="normal", bg=VisualAestheticConfig.PRIMARY_HEX, text="▶  Run Animation")
        self.telemetry_banner.config(text="Simulation Complete", fg=VisualAestheticConfig.SUCCESS_HEX)
        self._display_post_run_metrics(calculated_stats)

    def _compute_fcfs_profile(self, target_procs, sequence, metrics):
        ordered_procs = sorted(target_procs, key=lambda node: node["arrival"])
        temporal_tracker = 0
        for individual_node in ordered_procs:
            while temporal_tracker < individual_node["arrival"]:
                self._execute_frame_refresh(sequence, temporal_tracker, ready_queue=[])
                temporal_tracker += 1
            allocation_origin = temporal_tracker
            for _ in range(individual_node["burst"]):
                temporal_tracker += 1
                sequence.append((individual_node["pid"], allocation_origin, temporal_tracker))
                self._execute_frame_refresh(sequence, temporal_tracker, active_pid=individual_node["pid"])
            metrics.append({"pid": individual_node["pid"], "wait": allocation_origin - individual_node["arrival"], "turnaround": temporal_tracker - individual_node["arrival"]})

    def _compute_sjf_nonpreemptive_profile(self, target_procs, sequence, metrics):
        unprocessed_pool = list(deepcopy(target_procs))
        temporal_tracker = 0
        while unprocessed_pool:
            qualified_nodes = [node for node in unprocessed_pool if node["arrival"] <= temporal_tracker]
            ready_identifiers = [node["pid"] for node in qualified_nodes]
            if not qualified_nodes:
                self._execute_frame_refresh(sequence, temporal_tracker, ready_queue=[])
                temporal_tracker += 1
                continue
            optimal_node = min(qualified_nodes, key=lambda entry: entry["burst"])
            ready_identifiers.remove(optimal_node["pid"])
            allocation_origin = temporal_tracker
            for _ in range(optimal_node["burst"]):
                temporal_tracker += 1
                sequence.append((optimal_node["pid"], allocation_origin, temporal_tracker))
                dynamic_ready_state = ready_identifiers + [node["pid"] for node in unprocessed_pool if node["arrival"] <= temporal_tracker and node not in qualified_nodes]
                self._execute_frame_refresh(sequence, temporal_tracker, active_pid=optimal_node["pid"], ready_queue=dynamic_ready_state)
            metrics.append({"pid": optimal_node["pid"], "wait": allocation_origin - optimal_node["arrival"], "turnaround": temporal_tracker - optimal_node["arrival"]})
            unprocessed_pool.remove(optimal_node)

    def _compute_priority_nonpreemptive_profile(self, target_procs, sequence, metrics):
        unprocessed_pool = list(deepcopy(target_procs))
        temporal_tracker = 0
        while unprocessed_pool:
            qualified_nodes = [node for node in unprocessed_pool if node["arrival"] <= temporal_tracker]
            ready_identifiers = [node["pid"] for node in qualified_nodes]
            if not qualified_nodes:
                self._execute_frame_refresh(sequence, temporal_tracker, ready_queue=[])
                temporal_tracker += 1
                continue
            optimal_node = min(qualified_nodes, key=lambda entry: entry["priority"])
            ready_identifiers.remove(optimal_node["pid"])
            allocation_origin = temporal_tracker
            for _ in range(optimal_node["burst"]):
                temporal_tracker += 1
                sequence.append((optimal_node["pid"], allocation_origin, temporal_tracker))
                dynamic_ready_state = ready_identifiers + [node["pid"] for node in unprocessed_pool if node["arrival"] <= temporal_tracker and node not in qualified_nodes]
                self._execute_frame_refresh(sequence, temporal_tracker, active_pid=optimal_node["pid"], ready_queue=dynamic_ready_state)
            metrics.append({"pid": optimal_node["pid"], "wait": allocation_origin - optimal_node["arrival"], "turnaround": temporal_tracker - optimal_node["arrival"]})
            unprocessed_pool.remove(optimal_node)

    def _compute_sjf_preemptive_profile(self, target_procs, sequence, metrics):
        stateful_pool = [{**node, "remaining": node["burst"]} for node in deepcopy(target_procs)]
        temporal_tracker = 0
        finalized_pids = set()

        while len(finalized_pids) < len(target_procs):
            active_ready_pool = [node for node in stateful_pool if node["arrival"] <= temporal_tracker and node["remaining"] > 0]
            if not active_ready_pool:
                self._execute_frame_refresh(sequence, temporal_tracker, ready_queue=[])
                temporal_tracker += 1
                continue

            current_target = min(active_ready_pool, key=lambda entry: (entry["remaining"], entry["arrival"], entry["pid"]))
            current_target["remaining"] -= 1
            temporal_tracker += 1
            sequence.append((current_target["pid"], temporal_tracker - 1, temporal_tracker))
            waiting_identifiers = [node["pid"] for node in active_ready_pool if node["pid"] != current_target["pid"]]
            self._execute_frame_refresh(sequence, temporal_tracker, active_pid=current_target["pid"], ready_queue=waiting_identifiers)

            if current_target["remaining"] == 0:
                finalized_pids.add(current_target["pid"])
                metrics.append({
                    "pid": current_target["pid"],
                    "wait": temporal_tracker - current_target["arrival"] - current_target["burst"],
                    "turnaround": temporal_tracker - current_target["arrival"],
                })

    def _compute_priority_preemptive_profile(self, target_procs, sequence, metrics):
        stateful_pool = [{**node, "remaining": node["burst"]} for node in deepcopy(target_procs)]
        temporal_tracker = 0
        finalized_pids = set()

        while len(finalized_pids) < len(target_procs):
            active_ready_pool = [node for node in stateful_pool if node["arrival"] <= temporal_tracker and node["remaining"] > 0]
            if not active_ready_pool:
                self._execute_frame_refresh(sequence, temporal_tracker, ready_queue=[])
                temporal_tracker += 1
                continue

            current_target = min(active_ready_pool, key=lambda entry: (entry["priority"], entry["arrival"], entry["pid"]))
            current_target["remaining"] -= 1
            temporal_tracker += 1
            sequence.append((current_target["pid"], temporal_tracker - 1, temporal_tracker))
            waiting_identifiers = [node["pid"] for node in active_ready_pool if node["pid"] != current_target["pid"]]
            self._execute_frame_refresh(sequence, temporal_tracker, active_pid=current_target["pid"], ready_queue=waiting_identifiers)

            if current_target["remaining"] == 0:
                finalized_pids.add(current_target["pid"])
                metrics.append({
                    "pid": current_target["pid"],
                    "wait": temporal_tracker - current_target["arrival"] - current_target["burst"],
                    "turnaround": temporal_tracker - current_target["arrival"],
                })

    def _compute_round_robin_profile(self, target_procs, time_quantum, sequence, metrics):
        ordered_timeline = sorted(target_procs, key=lambda node: node["arrival"])
        residual_burst_dictionary = {node["pid"]: node["burst"] for node in target_procs}
        termination_log = {}
        awaiting_deque = deque()
        cloned_node_list = list(ordered_timeline)
        iteration_index, temporal_tracker = 0, 0

        while awaiting_deque or iteration_index < len(cloned_node_list):
            while iteration_index < len(cloned_node_list) and cloned_node_list[iteration_index]["arrival"] <= temporal_tracker:
                if cloned_node_list[iteration_index]["pid"] not in awaiting_deque: 
                    awaiting_deque.append(cloned_node_list[iteration_index]["pid"])
                iteration_index += 1
            if not awaiting_deque:
                self._execute_frame_refresh(sequence, temporal_tracker, ready_queue=[])
                temporal_tracker += 1
                continue
            active_target_pid = awaiting_deque.popleft()
            execution_duration = min(time_quantum, residual_burst_dictionary[active_target_pid])
            allocation_origin = temporal_tracker
            for _ in range(execution_duration):
                temporal_tracker += 1
                residual_burst_dictionary[active_target_pid] -= 1
                sequence.append((active_target_pid, allocation_origin, temporal_tracker))
                while iteration_index < len(cloned_node_list) and cloned_node_list[iteration_index]["arrival"] <= temporal_tracker:
                    if cloned_node_list[iteration_index]["pid"] not in awaiting_deque: 
                        awaiting_deque.append(cloned_node_list[iteration_index]["pid"])
                    iteration_index += 1
                self._execute_frame_refresh(sequence, temporal_tracker, active_pid=active_target_pid, ready_queue=list(awaiting_deque))
            if residual_burst_dictionary[active_target_pid] > 0: 
                awaiting_deque.append(active_target_pid)
            else: 
                termination_log[active_target_pid] = temporal_tracker

        for node in target_procs:
            if node["pid"] in termination_log:
                metrics.append({"pid": node["pid"], "wait": termination_log[node["pid"]] - node["arrival"] - node["burst"], "turnaround": termination_log[node["pid"]] - node["arrival"]})

    def _execute_frame_refresh(self, sequence, simulation_clock, active_pid=None, ready_queue=None):
        if ready_queue is None: ready_queue = []
        queue_text_representation = " → ".join(ready_queue) if ready_queue else "Empty"
        self.telemetry_banner.config(text=f"Time: {simulation_clock}s | Active CPU: {active_pid or 'IDLE'} | Ready Queue: [{queue_text_representation}]", fg=VisualAestheticConfig.MUTED_HEX if active_pid else VisualAestheticConfig.CAPTION_HEX)
        self._render_gantt_chart_frame(sequence, simulation_clock)
        time.sleep(0.4)

    def _render_gantt_chart_frame(self, sequence, simulation_clock):
        surface = self.graphic_render_surface; surface.delete("all")
        surface_width, surface_height = surface.winfo_width() or 800, surface.winfo_height() or 300
        telemetry_block_width = 220
        padding_left, padding_right, padding_top = 50, 40, 60
        block_height, block_y_axis = 44, padding_top + 30
        renderable_width = surface_width - padding_left - padding_right - telemetry_block_width - 20
        scaling_ratio = max(1.0, renderable_width / max(self.timeline_ceiling_limit, simulation_clock, 1))

        distinct_identifiers = list(dict.fromkeys(node for node, _, _ in sequence)) if sequence else []
        node_color_bindings = {node: self.HEX_ARRAY_PALETTE[idx % len(self.HEX_ARRAY_PALETTE)] for idx, node in enumerate(distinct_identifiers)}

        surface.create_rectangle(surface_width - padding_right - telemetry_block_width, padding_top - 20, surface_width - padding_right, surface_height - 20, fill="#fff7fb", outline=VisualAestheticConfig.OUTLINE_HEX, width=1)
        surface.create_text(surface_width - padding_right - telemetry_block_width + 12, padding_top - 10, text="Process Statistics", anchor="nw", fill=VisualAestheticConfig.BODY_HEX, font=VisualAestheticConfig.SUBHEADER_MATRICES)
        surface.create_text(surface_width//2, 18, text=f"Gantt Chart Real-Time Stream — {self.selected_strategy.get()}", fill=VisualAestheticConfig.BODY_HEX, font=VisualAestheticConfig.SUBHEADER_MATRICES)

        axis_baseline_y = block_y_axis + block_height + 2
        surface.create_line(padding_left, axis_baseline_y, padding_left + renderable_width, axis_baseline_y, fill=VisualAestheticConfig.OUTLINE_HEX, width=1)

        if not sequence:
            surface.create_text(padding_left + 10, block_y_axis + 20, text="System startup, resolving arrivals...", fill=VisualAestheticConfig.CAPTION_HEX, font=VisualAestheticConfig.REGULAR_MATRICES, anchor="w")
            self._inject_panel_metrics(surface, surface_width, surface_height, telemetry_block_width)
            return

        compact_timeline_blocks = []
        for pid, start_t, end_t in sequence:
            if not compact_timeline_blocks or compact_timeline_blocks[-1][0] != pid or compact_timeline_blocks[-1][2] != start_t:
                compact_timeline_blocks.append([pid, start_t, end_t])
            else: compact_timeline_blocks[-1][2] = end_t

        registered_ticks = set()
        for pid, start_t, end_t in compact_timeline_blocks:
            coord_x0, coord_x1 = padding_left + start_t * scaling_ratio, padding_left + end_t * scaling_ratio
            surface.create_rectangle(coord_x0, block_y_axis, coord_x1, block_y_axis + block_height, fill=node_color_bindings.get(pid, VisualAestheticConfig.SURFACE_HEX), outline=VisualAestheticConfig.CANVAS_HEX, width=2)
            if coord_x1 - coord_x0 > 24:
                surface.create_text((coord_x0+coord_x1)//2, block_y_axis + block_height//2, text=pid, fill=VisualAestheticConfig.CANVAS_HEX, font=("Segoe UI", 10, "bold"))
            surface.create_line(coord_x0, axis_baseline_y, coord_x0, axis_baseline_y + 6, fill=VisualAestheticConfig.OUTLINE_HEX)
            if start_t not in registered_ticks:
                surface.create_text(coord_x0, axis_baseline_y + 16, text=str(start_t), fill=VisualAestheticConfig.CAPTION_HEX, font=VisualAestheticConfig.COMPACT_MATRICES)
                registered_ticks.add(start_t)

        terminal_timestamp = sequence[-1][2]
        terminal_coord_x = padding_left + terminal_timestamp * scaling_ratio
        surface.create_line(terminal_coord_x, axis_baseline_y, terminal_coord_x, axis_baseline_y + 6, fill=VisualAestheticConfig.OUTLINE_HEX)
        surface.create_text(terminal_coord_x, axis_baseline_y + 16, text=str(terminal_timestamp), fill=VisualAestheticConfig.CAPTION_HEX, font=VisualAestheticConfig.COMPACT_MATRICES)

        legend_placement_x, legend_placement_y = padding_left, block_y_axis + block_height + 45
        for pid, assignment_color in node_color_bindings.items():
            surface.create_rectangle(legend_placement_x, legend_placement_y, legend_placement_x+12, legend_placement_y+12, fill=assignment_color, outline="")
            surface.create_text(legend_placement_x+16, legend_placement_y+6, text=pid, fill=VisualAestheticConfig.BODY_HEX, font=VisualAestheticConfig.COMPACT_MATRICES, anchor="w")
            legend_placement_x += 55

        self._inject_panel_metrics(surface, surface_width, surface_height, telemetry_block_width)

    def _display_post_run_metrics(self, metrics):
        self.cached_metrics = metrics
        self._render_gantt_chart_frame(self.active_chronology, self.timeline_ceiling_limit)

    def _inject_panel_metrics(self, surface, canvas_w, canvas_h, block_w):
        if not self.cached_metrics:
            surface.create_text(canvas_w - block_w - 20, canvas_h - 40, text="", fill=VisualAestheticConfig.CAPTION_HEX, font=VisualAestheticConfig.REGULAR_MATRICES, anchor="e")
            return

        aggregated_wait = sum(item["wait"] for item in self.cached_metrics) / len(self.cached_metrics)
        aggregated_turnaround = sum(item["turnaround"] for item in self.cached_metrics) / len(self.cached_metrics)
        formatted_rows = [f"Avg Wait   : {aggregated_wait:.2f}", f"Avg Turnaround: {aggregated_turnaround:.2f}", ""]
        formatted_rows += [f"{item['pid']}: W={item['wait']}, T={item['turnaround']}" for item in self.cached_metrics]

        render_x = canvas_w - block_w + 12
        render_y = 90
        for line_idx, textual_content in enumerate(formatted_rows):
            surface.create_text(render_x, render_y + line_idx * 20, text=textual_content, fill=VisualAestheticConfig.BODY_HEX, font=VisualAestheticConfig.MONOSPACE_MATRICES, anchor="nw")


class MemoryAllocationTab(tk.Frame):
    STRATEGIES = ["First Fit", "Best Fit", "Worst Fit", "Next Fit"]

    def __init__(self, master_canvas):
        super().__init__(master_canvas, bg=VisualAestheticConfig.CANVAS_HEX)
        self.simulation_active = False
        self._initialize_layout()

    def _initialize_layout(self):
        side_control_panel = tk.Frame(self, bg=VisualAestheticConfig.DOCK_HEX, width=260)
        side_control_panel.pack(side="left", fill="y", padx=(VisualAestheticConfig.PADDING_UNIT, 4), pady=VisualAestheticConfig.PADDING_UNIT)
        side_control_panel.pack_propagate(False)

        ElementFactory.craft_header_text(side_control_panel, "Memory Allocation").pack(anchor="w", padx=VisualAestheticConfig.PADDING_UNIT, pady=(VisualAestheticConfig.PADDING_UNIT, 2))

        tk.Label(side_control_panel, text="Algorithm", bg=VisualAestheticConfig.DOCK_HEX, fg=VisualAestheticConfig.CAPTION_HEX, font=VisualAestheticConfig.COMPACT_MATRICES).pack(anchor="w", padx=VisualAestheticConfig.PADDING_UNIT)
        self.selected_strategy = tk.StringVar(value="First Fit")
        ttk.Combobox(side_control_panel, textvariable=self.selected_strategy, values=self.STRATEGIES, state="readonly", font=VisualAestheticConfig.REGULAR_MATRICES).pack(fill="x", padx=VisualAestheticConfig.PADDING_UNIT, pady=(2, VisualAestheticConfig.PADDING_UNIT))

        tk.Label(side_control_panel, text="Memory Blocks (KB)", bg=VisualAestheticConfig.DOCK_HEX, fg=VisualAestheticConfig.CAPTION_HEX, font=VisualAestheticConfig.COMPACT_MATRICES).pack(anchor="w", padx=VisualAestheticConfig.PADDING_UNIT)
        self.memory_blocks_state = tk.StringVar(value="100 500 200 300 600")
        tk.Entry(side_control_panel, textvariable=self.memory_blocks_state, bg=VisualAestheticConfig.SURFACE_HEX, fg=VisualAestheticConfig.BODY_HEX, insertbackground=VisualAestheticConfig.BODY_HEX, relief="flat", font=VisualAestheticConfig.MONOSPACE_MATRICES, highlightthickness=1, highlightbackground=VisualAestheticConfig.OUTLINE_HEX).pack(fill="x", padx=VisualAestheticConfig.PADDING_UNIT, pady=(2, VisualAestheticConfig.PADDING_UNIT))

        tk.Label(side_control_panel, text="Process Sizes (KB)", bg=VisualAestheticConfig.DOCK_HEX, fg=VisualAestheticConfig.CAPTION_HEX, font=VisualAestheticConfig.COMPACT_MATRICES).pack(anchor="w", padx=VisualAestheticConfig.PADDING_UNIT)
        self.process_bounds_state = tk.StringVar(value="212 417 112 426")
        tk.Entry(side_control_panel, textvariable=self.process_bounds_state, bg=VisualAestheticConfig.SURFACE_HEX, fg=VisualAestheticConfig.BODY_HEX, insertbackground=VisualAestheticConfig.BODY_HEX, relief="flat", font=VisualAestheticConfig.MONOSPACE_MATRICES, highlightthickness=1, highlightbackground=VisualAestheticConfig.OUTLINE_HEX).pack(fill="x", padx=VisualAestheticConfig.PADDING_UNIT, pady=(2, VisualAestheticConfig.PADDING_UNIT))

        ElementFactory.craft_action_trigger(side_control_panel, "Random", self._generate_random_workload, VisualAestheticConfig.HIGHLIGHT_HEX).pack(anchor="w", padx=VisualAestheticConfig.PADDING_UNIT, pady=2)
        self.execution_trigger_btn = ElementFactory.craft_action_trigger(side_control_panel, "▶  Allocate", self._invoke_allocation, VisualAestheticConfig.PRIMARY_HEX)
        self.execution_trigger_btn.pack(fill="x", padx=VisualAestheticConfig.PADDING_UNIT, pady=(VisualAestheticConfig.PADDING_UNIT, 4))

        ElementFactory.craft_header_text(side_control_panel, "Allocation Summary").pack(anchor="w", padx=VisualAestheticConfig.PADDING_UNIT, pady=(4, 2))
        self.summary_text_log = tk.Text(side_control_panel, bg=VisualAestheticConfig.SURFACE_HEX, fg=VisualAestheticConfig.BODY_HEX, font=VisualAestheticConfig.MONOSPACE_MATRICES, height=10, relief="flat", state="disabled", highlightthickness=0, wrap="word", padx=6, pady=4)
        self.summary_text_log.pack(fill="both", expand=True, padx=VisualAestheticConfig.PADDING_UNIT, pady=(0, VisualAestheticConfig.PADDING_UNIT))

        display_viewframe = tk.Frame(self, bg=VisualAestheticConfig.CANVAS_HEX)
        display_viewframe.pack(side="left", fill="both", expand=True, padx=(4, VisualAestheticConfig.PADDING_UNIT), pady=VisualAestheticConfig.PADDING_UNIT)
        self.telemetry_banner = tk.Label(display_viewframe, text="System Idle", bg=VisualAestheticConfig.DOCK_HEX, fg=VisualAestheticConfig.CAPTION_HEX, font=VisualAestheticConfig.REGULAR_MATRICES, anchor="w", padx=10, pady=4)
        self.telemetry_banner.pack(fill="x", pady=(0, 4))
        self.graphic_render_surface = tk.Canvas(display_viewframe, bg=VisualAestheticConfig.SURFACE_HEX, bd=0, highlightthickness=0)
        self.graphic_render_surface.pack(fill="both", expand=True)

    def _generate_random_workload(self):
        scrambled_blocks = [random.randint(100, 600) for _ in range(5)]
        scrambled_procs = [random.randint(50, 450) for _ in range(4)]
        self.memory_blocks_state.set(" ".join(map(str, scrambled_blocks)))
        self.process_bounds_state.set(" ".join(map(str, scrambled_procs)))

    def _invoke_allocation(self):
        if self.simulation_active: return
        try:
            parsed_blocks = list(map(int, self.memory_blocks_state.get().split()))
            parsed_procs = list(map(int, self.process_bounds_state.get().split()))
        except ValueError:
            messagebox.showwarning("Error", "Enter space-separated integers.")
            return
        if not parsed_blocks or not parsed_procs:
            messagebox.showwarning("Error", "Inputs cannot be empty.")
            return

        self.simulation_active = True
        self.execution_trigger_btn.config(state="disabled", bg=VisualAestheticConfig.OUTLINE_HEX, text="⏳ Allocating...")
        threading.Thread(target=self._core_calculation_thread, args=(parsed_blocks, parsed_procs), daemon=True).start()

    def _core_calculation_thread(self, memory_partitions, dynamic_requests):
        selected_mode = self.selected_strategy.get()
        working_partitions_state = list(memory_partitions)
        placement_matrix = [-1] * len(dynamic_requests)
        historical_index_tracker = 0

        for req_idx, request_size in enumerate(dynamic_requests):
            identified_partition_idx = -1
            self.telemetry_banner.config(text=f"Scanning partitions for Process {req_idx+1} ({request_size}KB)...", fg=VisualAestheticConfig.HIGHLIGHT_HEX)

            if selected_mode == "First Fit":
                for part_idx, partition_size in enumerate(working_partitions_state):
                    self._execute_frame_refresh(memory_partitions, dynamic_requests, placement_matrix, target_partition_idx=part_idx, focused_request_idx=req_idx)
                    if partition_size >= request_size:
                        identified_partition_idx = part_idx
                        break
            elif selected_mode == "Best Fit":
                minimum_residual_space = float('inf')
                for part_idx, partition_size in enumerate(working_partitions_state):
                    self._execute_frame_refresh(memory_partitions, dynamic_requests, placement_matrix, target_partition_idx=part_idx, focused_request_idx=req_idx)
                    if partition_size >= request_size and (partition_size - request_size) < minimum_residual_space:
                        minimum_residual_space = partition_size - request_size
                        identified_partition_idx = part_idx
                if identified_partition_idx != -1: self._execute_frame_refresh(memory_partitions, dynamic_requests, placement_matrix, target_partition_idx=identified_partition_idx, focused_request_idx=req_idx)
            elif selected_mode == "Worst Fit":
                maximum_residual_space = -1
                for part_idx, partition_size in enumerate(working_partitions_state):
                    self._execute_frame_refresh(memory_partitions, dynamic_requests, placement_matrix, target_partition_idx=part_idx, focused_request_idx=req_idx)
                    if partition_size >= request_size and (partition_size - request_size) > maximum_residual_space:
                        maximum_residual_space = partition_size - request_size
                        identified_partition_idx = part_idx
                if identified_partition_idx != -1: self._execute_frame_refresh(memory_partitions, dynamic_requests, placement_matrix, target_partition_idx=identified_partition_idx, focused_request_idx=req_idx)
            elif selected_mode == "Next Fit":
                starting_scan_point = historical_index_tracker
                for lookup_offset in range(len(working_partitions_state)):
                    part_idx = (starting_scan_point + lookup_offset) % len(working_partitions_state)
                    self._execute_frame_refresh(memory_partitions, dynamic_requests, placement_matrix, target_partition_idx=part_idx, focused_request_idx=req_idx)
                    if working_partitions_state[part_idx] >= request_size:
                        identified_partition_idx = part_idx; historical_index_tracker = part_idx
                        break

            if identified_partition_idx != -1:
                placement_matrix[req_idx] = identified_partition_idx
                working_partitions_state[identified_partition_idx] -= request_size
                self.telemetry_banner.config(text=f"✅ Process {req_idx+1} allocated to Block {identified_partition_idx+1}!", fg=VisualAestheticConfig.SUCCESS_HEX)
                self._render_memory_blueprint(memory_partitions, dynamic_requests, placement_matrix, target_partition_idx=-1, focused_request_idx=-1)
                time.sleep(0.3)
            else:
                self.telemetry_banner.config(text=f"❌ Process {req_idx+1} failed to allocate.", fg=VisualAestheticConfig.CRITICAL_HEX)
                self._render_memory_blueprint(memory_partitions, dynamic_requests, placement_matrix, target_partition_idx=-1, focused_request_idx=-1)
                time.sleep(0.3)
            self._update_textual_log(memory_partitions, working_partitions_state, dynamic_requests, placement_matrix)

        self.simulation_active = False
        self.execution_trigger_btn.config(state="normal", bg=VisualAestheticConfig.PRIMARY_HEX, text="▶  Allocate")
        self.telemetry_banner.config(text="Allocation Mapping Complete", fg=VisualAestheticConfig.SUCCESS_HEX)

    def _execute_frame_refresh(self, memory_partitions, dynamic_requests, placement_matrix, target_partition_idx=-1, focused_request_idx=-1):
        self._render_memory_blueprint(memory_partitions, dynamic_requests, placement_matrix, target_partition_idx, focused_request_idx)
        time.sleep(0.5)

    HEX_ARRAY_PALETTE = ["#7c6af7", "#38c9b0", "#f7c26a", "#f76a6a", "#6af7a1", "#f7a26a"]

    def _render_memory_blueprint(self, memory_partitions, dynamic_requests, placement_matrix, target_partition_idx, focused_request_idx):
        surface = self.graphic_render_surface; surface.delete("all")
        surface_width, surface_height = surface.winfo_width() or 800, surface.winfo_height() or 350
        peak_partition_dimension = max(memory_partitions) if memory_partitions else 1
        column_width, dimensional_gap = 65, 35
        centered_x_origin = (surface_width - (len(memory_partitions) * (column_width + dimensional_gap))) // 2
        top_boundary_y, lower_boundary_y = 60, surface_height - 70

        surface.create_text(surface_width//2, 22, text=f"Memory Spaces Partition Map — {self.selected_strategy.get()}", fill=VisualAestheticConfig.BODY_HEX, font=VisualAestheticConfig.SUBHEADER_MATRICES)

        for current_idx, raw_dimension in enumerate(memory_partitions):
            calculated_x_pos = centered_x_origin + current_idx * (column_width + dimensional_gap)
            bar_scaled_height = int((raw_dimension / peak_partition_dimension) * (lower_boundary_y - top_boundary_y))
            calculated_top_y = lower_boundary_y - bar_scaled_height
            dynamic_outline_hex = VisualAestheticConfig.MUTED_HEX if current_idx == target_partition_idx else VisualAestheticConfig.OUTLINE_HEX
            calculated_thickness = 2 if current_idx == target_partition_idx else 1

            surface.create_rectangle(calculated_x_pos, calculated_top_y, calculated_x_pos+column_width, lower_boundary_y, fill="#2a2d40", outline=dynamic_outline_hex, width=calculated_thickness)
            surface.create_text(calculated_x_pos + column_width//2, calculated_top_y - 14, text=f"{raw_dimension}KB", fill=VisualAestheticConfig.CAPTION_HEX, font=VisualAestheticConfig.COMPACT_MATRICES)
            surface.create_text(calculated_x_pos + column_width//2, lower_boundary_y + 14, text=f"Block {current_idx+1}", fill=VisualAestheticConfig.BODY_HEX, font=("Segoe UI", 9, "bold"))

            total_block_pixel_span = lower_boundary_y - calculated_top_y
            requests_bound_to_partition = [req_idx for req_idx, map_idx in enumerate(placement_matrix) if map_idx == current_idx]
            
            if requests_bound_to_partition:
                summed_allocation_payload = sum(dynamic_requests[req_idx] for req_idx in requests_bound_to_partition)
                current_pixel_height_offset = 0
                
                for offset_idx, req_idx in enumerate(requests_bound_to_partition):
                    individual_payload_size = dynamic_requests[req_idx]

                    if offset_idx == len(requests_bound_to_partition) - 1:
                        allocated_slice_pixel_height = total_block_pixel_span - current_pixel_height_offset
                    else:
                        allocated_slice_pixel_height = max(1, int((individual_payload_size / summed_allocation_payload) * total_block_pixel_span))
                    
                    segment_y1 = lower_boundary_y - current_pixel_height_offset
                    segment_y0 = segment_y1 - allocated_slice_pixel_height
                    
                    surface.create_rectangle(calculated_x_pos+2, segment_y0+2, calculated_x_pos+column_width-2, segment_y1-2, fill=self.HEX_ARRAY_PALETTE[req_idx % len(self.HEX_ARRAY_PALETTE)], outline="")
                    surface.create_text(calculated_x_pos + column_width//2, (segment_y0 + segment_y1)//2, text=f"P{req_idx+1}\n{individual_payload_size}KB", fill=VisualAestheticConfig.CANVAS_HEX, font=("Segoe UI", 8, "bold"), justify="center")
                    current_pixel_height_offset += allocated_slice_pixel_height

        if focused_request_idx != -1 and target_partition_idx != -1:
            evaluation_marker_x = centered_x_origin + target_partition_idx * (column_width + dimensional_gap) + column_width // 2
            surface.create_text(evaluation_marker_x, top_boundary_y - 30, text=f"Testing P{focused_request_idx+1}?", fill=VisualAestheticConfig.HIGHLIGHT_HEX, font=VisualAestheticConfig.COMPACT_MATRICES)

        legend_cursor_x, legend_cursor_y = 20, surface_height - 20
        for req_idx, individual_payload_size in enumerate(dynamic_requests):
            surface.create_rectangle(legend_cursor_x, legend_cursor_y-8, legend_cursor_x+10, legend_cursor_y+2, fill=self.HEX_ARRAY_PALETTE[req_idx % len(self.HEX_ARRAY_PALETTE)], outline="")
            bound_block_index = placement_matrix[req_idx]
            status_text_output = f"In Block {bound_block_index+1}" if bound_block_index != -1 else ("Pending..." if req_idx == focused_request_idx else "Not Allocated")
            surface.create_text(legend_cursor_x+14, legend_cursor_y-3, text=f"P{req_idx+1} ({individual_payload_size}KB) → {status_text_output}", fill=VisualAestheticConfig.BODY_HEX, font=VisualAestheticConfig.COMPACT_MATRICES, anchor="w")
            legend_cursor_x += 170

    def _update_textual_log(self, raw_partitions, updated_partitions, requests, placements):
        text_buffer_lines = [f"{'Process':<10}{'Size':<10}{'Block':<10}{'Status'}", "─" * 45]
        for req_idx, (individual_payload_size, mapped_block_idx) in enumerate(zip(requests, placements)):
            status_summary_token = f"B{mapped_block_idx+1} (Frag {updated_partitions[mapped_block_idx]}KB)" if mapped_block_idx != -1 else "✗ Out of Space"
            text_buffer_lines.append(f"P{req_idx+1:<9}{individual_payload_size:<10}{mapped_block_idx+1 if mapped_block_idx!=-1 else '-':<10}{status_summary_token}")
        text_buffer_lines.append(f"\n  Allocated: {sum(1 for mark in placements if mark != -1)}/{len(requests)}")
        self.summary_text_log.config(state="normal")
        self.summary_text_log.delete("1.0", "end")
        self.summary_text_log.insert("end", "\n".join(text_buffer_lines))
        self.summary_text_log.config(state="disabled")


class VirtualMemoryTab(tk.Frame):
    STRATEGIES = ["FIFO", "LRU", "MRU", "Optimal"]

    def __init__(self, master_canvas):
        super().__init__(master_canvas, bg=VisualAestheticConfig.CANVAS_HEX)
        self.simulation_active = False
        self._initialize_layout()

    def _initialize_layout(self):
        side_control_panel = tk.Frame(self, bg=VisualAestheticConfig.DOCK_HEX, width=270)
        side_control_panel.pack(side="left", fill="y", padx=(VisualAestheticConfig.PADDING_UNIT, 4), pady=VisualAestheticConfig.PADDING_UNIT)
        side_control_panel.pack_propagate(False)

        ElementFactory.craft_header_text(side_control_panel, "Virtual Memory").pack(anchor="w", padx=VisualAestheticConfig.PADDING_UNIT, pady=(VisualAestheticConfig.PADDING_UNIT, 2))

        tk.Label(side_control_panel, text="Algorithm", bg=VisualAestheticConfig.DOCK_HEX, fg=VisualAestheticConfig.CAPTION_HEX, font=VisualAestheticConfig.COMPACT_MATRICES).pack(anchor="w", padx=VisualAestheticConfig.PADDING_UNIT)
        self.selected_strategy = tk.StringVar(value="FIFO")
        ttk.Combobox(side_control_panel, textvariable=self.selected_strategy, values=self.STRATEGIES, state="readonly", font=VisualAestheticConfig.REGULAR_MATRICES).pack(fill="x", padx=VisualAestheticConfig.PADDING_UNIT, pady=(2, VisualAestheticConfig.PADDING_UNIT))

        tk.Label(side_control_panel, text="Frame Count", bg=VisualAestheticConfig.DOCK_HEX, fg=VisualAestheticConfig.CAPTION_HEX, font=VisualAestheticConfig.COMPACT_MATRICES).pack(anchor="w", padx=VisualAestheticConfig.PADDING_UNIT)
        self.allocated_frames_state = tk.StringVar(value="3")
        tk.Entry(side_control_panel, textvariable=self.allocated_frames_state, width=6, bg=VisualAestheticConfig.SURFACE_HEX, fg=VisualAestheticConfig.BODY_HEX, insertbackground=VisualAestheticConfig.BODY_HEX, relief="flat", font=VisualAestheticConfig.MONOSPACE_MATRICES, highlightthickness=1, highlightbackground=VisualAestheticConfig.OUTLINE_HEX).pack(anchor="w", padx=VisualAestheticConfig.PADDING_UNIT, pady=(2, VisualAestheticConfig.PADDING_UNIT))

        tk.Label(side_control_panel, text="Reference String (space-separated)", bg=VisualAestheticConfig.DOCK_HEX, fg=VisualAestheticConfig.CAPTION_HEX, font=VisualAestheticConfig.COMPACT_MATRICES).pack(anchor="w", padx=VisualAestheticConfig.PADDING_UNIT)
        self.reference_stream_state = tk.StringVar(value="7 0 1 2 0 3 0 4 2 3 0 3 2 1 2 0 1 7 0 1")
        tk.Entry(side_control_panel, textvariable=self.reference_stream_state, bg=VisualAestheticConfig.SURFACE_HEX, fg=VisualAestheticConfig.BODY_HEX, insertbackground=VisualAestheticConfig.BODY_HEX, relief="flat", font=VisualAestheticConfig.MONOSPACE_MATRICES, highlightthickness=1, highlightbackground=VisualAestheticConfig.OUTLINE_HEX).pack(fill="x", padx=VisualAestheticConfig.PADDING_UNIT, pady=(2, VisualAestheticConfig.PADDING_UNIT))

        ElementFactory.craft_action_trigger(side_control_panel, "Random String", self._generate_random_reference_stream, VisualAestheticConfig.HIGHLIGHT_HEX).pack(anchor="w", padx=VisualAestheticConfig.PADDING_UNIT, pady=2)
        self.execution_trigger_btn = ElementFactory.craft_action_trigger(side_control_panel, "▶  Simulate", self._invoke_simulation, VisualAestheticConfig.PRIMARY_HEX)
        self.execution_trigger_btn.pack(fill="x", padx=VisualAestheticConfig.PADDING_UNIT, pady=(VisualAestheticConfig.PADDING_UNIT, 4))

        ElementFactory.craft_header_text(side_control_panel, "Page Replacement Stats").pack(anchor="w", padx=VisualAestheticConfig.PADDING_UNIT, pady=(4, 2))
        self.telemetry_text_summary = tk.Text(side_control_panel, bg=VisualAestheticConfig.SURFACE_HEX, fg=VisualAestheticConfig.BODY_HEX, font=VisualAestheticConfig.MONOSPACE_MATRICES, height=6, relief="flat", state="disabled", highlightthickness=0, wrap="word", padx=6, pady=4)
        self.telemetry_text_summary.pack(fill="both", expand=True, padx=VisualAestheticConfig.PADDING_UNIT, pady=(0, 4))

        tk.Label(side_control_panel, text="Step Log", bg=VisualAestheticConfig.DOCK_HEX, fg=VisualAestheticConfig.CAPTION_HEX, font=VisualAestheticConfig.COMPACT_MATRICES).pack(anchor="w", padx=VisualAestheticConfig.PADDING_UNIT, pady=(4, 2))
        self.historical_execution_log = tk.Text(side_control_panel, bg=VisualAestheticConfig.SURFACE_HEX, fg=VisualAestheticConfig.BODY_HEX, font=("Consolas", 8), height=8, relief="flat", state="disabled", highlightthickness=0)
        self.historical_execution_log.pack(fill="both", expand=True, padx=VisualAestheticConfig.PADDING_UNIT, pady=(0, VisualAestheticConfig.PADDING_UNIT))

        display_viewframe = tk.Frame(self, bg=VisualAestheticConfig.CANVAS_HEX)
        display_viewframe.pack(side="left", fill="both", expand=True, padx=(4, VisualAestheticConfig.PADDING_UNIT), pady=VisualAestheticConfig.PADDING_UNIT)
        self.telemetry_banner = tk.Label(display_viewframe, text="System Idle", bg=VisualAestheticConfig.DOCK_HEX, fg=VisualAestheticConfig.CAPTION_HEX, font=VisualAestheticConfig.REGULAR_MATRICES, anchor="w", padx=10, pady=4)
        self.telemetry_banner.pack(fill="x", pady=(0, 4))
        self.graphic_render_surface = tk.Canvas(display_viewframe, bg=VisualAestheticConfig.SURFACE_HEX, bd=0, highlightthickness=0)
        self.graphic_render_surface.pack(fill="both", expand=True)

    def _generate_random_reference_stream(self):
        self.reference_stream_state.set(" ".join([str(random.randint(0, 7)) for _ in range(15)]))

    def _invoke_simulation(self):
        if self.simulation_active: return
        try:
            parsed_stream = list(map(int, self.reference_stream_state.get().split()))
            parsed_frame_limit = int(self.allocated_frames_state.get())
        except ValueError:
            messagebox.showwarning("Error", "Invalid input.")
            return
        if not parsed_stream or parsed_frame_limit <= 0:
            messagebox.showwarning("Error", "Provide a valid reference string and frame count > 0.")
            return

        self.simulation_active = True
        self.execution_trigger_btn.config(state="disabled", bg=VisualAestheticConfig.OUTLINE_HEX, text="⏳ Simulating...")
        self.buffered_log_lines = []
        threading.Thread(target=self._core_calculation_thread, args=(parsed_stream, parsed_frame_limit), daemon=True).start()

    def _core_calculation_thread(self, stream, frame_cap):
        selected_mode = self.selected_strategy.get()
        state_history, logical_fault_log = [], []

        if selected_mode == "FIFO": self._simulate_fifo_logic(stream, frame_cap, state_history, logical_fault_log)
        elif selected_mode == "LRU": self._simulate_lru_logic(stream, frame_cap, state_history, logical_fault_log)
        elif selected_mode == "MRU": self._simulate_mru_logic(stream, frame_cap, state_history, logical_fault_log)
        else: self._simulate_optimal_logic(stream, frame_cap, state_history, logical_fault_log)

        self.simulation_active = False
        self.execution_trigger_btn.config(state="normal", bg=VisualAestheticConfig.PRIMARY_HEX, text="▶  Simulate")
        self.telemetry_banner.config(text="Simulation Complete", fg=VisualAestheticConfig.SUCCESS_HEX)
        total_fault_count = sum(logical_fault_log)
        computed_hit_percentage = ((len(stream) - total_fault_count) / len(stream)) * 100
        
        stat_border_separator = ["─────────────────────────────────"]
        stat_border_separator.append(f" Page Faults  : {total_fault_count:<18}   ")
        stat_border_separator.append(f" Page Hits    : {len(stream)-total_fault_count:<18}")
        stat_border_separator.append(f" Hit Rate     : {computed_hit_percentage:>5.1f}%    ")
        stat_border_separator.append("────────────────────────────")
        
        self.telemetry_text_summary.config(state="normal")
        self.telemetry_text_summary.delete("1.0", "end")
        self.telemetry_text_summary.insert("end", "\n".join(stat_border_separator))
        self.telemetry_text_summary.config(state="disabled")

    def _simulate_fifo_logic(self, stream, limit, history, faults):
        tracking_queue = deque()
        for lookup_idx, current_page in enumerate(stream):
            is_page_fault = current_page not in tracking_queue
            if is_page_fault:
                if len(tracking_queue) == limit: tracking_queue.popleft()
                tracking_queue.append(current_page)
            faults.append(is_page_fault)
            history.append(list(tracking_queue))
            self._execute_frame_refresh(stream[:lookup_idx+1], history, faults, limit, transactional_step=lookup_idx)

    def _simulate_lru_logic(self, stream, limit, history, faults):
        tracking_ordered_map = OrderedDict()
        for lookup_idx, current_page in enumerate(stream):
            is_page_fault = current_page not in tracking_ordered_map
            if is_page_fault:
                if len(tracking_ordered_map) == limit: tracking_ordered_map.popitem(last=False)
                tracking_ordered_map[current_page] = True
            else: tracking_ordered_map.move_to_end(current_page)
            faults.append(is_page_fault)
            history.append(list(tracking_ordered_map.keys()))
            self._execute_frame_refresh(stream[:lookup_idx+1], history, faults, limit, transactional_step=lookup_idx)

    def _simulate_mru_logic(self, stream, limit, history, faults):
        tracking_ordered_map = OrderedDict()
        for lookup_idx, current_page in enumerate(stream):
            is_page_fault = current_page not in tracking_ordered_map
            if is_page_fault:
                if len(tracking_ordered_map) == limit: tracking_ordered_map.popitem(last=True)
                tracking_ordered_map[current_page] = True
            else: tracking_ordered_map.move_to_end(current_page)
            faults.append(is_page_fault)
            history.append(list(tracking_ordered_map.keys()))
            self._execute_frame_refresh(stream[:lookup_idx+1], history, faults, limit, transactional_step=lookup_idx)

    def _simulate_optimal_logic(self, stream, limit, history, faults):
        active_memory_frames = []
        for lookup_idx, current_page in enumerate(stream):
            is_page_fault = current_page not in active_memory_frames
            if is_page_fault:
                if len(active_memory_frames) == limit:
                    future_usage_index_map = {}
                    for allocated_page in active_memory_frames:
                        try: future_usage_index_map[allocated_page] = stream[lookup_idx+1:].index(allocated_page)
                        except ValueError: future_usage_index_map[allocated_page] = float('inf')
                    active_memory_frames.remove(max(future_usage_index_map, key=future_usage_index_map.get))
                active_memory_frames.append(current_page)
            faults.append(is_page_fault)
            history.append(list(active_memory_frames))
            self._execute_frame_refresh(stream[:lookup_idx+1], history, faults, limit, transactional_step=lookup_idx)

    def _execute_frame_refresh(self, dynamic_substream, history, faults, limit, transactional_step):
        last_accessed_page, computational_fault_occurred = dynamic_substream[-1], faults[-1]
        self.telemetry_banner.config(text=f"Step {transactional_step + 1} | Referencing Page: {last_accessed_page} -> {'FAULT' if computational_fault_occurred else 'HIT'}", fg=VisualAestheticConfig.CRITICAL_HEX if computational_fault_occurred else VisualAestheticConfig.SUCCESS_HEX)
        self.buffered_log_lines.append(f"[{transactional_step+1:>2}] Ref: {last_accessed_page} | Frames: {str(history[-1]).ljust(18)} | {'❌ FAULT' if computational_fault_occurred else '✅ HIT'}")
        self.historical_execution_log.config(state="normal")
        self.historical_execution_log.delete("1.0", "end")
        self.historical_execution_log.insert("end", "\n".join(self.buffered_log_lines))
        self.historical_execution_log.see("end")
        self.historical_execution_log.config(state="disabled")
        self._render_matrix_grid(dynamic_substream, history, faults, limit)
        time.sleep(0.15)

    def _render_matrix_grid(self, stream, history, faults, frame_cap):
        surface = self.graphic_render_surface; surface.delete("all")
        surface_width, surface_height = surface.winfo_width() or 800, surface.winfo_height() or 350
        surface.create_text(surface_width//2, 18, text=f"Page Replacement Grid Stream — {self.selected_strategy.get()}", fill=VisualAestheticConfig.BODY_HEX, font=VisualAestheticConfig.SUBHEADER_MATRICES)
        grid_cell_width = max(28, min(48, (surface_width - 100) // max(len(self.reference_stream_state.get().split()), len(stream))))
        initial_x_offset, grid_y_origin = 55, 50
        color_palette_pool = [VisualAestheticConfig.PRIMARY_HEX, VisualAestheticConfig.MUTED_HEX, VisualAestheticConfig.HIGHLIGHT_HEX, "#f7a26a", "#a26af7", "#6ab8f7"]
        page_color_assignment_map = {}

        for current_step, (page_id, frame_snapshot, fault_registered) in enumerate(zip(stream, history, faults)):
            calculated_x_pos = initial_x_offset + current_step * grid_cell_width
            if current_step == len(stream) - 1:
                surface.create_rectangle(calculated_x_pos, grid_y_origin + 10, calculated_x_pos + grid_cell_width, grid_y_origin + frame_cap * 40 + 45, outline=VisualAestheticConfig.OUTLINE_HEX, fill="")
            surface.create_text(calculated_x_pos + grid_cell_width//2, 38, text=str(page_id), fill=VisualAestheticConfig.CRITICAL_HEX if fault_registered else VisualAestheticConfig.SUCCESS_HEX, font=("Consolas", 10, "bold"))
            
            for slot_idx in range(frame_cap):
                calculated_slot_y = grid_y_origin + slot_idx * 40 + 20
                if slot_idx < len(frame_snapshot):
                    current_mapped_page = frame_snapshot[slot_idx]
                    if current_mapped_page not in page_color_assignment_map: 
                        page_color_assignment_map[current_mapped_page] = color_palette_pool[len(page_color_assignment_map) % len(color_palette_pool)]
                    surface.create_rectangle(calculated_x_pos+2, calculated_slot_y, calculated_x_pos+grid_cell_width-2, calculated_slot_y+36, fill=page_color_assignment_map[current_mapped_page], outline=VisualAestheticConfig.CANVAS_HEX, width=1)
                    surface.create_text(calculated_x_pos + grid_cell_width//2, calculated_slot_y + 18, text=str(current_mapped_page), fill=VisualAestheticConfig.CANVAS_HEX, font=("Consolas", 10, "bold"))
                else:
                    surface.create_rectangle(calculated_x_pos+2, calculated_slot_y, calculated_x_pos+grid_cell_width-2, calculated_slot_y+36, fill="#1e2133", outline=VisualAestheticConfig.OUTLINE_HEX, width=1)
            if fault_registered: 
                surface.create_text(calculated_x_pos + grid_cell_width//2, grid_y_origin + frame_cap * 40 + 30, text="F", fill=VisualAestheticConfig.CRITICAL_HEX, font=("Consolas", 9, "bold"))
            else: 
                surface.create_text(calculated_x_pos + grid_cell_width//2, grid_y_origin + frame_cap * 40 + 30, text="•", fill=VisualAestheticConfig.SUCCESS_HEX, font=("Consolas", 12, "bold"))

        for slot_idx in range(frame_cap): 
            surface.create_text(32, grid_y_origin + slot_idx * 40 + 38, text=f"Slot {slot_idx+1}", fill=VisualAestheticConfig.CAPTION_HEX, font=VisualAestheticConfig.COMPACT_MATRICES)
        surface.create_text(32, grid_y_origin + frame_cap * 40 + 30, text="State", fill=VisualAestheticConfig.CAPTION_HEX, font=VisualAestheticConfig.COMPACT_MATRICES)


class MassStorageTab(tk.Frame):
    STRATEGIES = ["FCFS", "SSTF", "SCAN", "C-SCAN", "LOOK", "C-LOOK"]

    def __init__(self, master_canvas):
        super().__init__(master_canvas, bg=VisualAestheticConfig.CANVAS_HEX)
        self.simulation_active = False
        self._initialize_layout()

    def _initialize_layout(self):
        side_control_panel = tk.Frame(self, bg=VisualAestheticConfig.DOCK_HEX, width=270)
        side_control_panel.pack(side="left", fill="y", padx=(VisualAestheticConfig.PADDING_UNIT, 4), pady=VisualAestheticConfig.PADDING_UNIT)
        side_control_panel.pack_propagate(False)

        ElementFactory.craft_header_text(side_control_panel, "Disk Scheduling").pack(anchor="w", padx=VisualAestheticConfig.PADDING_UNIT, pady=(VisualAestheticConfig.PADDING_UNIT, 2))
        tk.Label(side_control_panel, text="Algorithm", bg=VisualAestheticConfig.DOCK_HEX, fg=VisualAestheticConfig.CAPTION_HEX, font=VisualAestheticConfig.COMPACT_MATRICES).pack(anchor="w", padx=VisualAestheticConfig.PADDING_UNIT)
        self.selected_strategy = tk.StringVar(value="FCFS")
        ttk.Combobox(side_control_panel, textvariable=self.selected_strategy, values=self.STRATEGIES, state="readonly", font=VisualAestheticConfig.REGULAR_MATRICES).pack(fill="x", padx=VisualAestheticConfig.PADDING_UNIT, pady=(2, VisualAestheticConfig.PADDING_UNIT))

        row_container_1, self.initial_head_state = ElementFactory.craft_input_composite(side_control_panel, "Initial Head Position", "53", 6)
        row_container_1.pack(anchor="w", padx=VisualAestheticConfig.PADDING_UNIT, pady=2)
        row_container_2, self.maximum_cylinder_state = ElementFactory.craft_input_composite(side_control_panel, "Max Cylinder", "199", 6)
        row_container_2.pack(anchor="w", padx=VisualAestheticConfig.PADDING_UNIT, pady=2)

        self.direction_radio_wrapper = tk.Frame(side_control_panel, bg=VisualAestheticConfig.DOCK_HEX)
        self.direction_radio_wrapper.pack(anchor="w", padx=VisualAestheticConfig.PADDING_UNIT, pady=2)
        tk.Label(self.direction_radio_wrapper, text="Initial Direction:", bg=VisualAestheticConfig.DOCK_HEX, fg=VisualAestheticConfig.CAPTION_HEX, font=VisualAestheticConfig.COMPACT_MATRICES).pack(side="left")
        self.traversal_direction_state = tk.StringVar(value="right")
        tk.Radiobutton(self.direction_radio_wrapper, text="→", variable=self.traversal_direction_state, value="right", bg=VisualAestheticConfig.DOCK_HEX, fg=VisualAestheticConfig.BODY_HEX, selectcolor=VisualAestheticConfig.SURFACE_HEX, font=VisualAestheticConfig.COMPACT_MATRICES).pack(side="left")
        tk.Radiobutton(self.direction_radio_wrapper, text="←", variable=self.traversal_direction_state, value="left", bg=VisualAestheticConfig.DOCK_HEX, fg=VisualAestheticConfig.BODY_HEX, selectcolor=VisualAestheticConfig.SURFACE_HEX, font=VisualAestheticConfig.COMPACT_MATRICES).pack(side="left")

        tk.Label(side_control_panel, text="Request Queue (space-separated)", bg=VisualAestheticConfig.DOCK_HEX, fg=VisualAestheticConfig.CAPTION_HEX, font=VisualAestheticConfig.COMPACT_MATRICES).pack(anchor="w", padx=VisualAestheticConfig.PADDING_UNIT, pady=(VisualAestheticConfig.PADDING_UNIT, 0))
        self.request_queue_state = tk.StringVar(value="98 183 37 122 14 124 65 67")
        tk.Entry(side_control_panel, textvariable=self.request_queue_state, bg=VisualAestheticConfig.SURFACE_HEX, fg=VisualAestheticConfig.BODY_HEX, insertbackground=VisualAestheticConfig.BODY_HEX, relief="flat", font=VisualAestheticConfig.MONOSPACE_MATRICES, highlightthickness=1, highlightbackground=VisualAestheticConfig.OUTLINE_HEX).pack(fill="x", padx=VisualAestheticConfig.PADDING_UNIT, pady=(2, VisualAestheticConfig.PADDING_UNIT))

        ElementFactory.craft_action_trigger(side_control_panel, "Random", self._scramble_cylinder_requests, VisualAestheticConfig.HIGHLIGHT_HEX).pack(anchor="w", padx=VisualAestheticConfig.PADDING_UNIT, pady=2)
        self.execution_trigger_btn = ElementFactory.craft_action_trigger(side_control_panel, "▶  Simulate", self._invoke_simulation, VisualAestheticConfig.PRIMARY_HEX)
        self.execution_trigger_btn.pack(fill="x", padx=VisualAestheticConfig.PADDING_UNIT, pady=(VisualAestheticConfig.PADDING_UNIT, 4))

        ElementFactory.craft_header_text(side_control_panel, "Disk Seek Summary").pack(anchor="w", padx=VisualAestheticConfig.PADDING_UNIT, pady=(4, 2))
        self.telemetry_text_summary = tk.Text(side_control_panel, bg=VisualAestheticConfig.SURFACE_HEX, fg=VisualAestheticConfig.BODY_HEX, font=VisualAestheticConfig.MONOSPACE_MATRICES, height=10, relief="flat", state="disabled", highlightthickness=0, wrap="word", padx=6, pady=4)
        self.telemetry_text_summary.pack(fill="both", expand=True, padx=VisualAestheticConfig.PADDING_UNIT, pady=(0, VisualAestheticConfig.PADDING_UNIT))

        display_viewframe = tk.Frame(self, bg=VisualAestheticConfig.CANVAS_HEX)
        display_viewframe.pack(side="left", fill="both", expand=True, padx=(4, VisualAestheticConfig.PADDING_UNIT), pady=VisualAestheticConfig.PADDING_UNIT)
        self.telemetry_banner = tk.Label(display_viewframe, text="System Idle", bg=VisualAestheticConfig.DOCK_HEX, fg=VisualAestheticConfig.CAPTION_HEX, font=VisualAestheticConfig.REGULAR_MATRICES, anchor="w", padx=10, pady=4)
        self.telemetry_banner.pack(fill="x", pady=(0, 4))
        self.graphic_render_surface = tk.Canvas(display_viewframe, bg=VisualAestheticConfig.SURFACE_HEX, bd=0, highlightthickness=0)
        self.graphic_render_surface.pack(fill="both", expand=True)

    def _scramble_cylinder_requests(self):
        try: target_ceiling = int(self.maximum_cylinder_state.get())
        except: target_ceiling = 199
        self.request_queue_state.set(" ".join(map(str, sorted(random.sample(range(0, target_ceiling+1), min(8, target_ceiling+1))))))
        self.initial_head_state.set(str(random.randint(0, target_ceiling)))

    def _invoke_simulation(self):
        if self.simulation_active: return
        try:
            parsed_head_position = int(self.initial_head_state.get())
            parsed_max_cylinder = int(self.maximum_cylinder_state.get())
            parsed_requests_list = list(map(int, self.request_queue_state.get().split()))
        except ValueError:
            messagebox.showwarning("Error", "Invalid input.")
            return

        self.simulation_active = True
        self.execution_trigger_btn.config(state="disabled", bg=VisualAestheticConfig.OUTLINE_HEX, text="⏳ Seeking...")
        threading.Thread(target=self._core_calculation_thread, args=(parsed_requests_list, parsed_head_position, parsed_max_cylinder), daemon=True).start()

    def _core_calculation_thread(self, requests, head, limit):
        selected_mode = self.selected_strategy.get()
        selected_direction = self.traversal_direction_state.get()
        
        if selected_mode == "FCFS": execution_sequence = list(requests)
        elif selected_mode == "SSTF":
            execution_sequence, unprocessed_residuals, structural_head_cursor = [], list(requests), head
            while unprocessed_residuals:
                nearest_node = min(unprocessed_residuals, key=lambda target: abs(target - structural_head_cursor))
                execution_sequence.append(nearest_node); unprocessed_residuals.remove(nearest_node); structural_head_cursor = nearest_node
        elif selected_mode in ("SCAN", "LOOK"):
            nodes_to_left = sorted([req for req in requests if req < head], reverse=True)
            nodes_to_right = sorted([req for req in requests if req >= head])
            if selected_mode == "SCAN": execution_sequence = (nodes_to_right + [limit] + nodes_to_left) if selected_direction == "right" else (nodes_to_left + [0] + nodes_to_right)
            else: execution_sequence = (nodes_to_right + nodes_to_left) if selected_direction == "right" else (nodes_to_left + nodes_to_right)
        elif selected_mode in ("C-SCAN", "C-LOOK"):
            nodes_to_right = sorted([req for req in requests if req >= head])
            nodes_to_left = sorted([req for req in requests if req < head])
            execution_sequence = (nodes_to_right + [limit, 0] + nodes_to_left) if selected_mode == "C-SCAN" else (nodes_to_right + nodes_to_left)
        else: execution_sequence = list(requests)

        complete_plotted_path = [head] + execution_sequence
        computed_total_displacement = sum(abs(complete_plotted_path[idx+1] - complete_plotted_path[idx]) for idx in range(len(complete_plotted_path)-1))
        
        for step_idx in range(1, len(complete_plotted_path) + 1):
            runtime_partial_path = complete_plotted_path[:step_idx]
            self.telemetry_banner.config(text=f"Seeking Cylinder: {runtime_partial_path[-1]} (Track Step {step_idx-1}/{len(complete_plotted_path)-1})", fg=VisualAestheticConfig.HIGHLIGHT_HEX)
            self._render_graphical_plot(runtime_partial_path, limit, total_points_count=len(complete_plotted_path))
            time.sleep(0.6)

        self.simulation_active = False
        self.execution_trigger_btn.config(state="normal", bg=VisualAestheticConfig.PRIMARY_HEX, text="▶  Simulate")
        self.telemetry_banner.config(text="Head Scan Sequence Complete", fg=VisualAestheticConfig.SUCCESS_HEX)
        
        summary_panel_text = ["┌─────────────────────────────┐"]
        summary_panel_text.append(f"│ Total Movement: {computed_total_displacement:<16} │")
        summary_panel_text.append(f"│ Requests Served: {len(requests):<15} │")
        summary_panel_text.append("├─────────────────────────────┤")
        summary_panel_text.append(f"│ Service Order:              │")
        flattened_service_order_string = " → ".join(map(str, [node for node in execution_sequence if node in requests]))
        summary_panel_text.append(f"│ {flattened_service_order_string[:26]:<27} │")
        if len(flattened_service_order_string) > 26:
            summary_panel_text.append(f"│ {flattened_service_order_string[26:]:<27} │")
        summary_panel_text.append("└─────────────────────────────┘")
        
        self.telemetry_text_summary.config(state="normal")
        self.telemetry_text_summary.delete("1.0", "end")
        self.telemetry_text_summary.insert("end", "\n".join(summary_panel_text))
        self.telemetry_text_summary.config(state="disabled")

    def _render_graphical_plot(self, path, limit, total_points_count):
        surface = self.graphic_render_surface; surface.delete("all")
        surface_width, surface_height = surface.winfo_width() or 800, surface.winfo_height() or 350
        surface.create_text(surface_width//2, 18, text=f"Disk Head Seek Path Plot — {self.selected_strategy.get()}", fill=VisualAestheticConfig.BODY_HEX, font=VisualAestheticConfig.SUBHEADER_MATRICES)

        pad_l, pad_r, pad_t, pad_b = 80, 40, 50, 40
        graph_width, graph_height = surface_width - pad_l - pad_r, surface_height - pad_t - pad_b
        horizontal_increment_step = graph_width / max(total_points_count - 1, 1)

        def transform_x(i): return pad_l + i * horizontal_increment_step
        def transform_y(val): return pad_t + graph_height - (val / limit) * graph_height

        for tick_value in range(0, limit+1, max(1, limit//10)):
            calculated_y_pos = transform_y(tick_value)
            surface.create_line(pad_l-4, calculated_y_pos, pad_l, calculated_y_pos, fill=VisualAestheticConfig.OUTLINE_HEX)
            surface.create_text(pad_l-8, calculated_y_pos, text=str(tick_value), fill=VisualAestheticConfig.CAPTION_HEX, font=VisualAestheticConfig.COMPACT_MATRICES, anchor="e")
        surface.create_line(pad_l, pad_t, pad_l, pad_t+graph_height, fill=VisualAestheticConfig.OUTLINE_HEX, width=1)
        surface.create_line(pad_l, pad_t+graph_height, pad_l+graph_width, pad_t+graph_height, fill=VisualAestheticConfig.OUTLINE_HEX, width=1)

        for marker_idx in range(total_points_count):
            surface.create_text(transform_x(marker_idx), pad_t+graph_height+14, text="Start" if marker_idx == 0 else str(marker_idx), fill=VisualAestheticConfig.CAPTION_HEX, font=VisualAestheticConfig.COMPACT_MATRICES)

        for segment_idx in range(len(path)-1):
            surface.create_line(transform_x(segment_idx), transform_y(path[segment_idx]), transform_x(segment_idx+1), transform_y(path[segment_idx+1]), fill=VisualAestheticConfig.PRIMARY_HEX, width=2)

        for marker_idx, scalar_value in enumerate(path):
            current_node_color = VisualAestheticConfig.HIGHLIGHT_HEX if marker_idx == 0 else (VisualAestheticConfig.MUTED_HEX if marker_idx == len(path)-1 else VisualAestheticConfig.PRIMARY_HEX)
            surface.create_oval(transform_x(marker_idx)-6, transform_y(scalar_value)-6, transform_x(marker_idx)+6, transform_y(scalar_value)+6, fill=current_node_color, outline=VisualAestheticConfig.CANVAS_HEX, width=2)
            surface.create_text(transform_x(marker_idx), transform_y(scalar_value)-16, text=str(scalar_value), fill=current_node_color, font=VisualAestheticConfig.COMPACT_MATRICES)
        surface.create_text(14, pad_t + graph_height//2, text="Cylinder ID", fill=VisualAestheticConfig.CAPTION_HEX, font=VisualAestheticConfig.COMPACT_MATRICES, angle=90)


class OSVisualizerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("OS Algorithm Visualizer")
        self.geometry("1100x700")
        self.resizable(False, False)
        self.wm_state("zoomed")
        self.configure(bg=VisualAestheticConfig.CANVAS_HEX)
        self._configure_ttk_theme_engine()
        self._instantiate_user_interface()

    def _configure_ttk_theme_engine(self):
        theme_runtime_style = ttk.Style(self)
        theme_runtime_style.theme_use("clam")
        theme_runtime_style.configure("TCombobox", fieldbackground=VisualAestheticConfig.SURFACE_HEX, background=VisualAestheticConfig.SURFACE_HEX, foreground=VisualAestheticConfig.BODY_HEX,
                                selectbackground=VisualAestheticConfig.PRIMARY_HEX, selectforeground=VisualAestheticConfig.BODY_HEX, bordercolor=VisualAestheticConfig.OUTLINE_HEX, arrowcolor=VisualAestheticConfig.CAPTION_HEX, relief="flat")
        theme_runtime_style.map("TCombobox", fieldbackground=[("readonly", VisualAestheticConfig.SURFACE_HEX)], foreground=[("readonly", VisualAestheticConfig.BODY_HEX)])
        theme_runtime_style.configure("Pink.TButton", background=VisualAestheticConfig.DOCK_HEX, foreground=VisualAestheticConfig.BODY_HEX, borderwidth=0, padding=[10, 6], font=VisualAestheticConfig.REGULAR_MATRICES)
        theme_runtime_style.map("Pink.TButton", background=[("active", VisualAestheticConfig.MUTED_HEX), ("pressed", VisualAestheticConfig.PRIMARY_HEX)], foreground=[("active", VisualAestheticConfig.BODY_HEX), ("pressed", VisualAestheticConfig.BODY_HEX)])

    def _instantiate_user_interface(self):
        application_header_panel = tk.Frame(self, bg=VisualAestheticConfig.DOCK_HEX, height=78)
        application_header_panel.pack(fill="x")
        application_header_panel.pack_propagate(False)
        tk.Label(application_header_panel, text="Scheduling Algorithm Visualizer", bg=VisualAestheticConfig.DOCK_HEX, fg=VisualAestheticConfig.BODY_HEX, font=VisualAestheticConfig.HEADER_MATRICES).pack(pady=(14, 2))
        tk.Label(application_header_panel, text="Choose an algorithm, adjust the inputs, and watch the simulation unfold.", bg=VisualAestheticConfig.DOCK_HEX, fg=VisualAestheticConfig.CAPTION_HEX, font=VisualAestheticConfig.REGULAR_MATRICES).pack()

        central_viewport_container = tk.Frame(self, bg=VisualAestheticConfig.CANVAS_HEX)
        central_viewport_container.pack(fill="both", expand=True, padx=VisualAestheticConfig.PADDING_UNIT, pady=(VisualAestheticConfig.PADDING_UNIT, 0))

        self.mapped_component_tabs = {}
        self.structural_navigation_manifest = [
            ("CPU Scheduling", CPUSchedulingTab),
            ("Memory Allocation", MemoryAllocationTab),
            ("Virtual Memory", VirtualMemoryTab),
            ("Disk Scheduling", MassStorageTab),
        ]

        for block_title, target_class in self.structural_navigation_manifest:
            instantiated_frame_instance = target_class(central_viewport_container)
            instantiated_frame_instance.pack(fill="both", expand=True)
            instantiated_frame_instance.pack_forget()
            self.mapped_component_tabs[block_title] = instantiated_frame_instance

        self.active_module_token = self.structural_navigation_manifest[0][0]
        self._route_active_view(self.active_module_token)

        application_footer_panel = tk.Frame(self, bg=VisualAestheticConfig.DOCK_HEX, height=68)
        application_footer_panel.pack(fill="x", side="bottom")
        application_footer_panel.pack_propagate(False)

        footer_navigation_subdeck = tk.Frame(application_footer_panel, bg=VisualAestheticConfig.DOCK_HEX)
        footer_navigation_subdeck.pack(expand=True, pady=10)
        for block_title, _ in self.structural_navigation_manifest:
            navigation_button = ttk.Button(
                footer_navigation_subdeck,
                text=block_title,
                style="Pink.TButton",
                command=lambda tracking_token=block_title: self._route_active_view(tracking_token)
            )
            navigation_button.pack(side="left", padx=6)

        tk.Frame(self, bg=VisualAestheticConfig.CANVAS_HEX, height=24).pack(fill="x", side="bottom")

    def _route_active_view(self, target_token):
        for block_title, component_frame in self.mapped_component_tabs.items():
            component_frame.pack_forget()
        self.mapped_component_tabs[target_token].pack(fill="both", expand=True)
        self.active_module_token = target_token


def main():
    execution_environment_app = OSVisualizerApp()
    execution_environment_app.mainloop()

if __name__ == "__main__":
    main()
