"""
OS Algorithm Visualizer
========================
Visualizes core Operating System algorithms:
  1. CPU Scheduling (FCFS, SJF, Priority, Round Robin)
  2. Memory Allocation (First Fit, Best Fit, Worst Fit, Next Fit)
  3. Virtual Memory / Page Replacement (FIFO, LRU, Optimal)
  4. Mass Storage Management (FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK)

Run with:  python3 os_visualizer.py
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
        cb = ttk.Combobox(ctrl, textvariable=self.algo_var, values=self.ALGOS,
                          state="readonly", font=FONT_BODY)
        cb.pack(fill="x", padx=PAD, pady=(2, PAD))
        cb.bind("<<ComboboxSelected>>", self._on_algo_change)

        # RR quantum
        self.rr_frame = tk.Frame(ctrl, bg=PANEL)
        self.rr_frame.pack(fill="x", padx=PAD)
        tk.Label(self.rr_frame, text="Time Quantum", bg=PANEL, fg=SUBTEXT,
                 font=FONT_TINY).pack(anchor="w")
        self.quantum_var = tk.StringVar(value="2")
        tk.Entry(self.rr_frame, textvariable=self.quantum_var, width=6,
                 bg=CARD, fg=TEXT, insertbackground=TEXT,
                 relief="flat", font=FONT_MONO,
                 highlightthickness=1, highlightbackground=BORDER).pack(anchor="w", pady=2)
        self.rr_frame.pack_forget()

        # Process table header
        tk.Label(ctrl, text="Processes", bg=PANEL, fg=SUBTEXT,
                 font=FONT_TINY).pack(anchor="w", padx=PAD, pady=(PAD, 0))
        hdr = tk.Frame(ctrl, bg=PANEL)
        hdr.pack(fill="x", padx=PAD)
        for h, w in [("PID", 4), ("Arrival", 6), ("Burst", 5), ("Priority", 7)]:
            tk.Label(hdr, text=h, bg=PANEL, fg=SUBTEXT,
                     font=FONT_TINY, width=w).pack(side="left")

        self.proc_rows = []
        self.row_container = tk.Frame(ctrl, bg=PANEL)
        self.row_container.pack(fill="x", padx=PAD)
        for i in range(6):
            self._add_row(i)

        btn_f = tk.Frame(ctrl, bg=PANEL)
        btn_f.pack(fill="x", padx=PAD, pady=PAD)
        styled_button(btn_f, "+ Row", self._add_process, ACCENT2).pack(side="left", padx=2)
        styled_button(btn_f, "Random", self._randomize, WARN).pack(side="left", padx=2)

        styled_button(ctrl, "▶  Run Simulation", self._run, ACCENT).pack(
            fill="x", padx=PAD, pady=(0, PAD))

        # Results area
        self.stats_label = tk.Label(ctrl, text="", bg=PANEL, fg=ACCENT2,
                                     font=FONT_TINY, justify="left", wraplength=230)
        self.stats_label.pack(anchor="w", padx=PAD)

        # ── Right canvas ──
        right = tk.Frame(self, bg=BG)
        right.pack(side="left", fill="both", expand=True, padx=(4, PAD), pady=PAD)

        tk.Label(right, text="Gantt Chart", bg=BG, fg=SUBTEXT,
                 font=FONT_TINY).pack(anchor="w")
        self.canvas = tk.Canvas(right, bg=CARD, bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

    def _add_row(self, pid):
        f = tk.Frame(self.row_container, bg=PANEL)
        f.pack(fill="x", pady=1)
        pid_var = tk.StringVar(value=f"P{pid+1}")
        arr_var = tk.StringVar(value=str(pid))
        burst_var = tk.StringVar(value=str(random.randint(2, 8)))
        prio_var = tk.StringVar(value=str(random.randint(1, 5)))
        for var, w in [(pid_var, 4), (arr_var, 6), (burst_var, 5), (prio_var, 7)]:
            tk.Entry(f, textvariable=var, width=w, bg=CARD, fg=TEXT,
                     insertbackground=TEXT, relief="flat", font=FONT_MONO,
                     highlightthickness=1, highlightbackground=BORDER).pack(side="left", padx=1)
        self.proc_rows.append((pid_var, arr_var, burst_var, prio_var))

    def _add_process(self):
        pid = len(self.proc_rows)
        self._add_row(pid)

    def _randomize(self):
        for pid_v, arr_v, burst_v, prio_v in self.proc_rows:
            pid_idx = self.proc_rows.index((pid_v, arr_v, burst_v, prio_v))
            arr_v.set(str(random.randint(0, 5)))
            burst_v.set(str(random.randint(1, 10)))
            prio_v.set(str(random.randint(1, 6)))

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

    def _run(self):
        procs = self._get_processes()
        if not procs:
            messagebox.showwarning("No Data", "Add at least one process.")
            return
        algo = self.algo_var.get()
        if algo == "FCFS":
            timeline, stats = self._fcfs(procs)
        elif "SJF" in algo:
            timeline, stats = self._sjf(procs)
        elif "Priority" in algo:
            timeline, stats = self._priority(procs)
        else:
            try:
                q = int(self.quantum_var.get())
            except ValueError:
                q = 2
            timeline, stats = self._round_robin(procs, q)
        self._draw_gantt(timeline)
        self._show_stats(stats)

    # ── Algorithms ──────────────────────────────────────────────────────────
    def _fcfs(self, procs):
        procs = sorted(procs, key=lambda p: p["arrival"])
        t = 0; timeline = []; stats = []
        for p in procs:
            t = max(t, p["arrival"])
            start = t; t += p["burst"]
            timeline.append((p["pid"], start, t))
            stats.append({"pid": p["pid"], "wait": start - p["arrival"],
                           "turnaround": t - p["arrival"]})
        return timeline, stats

    def _sjf(self, procs):
        procs = sorted(procs, key=lambda p: (p["arrival"], p["burst"]))
        remaining = list(deepcopy(procs)); t = 0; timeline = []; stats = []
        while remaining:
            available = [p for p in remaining if p["arrival"] <= t]
            if not available:
                t = remaining[0]["arrival"]; continue
            p = min(available, key=lambda x: x["burst"])
            start = t; t += p["burst"]
            timeline.append((p["pid"], start, t))
            stats.append({"pid": p["pid"], "wait": start - p["arrival"],
                           "turnaround": t - p["arrival"]})
            remaining.remove(p)
        return timeline, stats

    def _priority(self, procs):
        remaining = list(deepcopy(procs)); t = 0; timeline = []; stats = []
        while remaining:
            available = [p for p in remaining if p["arrival"] <= t]
            if not available:
                t = min(p["arrival"] for p in remaining); continue
            p = min(available, key=lambda x: x["priority"])
            start = t; t += p["burst"]
            timeline.append((p["pid"], start, t))
            stats.append({"pid": p["pid"], "wait": start - p["arrival"],
                           "turnaround": t - p["arrival"]})
            remaining.remove(p)
        return timeline, stats

    def _round_robin(self, procs, quantum):
        queue = deque()
        remaining = {p["pid"]: p["burst"] for p in procs}
        arrival = {p["pid"]: p["arrival"] for p in procs}
        arrived_at = {p["pid"]: p["arrival"] for p in procs}
        order = sorted(procs, key=lambda p: p["arrival"])
        added = set(); t = 0; timeline = []; finish = {}
        ready = deque()
        proc_list = list(order)
        idx = 0
        # seed first arrivals
        while idx < len(proc_list) and proc_list[idx]["arrival"] <= t:
            ready.append(proc_list[idx]["pid"]); added.add(proc_list[idx]["pid"]); idx += 1
        while ready or idx < len(proc_list):
            if not ready:
                t = proc_list[idx]["arrival"]
                while idx < len(proc_list) and proc_list[idx]["arrival"] <= t:
                    ready.append(proc_list[idx]["pid"]); added.add(proc_list[idx]["pid"]); idx += 1
            pid = ready.popleft()
            run = min(quantum, remaining[pid])
            timeline.append((pid, t, t + run))
            t += run; remaining[pid] -= run
            # enqueue newly arrived
            while idx < len(proc_list) and proc_list[idx]["arrival"] <= t:
                ready.append(proc_list[idx]["pid"]); added.add(proc_list[idx]["pid"]); idx += 1
            if remaining[pid] > 0:
                ready.append(pid)
            else:
                finish[pid] = t
        stats = [{"pid": p["pid"],
                   "wait": finish[p["pid"]] - p["arrival"] - p["burst"],
                   "turnaround": finish[p["pid"]] - p["arrival"]}
                 for p in procs if p["pid"] in finish]
        return timeline, stats

    # ── Drawing ──────────────────────────────────────────────────────────────
    COLORS = ["#7c6af7","#38c9b0","#f7c26a","#f76a6a","#6af7a1","#f7a26a","#a26af7","#6ab8f7"]

    def _draw_gantt(self, timeline):
        c = self.canvas; c.delete("all")
        if not timeline: return
        W = c.winfo_width() or 800; H = c.winfo_height() or 300
        margin_l, margin_r, margin_top = 60, 20, 60
        bar_h = 44; bar_y = margin_top + 30
        total_t = timeline[-1][2]
        if total_t == 0: return
        scale = (W - margin_l - margin_r) / total_t
        pids = list(dict.fromkeys(p for p, _, _ in timeline))
        pid_color = {p: self.COLORS[i % len(self.COLORS)] for i, p in enumerate(pids)}

        # Title
        c.create_text(W//2, 18, text="Gantt Chart  —  " + self.algo_var.get(),
                      fill=TEXT, font=FONT_H3, anchor="center")
        # Axis line
        ax_y = bar_y + bar_h + 2
        c.create_line(margin_l, ax_y, W - margin_r, ax_y, fill=BORDER, width=1)

        drawn_labels = set()
        for pid, start, end in timeline:
            x0 = margin_l + start * scale
            x1 = margin_l + end * scale
            color = pid_color[pid]
            # bar
            c.create_rectangle(x0, bar_y, x1, bar_y + bar_h,
                                fill=color, outline=BG, width=2)
            # label
            if x1 - x0 > 18:
                c.create_text((x0+x1)//2, bar_y + bar_h//2,
                               text=pid, fill=BG, font=("Segoe UI", 9, "bold"))
            # tick + time
            c.create_line(x0, ax_y, x0, ax_y + 6, fill=SUBTEXT)
            if start not in drawn_labels:
                c.create_text(x0, ax_y + 16, text=str(start),
                               fill=SUBTEXT, font=FONT_TINY)
                drawn_labels.add(start)
        # last tick
        xf = margin_l + total_t * scale
        c.create_line(xf, ax_y, xf, ax_y + 6, fill=SUBTEXT)
        c.create_text(xf, ax_y + 16, text=str(total_t),
                       fill=SUBTEXT, font=FONT_TINY)

        # Legend
        lx = margin_l; ly = bar_y + bar_h + 40
        for pid, col in pid_color.items():
            c.create_rectangle(lx, ly, lx+12, ly+12, fill=col, outline="")
            c.create_text(lx+16, ly+6, text=pid, fill=TEXT,
                           font=FONT_TINY, anchor="w")
            lx += 50

    def _show_stats(self, stats):
        if not stats: return
        avg_w = sum(s["wait"] for s in stats) / len(stats)
        avg_t = sum(s["turnaround"] for s in stats) / len(stats)
        lines = ["  PID   Wait   Turnaround"]
        for s in stats:
            lines.append(f"  {s['pid']:<6} {s['wait']:<7} {s['turnaround']}")
        lines.append(f"\n  Avg Wait: {avg_w:.2f}   Avg Turnaround: {avg_t:.2f}")
        self.stats_label.config(text="\n".join(lines))


# ═══════════════════════════════════════════════════════════════════════════
#  2 ─ MEMORY ALLOCATION
# ═══════════════════════════════════════════════════════════════════════════

class MemoryAllocationTab(tk.Frame):
    ALGOS = ["First Fit", "Best Fit", "Worst Fit", "Next Fit"]

    def __init__(self, parent):
        super().__init__(parent, bg=BG)
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
        tk.Label(ctrl, text="Memory Blocks (KB)", bg=PANEL, fg=SUBTEXT,
                 font=FONT_TINY).pack(anchor="w", padx=PAD)
        self.blocks_var = tk.StringVar(value="100 500 200 300 600")
        tk.Entry(ctrl, textvariable=self.blocks_var, bg=CARD, fg=TEXT,
                 insertbackground=TEXT, relief="flat", font=FONT_MONO,
                 highlightthickness=1, highlightbackground=BORDER).pack(
                 fill="x", padx=PAD, pady=(2, PAD))

        # Process sizes
        tk.Label(ctrl, text="Process Sizes (KB)", bg=PANEL, fg=SUBTEXT,
                 font=FONT_TINY).pack(anchor="w", padx=PAD)
        self.procs_var = tk.StringVar(value="212 417 112 426")
        tk.Entry(ctrl, textvariable=self.procs_var, bg=CARD, fg=TEXT,
                 insertbackground=TEXT, relief="flat", font=FONT_MONO,
                 highlightthickness=1, highlightbackground=BORDER).pack(
                 fill="x", padx=PAD, pady=(2, PAD))

        styled_button(ctrl, "Random", self._randomize, WARN).pack(anchor="w", padx=PAD, pady=2)
        styled_button(ctrl, "▶  Allocate", self._run, ACCENT).pack(
            fill="x", padx=PAD, pady=(PAD, 0))

        self.result_text = tk.Text(ctrl, bg=CARD, fg=TEXT, font=FONT_TINY,
                                    height=12, relief="flat", state="disabled",
                                    highlightthickness=0)
        self.result_text.pack(fill="x", padx=PAD, pady=PAD)

        right = tk.Frame(self, bg=BG)
        right.pack(side="left", fill="both", expand=True, padx=(4, PAD), pady=PAD)
        tk.Label(right, text="Memory Map", bg=BG, fg=SUBTEXT, font=FONT_TINY).pack(anchor="w")
        self.canvas = tk.Canvas(right, bg=CARD, bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

    def _randomize(self):
        blocks = sorted([random.randint(50, 600) for _ in range(6)], reverse=True)
        procs = [random.randint(50, 450) for _ in range(5)]
        self.blocks_var.set(" ".join(map(str, blocks)))
        self.procs_var.set(" ".join(map(str, procs)))

    def _run(self):
        try:
            blocks = list(map(int, self.blocks_var.get().split()))
            procs  = list(map(int, self.procs_var.get().split()))
        except ValueError:
            messagebox.showwarning("Error", "Enter space-separated integers.")
            return
        algo = self.algo_var.get()
        alloc = self._allocate(blocks, procs, algo)
        self._draw(blocks, procs, alloc)
        self._show_result(blocks, procs, alloc)

    def _allocate(self, blocks, procs, algo):
        remaining = list(blocks); alloc = [-1] * len(procs)
        last_idx = 0  # for Next Fit

        for i, size in enumerate(procs):
            if algo == "First Fit":
                for j, b in enumerate(remaining):
                    if b >= size:
                        alloc[i] = j; remaining[j] -= size; break
            elif algo == "Best Fit":
                best = -1
                for j, b in enumerate(remaining):
                    if b >= size:
                        if best == -1 or remaining[j] < remaining[best]:
                            best = j
                if best != -1:
                    alloc[i] = best; remaining[best] -= size
            elif algo == "Worst Fit":
                worst = -1
                for j, b in enumerate(remaining):
                    if b >= size:
                        if worst == -1 or remaining[j] > remaining[worst]:
                            worst = j
                if worst != -1:
                    alloc[i] = worst; remaining[worst] -= size
            elif algo == "Next Fit":
                start = last_idx
                for k in range(len(remaining)):
                    j = (start + k) % len(remaining)
                    if remaining[j] >= size:
                        alloc[i] = j; remaining[j] -= size
                        last_idx = j; break
        return alloc

    BLOCK_COLORS = ["#7c6af7","#38c9b0","#f7c26a","#f76a6a","#6af7a1","#f7a26a"]

    def _draw(self, blocks, procs, alloc):
        c = self.canvas; c.delete("all")
        W = c.winfo_width() or 800; H = c.winfo_height() or 350
        max_b = max(blocks) if blocks else 1
        bar_w = 60; gap = 30
        total_w = len(blocks) * (bar_w + gap)
        start_x = (W - total_w) // 2
        top_y = 60; bottom_y = H - 60

        c.create_text(W//2, 22, text=f"Memory Allocation  —  {self.algo_var.get()}",
                      fill=TEXT, font=FONT_H3)

        proc_colors = {}
        for pi, bi in enumerate(alloc):
            if bi != -1:
                proc_colors[bi] = self.BLOCK_COLORS[pi % len(self.BLOCK_COLORS)]

        for i, block in enumerate(blocks):
            x = start_x + i * (bar_w + gap)
            bh = int((block / max_b) * (bottom_y - top_y))
            by = bottom_y - bh

            # full block (gray)
            c.create_rectangle(x, by, x+bar_w, bottom_y,
                                fill="#2a2d40", outline=BORDER, width=1)
            c.create_text(x + bar_w//2, by - 14,
                           text=f"{block}KB", fill=SUBTEXT, font=FONT_TINY)
            c.create_text(x + bar_w//2, bottom_y + 14,
                           text=f"B{i+1}", fill=TEXT, font=("Segoe UI", 9, "bold"))

            # allocated portion
            for pi, bi in enumerate(alloc):
                if bi == i:
                    proc_h = int((procs[pi] / max_b) * (bottom_y - top_y))
                    py = bottom_y - proc_h
                    col = self.BLOCK_COLORS[pi % len(self.BLOCK_COLORS)]
                    c.create_rectangle(x+2, py+2, x+bar_w-2, bottom_y-2,
                                       fill=col, outline="")
                    label = f"P{pi+1}\n{procs[pi]}KB"
                    c.create_text(x + bar_w//2, (py + bottom_y)//2,
                                   text=label, fill=BG,
                                   font=("Segoe UI", 8, "bold"), justify="center")

        # legend
        lx = 20; ly = H - 20
        for pi in range(len(procs)):
            col = self.BLOCK_COLORS[pi % len(self.BLOCK_COLORS)]
            c.create_rectangle(lx, ly-8, lx+10, ly+2, fill=col, outline="")
            status = f"Block {alloc[pi]+1}" if alloc[pi] != -1 else "Not Allocated"
            c.create_text(lx+14, ly-3, text=f"P{pi+1} ({procs[pi]}KB) → {status}",
                           fill=TEXT, font=FONT_TINY, anchor="w")
            lx += 160

    def _show_result(self, blocks, procs, alloc):
        lines = [f"{'Process':<10}{'Size':<10}{'Block':<10}{'Status'}"]
        lines.append("─" * 42)
        for i, (size, bi) in enumerate(zip(procs, alloc)):
            status = f"B{bi+1} (rem {blocks[bi]-size}KB)" if bi != -1 else "✗ Not allocated"
            lines.append(f"P{i+1:<9}{size:<10}{bi+1 if bi!=-1 else '-':<10}{status}")
        allocated = sum(1 for b in alloc if b != -1)
        lines.append(f"\n  Allocated: {allocated}/{len(procs)}")
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("end", "\n".join(lines))
        self.result_text.config(state="disabled")


# ═══════════════════════════════════════════════════════════════════════════
#  3 ─ VIRTUAL MEMORY / PAGE REPLACEMENT
# ═══════════════════════════════════════════════════════════════════════════

class VirtualMemoryTab(tk.Frame):
    ALGOS = ["FIFO", "LRU", "Optimal"]

    def __init__(self, parent):
        super().__init__(parent, bg=BG)
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
        styled_button(ctrl, "▶  Simulate", self._run, ACCENT).pack(
            fill="x", padx=PAD, pady=(PAD, 0))

        self.stats_label = tk.Label(ctrl, text="", bg=PANEL, fg=ACCENT2,
                                     font=FONT_TINY, justify="left")
        self.stats_label.pack(anchor="w", padx=PAD, pady=PAD)

        # Step-through log
        tk.Label(ctrl, text="Step Log", bg=PANEL, fg=SUBTEXT, font=FONT_TINY).pack(anchor="w", padx=PAD)
        self.log_text = tk.Text(ctrl, bg=CARD, fg=TEXT, font=("Consolas", 8),
                                 height=14, relief="flat", state="disabled",
                                 highlightthickness=0)
        self.log_text.pack(fill="both", expand=True, padx=PAD, pady=(2, PAD))

        right = tk.Frame(self, bg=BG)
        right.pack(side="left", fill="both", expand=True, padx=(4, PAD), pady=PAD)
        tk.Label(right, text="Page Frame State", bg=BG, fg=SUBTEXT, font=FONT_TINY).pack(anchor="w")
        self.canvas = tk.Canvas(right, bg=CARD, bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

    def _randomize(self):
        pages = [str(random.randint(0, 7)) for _ in range(20)]
        self.ref_var.set(" ".join(pages))

    def _run(self):
        try:
            refs = list(map(int, self.ref_var.get().split()))
            frames = int(self.frames_var.get())
        except ValueError:
            messagebox.showwarning("Error", "Invalid input."); return
        algo = self.algo_var.get()
        if algo == "FIFO":
            history, faults = self._fifo(refs, frames)
        elif algo == "LRU":
            history, faults = self._lru(refs, frames)
        else:
            history, faults = self._optimal(refs, frames)
        self._draw(refs, history, faults, frames)
        hits = len(refs) - len([f for f in faults if f])
        self.stats_label.config(
            text=f"  Page Faults : {sum(faults)}\n"
                 f"  Page Hits   : {len(refs)-sum(faults)}\n"
                 f"  Hit Rate    : {(len(refs)-sum(faults))/len(refs)*100:.1f}%")
        self._show_log(refs, history, faults)

    def _fifo(self, refs, n):
        queue = deque(); frames = []; history = []; faults = []
        for p in refs:
            fault = p not in queue
            if fault:
                if len(queue) == n:
                    queue.popleft()
                queue.append(p)
            faults.append(fault)
            history.append(list(queue))
        return history, faults

    def _lru(self, refs, n):
        frames = OrderedDict(); history = []; faults = []
        for p in refs:
            fault = p not in frames
            if fault:
                if len(frames) == n:
                    frames.popitem(last=False)
                frames[p] = True
            else:
                frames.move_to_end(p)
            faults.append(fault)
            history.append(list(frames.keys()))
        return history, faults

    def _optimal(self, refs, n):
        frames = []; history = []; faults = []
        for i, p in enumerate(refs):
            fault = p not in frames
            if fault:
                if len(frames) == n:
                    future = {}
                    for f in frames:
                        try: future[f] = refs[i+1:].index(f)
                        except ValueError: future[f] = float('inf')
                    victim = max(future, key=future.get)
                    frames.remove(victim)
                frames.append(p)
            faults.append(fault)
            history.append(list(frames))
        return history, faults

    def _draw(self, refs, history, faults, n_frames):
        c = self.canvas; c.delete("all")
        W = c.winfo_width() or 800; H = c.winfo_height() or 350
        c.create_text(W//2, 18, text=f"Page Replacement  —  {self.algo_var.get()}",
                      fill=TEXT, font=FONT_H3)

        n = len(refs)
        cell_w = max(28, min(48, (W - 80) // n))
        cell_h = 36
        start_x = 40
        frame_y_start = 50

        colors_map = {}
        palette = [ACCENT, ACCENT2, WARN, DANGER, GREEN, "#f7a26a"]

        for step, (ref, state, fault) in enumerate(zip(refs, history, faults)):
            x = start_x + step * cell_w
            # reference label
            c.create_text(x + cell_w//2, 36, text=str(ref),
                           fill=WARN if fault else GREEN, font=("Consolas", 9, "bold"))
            # frame cells
            for fi in range(n_frames):
                fy = frame_y_start + fi * (cell_h + 4) + 20
                if fi < len(state):
                    page = state[fi]
                    if page not in colors_map:
                        colors_map[page] = palette[len(colors_map) % len(palette)]
                    fill = colors_map[page]
                    c.create_rectangle(x+2, fy, x+cell_w-2, fy+cell_h,
                                       fill=fill, outline=BG, width=1)
                    c.create_text(x + cell_w//2, fy + cell_h//2,
                                   text=str(page), fill=BG, font=("Consolas", 9, "bold"))
                else:
                    c.create_rectangle(x+2, fy, x+cell_w-2, fy+cell_h,
                                       fill="#1e2133", outline=BORDER, width=1)
            # fault marker
            fault_y = frame_y_start + n_frames * (cell_h + 4) + 30
            if fault:
                c.create_text(x + cell_w//2, fault_y, text="F",
                               fill=DANGER, font=("Consolas", 8, "bold"))

        # row labels
        for fi in range(n_frames):
            fy = frame_y_start + fi * (cell_h + 4) + 20 + cell_h//2
            c.create_text(28, fy, text=f"F{fi+1}", fill=SUBTEXT, font=FONT_TINY)

        fault_y = frame_y_start + n_frames * (cell_h + 4) + 30
        c.create_text(28, fault_y, text="Flt", fill=DANGER, font=FONT_TINY)

    def _show_log(self, refs, history, faults):
        lines = []
        for i, (r, h, f) in enumerate(zip(refs, history, faults)):
            state = str(h).ljust(20)
            lines.append(f"[{i+1:>2}] ref={r}  frames={state}  {'FAULT' if f else 'hit'}")
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.insert("end", "\n".join(lines))
        self.log_text.config(state="disabled")


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
