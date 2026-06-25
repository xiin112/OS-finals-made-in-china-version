"""
OS Algorithm Visualizer
========================
Visualizes core Operating System algorithms:
  1. CPU Scheduling (FCFS, SJF, Priority, Round Robin)
  2. Memory Allocation (First Fit, Best Fit, Worst Fit, Next Fit)
  3. Virtual Memory / Page Replacement (FIFO, LRU, Optimal)
  4. Mass Storage Management (FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK)

Run with:  python3 app_visualizer.py
Requires:  Python 3.8+ with tkinter (bundled with most Python installs)
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
BG        = "#0f1117"
PANEL     = "#1a1d27"
CARD      = "#22263a"
ACCENT    = "#7c6af7"      # soft violet
ACCENT2   = "#38c9b0"      # teal
WARN      = "#f7c26a"      # amber
DANGER    = "#f76a6a"      # red
TEXT      = "#e8eaf6"
SUBTEXT   = "#8b8fa8"
BORDER    = "#2e3148"
GREEN     = "#6af7a1"

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
    return tk.Label(parent, text=text, bg=PANEL, fg=TEXT,
                    font=FONT_H2, **kwargs)

def info_label(parent, text, color=SUBTEXT, **kwargs):
    return tk.Label(parent, text=text, bg=PANEL, fg=color,
                    font=FONT_TINY, wraplength=520, justify="left", **kwargs)

def card_frame(parent, **kwargs):
    return tk.Frame(parent, bg=CARD, bd=0, relief="flat",
                    highlightthickness=1, highlightbackground=BORDER, **kwargs)

def entry_row(parent, label, default="", width=8):
    f = tk.Frame(parent, bg=PANEL)
    tk.Label(f, text=label, bg=PANEL, fg=SUBTEXT,
             font=FONT_TINY).pack(side="left", padx=(0, 4))
    v = tk.StringVar(value=default)
    e = tk.Entry(f, textvariable=v, width=width,
                 bg=CARD, fg=TEXT, insertbackground=TEXT,
                 relief="flat", font=FONT_MONO,
                 highlightthickness=1, highlightbackground=BORDER)
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
        # ── Left controls ──
        ctrl = tk.Frame(self, bg=PANEL, width=260)
        ctrl.pack(side="left", fill="y", padx=(PAD, 4), pady=PAD)
        ctrl.pack_propagate(False)

        section_label(ctrl, "CPU Scheduling").pack(anchor="w", padx=PAD, pady=(PAD, 2))
        info_label(ctrl, "Simulate how the OS picks which process runs next on the CPU.").pack(anchor="w", padx=PAD, pady=(0, PAD))

        # Algorithm picker
        tk.Label(ctrl, text="Algorithm", bg=PANEL, fg=SUBTEXT, font=FONT_TINY).pack(anchor="w", padx=PAD)
        self.algo_var = tk.StringVar(value=self.ALGOS[0])
        cb = ttk.Combobox(ctrl, textvariable=self.algo_var, values=self.ALGOS, state="readonly", font=FONT_BODY)
        cb.pack(fill="x", padx=PAD, pady=(2, PAD))
        cb.bind("<<ComboboxSelected>>", self._on_algo_change)

        # RR quantum
        self.rr_frame = tk.Frame(ctrl, bg=PANEL)
        self.rr_frame.pack(fill="x", padx=PAD)
        tk.Label(self.rr_frame, text="Time Quantum", bg=PANEL, fg=SUBTEXT, font=FONT_TINY).pack(anchor="w")
        self.quantum_var = tk.StringVar(value="2")
        tk.Entry(self.rr_frame, textvariable=self.quantum_var, width=6,
                 bg=CARD, fg=TEXT, insertbackground=TEXT, relief="flat", font=FONT_MONO,
                 highlightthickness=1, highlightbackground=BORDER).pack(anchor="w", pady=2)
        self.rr_frame.pack_forget()

        # Process table header
        tk.Label(ctrl, text="Processes", bg=PANEL, fg=SUBTEXT, font=FONT_TINY).pack(anchor="w", padx=PAD, pady=(PAD, 0))
        hdr = tk.Frame(ctrl, bg=PANEL)
        hdr.pack(fill="x", padx=PAD)
        for h, w in [("PID", 4), ("Arrival", 6), ("Burst", 5), ("Priority", 7)]:
            tk.Label(hdr, text=h, bg=PANEL, fg=SUBTEXT, font=FONT_TINY, width=w).pack(side="left")

        self.proc_rows = []
        self.row_container = tk.Frame(ctrl, bg=PANEL)
        self.row_container.pack(fill="x", padx=PAD)
        for i in range(5):  # Adjusted slightly for clean layout space
            self._add_row(i)

        btn_f = tk.Frame(ctrl, bg=PANEL)
        btn_f.pack(fill="x", padx=PAD, pady=PAD)
        styled_button(btn_f, "+ Row", self._add_process, ACCENT2).pack(side="left", padx=2)
        styled_button(btn_f, "Random", self._randomize, WARN).pack(side="left", padx=2)

        self.run_btn = styled_button(ctrl, "▶  Run Animation", self._start_simulation, ACCENT)
        self.run_btn.pack(fill="x", padx=PAD, pady=(0, PAD))

        # Results area
        self.stats_label = tk.Label(ctrl, text="", bg=PANEL, fg=ACCENT2, font=FONT_TINY, justify="left", wraplength=230)
        self.stats_label.pack(anchor="w", padx=PAD)

        # ── Right Canvas Frame ──
        right = tk.Frame(self, bg=BG)
        right.pack(side="left", fill="both", expand=True, padx=(4, PAD), pady=PAD)

        # Live Status bar right above Canvas
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
                    "pid": pid_v.get(),
                    "arrival": int(arr_v.get()),
                    "burst": int(burst_v.get()),
                    "priority": int(prio_v.get()),
                })
            except ValueError:
                continue
        return procs

    COLORS = ["#7c6af7", "#38c9b0", "#f7c26a", "#f76a6a", "#6af7a1", "#f7a26a", "#a26af7", "#6ab8f7"]

    def _start_simulation(self):
        if self.is_running:
            return
        procs = self._get_processes()
        if not procs:
            messagebox.showwarning("No Data", "Add at least one process.")
            return

        self.is_running = True
        self.run_btn.config(state="disabled", bg=BORDER, text="⏳ Running...")
        
        # Calculate maximum possible runtime scale bound
        total_burst = sum(p["burst"] for p in procs)
        max_arrival = max(p["arrival"] for p in procs)
        self.max_time_bound = max_arrival + total_burst + 5 

        # Fire off animation onto its own thread to keep UI unfrozen
        threading.Thread(target=self._run_engine, args=(procs,), daemon=True).start()

    def _run_engine(self, procs):
        algo = self.algo_var.get()
        timeline = []
        stats = []

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

        # Re-enable execute triggers
        self.is_running = False
        self.run_btn.config(state="normal", bg=ACCENT, text="▶  Run Animation")
        self.status_bar.config(text="Simulation Complete", fg=GREEN)
        self._show_stats(stats)

    # ── Animated Step Engines ───────────────────────────────────────────────
    
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
                # Peek at incoming elements while processing
                current_ready = ready_pids + [r["pid"] for r in remaining if r["arrival"] <= t and r not in available]
                self._ui_tick(timeline, t, active_pid=p["pid"], ready_queue=current_ready)
                
            stats.append({"pid": p["pid"], "wait": start - p["arrival"], "turnaround": t - p["arrival"]})
            remaining.


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
        info_label(ctrl, "Allocate process memory into fixed-size memory blocks.").pack(
            anchor="w", padx=PAD, pady=(0, PAD))

        tk.Label(ctrl, text="Algorithm", bg=PANEL, fg=SUBTEXT, font=FONT_TINY).pack(anchor="w", padx=PAD)
        self.algo_var = tk.StringVar(value="First Fit")
        ttk.Combobox(ctrl, textvariable=self.algo_var, values=self.ALGOS,
                     state="readonly", font=FONT_BODY).pack(fill="x", padx=PAD, pady=(2, PAD))

        # Memory blocks
        tk.Label(ctrl, text="Memory Blocks (KB)", bg=PANEL, fg=SUBTEXT, font=FONT_TINY).pack(anchor="w", padx=PAD)
        self.blocks_var = tk.StringVar(value="100 500 200 300 600")
        tk.Entry(ctrl, textvariable=self.blocks_var, bg=CARD, fg=TEXT,
                 insertbackground=TEXT, relief="flat", font=FONT_MONO,
                 highlightthickness=1, highlightbackground=BORDER).pack(fill="x", padx=PAD, pady=(2, PAD))

        # Process sizes
        tk.Label(ctrl, text="Process Sizes (KB)", bg=PANEL, fg=SUBTEXT, font=FONT_TINY).pack(anchor="w", padx=PAD)
        self.procs_var = tk.StringVar(value="212 417 112 426")
        tk.Entry(ctrl, textvariable=self.procs_var, bg=CARD, fg=TEXT,
                 insertbackground=TEXT, relief="flat", font=FONT_MONO,
                 highlightthickness=1, highlightbackground=BORDER).pack(fill="x", padx=PAD, pady=(2, PAD))

        styled_button(ctrl, "Random", self._randomize, WARN).pack(anchor="w", padx=PAD, pady=2)
        self.run_btn = styled_button(ctrl, "▶  Allocate", self._start_simulation, ACCENT)
        self.run_btn.pack(fill="x", padx=PAD, pady=(PAD, 0))

        self.result_text = tk.Text(ctrl, bg=CARD, fg=TEXT, font=FONT_TINY,
                                   height=12, relief="flat", state="disabled", highlightthickness=0)
        self.result_text.pack(fill="x", padx=PAD, pady=PAD)

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
        last_idx = 0  # Support track for Next Fit pointer bounds

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
                if chosen_block_idx != -1:
                    self._ui_tick(blocks, procs, allocations, scan_block_idx=chosen_block_idx, active_proc_idx=pi)

            elif algo == "Worst Fit":
                worst_fit_diff = -1
                for bi, b_size in enumerate(remaining_blocks):
                    self._ui_tick(blocks, procs, allocations, scan_block_idx=bi, active_proc_idx=pi)
                    if b_size >= p_size and (b_size - p_size) > worst_fit_diff:
                        worst_fit_diff = b_size - p_size
                        chosen_block_idx = bi
                if chosen_block_idx != -1:
                    self._ui_tick(blocks, procs, allocations, scan_block_idx=chosen_block_idx, active_proc_idx=pi)

            elif algo == "Next Fit":
                start = last_idx
                for k in range(len(remaining_blocks)):
                    bi = (start + k) % len(remaining_blocks)
                    self._ui_tick(blocks, procs, allocations, scan_block_idx=bi, active_proc_idx=pi)
                    if remaining_blocks[bi] >= p_size:
                        chosen_block_idx = bi
                        last_idx = bi
                        break

            if chosen_block_idx != -1:
                allocations[pi] = chosen_block_idx
                remaining_blocks[chosen_block_idx] -= p_size
                self.status_bar.config(text=f"✅ Process {pi+1} allocated to Block {chosen_block_idx+1}!", fg=GREEN)
            else:
                self.status_bar.config(text=f"❌ Process {pi+1} failed to allocate (Insufficent Memory).", fg=DANGER)
            
            time.sleep(0.6)  # Pause to notice settlement bound
            self._update_text_results(blocks, remaining_blocks, procs, allocations)

        self.is_running = False
        self.run_btn.config(state="normal", bg=ACCENT, text="▶  Allocate")
        self.status_bar.config(text="Allocation Mapping Complete", fg=GREEN)

    # ── UI Renderer Sync ────────────────────────────────────────────────────
    
    def _ui_tick(self, blocks, procs, alloc, scan_block_idx=-1, active_proc_idx=-1):
        self._draw_memory_map(blocks, procs, alloc, scan_block_idx, active_proc_idx)
        time.sleep(0.5)

    BLOCK_COLORS = ["#7c6af7", "#38c9b0", "#f7c26a", "#f76a6a", "#6af7a1", "#f7a26a"]

    def _draw_memory_map(self, blocks, procs, alloc, scan_block_idx, active_proc_idx):
        c = self.canvas
        c.delete("all")
        
        W = c.winfo_width() or 800
        H = c.winfo_height() or 350
        max_b = max(blocks) if blocks else 1
        bar_w = 65
        gap = 35
        total_w = len(blocks) * (bar_w + gap)
        start_x = (W - total_w) // 2
        top_y = 60
        bottom_y = H - 70

        c.create_text(W//2, 22, text=f"Memory Spaces Partition Map — {self.algo_var.get()}", fill=TEXT, font=FONT_H3)

        for i, block in enumerate(blocks):
            x = start_x + i * (bar_w + gap)
            bh = int((block / max_b) * (bottom_y - top_y))
            by = bottom_y - bh

            # Evaluate checking border highlights
            border_color = ACCENT2 if i == scan_block_idx else BORDER
            line_w = 2 if i == scan_block_idx else 1

            # Render full base physical structure
            c.create_rectangle(x, by, x+bar_w, bottom_y, fill="#2a2d40", outline=border_color, width=line_w)
            c.create_text(x + bar_w//2, by - 14, text=f"{block}KB", fill=SUBTEXT, font=FONT_TINY)
            c.create_text(x + bar_w//2, bottom_y + 14, text=f"Block {i+1}", fill=TEXT, font=("Segoe UI", 9, "bold"))

            # Calculate slice components inside current slot block
            current_occupied_offset = 0
            for pi, bi in enumerate(alloc):
                if bi == i:
                    proc_size = procs[pi]
                    proc_h = int((proc_size / max_b) * (bottom_y - top_y))
                    
                    py0 = bottom_y - current_occupied_offset - proc_h
                    py1 = bottom_y - current_occupied_offset
                    
                    col = self.BLOCK_COLORS[pi % len(self.BLOCK_COLORS)]
                    c.create_rectangle(x+2, py0+2, x+bar_w-2, py1-2, fill=col, outline="")
                    
                    lbl = f"P{pi+1}\n{proc_size}KB"
                    c.create_text(x + bar_w//2, (py0 + py1)//2, text=lbl, fill=BG, font=("Segoe UI", 8, "bold"), justify="center")
                    
                    current_occupied_offset += proc_h

        # Print active staging evaluation bubble indicators
        if active_proc_idx != -1 and scan_block_idx != -1:
            cx_target = start_x + scan_block_idx * (bar_w + gap) + bar_w // 2
            c.create_text(cx_target, top_y - 30, text=f"Testing P{active_proc_idx+1}?", fill=WARN, font=FONT_TINY)

        # Bottom dynamic placement index definitions
        lx = 20
        ly = H - 20
        for pi, size in enumerate(procs):
            col = self.BLOCK_COLORS[pi % len(self.BLOCK_COLORS)]
            c.create_rectangle(lx, ly-8, lx+10, ly+2, fill=col, outline="")
            
            bi = alloc[pi]
            status = f"In Block {bi+1}" if bi != -1 else ("Pending..." if pi == active_proc_idx else "Not Allocated")
            c.create_text(lx+14, ly-3, text=f"P{pi+1} ({size}KB) → {status}", fill=TEXT, font=FONT_TINY, anchor="w")
            lx += 170

    def _update_text_results(self, blocks, remaining_blocks, procs, alloc):
        lines = [f"{'Process':<10}{'Size':<10}{'Block':<10}{'Status'}"]
        lines.append("─" * 45)
        for i, (size, bi) in enumerate(zip(procs, alloc)):
            if bi != -1:
                status = f"B{bi+1} (Frag {remaining_blocks[bi]}KB)"
            else:
                status = "✗ Out of Space"
            lines.append(f"P{i+1:<9}{size:<10}{bi+1 if bi!=-1 else '-':<10}{status}")
            
        allocated = sum(1 for b in alloc if b != -1)
        lines.append(f"\n  Allocated: {allocated}/{len(procs)}")
        
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("end", "\n".join(lines))
        self.result_text.config(state="disabled")


# ═══════════════════════════════════════════════════════════════════════════
#  3 ─ VIRTUAL MEMORY (ANIMATED DROPIN REPLACEMENT)
# ═══════════════════════════════════════════════════════════════════════════

class VirtualMemoryTab(tk.Frame):
    ALGOS = ["FIFO", "LRU", "Optimal"]

    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self.is_running = False
        self._build_ui()

    def _build_ui(self):
        ctrl = tk.Frame(self, bg=PANEL, width=270)
        ctrl.pack(side="left", fill="y", padx=(PAD, 4), pady=PAD)
        ctrl.pack_propagate(False)

        section_label(ctrl, "Virtual Memory").pack(anchor="w", padx=PAD, pady=(PAD, 2))
        info_label(ctrl, "Page replacement decides which memory page to evict when a page fault occurs.").pack(
            anchor="w", padx=PAD, pady=(0, PAD))

        tk.Label(ctrl, text="Algorithm", bg=PANEL, fg=SUBTEXT, font=FONT_TINY).pack(anchor="w", padx=PAD)
        self.algo_var = tk.StringVar(value="FIFO")
        ttk.Combobox(ctrl, textvariable=self.algo_var, values=self.ALGOS,
                     state="readonly", font=FONT_BODY).pack(fill="x", padx=PAD, pady=(2, PAD))

        tk.Label(ctrl, text="Frame Count", bg=PANEL, fg=SUBTEXT, font=FONT_TINY).pack(anchor="w", padx=PAD)
        self.frames_var = tk.StringVar(value="3")
        tk.Entry(ctrl, textvariable=self.frames_var, width=6, bg=CARD, fg=TEXT,
                 insertbackground=TEXT, relief="flat", font=FONT_MONO,
                 highlightthickness=1, highlightbackground=BORDER).pack(anchor="w", padx=PAD, pady=(2, PAD))

        tk.Label(ctrl, text="Reference String (space-separated)", bg=PANEL,
                 fg=SUBTEXT, font=FONT_TINY).pack(anchor="w", padx=PAD)
        self.ref_var = tk.StringVar(value="7 0 1 2 0 3 0 4 2 3 0 3 2 1 2 0 1 7 0 1")
        tk.Entry(ctrl, textvariable=self.ref_var, bg=CARD, fg=TEXT,
                 insertbackground=TEXT, relief="flat", font=FONT_MONO,
                 highlightthickness=1, highlightbackground=BORDER).pack(
                 fill="x", padx=PAD, pady=(2, PAD))

        styled_button(ctrl, "Random String", self._randomize, WARN).pack(anchor="w", padx=PAD, pady=2)
        self.run_btn = styled_button(ctrl, "▶  Simulate", self._start_simulation, ACCENT)
        self.run_btn.pack(fill="x", padx=PAD, pady=(PAD, 0))

        self.stats_label = tk.Label(ctrl, text="", bg=PANEL, fg=ACCENT2, font=FONT_TINY, justify="left")
        self.stats_label.pack(anchor="w", padx=PAD, pady=PAD)

        # Step-through log
        tk.Label(ctrl, text="Step Log", bg=PANEL, fg=SUBTEXT, font=FONT_TINY).pack(anchor="w", padx=PAD)
        self.log_text = tk.Text(ctrl, bg=CARD, fg=TEXT, font=("Consolas", 8),
                                 height=14, relief="flat", state="disabled", highlightthickness=0)
        self.log_text.pack(fill="both", expand=True, padx=PAD, pady=(2, PAD))

        right = tk.Frame(self, bg=BG)
        right.pack(side="left", fill="both", expand=True, padx=(4, PAD), pady=PAD)
        
        self.status_bar = tk.Label(right, text="System Idle", bg=PANEL, fg=SUBTEXT, font=FONT_BODY, anchor="w", padx=10, pady=4)
        self.status_bar.pack(fill="x", pady=(0, 4))
        
        self.canvas = tk.Canvas(right, bg=CARD, bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

    def _randomize(self):
        pages = [str(random.randint(0, 7)) for _ in range(15)] # Kept around 15 for optimal visual scaling
        self.ref_var.set(" ".join(pages))

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
        history = []
        faults = []

        if algo == "FIFO":
            self._animate_fifo(refs, frames, history, faults)
        elif algo == "LRU":
            self._animate_lru(refs, frames, history, faults)
        else:
            self._animate_optimal(refs, frames, history, faults)

        self.is_running = False
        self.run_btn.config(state="normal", bg=ACCENT, text="▶  Simulate")
        self.status_bar.config(text="Simulation Complete", fg=GREEN)
        
        # Calculate terminal metrics
        total_faults = sum(faults)
        total_refs = len(refs)
        self.stats_label.config(
            text=f"  Page Faults : {total_faults}\n"
                 f"  Page Hits   : {total_refs - total_faults}\n"
                 f"  Hit Rate    : {((total_refs - total_faults) / total_refs) * 100:.1f}%"
        )

    # ── Stepped Core Engines ────────────────────────────────────────────────
    
    def _animate_fifo(self, refs, n, history, faults):
        queue = deque()
        for idx, p in enumerate(refs):
            fault = p not in queue
            if fault:
                if len(queue) == n:
                    queue.popleft()
                queue.append(p)
            faults.append(fault)
            history.append(list(queue))
            
            self._ui_tick(refs[:idx+1], history, faults, n, current_step=idx)

    def _animate_lru(self, refs, n, history, faults):
        frames = OrderedDict()
        for idx, p in enumerate(refs):
            fault = p not in frames
            if fault:
                if len(frames) == n:
                    frames.popitem(last=False)
                frames[p] = True
            else:
                frames.move_to_end(p)
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
                    victim = max(future, key=future.get)
                    frames.remove(victim)
                frames.append(p)
            faults.append(fault)
            history.append(list(frames))
            
            self._ui_tick(refs[:idx+1], history, faults, n, current_step=idx)

    # ── UI Sync Hooks ───────────────────────────────────────────────────────
    
    def _ui_tick(self, current_refs, history, faults, n_frames, current_step):
        last_ref = current_refs[-1]
        is_fault = faults[-1]
        status = "FAULT (Eviction/Insertion)" if is_fault else "HIT (Page in memory)"
        
        self.status_bar.config(text=f"Step {current_step + 1} | Referencing Page: {last_ref} -> {status}",
                               fg=DANGER if is_fault else GREEN)
        
        # Append to live step log
        state_str = str(history[-1]).ljust(18)
        self.log_lines.append(f"[{current_step+1:>2}] Ref: {last_ref} | Frames: {state_str} | {'❌ FAULT' if is_fault else '✅ HIT'}")
        
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.insert("end", "\n".join(self.log_lines))
        self.log_text.see("end")
        self.log_text.config(state="disabled")

        self._draw_matrix(current_refs, history, faults, n_frames)
        time.sleep(0.5)

    def _draw_matrix(self, refs, history, faults, n_frames):
        c = self.canvas
        c.delete("all")
        
        W = c.winfo_width() or 800
        H = c.winfo_height() or 350
        c.create_text(W//2, 18, text=f"Page Replacement Grid Stream — {self.algo_var.get()}", fill=TEXT, font=FONT_H3)

        n = len(refs)
        cell_w = max(28, min(48, (W - 100) // max(len(self.ref_var.get().split()), n)))
        cell_h = 36
        start_x = 55
        frame_y_start = 50

        colors_map = {}
        palette = [ACCENT, ACCENT2, WARN, "#f7a26a", "#a26af7", "#6ab8f7"]

        for step, (ref, state, fault) in enumerate(zip(refs, history, faults)):
            x = start_x + step * cell_w
            
            # Highlight current step column boundary lightly
            if step == n - 1:
                c.create_rectangle(x, frame_y_start + 10, x + cell_w, frame_y_start + n_frames * (cell_h + 4) + 45, 
                                   outline=BORDER, fill="")

            # Draw reference string row headers dynamically 
            c.create_text(x + cell_w//2, 38, text=str(ref), fill=DANGER if fault else GREEN, font=("Consolas", 10, "bold"))
            
            # Stack memory blocks inside execution slot bounds
            for fi in range(n_frames):
                fy = frame_y_start + fi * (cell_h + 4) + 20
                if fi < len(state):
                    page = state[fi]
                    if page not in colors_map:
                        colors_map[page] = palette[len(colors_map) % len(palette)]
                    fill = colors_map[page]
                    
                    c.create_rectangle(x+2, fy, x+cell_w-2, fy+cell_h, fill=fill, outline=BG, width=1)
                    c.create_text(x + cell_w//2, fy + cell_h//2, text=str(page), fill=BG, font=("Consolas", 10, "bold"))
                else:
                    c.create_rectangle(x+2, fy, x+cell_w-2, fy+cell_h, fill="#1e2133", outline=BORDER, width=1)
            
            # Print state evaluation triggers beneath slots
            fault_y = frame_y_start + n_frames * (cell_h + 4) + 30
            if fault:
                c.create_text(x + cell_w//2, fault_y, text="F", fill=DANGER, font=("Consolas", 9, "bold"))
            else:
                c.create_text(x + cell_w//2, fault_y, text="•", fill=GREEN, font=("Consolas", 12, "bold"))

        # Redraw persistent left vertical row mapping ticks
        for fi in range(n_frames):
            fy = frame_y_start + fi * (cell_h + 4) + 20 + cell_h//2
            c.create_text(32, fy, text=f"Slot {fi+1}", fill=SUBTEXT, font=FONT_TINY)

        fault_y = frame_y_start + n_frames * (cell_h + 4) + 30
        c.create_text(32, fault_y, text="State", fill=SUBTEXT, font=FONT_TINY)


# ═══════════════════════════════════════════════════════════════════════════
#  4 ─ MASS STORAGE (DISK SCHEDULING)
# ═══════════════════════════════════════════════════════════════════════════

class MassStorageTab(tk.Frame):
    ALGOS = ["FCFS", "SSTF", "SCAN", "C-SCAN", "LOOK", "C-LOOK"]

    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self._build_ui()

    def _build_ui(self):
        ctrl = tk.Frame(self, bg=PANEL, width=270)
        ctrl.pack(side="left", fill="y", padx=(PAD, 4), pady=PAD)
        ctrl.pack_propagate(False)

        section_label(ctrl, "Disk Scheduling").pack(anchor="w", padx=PAD, pady=(PAD, 2))
        info_label(ctrl, "Visualize how the disk head moves across cylinders to service I/O requests.").pack(
            anchor="w", padx=PAD, pady=(0, PAD))

        tk.Label(ctrl, text="Algorithm", bg=PANEL, fg=SUBTEXT, font=FONT_TINY).pack(anchor="w", padx=PAD)
        self.algo_var = tk.StringVar(value="FCFS")
        ttk.Combobox(ctrl, textvariable=self.algo_var, values=self.ALGOS,
                     state="readonly", font=FONT_BODY).pack(fill="x", padx=PAD, pady=(2, PAD))

        r1, self.head_var = entry_row(ctrl, "Initial Head Position", "53", 6)
        r1.pack(anchor="w", padx=PAD, pady=2)
        r2, self.max_var = entry_row(ctrl, "Max Cylinder", "199", 6)
        r2.pack(anchor="w", padx=PAD, pady=2)

        # SCAN direction
        self.dir_frame = tk.Frame(ctrl, bg=PANEL)
        self.dir_frame.pack(anchor="w", padx=PAD, pady=2)
        tk.Label(self.dir_frame, text="Initial Direction:", bg=PANEL,
                 fg=SUBTEXT, font=FONT_TINY).pack(side="left")
        self.dir_var = tk.StringVar(value="right")
        tk.Radiobutton(self.dir_frame, text="→", variable=self.dir_var,
                       value="right", bg=PANEL, fg=TEXT,
                       selectcolor=CARD, font=FONT_TINY).pack(side="left")
        tk.Radiobutton(self.dir_frame, text="←", variable=self.dir_var,
                       value="left", bg=PANEL, fg=TEXT,
                       selectcolor=CARD, font=FONT_TINY).pack(side="left")

        tk.Label(ctrl, text="Request Queue (space-separated)", bg=PANEL,
                 fg=SUBTEXT, font=FONT_TINY).pack(anchor="w", padx=PAD, pady=(PAD, 0))
        self.req_var = tk.StringVar(value="98 183 37 122 14 124 65 67")
        tk.Entry(ctrl, textvariable=self.req_var, bg=CARD, fg=TEXT,
                 insertbackground=TEXT, relief="flat", font=FONT_MONO,
                 highlightthickness=1, highlightbackground=BORDER).pack(
                 fill="x", padx=PAD, pady=(2, PAD))

        styled_button(ctrl, "Random", self._randomize, WARN).pack(anchor="w", padx=PAD, pady=2)
        styled_button(ctrl, "▶  Simulate", self._run, ACCENT).pack(
            fill="x", padx=PAD, pady=(PAD, 0))

        self.stats_label = tk.Label(ctrl, text="", bg=PANEL, fg=ACCENT2,
                                     font=FONT_TINY, justify="left")
        self.stats_label.pack(anchor="w", padx=PAD, pady=PAD)

        self.order_label = tk.Label(ctrl, text="", bg=PANEL, fg=TEXT,
                                     font=FONT_TINY, justify="left", wraplength=230)
        self.order_label.pack(anchor="w", padx=PAD)

        right = tk.Frame(self, bg=BG)
        right.pack(side="left", fill="both", expand=True, padx=(4, PAD), pady=PAD)
        tk.Label(right, text="Disk Head Movement", bg=BG, fg=SUBTEXT, font=FONT_TINY).pack(anchor="w")
        self.canvas = tk.Canvas(right, bg=CARD, bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

    def _randomize(self):
        try: m = int(self.max_var.get())
        except: m = 199
        reqs = sorted(random.sample(range(0, m+1), min(10, m+1)))
        self.req_var.set(" ".join(map(str, reqs)))
        self.head_var.set(str(random.randint(0, m)))

    def _run(self):
        try:
            head = int(self.head_var.get())
            max_c = int(self.max_var.get())
            reqs = list(map(int, self.req_var.get().split()))
        except ValueError:
            messagebox.showwarning("Error", "Invalid input."); return
        algo = self.algo_var.get()
        direction = self.dir_var.get()
        order, total = self._schedule(reqs, head, max_c, algo, direction)
        self._draw(order, head, max_c)
        self.stats_label.config(text=f"  Total Head Movement: {total} cylinders\n"
                                      f"  Requests Served    : {len(reqs)}")
        self.order_label.config(text="Service Order: " + " → ".join(map(str, order)))

    def _schedule(self, reqs, head, max_c, algo, direction):
        if algo == "FCFS":
            order = list(reqs)
        elif algo == "SSTF":
            order = []; rem = list(reqs); cur = head
            while rem:
                nxt = min(rem, key=lambda x: abs(x - cur))
                order.append(nxt); rem.remove(nxt); cur = nxt
        elif algo in ("SCAN", "LOOK"):
            left  = sorted([r for r in reqs if r < head], reverse=True)
            right = sorted([r for r in reqs if r >= head])
            if algo == "SCAN":
                if direction == "right":
                    order = right + [max_c] + left
                else:
                    order = left + [0] + right
            else:  # LOOK
                if direction == "right":
                    order = right + left
                else:
                    order = left + right
        elif algo in ("C-SCAN", "C-LOOK"):
            right = sorted([r for r in reqs if r >= head])
            left  = sorted([r for r in reqs if r < head])
            if algo == "C-SCAN":
                order = right + [max_c, 0] + left
            else:
                order = right + left
        else:
            order = list(reqs)

        seq = [head] + [o for o in order if o in reqs or o in (0, max_c)]
        total = sum(abs(seq[i+1] - seq[i]) for i in range(len(seq)-1))
        serve_order = [o for o in order if o in reqs]
        return serve_order, total

    def _draw(self, order, head, max_c):
        c = self.canvas; c.delete("all")
        W = c.winfo_width() or 800; H = c.winfo_height() or 350
        c.create_text(W//2, 18, text=f"Disk Scheduling  —  {self.algo_var.get()}",
                      fill=TEXT, font=FONT_H3)

        ml, mr, mt, mb = 80, 40, 50, 40
        plot_w = W - ml - mr; plot_h = H - mt - mb
        steps = [head] + order
        n = len(steps)
        x_step = plot_w / max(n - 1, 1)

        def cx(i): return ml + i * x_step
        def cy(val): return mt + plot_h - (val / max_c) * plot_h

        # y-axis
        for tick in range(0, max_c+1, max(1, max_c//10)):
            y = cy(tick)
            c.create_line(ml-4, y, ml, y, fill=BORDER)
            c.create_text(ml-8, y, text=str(tick), fill=SUBTEXT,
                           font=FONT_TINY, anchor="e")
        c.create_line(ml, mt, ml, mt+plot_h, fill=BORDER, width=1)

        # x-axis (step labels)
        c.create_line(ml, mt+plot_h, ml+plot_w, mt+plot_h, fill=BORDER, width=1)
        for i in range(n):
            lbl = "Start" if i == 0 else str(i)
            c.create_text(cx(i), mt+plot_h+14, text=lbl, fill=SUBTEXT, font=FONT_TINY)

        # path
        for i in range(n-1):
            x1, y1 = cx(i), cy(steps[i])
            x2, y2 = cx(i+1), cy(steps[i+1])
            c.create_line(x1, y1, x2, y2, fill=ACCENT, width=2, smooth=False)

        # dots
        for i, val in enumerate(steps):
            x, y = cx(i), cy(val)
            col = WARN if i == 0 else ACCENT2
            c.create_oval(x-5, y-5, x+5, y+5, fill=col, outline=BG, width=2)
            c.create_text(x, y-14, text=str(val), fill=col, font=FONT_TINY)

        # y-axis label
        c.create_text(14, mt + plot_h//2, text="Cylinder", fill=SUBTEXT,
                       font=FONT_TINY, angle=90)


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN APPLICATION
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
        style.configure("TCombobox",
                         fieldbackground=CARD, background=CARD,
                         foreground=TEXT, selectbackground=ACCENT,
                         selectforeground=TEXT, bordercolor=BORDER,
                         arrowcolor=SUBTEXT, relief="flat")
        style.map("TCombobox",
                   fieldbackground=[("readonly", CARD)],
                   foreground=[("readonly", TEXT)])
        style.configure("Custom.TNotebook",
                         background=BG, borderwidth=0, tabmargins=0)
        style.configure("Custom.TNotebook.Tab",
                         background=PANEL, foreground=SUBTEXT,
                         padding=[16, 8], font=FONT_BODY, borderwidth=0)
        style.map("Custom.TNotebook.Tab",
                   background=[("selected", CARD)],
                   foreground=[("selected", TEXT)])

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=PANEL, height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="⚙  OS Algorithm Visualizer",
                 bg=PANEL, fg=TEXT, font=FONT_H1).pack(side="left", padx=20, pady=10)
        tk.Label(hdr, text="CPU · Memory · Virtual Memory · Mass Storage",
                 bg=PANEL, fg=SUBTEXT, font=FONT_TINY).pack(side="left", padx=4)

        # Notebook
        nb = ttk.Notebook(self, style="Custom.TNotebook")
        nb.pack(fill="both", expand=True, padx=0, pady=0)

        tabs = [
            ("🖥  CPU Scheduling",   CPUSchedulingTab),
            ("🗃  Memory Allocation", MemoryAllocationTab),
            ("📄  Virtual Memory",   VirtualMemoryTab),
            ("💽  Disk Scheduling",  MassStorageTab),
        ]
        for name, cls in tabs:
            frame = cls(nb)
            nb.add(frame, text=name)

        # Status bar
        status = tk.Frame(self, bg=PANEL, height=24)
        status.pack(fill="x", side="bottom")
        tk.Label(status,
                 text="Select a tab, configure parameters, then click ▶ Run / Simulate",
                 bg=PANEL, fg=SUBTEXT, font=FONT_TINY).pack(side="left", padx=12)


def main():
    app = OSVisualizerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
