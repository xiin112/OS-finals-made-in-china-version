"""
OS Algorithm Visualizer
========================
Run command:  python3 app_visualizer.py
Required:  Python 3.8+ with tkinter
"""

import tkinter as tk
from tkinter import ttk, messagebox, font
import random
import math
import time
import threading
from collections import deque, OrderedDict
from copy import deepcopy

# ─── THEME ──────────────────────────────────────────────────────────────────
BG        = "#fce4ec"
PANEL     = "#f8bbd0"
CARD      = "#fef5f8"
ACCENT    = "#ff1493"      # deep pink
ACCENT2   = "#ffb6d9"      # light pink
WARN      = "#ff88cc"      # rose pink
DANGER    = "#ff6b7a"      # coral pink
TEXT      = "#3B031B"
SUBTEXT   = "#795569"
BORDER    = "#e5b3d0"
GREEN     = "#ff69b4"

FONT_H1   = ("Segoe UI", 18, "bold")
FONT_H2   = ("Segoe UI", 13, "bold")
FONT_H3   = ("Segoe UI", 11, "bold")
FONT_BODY = ("Segoe UI", 10)
FONT_MONO = ("Consolas", 10)
FONT_TINY = ("Segoe UI", 9)

PAD = 10


# ═══════════════════════════════════════════════════════════════════════════
#  UTILITY WIDGETS
# ═══════════════════════════════════════════════════════════════════════════

def styled_button(parent, text, command, color=ACCENT, **kwargs):
    btn = tk.Button(
        parent, text=text, command=command,
        bg=color, fg=TEXT, relief="flat",
        activebackground=ACCENT2, activeforeground=TEXT,
        font=FONT_BODY, padx=12, pady=6, cursor="hand2",
        bd=0, **kwargs
    )
    return btn

def section_label(parent, text, **kwargs):
    return tk.Label(parent, text=text, bg=PANEL, fg=TEXT, font=FONT_H2, **kwargs)

def info_label(parent, text, color=SUBTEXT, **kwargs):
    return tk.Label(parent, text=text, bg=PANEL, fg=color, font=FONT_TINY, wraplength=520, justify="left", **kwargs)

def entry_row(parent, label, default="", width=8):
    f = tk.Frame(parent, bg=PANEL)
    tk.Label(f, text=label, bg=PANEL, fg=SUBTEXT, font=FONT_TINY).pack(side="left", padx=(0, 4))
    v = tk.StringVar(value=default)
    e = tk.Entry(f, textvariable=v, width=width, bg=CARD, fg=TEXT, insertbackground=TEXT,
                 relief="flat", font=FONT_MONO, highlightthickness=1, highlightbackground=BORDER)
    e.pack(side="left")
    return f, v


# ═══════════════════════════════════════════════════════════════════════════
#  1 ─ CPU SCHEDULING
# ═══════════════════════════════════════════════════════════════════════════

class CPUSchedulingTab(tk.Frame):
    ALGOS = ["FCFS", "SJF (Non-Preemptive)", "Priority (Non-Preemptive)", "Round Robin"]

    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self.is_running = False
        self._build_ui()

    def _build_ui(self):
        ctrl = tk.Frame(self, bg=PANEL, width=260)
        ctrl.pack(side="left", fill="y", padx=(PAD, 4), pady=PAD)
        ctrl.pack_propagate(False)

        section_label(ctrl, "CPU Scheduling").pack(anchor="w", padx=PAD, pady=(PAD, 2))

        tk.Label(ctrl, text="Algorithm", bg=PANEL, fg=SUBTEXT, font=FONT_TINY).pack(anchor="w", padx=PAD)
        self.algo_var = tk.StringVar(value=self.ALGOS[0])
        cb = ttk.Combobox(ctrl, textvariable=self.algo_var, values=self.ALGOS, state="readonly", font=FONT_BODY)
        cb.pack(fill="x", padx=PAD, pady=(2, PAD))
        cb.bind("<<ComboboxSelected>>", self._on_algo_change)

        self.rr_frame = tk.Frame(ctrl, bg=PANEL)
        self.rr_frame.pack(fill="x", padx=PAD)
        tk.Label(self.rr_frame, text="Time Quantum", bg=PANEL, fg=SUBTEXT, font=FONT_TINY).pack(anchor="w")
        self.quantum_var = tk.StringVar(value="2")
        tk.Entry(self.rr_frame, textvariable=self.quantum_var, width=6,
                 bg=CARD, fg=TEXT, insertbackground=TEXT, relief="flat", font=FONT_MONO,
                 highlightthickness=1, highlightbackground=BORDER).pack(anchor="w", pady=2)
        self.rr_frame.pack_forget()

        tk.Label(ctrl, text="Processes", bg=PANEL, fg=SUBTEXT, font=FONT_TINY).pack(anchor="w", padx=PAD, pady=(PAD, 0))
        hdr = tk.Frame(ctrl, bg=PANEL)
        hdr.pack(fill="x", padx=PAD)
        for h, w in [("PID", 4), ("Arrival", 6), ("Burst", 5), ("Priority", 7)]:
            tk.Label(hdr, text=h, bg=PANEL, fg=SUBTEXT, font=FONT_TINY, width=w).pack(side="left")

        self.proc_rows = []
        self.row_container = tk.Frame(ctrl, bg=PANEL)
        self.row_container.pack(fill="x", padx=PAD)
        for i in range(5):
            self._add_row(i)

        btn_f = tk.Frame(ctrl, bg=PANEL)
        btn_f.pack(fill="x", padx=PAD, pady=PAD)
        styled_button(btn_f, "+ Row", self._add_process, ACCENT2).pack(side="left", padx=2)
        styled_button(btn_f, "Random", self._randomize, WARN).pack(side="left", padx=2)

        self.run_btn = styled_button(ctrl, "▶  Run Animation", self._start_simulation, ACCENT)
        self.run_btn.pack(fill="x", padx=PAD, pady=(PAD, 4))

        tk.Label(ctrl, text="Process Statistics", bg=PANEL, fg=TEXT, font=FONT_H3).pack(anchor="w", padx=PAD, pady=(4, 2))
        self.stats_text = tk.Text(ctrl, bg=CARD, fg=TEXT, font=FONT_MONO, height=10, relief="flat", state="disabled", 
                                   highlightthickness=0, wrap="word", padx=6, pady=4)
        self.stats_text.pack(fill="both", expand=True, padx=PAD, pady=(0, PAD))

        right = tk.Frame(self, bg=BG)
        right.pack(side="left", fill="both", expand=True, padx=(4, PAD), pady=PAD)

        self.status_bar = tk.Label(right, text="System Idle", bg=PANEL, fg=SUBTEXT, font=FONT_BODY, anchor="w", padx=10, pady=4)
        self.status_bar.pack(fill="x", pady=(0, 4))

        self.canvas = tk.Canvas(right, bg=CARD, bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

    def _add_row(self, pid):
        f = tk.Frame(self.row_container, bg=PANEL)
        f.pack(fill="x", pady=1)
        pid_var = tk.StringVar(value=f"P{pid+1}")
        arr_var = tk.StringVar(value=str(pid if pid < 3 else random.randint(0,4)))
        burst_var = tk.StringVar(value=str(random.randint(2, 6)))
        prio_var = tk.StringVar(value=str(random.randint(1, 5)))
        for var, w in [(pid_var, 4), (arr_var, 6), (burst_var, 5), (prio_var, 7)]:
            tk.Entry(f, textvariable=var, width=w, bg=CARD, fg=TEXT,
                     insertbackground=TEXT, relief="flat", font=FONT_MONO,
                     highlightthickness=1, highlightbackground=BORDER).pack(side="left", padx=1)
        self.proc_rows.append((pid_var, arr_var, burst_var, prio_var))

    def _add_process(self):
        self._add_row(len(self.proc_rows))

    def _randomize(self):
        for pid_v, arr_v, burst_v, prio_v in self.proc_rows:
            arr_v.set(str(random.randint(0, 5)))
            burst_v.set(str(random.randint(1, 8)))
            prio_v.set(str(random.randint(1, 5)))

    def _on_algo_change(self, *_):
        if "Round Robin" in self.algo_var.get():
            self.rr_frame.pack(fill="x", padx=PAD)
        else:
            self.rr_frame.pack_forget()

    def _get_processes(self):
        procs = []
        for pid_v, arr_v, burst_v, prio_v in self.proc_rows:
            try:
                procs.append({
                    "pid": pid_v.get(), "arrival": int(arr_v.get()),
                    "burst": int(burst_v.get()), "priority": int(prio_v.get()),
                })
            except ValueError: continue
        return procs

    COLORS = ["#7c6af7", "#38c9b0", "#f7c26a", "#f76a6a", "#6af7a1", "#f7a26a", "#a26af7", "#6ab8f7"]

    def _start_simulation(self):
        if self.is_running: return
        procs = self._get_processes()
        if not procs:
            messagebox.showwarning("No Data", "Add at least one process.")
            return

        self.is_running = True
        self.run_btn.config(state="disabled", bg=BORDER, text="⏳ Running...")
        
        total_burst = sum(p["burst"] for p in procs)
        max_arrival = max(p["arrival"] for p in procs)
        self.max_time_bound = max_arrival + total_burst + 5 

        threading.Thread(target=self._run_engine, args=(procs,), daemon=True).start()

    def _run_engine(self, procs):
        algo = self.algo_var.get()
        timeline, stats = [], []

        if algo == "FCFS":
            self._animate_fcfs(procs, timeline, stats)
        elif "SJF" in algo:
            self._animate_sjf(procs, timeline, stats)
        elif "Priority" in algo:
            self._animate_priority(procs, timeline, stats)
        else:
            try: q = int(self.quantum_var.get())
            except ValueError: q = 2
            self._animate_rr(procs, q, timeline, stats)

        self.is_running = False
        self.run_btn.config(state="normal", bg=ACCENT, text="▶  Run Animation")
        self.status_bar.config(text="Simulation Complete", fg=GREEN)
        self._show_stats(stats)

    def _animate_fcfs(self, procs, timeline, stats):
        procs = sorted(procs, key=lambda p: p["arrival"])
        t = 0
        for p in procs:
            while t < p["arrival"]:
                self._ui_tick(timeline, t, ready_queue=[])
                t += 1
            start = t
            for _ in range(p["burst"]):
                t += 1
                timeline.append((p["pid"], start, t))
                self._ui_tick(timeline, t, active_pid=p["pid"])
            stats.append({"pid": p["pid"], "wait": start - p["arrival"], "turnaround": t - p["arrival"]})

    def _animate_sjf(self, procs, timeline, stats):
        remaining = list(deepcopy(procs))
        t = 0
        while remaining:
            available = [p for p in remaining if p["arrival"] <= t]
            ready_pids = [p["pid"] for p in available]
            if not available:
                self._ui_tick(timeline, t, ready_queue=[])
                t += 1
                continue
            p = min(available, key=lambda x: x["burst"])
            ready_pids.remove(p["pid"])
            start = t
            for _ in range(p["burst"]):
                t += 1
                timeline.append((p["pid"], start, t))
                current_ready = ready_pids + [r["pid"] for r in remaining if r["arrival"] <= t and r not in available]
                self._ui_tick(timeline, t, active_pid=p["pid"], ready_queue=current_ready)
            stats.append({"pid": p["pid"], "wait": start - p["arrival"], "turnaround": t - p["arrival"]})
            remaining.remove(p)

    def _animate_priority(self, procs, timeline, stats):
        remaining = list(deepcopy(procs))
        t = 0
        while remaining:
            available = [p for p in remaining if p["arrival"] <= t]
            ready_pids = [p["pid"] for p in available]
            if not available:
                self._ui_tick(timeline, t, ready_queue=[])
                t += 1
                continue
            p = min(available, key=lambda x: x["priority"])
            ready_pids.remove(p["pid"])
            start = t
            for _ in range(p["burst"]):
                t += 1
                timeline.append((p["pid"], start, t))
                current_ready = ready_pids + [r["pid"] for r in remaining if r["arrival"] <= t and r not in available]
                self._ui_tick(timeline, t, active_pid=p["pid"], ready_queue=current_ready)
            stats.append({"pid": p["pid"], "wait": start - p["arrival"], "turnaround": t - p["arrival"]})
            remaining.remove(p)

    def _animate_rr(self, procs, quantum, timeline, stats):
        order = sorted(procs, key=lambda p: p["arrival"])
        remaining_burst = {p["pid"]: p["burst"] for p in procs}
        finish = {}
        ready = deque()
        proc_list = list(order)
        idx, t = 0, 0

        while ready or idx < len(proc_list):
            while idx < len(proc_list) and proc_list[idx]["arrival"] <= t:
                if proc_list[idx]["pid"] not in ready: ready.append(proc_list[idx]["pid"])
                idx += 1
            if not ready:
                self._ui_tick(timeline, t, ready_queue=[])
                t += 1
                continue
            pid = ready.popleft()
            run = min(quantum, remaining_burst[pid])
            start = t
            for _ in range(run):
                t += 1
                remaining_burst[pid] -= 1
                timeline.append((pid, start, t))
                while idx < len(proc_list) and proc_list[idx]["arrival"] <= t:
                    if proc_list[idx]["pid"] not in ready: ready.append(proc_list[idx]["pid"])
                    idx += 1
                self._ui_tick(timeline, t, active_pid=pid, ready_queue=list(ready))
            if remaining_burst[pid] > 0: ready.append(pid)
            else: finish[pid] = t

        for p in procs:
            if p["pid"] in finish:
                stats.append({"pid": p["pid"], "wait": finish[p["pid"]] - p["arrival"] - p["burst"], "turnaround": finish[p["pid"]] - p["arrival"]})

    def _ui_tick(self, timeline, current_time, active_pid=None, ready_queue=None):
        if ready_queue is None: ready_queue = []
        q_str = " → ".join(ready_queue) if ready_queue else "Empty"
        self.status_bar.config(text=f"Time: {current_time}s | Active CPU: {active_pid or 'IDLE'} | Ready Queue: [{q_str}]", fg=ACCENT2 if active_pid else SUBTEXT)
        self._draw_gantt_frame(timeline, current_time)
        time.sleep(0.4)

    def _draw_gantt_frame(self, timeline, current_time):
        c = self.canvas; c.delete("all")
        W, H = c.winfo_width() or 800, c.winfo_height() or 300
        margin_l, margin_r, margin_top = 60, 40, 60
        bar_h, bar_y = 44, margin_top + 30
        scale = (W - margin_l - margin_r) / max(self.max_time_bound, current_time, 1)

        pids = list(dict.fromkeys(p for p, _, _ in timeline)) if timeline else []
        pid_color = {p: self.COLORS[i % len(self.COLORS)] for i, p in enumerate(pids)}

        c.create_text(W//2, 18, text=f"Gantt Chart Real-Time Stream — {self.algo_var.get()}", fill=TEXT, font=FONT_H3)
        ax_y = bar_y + bar_h + 2
        c.create_line(margin_l, ax_y, W - margin_r, ax_y, fill=BORDER, width=1)

        if not timeline:
            c.create_text(margin_l + 10, bar_y + 20, text="System startup, resolving arrivals...", fill=SUBTEXT, font=FONT_BODY, anchor="w")
            return

        drawn_blocks = []
        for pid, start, end in timeline:
            if not drawn_blocks or drawn_blocks[-1][0] != pid or drawn_blocks[-1][2] != start:
                drawn_blocks.append([pid, start, end])
            else: drawn_blocks[-1][2] = end

        drawn_labels = set()
        for pid, start, end in drawn_blocks:
            x0, x1 = margin_l + start * scale, margin_l + end * scale
            c.create_rectangle(x0, bar_y, x1, bar_y + bar_h, fill=pid_color.get(pid, CARD), outline=BG, width=2)
            if x1 - x0 > 24:
                c.create_text((x0+x1)//2, bar_y + bar_h//2, text=pid, fill=BG, font=("Segoe UI", 10, "bold"))
            c.create_line(x0, ax_y, x0, ax_y + 6, fill=BORDER)
            if start not in drawn_labels:
                c.create_text(x0, ax_y + 16, text=str(start), fill=SUBTEXT, font=FONT_TINY)
                drawn_labels.add(start)

        last_t = timeline[-1][2]
        xf = margin_l + last_t * scale
        c.create_line(xf, ax_y, xf, ax_y + 6, fill=BORDER)
        c.create_text(xf, ax_y + 16, text=str(last_t), fill=SUBTEXT, font=FONT_TINY)

        lx, ly = margin_l, bar_y + bar_h + 45
        for pid, col in pid_color.items():
            c.create_rectangle(lx, ly, lx+12, ly+12, fill=col, outline="")
            c.create_text(lx+16, ly+6, text=pid, fill=TEXT, font=FONT_TINY, anchor="w")
            lx += 55

    def _show_stats(self, stats):
        if not stats: return
        avg_w = sum(s["wait"] for s in stats) / len(stats)
        avg_t = sum(s["turnaround"] for s in stats) / len(stats)
        
        # Build formatted table
        lines = ["┌──────┬──────────┬──────────────┐"]
        lines.append("│ PID  │ Waiting  │ Turnaround   │")
        lines.append("├──────┼──────────┼──────────────┤")
        
        for s in stats:
            pid = s['pid'].ljust(4)
            wait = str(s['wait']).ljust(8)
            turnaround = str(s['turnaround']).ljust(12)
            lines.append(f"│ {pid} │ {wait} │ {turnaround} │")
        
        lines.append("└──────┴──────────┴──────────────┘")
        lines.append("")
        lines.append(f"Average Waiting Time    : {avg_w:.2f} ms")
        lines.append(f"Average Turnaround Time : {avg_t:.2f} ms")
        
        self.stats_text.config(state="normal")
        self.stats_text.delete("1.0", "end")
        self.stats_text.insert("end", "\n".join(lines))
        self.stats_text.config(state="disabled")


# ═══════════════════════════════════════════════════════════════════════════
#  2 ─ MEMORY ALLOCATION
# ═══════════════════════════════════════════════════════════════════════════

class MemoryAllocationTab(tk.Frame):
    ALGOS = ["First Fit", "Best Fit", "Worst Fit", "Next Fit"]

    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self.is_running = False
        self._build_ui()

    def _build_ui(self):
        ctrl = tk.Frame(self, bg=PANEL, width=260)
        ctrl.pack(side="left", fill="y", padx=(PAD, 4), pady=PAD)
        ctrl.pack_propagate(False)

        section_label(ctrl, "Memory Allocation").pack(anchor="w", padx=PAD, pady=(PAD, 2))

        tk.Label(ctrl, text="Algorithm", bg=PANEL, fg=SUBTEXT, font=FONT_TINY).pack(anchor="w", padx=PAD)
        self.algo_var = tk.StringVar(value="First Fit")
        ttk.Combobox(ctrl, textvariable=self.algo_var, values=self.ALGOS, state="readonly", font=FONT_BODY).pack(fill="x", padx=PAD, pady=(2, PAD))

        tk.Label(ctrl, text="Memory Blocks (KB)", bg=PANEL, fg=SUBTEXT, font=FONT_TINY).pack(anchor="w", padx=PAD)
        self.blocks_var = tk.StringVar(value="100 500 200 300 600")
        tk.Entry(ctrl, textvariable=self.blocks_var, bg=CARD, fg=TEXT, insertbackground=TEXT, relief="flat", font=FONT_MONO, highlightthickness=1, highlightbackground=BORDER).pack(fill="x", padx=PAD, pady=(2, PAD))

        tk.Label(ctrl, text="Process Sizes (KB)", bg=PANEL, fg=SUBTEXT, font=FONT_TINY).pack(anchor="w", padx=PAD)
        self.procs_var = tk.StringVar(value="212 417 112 426")
        tk.Entry(ctrl, textvariable=self.procs_var, bg=CARD, fg=TEXT, insertbackground=TEXT, relief="flat", font=FONT_MONO, highlightthickness=1, highlightbackground=BORDER).pack(fill="x", padx=PAD, pady=(2, PAD))

        styled_button(ctrl, "Random", self._randomize, WARN).pack(anchor="w", padx=PAD, pady=2)
        self.run_btn = styled_button(ctrl, "▶  Allocate", self._start_simulation, ACCENT)
        self.run_btn.pack(fill="x", padx=PAD, pady=(PAD, 4))

        tk.Label(ctrl, text="Allocation Summary", bg=PANEL, fg=TEXT, font=FONT_H3).pack(anchor="w", padx=PAD, pady=(4, 2))
        self.result_text = tk.Text(ctrl, bg=CARD, fg=TEXT, font=FONT_MONO, height=10, relief="flat", state="disabled", highlightthickness=0, wrap="word", padx=6, pady=4)
        self.result_text.pack(fill="both", expand=True, padx=PAD, pady=(0, PAD))

        right = tk.Frame(self, bg=BG)
        right.pack(side="left", fill="both", expand=True, padx=(4, PAD), pady=PAD)
        self.status_bar = tk.Label(right, text="System Idle", bg=PANEL, fg=SUBTEXT, font=FONT_BODY, anchor="w", padx=10, pady=4)
        self.status_bar.pack(fill="x", pady=(0, 4))
        self.canvas = tk.Canvas(right, bg=CARD, bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

    def _randomize(self):
        blocks = [random.randint(100, 600) for _ in range(5)]
        procs = [random.randint(50, 450) for _ in range(4)]
        self.blocks_var.set(" ".join(map(str, blocks)))
        self.procs_var.set(" ".join(map(str, procs)))

    def _start_simulation(self):
        if self.is_running: return
        try:
            blocks = list(map(int, self.blocks_var.get().split()))
            procs = list(map(int, self.procs_var.get().split()))
        except ValueError:
            messagebox.showwarning("Error", "Enter space-separated integers.")
            return
        if not blocks or not procs:
            messagebox.showwarning("Error", "Inputs cannot be empty.")
            return

        self.is_running = True
        self.run_btn.config(state="disabled", bg=BORDER, text="⏳ Allocating...")
        threading.Thread(target=self._run_engine, args=(blocks, procs), daemon=True).start()

    def _run_engine(self, blocks, procs):
        algo = self.algo_var.get()
        remaining_blocks = list(blocks)
        allocations = [-1] * len(procs)
        last_idx = 0

        for pi, p_size in enumerate(procs):
            chosen_block_idx = -1
            self.status_bar.config(text=f"Scanning partitions for Process {pi+1} ({p_size}KB)...", fg=WARN)

            if algo == "First Fit":
                for bi, b_size in enumerate(remaining_blocks):
                    self._ui_tick(blocks, procs, allocations, scan_block_idx=bi, active_proc_idx=pi)
                    if b_size >= p_size:
                        chosen_block_idx = bi
                        break
            elif algo == "Best Fit":
                best_fit_diff = float('inf')
                for bi, b_size in enumerate(remaining_blocks):
                    self._ui_tick(blocks, procs, allocations, scan_block_idx=bi, active_proc_idx=pi)
                    if b_size >= p_size and (b_size - p_size) < best_fit_diff:
                        best_fit_diff = b_size - p_size
                        chosen_block_idx = bi
                if chosen_block_idx != -1: self._ui_tick(blocks, procs, allocations, scan_block_idx=chosen_block_idx, active_proc_idx=pi)
            elif algo == "Worst Fit":
                worst_fit_diff = -1
                for bi, b_size in enumerate(remaining_blocks):
                    self._ui_tick(blocks, procs, allocations, scan_block_idx=bi, active_proc_idx=pi)
                    if b_size >= p_size and (b_size - p_size) > worst_fit_diff:
                        worst_fit_diff = b_size - p_size
                        chosen_block_idx = bi
                if chosen_block_idx != -1: self._ui_tick(blocks, procs, allocations, scan_block_idx=chosen_block_idx, active_proc_idx=pi)
            elif algo == "Next Fit":
                start = last_idx
                for k in range(len(remaining_blocks)):
                    bi = (start + k) % len(remaining_blocks)
                    self._ui_tick(blocks, procs, allocations, scan_block_idx=bi, active_proc_idx=pi)
                    if remaining_blocks[bi] >= p_size:
                        chosen_block_idx = bi; last_idx = bi
                        break

            if chosen_block_idx != -1:
                allocations[pi] = chosen_block_idx
                remaining_blocks[chosen_block_idx] -= p_size
                self.status_bar.config(text=f"✅ Process {pi+1} allocated to Block {chosen_block_idx+1}!", fg=GREEN)
                self._draw_memory_map(blocks, procs, allocations, scan_block_idx=-1, active_proc_idx=-1)
                time.sleep(0.3)
            else:
                self.status_bar.config(text=f"❌ Process {pi+1} failed to allocate.", fg=DANGER)
                self._draw_memory_map(blocks, procs, allocations, scan_block_idx=-1, active_proc_idx=-1)
                time.sleep(0.3)
            self._update_text_results(blocks, remaining_blocks, procs, allocations)

        self.is_running = False
        self.run_btn.config(state="normal", bg=ACCENT, text="▶  Allocate")
        self.status_bar.config(text="Allocation Mapping Complete", fg=GREEN)

    def _ui_tick(self, blocks, procs, alloc, scan_block_idx=-1, active_proc_idx=-1):
        self._draw_memory_map(blocks, procs, alloc, scan_block_idx, active_proc_idx)
        time.sleep(0.5)

    BLOCK_COLORS = ["#7c6af7", "#38c9b0", "#f7c26a", "#f76a6a", "#6af7a1", "#f7a26a"]

    def _draw_memory_map(self, blocks, procs, alloc, scan_block_idx, active_proc_idx):
        c = self.canvas; c.delete("all")
        W, H = c.winfo_width() or 800, c.winfo_height() or 350
        max_b = max(blocks) if blocks else 1
        bar_w, gap = 65, 35
        start_x = (W - (len(blocks) * (bar_w + gap))) // 2
        top_y, bottom_y = 60, H - 70

        c.create_text(W//2, 22, text=f"Memory Spaces Partition Map — {self.algo_var.get()}", fill=TEXT, font=FONT_H3)

        for i, block in enumerate(blocks):
            x = start_x + i * (bar_w + gap)
            bh = int((block / max_b) * (bottom_y - top_y))
            by = bottom_y - bh
            border_color = ACCENT2 if i == scan_block_idx else BORDER
            line_w = 2 if i == scan_block_idx else 1

            c.create_rectangle(x, by, x+bar_w, bottom_y, fill="#2a2d40", outline=border_color, width=line_w)
            c.create_text(x + bar_w//2, by - 14, text=f"{block}KB", fill=SUBTEXT, font=FONT_TINY)
            c.create_text(x + bar_w//2, bottom_y + 14, text=f"Block {i+1}", fill=TEXT, font=("Segoe UI", 9, "bold"))

            block_height = bottom_y - by
            proc_indices_in_block = [pi for pi, bi in enumerate(alloc) if bi == i]
            
            if proc_indices_in_block:
                total_proc_size = sum(procs[pi] for pi in proc_indices_in_block)
                current_occupied_offset = 0
                
                for idx, pi in enumerate(proc_indices_in_block):
                    proc_size = procs[pi]

                    if idx == len(proc_indices_in_block) - 1:
                        proc_h = block_height - current_occupied_offset
                    else:
                        proc_h = max(1, int((proc_size / total_proc_size) * block_height))
                    
                    py1 = bottom_y - current_occupied_offset
                    py0 = py1 - proc_h
                    
                    c.create_rectangle(x+2, py0+2, x+bar_w-2, py1-2, fill=self.BLOCK_COLORS[pi % len(self.BLOCK_COLORS)], outline="")
                    c.create_text(x + bar_w//2, (py0 + py1)//2, text=f"P{pi+1}\n{proc_size}KB", fill=BG, font=("Segoe UI", 8, "bold"), justify="center")
                    current_occupied_offset += proc_h

        if active_proc_idx != -1 and scan_block_idx != -1:
            cx_target = start_x + scan_block_idx * (bar_w + gap) + bar_w // 2
            c.create_text(cx_target, top_y - 30, text=f"Testing P{active_proc_idx+1}?", fill=WARN, font=FONT_TINY)

        lx, ly = 20, H - 20
        for pi, size in enumerate(procs):
            c.create_rectangle(lx, ly-8, lx+10, ly+2, fill=self.BLOCK_COLORS[pi % len(self.BLOCK_COLORS)], outline="")
            bi = alloc[pi]
            status = f"In Block {bi+1}" if bi != -1 else ("Pending..." if pi == active_proc_idx else "Not Allocated")
            c.create_text(lx+14, ly-3, text=f"P{pi+1} ({size}KB) → {status}", fill=TEXT, font=FONT_TINY, anchor="w")
            lx += 170

    def _update_text_results(self, blocks, remaining_blocks, procs, alloc):
        lines = [f"{'Process':<10}{'Size':<10}{'Block':<10}{'Status'}", "─" * 45]
        for i, (size, bi) in enumerate(zip(procs, alloc)):
            status = f"B{bi+1} (Frag {remaining_blocks[bi]}KB)" if bi != -1 else "✗ Out of Space"
            lines.append(f"P{i+1:<9}{size:<10}{bi+1 if bi!=-1 else '-':<10}{status}")
        lines.append(f"\n  Allocated: {sum(1 for b in alloc if b != -1)}/{len(procs)}")
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("end", "\n".join(lines))
        self.result_text.config(state="disabled")


# ═══════════════════════════════════════════════════════════════════════════
#  3 ─ VIRTUAL MEMORY
# ═══════════════════════════════════════════════════════════════════════════

class VirtualMemoryTab(tk.Frame):
    ALGOS = ["FIFO", "LRU", "MRU", "Optimal"]

    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self.is_running = False
        self._build_ui()

    def _build_ui(self):
        ctrl = tk.Frame(self, bg=PANEL, width=270)
        ctrl.pack(side="left", fill="y", padx=(PAD, 4), pady=PAD)
        ctrl.pack_propagate(False)

        section_label(ctrl, "Virtual Memory").pack(anchor="w", padx=PAD, pady=(PAD, 2))

        tk.Label(ctrl, text="Algorithm", bg=PANEL, fg=SUBTEXT, font=FONT_TINY).pack(anchor="w", padx=PAD)
        self.algo_var = tk.StringVar(value="FIFO")
        ttk.Combobox(ctrl, textvariable=self.algo_var, values=self.ALGOS, state="readonly", font=FONT_BODY).pack(fill="x", padx=PAD, pady=(2, PAD))

        tk.Label(ctrl, text="Frame Count", bg=PANEL, fg=SUBTEXT, font=FONT_TINY).pack(anchor="w", padx=PAD)
        self.frames_var = tk.StringVar(value="3")
        tk.Entry(ctrl, textvariable=self.frames_var, width=6, bg=CARD, fg=TEXT, insertbackground=TEXT, relief="flat", font=FONT_MONO, highlightthickness=1, highlightbackground=BORDER).pack(anchor="w", padx=PAD, pady=(2, PAD))

        tk.Label(ctrl, text="Reference String (space-separated)", bg=PANEL, fg=SUBTEXT, font=FONT_TINY).pack(anchor="w", padx=PAD)
        self.ref_var = tk.StringVar(value="7 0 1 2 0 3 0 4 2 3 0 3 2 1 2 0 1 7 0 1")
        tk.Entry(ctrl, textvariable=self.ref_var, bg=CARD, fg=TEXT, insertbackground=TEXT, relief="flat", font=FONT_MONO, highlightthickness=1, highlightbackground=BORDER).pack(fill="x", padx=PAD, pady=(2, PAD))

        styled_button(ctrl, "Random String", self._randomize, WARN).pack(anchor="w", padx=PAD, pady=2)
        self.run_btn = styled_button(ctrl, "▶  Simulate", self._start_simulation, ACCENT)
        self.run_btn.pack(fill="x", padx=PAD, pady=(PAD, 4))

        tk.Label(ctrl, text="Page Replacement Stats", bg=PANEL, fg=TEXT, font=FONT_H3).pack(anchor="w", padx=PAD, pady=(4, 2))
        self.stats_text = tk.Text(ctrl, bg=CARD, fg=TEXT, font=FONT_MONO, height=6, relief="flat", state="disabled", highlightthickness=0, wrap="word", padx=6, pady=4)
        self.stats_text.pack(fill="both", expand=True, padx=PAD, pady=(0, 4))

        tk.Label(ctrl, text="Step Log", bg=PANEL, fg=SUBTEXT, font=FONT_TINY).pack(anchor="w", padx=PAD, pady=(4, 2))
        self.log_text = tk.Text(ctrl, bg=CARD, fg=TEXT, font=("Consolas", 8), height=8, relief="flat", state="disabled", highlightthickness=0)
        self.log_text.pack(fill="both", expand=True, padx=PAD, pady=(0, PAD))

        right = tk.Frame(self, bg=BG)
        right.pack(side="left", fill="both", expand=True, padx=(4, PAD), pady=PAD)
        self.status_bar = tk.Label(right, text="System Idle", bg=PANEL, fg=SUBTEXT, font=FONT_BODY, anchor="w", padx=10, pady=4)
        self.status_bar.pack(fill="x", pady=(0, 4))
        self.canvas = tk.Canvas(right, bg=CARD, bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

    def _randomize(self):
        self.ref_var.set(" ".join([str(random.randint(0, 7)) for _ in range(15)]))

    def _start_simulation(self):
        if self.is_running: return
        try:
            refs = list(map(int, self.ref_var.get().split()))
            frames = int(self.frames_var.get())
        except ValueError:
            messagebox.showwarning("Error", "Invalid input.")
            return
        if not refs or frames <= 0:
            messagebox.showwarning("Error", "Provide a valid reference string and frame count > 0.")
            return

        self.is_running = True
        self.run_btn.config(state="disabled", bg=BORDER, text="⏳ Simulating...")
        self.log_lines = []
        threading.Thread(target=self._run_engine, args=(refs, frames), daemon=True).start()

    def _run_engine(self, refs, frames):
        algo = self.algo_var.get()
        history, faults = [], []

        if algo == "FIFO": self._animate_fifo(refs, frames, history, faults)
        elif algo == "LRU": self._animate_lru(refs, frames, history, faults)
        elif algo == "MRU": self._animate_mru(refs, frames, history, faults)
        else: self._animate_optimal(refs, frames, history, faults)

        self.is_running = False
        self.run_btn.config(state="normal", bg=ACCENT, text="▶  Simulate")
        self.status_bar.config(text="Simulation Complete", fg=GREEN)
        total_faults = sum(faults)
        hit_rate = ((len(refs)-total_faults)/len(refs))*100
        
        # Update stats panel
        lines = ["─────────────────────────────────"]
        lines.append(f" Page Faults  : {total_faults:<18}   ")
        lines.append(f" Page Hits    : {len(refs)-total_faults:<18}")
        lines.append(f" Hit Rate     : {hit_rate:>5.1f}%    ")
        lines.append("────────────────────────────")
        
        self.stats_text.config(state="normal")
        self.stats_text.delete("1.0", "end")
        self.stats_text.insert("end", "\n".join(lines))
        self.stats_text.config(state="disabled")

    def _animate_fifo(self, refs, n, history, faults):
        queue = deque()
        for idx, p in enumerate(refs):
            fault = p not in queue
            if fault:
                if len(queue) == n: queue.popleft()
                queue.append(p)
            faults.append(fault)
            history.append(list(queue))
            self._ui_tick(refs[:idx+1], history, faults, n, current_step=idx)

    def _animate_lru(self, refs, n, history, faults):
        frames = OrderedDict()
        for idx, p in enumerate(refs):
            fault = p not in frames
            if fault:
                if len(frames) == n: frames.popitem(last=False)
                frames[p] = True
            else: frames.move_to_end(p)
            faults.append(fault)
            history.append(list(frames.keys()))
            self._ui_tick(refs[:idx+1], history, faults, n, current_step=idx)

    def _animate_mru(self, refs, n, history, faults):
        frames = OrderedDict()
        for idx, p in enumerate(refs):
            fault = p not in frames
            if fault:
                if len(frames) == n: frames.popitem(last=True)
                frames[p] = True
            else: frames.move_to_end(p)
            faults.append(fault)
            history.append(list(frames.keys()))
            self._ui_tick(refs[:idx+1], history, faults, n, current_step=idx)

    def _animate_optimal(self, refs, n, history, faults):
        frames = []
        for idx, p in enumerate(refs):
            fault = p not in frames
            if fault:
                if len(frames) == n:
                    future = {}
                    for f in frames:
                        try: future[f] = refs[idx+1:].index(f)
                        except ValueError: future[f] = float('inf')
                    frames.remove(max(future, key=future.get))
                frames.append(p)
            faults.append(fault)
            history.append(list(frames))
            self._ui_tick(refs[:idx+1], history, faults, n, current_step=idx)

    def _ui_tick(self, current_refs, history, faults, n_frames, current_step):
        last_ref, is_fault = current_refs[-1], faults[-1]
        self.status_bar.config(text=f"Step {current_step + 1} | Referencing Page: {last_ref} -> {'FAULT' if is_fault else 'HIT'}", fg=DANGER if is_fault else GREEN)
        self.log_lines.append(f"[{current_step+1:>2}] Ref: {last_ref} | Frames: {str(history[-1]).ljust(18)} | {'❌ FAULT' if is_fault else '✅ HIT'}")
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.insert("end", "\n".join(self.log_lines))
        self.log_text.see("end")
        self.log_text.config(state="disabled")
        self._draw_matrix(current_refs, history, faults, n_frames)
        time.sleep(0.15)

    def _draw_matrix(self, refs, history, faults, n_frames):
        c = self.canvas; c.delete("all")
        W, H = c.winfo_width() or 800, c.winfo_height() or 350
        c.create_text(W//2, 18, text=f"Page Replacement Grid Stream — {self.algo_var.get()}", fill=TEXT, font=FONT_H3)
        cell_w = max(28, min(48, (W - 100) // max(len(self.ref_var.get().split()), len(refs))))
        start_x, frame_y_start = 55, 50
        palette = [ACCENT, ACCENT2, WARN, "#f7a26a", "#a26af7", "#6ab8f7"]
        colors_map = {}

        for step, (ref, state, fault) in enumerate(zip(refs, history, faults)):
            x = start_x + step * cell_w
            if step == len(refs) - 1:
                c.create_rectangle(x, frame_y_start + 10, x + cell_w, frame_y_start + n_frames * 40 + 45, outline=BORDER, fill="")
            c.create_text(x + cell_w//2, 38, text=str(ref), fill=DANGER if fault else GREEN, font=("Consolas", 10, "bold"))
            
            for fi in range(n_frames):
                fy = frame_y_start + fi * 40 + 20
                if fi < len(state):
                    page = state[fi]
                    if page not in colors_map: colors_map[page] = palette[len(colors_map) % len(palette)]
                    c.create_rectangle(x+2, fy, x+cell_w-2, fy+36, fill=colors_map[page], outline=BG, width=1)
                    c.create_text(x + cell_w//2, fy + 18, text=str(page), fill=BG, font=("Consolas", 10, "bold"))
                else:
                    c.create_rectangle(x+2, fy, x+cell_w-2, fy+36, fill="#1e2133", outline=BORDER, width=1)
            if fault: c.create_text(x + cell_w//2, frame_y_start + n_frames * 40 + 30, text="F", fill=DANGER, font=("Consolas", 9, "bold"))
            else: c.create_text(x + cell_w//2, frame_y_start + n_frames * 40 + 30, text="•", fill=GREEN, font=("Consolas", 12, "bold"))

        for fi in range(n_frames): c.create_text(32, frame_y_start + fi * 40 + 38, text=f"Slot {fi+1}", fill=SUBTEXT, font=FONT_TINY)
        c.create_text(32, frame_y_start + n_frames * 40 + 30, text="State", fill=SUBTEXT, font=FONT_TINY)


# ═══════════════════════════════════════════════════════════════════════════
#  4 ─ MASS STORAGE (DISK SCHEDULING)
# ═══════════════════════════════════════════════════════════════════════════

class MassStorageTab(tk.Frame):
    ALGOS = ["FCFS", "SSTF", "SCAN", "C-SCAN", "LOOK", "C-LOOK"]

    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self.is_running = False
        self._build_ui()

    def _build_ui(self):
        ctrl = tk.Frame(self, bg=PANEL, width=270)
        ctrl.pack(side="left", fill="y", padx=(PAD, 4), pady=PAD)
        ctrl.pack_propagate(False)

        section_label(ctrl, "Disk Scheduling").pack(anchor="w", padx=PAD, pady=(PAD, 2))
        info_label(ctrl, "Visualize how the disk head moves across cylinders to service I/O requests.").pack(anchor="w", padx=PAD, pady=(0, PAD))

        tk.Label(ctrl, text="Algorithm", bg=PANEL, fg=SUBTEXT, font=FONT_TINY).pack(anchor="w", padx=PAD)
        self.algo_var = tk.StringVar(value="FCFS")
        ttk.Combobox(ctrl, textvariable=self.algo_var, values=self.ALGOS, state="readonly", font=FONT_BODY).pack(fill="x", padx=PAD, pady=(2, PAD))

        r1, self.head_var = entry_row(ctrl, "Initial Head Position", "53", 6)
        r1.pack(anchor="w", padx=PAD, pady=2)
        r2, self.max_var = entry_row(ctrl, "Max Cylinder", "199", 6)
        r2.pack(anchor="w", padx=PAD, pady=2)

        self.dir_frame = tk.Frame(ctrl, bg=PANEL)
        self.dir_frame.pack(anchor="w", padx=PAD, pady=2)
        tk.Label(self.dir_frame, text="Initial Direction:", bg=PANEL, fg=SUBTEXT, font=FONT_TINY).pack(side="left")
        self.dir_var = tk.StringVar(value="right")
        tk.Radiobutton(self.dir_frame, text="→", variable=self.dir_var, value="right", bg=PANEL, fg=TEXT, selectcolor=CARD, font=FONT_TINY).pack(side="left")
        tk.Radiobutton(self.dir_frame, text="←", variable=self.dir_var, value="left", bg=PANEL, fg=TEXT, selectcolor=CARD, font=FONT_TINY).pack(side="left")

        tk.Label(ctrl, text="Request Queue (space-separated)", bg=PANEL, fg=SUBTEXT, font=FONT_TINY).pack(anchor="w", padx=PAD, pady=(PAD, 0))
        self.req_var = tk.StringVar(value="98 183 37 122 14 124 65 67")
        tk.Entry(ctrl, textvariable=self.req_var, bg=CARD, fg=TEXT, insertbackground=TEXT, relief="flat", font=FONT_MONO, highlightthickness=1, highlightbackground=BORDER).pack(fill="x", padx=PAD, pady=(2, PAD))

        styled_button(ctrl, "Random", self._randomize, WARN).pack(anchor="w", padx=PAD, pady=2)
        self.run_btn = styled_button(ctrl, "▶  Simulate", self._start_simulation, ACCENT)
        self.run_btn.pack(fill="x", padx=PAD, pady=(PAD, 4))

        tk.Label(ctrl, text="Disk Seek Summary", bg=PANEL, fg=TEXT, font=FONT_H3).pack(anchor="w", padx=PAD, pady=(4, 2))
        self.stats_text = tk.Text(ctrl, bg=CARD, fg=TEXT, font=FONT_MONO, height=10, relief="flat", state="disabled", highlightthickness=0, wrap="word", padx=6, pady=4)
        self.stats_text.pack(fill="both", expand=True, padx=PAD, pady=(0, PAD))

        right = tk.Frame(self, bg=BG)
        right.pack(side="left", fill="both", expand=True, padx=(4, PAD), pady=PAD)
        self.status_bar = tk.Label(right, text="System Idle", bg=PANEL, fg=SUBTEXT, font=FONT_BODY, anchor="w", padx=10, pady=4)
        self.status_bar.pack(fill="x", pady=(0, 4))
        self.canvas = tk.Canvas(right, bg=CARD, bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

    def _randomize(self):
        try: m = int(self.max_var.get())
        except: m = 199
        self.req_var.set(" ".join(map(str, sorted(random.sample(range(0, m+1), min(8, m+1))))))
        self.head_var.set(str(random.randint(0, m)))

    def _start_simulation(self):
        if self.is_running: return
        try:
            head = int(self.head_var.get())
            max_c = int(self.max_var.get())
            reqs = list(map(int, self.req_var.get().split()))
        except ValueError:
            messagebox.showwarning("Error", "Invalid input.")
            return

        self.is_running = True
        self.run_btn.config(state="disabled", bg=BORDER, text="⏳ Seeking...")
        threading.Thread(target=self._run_engine, args=(reqs, head, max_c), daemon=True).start()

    def _run_engine(self, reqs, head, max_c):
        algo = self.algo_var.get()
        direction = self.dir_var.get()
        
        # Core Schedule Calculators
        if algo == "FCFS": order = list(reqs)
        elif algo == "SSTF":
            order, rem, cur = [], list(reqs), head
            while rem:
                nxt = min(rem, key=lambda x: abs(x - cur))
                order.append(nxt); rem.remove(nxt); cur = nxt
        elif algo in ("SCAN", "LOOK"):
            left, right = sorted([r for r in reqs if r < head], reverse=True), sorted([r for r in reqs if r >= head])
            if algo == "SCAN": order = (right + [max_c] + left) if direction == "right" else (left + [0] + right)
            else: order = (right + left) if direction == "right" else (left + right)
        elif algo in ("C-SCAN", "C-LOOK"):
            right, left = sorted([r for r in reqs if r >= head]), sorted([r for r in reqs if r < head])
            order = (right + [max_c, 0] + left) if algo == "C-SCAN" else (right + left)
        else: order = list(reqs)

        steps = [head] + order
        total_movement = sum(abs(steps[i+1] - steps[i]) for i in range(len(steps)-1))
        
        # Incremental dynamic UI streaming plot loop
        for idx in range(1, len(steps) + 1):
            current_path = steps[:idx]
            self.status_bar.config(text=f"Seeking Cylinder: {current_path[-1]} (Track Step {idx-1}/{len(steps)-1})", fg=WARN)
            self._draw_graph(current_path, max_c, final_len=len(steps))
            time.sleep(0.6)

        self.is_running = False
        self.run_btn.config(state="normal", bg=ACCENT, text="▶  Simulate")
        self.status_bar.config(text="Head Scan Sequence Complete", fg=GREEN)
        
        # Update stats panel
        lines = ["┌─────────────────────────────┐"]
        lines.append(f"│ Total Movement: {total_movement:<16} │")
        lines.append(f"│ Requests Served: {len(reqs):<15} │")
        lines.append("├─────────────────────────────┤")
        lines.append(f"│ Service Order:              │")
        service_order = " → ".join(map(str, [o for o in order if o in reqs]))
        lines.append(f"│ {service_order[:26]:<27} │")
        if len(service_order) > 26:
            lines.append(f"│ {service_order[26:]:<27} │")
        lines.append("└─────────────────────────────┘")
        
        self.stats_text.config(state="normal")
        self.stats_text.delete("1.0", "end")
        self.stats_text.insert("end", "\n".join(lines))
        self.stats_text.config(state="disabled")

    def _draw_graph(self, path, max_c, final_len):
        c = self.canvas; c.delete("all")
        W, H = c.winfo_width() or 800, c.winfo_height() or 350
        c.create_text(W//2, 18, text=f"Disk Head Seek Path Plot — {self.algo_var.get()}", fill=TEXT, font=FONT_H3)

        ml, mr, mt, mb = 80, 40, 50, 40
        plot_w, plot_h = W - ml - mr, H - mt - mb
        x_step = plot_w / max(final_len - 1, 1)

        def cx(i): return ml + i * x_step
        def cy(val): return mt + plot_h - (val / max_c) * plot_h

        for tick in range(0, max_c+1, max(1, max_c//10)):
            y = cy(tick)
            c.create_line(ml-4, y, ml, y, fill=BORDER)
            c.create_text(ml-8, y, text=str(tick), fill=SUBTEXT, font=FONT_TINY, anchor="e")
        c.create_line(ml, mt, ml, mt+plot_h, fill=BORDER, width=1)
        c.create_line(ml, mt+plot_h, ml+plot_w, mt+plot_h, fill=BORDER, width=1)

        for i in range(final_len):
            c.create_text(cx(i), mt+plot_h+14, text="Start" if i == 0 else str(i), fill=SUBTEXT, font=FONT_TINY)

        for i in range(len(path)-1):
            c.create_line(cx(i), cy(path[i]), cx(i+1), cy(path[i+1]), fill=ACCENT, width=2)

        for i, val in enumerate(path):
            col = WARN if i == 0 else (ACCENT2 if i == len(path)-1 else ACCENT)
            c.create_oval(cx(i)-6, cy(val)-6, cx(i)+6, cy(val)+6, fill=col, outline=BG, width=2)
            c.create_text(cx(i), cy(val)-16, text=str(val), fill=col, font=FONT_TINY)
        c.create_text(14, mt + plot_h//2, text="Cylinder ID", fill=SUBTEXT, font=FONT_TINY, angle=90)


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN APPLICATION ENTRYPOINT
# ═══════════════════════════════════════════════════════════════════════════

class OSVisualizerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("OS Algorithm Visualizer")
        self.geometry("1100x700")
        self.resizable(False, False)
        self.wm_state("zoomed")
        self.configure(bg=BG)
        self._apply_theme()
        self._build_ui()

    def _apply_theme(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground=CARD, background=CARD, foreground=TEXT,
                        selectbackground=ACCENT, selectforeground=TEXT, bordercolor=BORDER, arrowcolor=SUBTEXT, relief="flat")
        style.map("TCombobox", fieldbackground=[("readonly", CARD)], foreground=[("readonly", TEXT)])
        style.configure("Custom.TNotebook", background=BG, borderwidth=0, tabmargins=0)
        style.configure("Custom.TNotebook.Tab", background=PANEL, foreground=SUBTEXT, padding=[16, 8], font=FONT_BODY, borderwidth=0)
        style.map("Custom.TNotebook.Tab", background=[("selected", CARD)], foreground=[("selected", TEXT)])

    def _build_ui(self):
        hdr = tk.Frame(self, bg=PANEL, height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Scheduling Algorithm Visualizer", bg=PANEL, fg=TEXT, font=FONT_H1).pack(pady=10)

        nb = ttk.Notebook(self, style="Custom.TNotebook")
        nb.pack(fill="both", expand=True, padx=0, pady=0)

        tabs = [
            ("🖥  CPU Scheduling",   CPUSchedulingTab),
            ("🗃  Memory Allocation", MemoryAllocationTab),
            ("📄  Virtual Memory",    VirtualMemoryTab),
            ("💽  Disk Scheduling",   MassStorageTab),
        ]
        for name, cls in tabs:
            nb.add(cls(nb), text=name)

        status = tk.Frame(self, bg=PANEL, height=24)
        status.pack(fill="x", side="bottom")
        tk.Label(status, text="Select a tab, configure parameters, then click ▶ Run / Simulate", bg=PANEL, fg=SUBTEXT, font=FONT_TINY).pack(side="left", padx=12)

def main():
    app = OSVisualizerApp()
    app.mainloop()

if __name__ == "__main__":
    main()
