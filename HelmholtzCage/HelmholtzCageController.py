"""
Helmholtz Cage Controller GUI
Tkinter-based interface for controlling a 3-axis Helmholtz cage system.
Integrates CSV magnetic field data loading, current generation, duty cycle
calculation, and PWM output via I2C.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import math
import threading
import os
import time


# ===========================================================================
# Backend Logic (adapted from uploaded modules)
# ===========================================================================

class CsvMagData:
    """Reads and stores magnetic field data from the MagArrayVals CSV."""

    def __init__(self):
        self.mag490m1s = []
        self.mag520m1s = []
        self.mag490mhalfs = []
        self.mag520mhalfs = []
        self.filepath = None

    @staticmethod
    def _filter_xyz(entry):
        components = entry.split()
        components[-1] = components[-1].replace("}", "")
        values = []
        for c in components:
            c = c.replace("{", "").replace("}", "").strip()
            if c:
                try:
                    values.append(float(c))
                except ValueError:
                    pass
        return values[:3] if len(values) >= 3 else None

    def load(self, filepath):
        self.filepath = filepath
        self.mag490m1s.clear()
        self.mag520m1s.clear()
        self.mag490mhalfs.clear()
        self.mag520mhalfs.clear()

        with open(filepath, mode="r") as fh:
            reader = csv.reader(fh)
            header = next(reader)  # skip header
            for row in reader:
                # strip leading empty cells
                while row and not row[0].startswith("{"):
                    row.pop(0)
                if len(row) >= 1:
                    v = self._filter_xyz(row[0])
                    if v:
                        self.mag490m1s.append(v)
                if len(row) >= 2:
                    v = self._filter_xyz(row[1])
                    if v:
                        self.mag520m1s.append(v)
                if len(row) >= 3:
                    v = self._filter_xyz(row[2])
                    if v:
                        self.mag490mhalfs.append(v)
                if len(row) >= 4:
                    v = self._filter_xyz(row[3])
                    if v:
                        self.mag520mhalfs.append(v)

    @property
    def loaded(self):
        return self.filepath is not None and len(self.mag490m1s) > 0

    def dataset(self, choice: int):
        return {
            1: self.mag490m1s,
            2: self.mag520m1s,
            3: self.mag490mhalfs,
            4: self.mag520mhalfs,
        }.get(choice, [])

    def dataset_label(self, choice: int):
        return {
            1: "490 km – 1 s step",
            2: "520 km – 1 s step",
            3: "490 km – 0.5 s step",
            4: "520 km – 0.5 s step",
        }.get(choice, "Unknown")


class Coil:
    """Compute required coil current for a desired B field (Gauss)."""

    def __init__(self, name, B, N, a, gamma):
        self.name = name
        self.B = B
        self.N = N
        self.a = a
        self.gamma = gamma

    def single_current(self):
        num = self.B * self.a
        den = (0.8144e-6) * self.N * 10000
        return num / den if den != 0 else 0.0


class DutyCycleCalc:
    """Convert current values to 16-bit PWM duty-cycle counts."""

    MAX_CURRENT = 7.5  # full-scale current for 100 % duty

    @classmethod
    def to_duty(cls, current_abs):
        ratio = min(abs(current_abs) / cls.MAX_CURRENT, 1.0)
        return int(ratio * 65535)


# ===========================================================================
# GUI Application
# ===========================================================================

class HelmholtzCageApp(tk.Tk):
    """Main application window."""

    # Default coil parameters per axis
    COIL_PARAMS = {
        "X": {"N": 30, "a": 1, "gamma": 0.50},
        "Y": {"N": 30, "a": 1, "gamma": 0.55},
        "Z": {"N": 30, "a": 1, "gamma": 0.525},
    }

    # Baseline ambient field (Gauss) used as calibration offsets
    BASELINE = {"X": -0.0573, "Y": -0.1365, "Z": 0.00242}

    def __init__(self):
        super().__init__()
        self.title("Helmholtz Cage Controller")
        self.configure(bg="#2E2E2E")
        self.resizable(True, True)
        self.minsize(1000, 640)
        self.geometry("1060x680")

        # ---- state ----------------------------------------------------------
        self.csv_data = CsvMagData()
        self._sim_thread = None
        self._sim_running = False
        self._sim_paused = False

        # ---- styles ---------------------------------------------------------
        self._configure_styles()

        # ---- menu bar -------------------------------------------------------
        menubar = tk.Menu(self, bg="#3C3C3C", fg="white",
                          activebackground="#555", activeforeground="white")
        file_menu = tk.Menu(menubar, tearoff=0, bg="#3C3C3C", fg="white",
                            activebackground="#555", activeforeground="white")
        file_menu.add_command(label="Open CSV…", command=self._browse_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        settings_menu = tk.Menu(menubar, tearoff=0, bg="#3C3C3C", fg="white",
                                activebackground="#555", activeforeground="white")
        settings_menu.add_command(label="Coil Parameters…", command=self._open_settings)
        menubar.add_cascade(label="Settings", menu=settings_menu)

        help_menu = tk.Menu(menubar, tearoff=0, bg="#3C3C3C", fg="white",
                            activebackground="#555", activeforeground="white")
        help_menu.add_command(label="About", command=lambda: messagebox.showinfo(
            "About", "Helmholtz Cage Controller\nUGA SSRL"))
        menubar.add_cascade(label="Help", menu=help_menu)
        self.config(menu=menubar)

        # ---- build frames ---------------------------------------------------
        self._build_data_extraction_frame()
        self._build_port_connection_frame()
        self._build_simulation_control_frame()
        self._build_info_frame()
        self._log("Application started. Load a CSV to begin.")

    # --------------------------------------------------------------------- #
    # Styles
    # --------------------------------------------------------------------- #
    def _configure_styles(self):
        self.BG = "#2E2E2E"
        self.FG = "#ECECEC"
        self.FRAME_BG = "#383838"
        self.ENTRY_BG = "#4A4A4A"
        self.ENTRY_FG = "#FFFFFF"
        self.BTN_BG = "#505050"
        self.BTN_FG = "#ECECEC"
        self.BTN_ACTIVE = "#6A6A6A"
        self.ACCENT = "#5B9BD5"
        self.LABEL_BOLD = ("Segoe UI", 10, "bold")
        self.LABEL_NORM = ("Segoe UI", 9)
        self.HEADER_FONT = ("Segoe UI", 11, "bold")

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=self.FRAME_BG)
        style.configure("TLabel", background=self.FRAME_BG, foreground=self.FG,
                         font=self.LABEL_NORM)
        style.configure("Header.TLabel", font=self.HEADER_FONT,
                         background=self.FRAME_BG, foreground=self.FG)
        style.configure("Bold.TLabel", font=self.LABEL_BOLD,
                         background=self.FRAME_BG, foreground=self.FG)
        style.configure("TButton", font=self.LABEL_NORM,
                         background=self.BTN_BG, foreground=self.BTN_FG)
        style.map("TButton",
                   background=[("active", self.BTN_ACTIVE)],
                   foreground=[("active", self.BTN_FG)])
        style.configure("Accent.TButton", font=self.LABEL_BOLD,
                         background=self.ACCENT, foreground="white")
        style.map("Accent.TButton",
                   background=[("active", "#4A8BC2")])
        style.configure("Stop.TButton", font=self.LABEL_BOLD,
                         background="#C0392B", foreground="white")
        style.map("Stop.TButton", background=[("active", "#A93226")])
        style.configure("TEntry", fieldbackground=self.ENTRY_BG,
                         foreground=self.ENTRY_FG)
        style.configure("TCombobox", fieldbackground=self.ENTRY_BG,
                         foreground=self.ENTRY_FG, background=self.BTN_BG)
        style.configure("Horizontal.TProgressbar",
                         troughcolor=self.ENTRY_BG, background=self.ACCENT)
        style.configure("TLabelframe", background=self.FRAME_BG,
                         foreground=self.FG, font=self.LABEL_BOLD)
        style.configure("TLabelframe.Label",
                         background=self.FRAME_BG, foreground=self.ACCENT,
                         font=self.HEADER_FONT)

    # --------------------------------------------------------------------- #
    # Helpers to reduce boilerplate
    # --------------------------------------------------------------------- #
    def _make_label(self, parent, text, **kw):
        return ttk.Label(parent, text=text, **kw)

    def _make_entry(self, parent, textvariable=None, width=10, state="readonly"):
        e = ttk.Entry(parent, textvariable=textvariable, width=width,
                      justify="center", font=self.LABEL_NORM)
        if state == "readonly":
            e.configure(state="readonly")
        return e

    def _make_button(self, parent, text, command, style="TButton", width=16):
        return ttk.Button(parent, text=text, command=command,
                          style=style, width=width)

    # --------------------------------------------------------------------- #
    # Data Extraction Frame (top-left)
    # --------------------------------------------------------------------- #
    def _build_data_extraction_frame(self):
        frame = ttk.LabelFrame(self, text="Data Extraction", padding=10)
        frame.place(x=15, y=10, width=470, height=170)

        # Browse row
        self._make_button(frame, "Browse for File", self._browse_file,
                          width=16).grid(row=0, column=0, padx=5, pady=4)
        self.file_var = tk.StringVar()
        ttk.Entry(frame, textvariable=self.file_var, width=30,
                  font=self.LABEL_NORM, state="readonly"
                  ).grid(row=0, column=1, columnspan=2, padx=5, pady=4, sticky="ew")

        ttk.Label(frame, text="Only .csv files are supported!",
                  font=("Segoe UI", 8, "italic")).grid(
                      row=1, column=0, columnspan=3, pady=2)

        # Dataset chooser
        ttk.Label(frame, text="Dataset:", style="Bold.TLabel").grid(
            row=2, column=0, padx=5, sticky="e")
        self.dataset_var = tk.IntVar(value=1)
        ds_combo = ttk.Combobox(frame, state="readonly", width=26,
                                font=self.LABEL_NORM,
                                values=[
                                    "1 – 490 km, 1 s step",
                                    "2 – 520 km, 1 s step",
                                    "3 – 490 km, 0.5 s step",
                                    "4 – 520 km, 0.5 s step",
                                ])
        ds_combo.current(0)
        ds_combo.grid(row=2, column=1, columnspan=2, padx=5, pady=4, sticky="w")
        ds_combo.bind("<<ComboboxSelected>>",
                       lambda e: self.dataset_var.set(
                           int(ds_combo.get()[0])))
        self._ds_combo = ds_combo

        # Extract & STK buttons
        self._make_button(frame, "Extract Data", self._extract_data,
                          style="Accent.TButton", width=14).grid(
                              row=3, column=0, padx=5, pady=6)
        self._make_button(frame, "STK Extraction", self._stk_extraction,
                          width=14).grid(row=3, column=2, padx=5, pady=6)

    # --------------------------------------------------------------------- #
    # Port Connection Frame (top-right)
    # --------------------------------------------------------------------- #
    def _build_port_connection_frame(self):
        frame = ttk.LabelFrame(self, text="Port Connection Control", padding=10)
        frame.place(x=500, y=10, width=545, height=170)

        ports = ["PSU X Port", "PSU Y Port", "PSU Z Port", "Arduino Port"]
        self.port_vars = {}
        for i, label in enumerate(ports):
            ttk.Label(frame, text=label, style="Bold.TLabel").grid(
                row=0, column=i, padx=8, pady=2)
            var = tk.StringVar()
            ttk.Entry(frame, textvariable=var, width=10,
                      font=self.LABEL_NORM).grid(
                          row=1, column=i, padx=8, pady=2)
            self.port_vars[label] = var

        ttk.Label(frame,
                  text='Check "Device Manager" before trying to connect to ports!',
                  font=("Segoe UI", 8, "italic")).grid(
                      row=2, column=0, columnspan=4, pady=6)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=4, pady=4)
        self._make_button(btn_frame, "Connect", self._connect_ports,
                          style="Accent.TButton", width=14).pack(
                              side="left", padx=15)
        self._make_button(btn_frame, "Disconnect", self._disconnect_ports,
                          width=14).pack(side="left", padx=15)

    # --------------------------------------------------------------------- #
    # Simulation Control Frame (bottom-left)
    # --------------------------------------------------------------------- #
    def _build_simulation_control_frame(self):
        frame = ttk.LabelFrame(self, text="Simulation Control", padding=10)
        frame.place(x=15, y=190, width=620, height=440)

        # --- Row 0: control buttons + rate of change -------------------------
        btn_col = ttk.Frame(frame)
        btn_col.grid(row=0, column=0, rowspan=3, padx=(0, 10), sticky="n")

        self.btn_run = self._make_button(
            btn_col, "▶  Run Simulation", self._run_simulation,
            style="Accent.TButton", width=18)
        self.btn_run.pack(pady=4, fill="x")

        self.btn_stop = self._make_button(
            btn_col, "■  Stop Simulation", self._stop_simulation,
            style="Stop.TButton", width=18)
        self.btn_stop.pack(pady=4, fill="x")

        self.btn_pause = self._make_button(
            btn_col, "⏸  Pause Simulation", self._pause_simulation,
            width=18)
        self.btn_pause.pack(pady=4, fill="x")

        # Rate of change
        roc_frame = ttk.Frame(frame)
        roc_frame.grid(row=0, column=1, columnspan=3, sticky="w", pady=4)
        ttk.Label(roc_frame, text="Rate of Change", style="Bold.TLabel").pack(
            side="left", padx=(10, 5))
        self.rate_var = tk.StringVar(value="1000")
        ttk.Entry(roc_frame, textvariable=self.rate_var, width=8,
                  font=self.LABEL_NORM, justify="center").pack(side="left", padx=2)
        self.rate_unit_var = tk.StringVar(value="millisecond(s)")
        ttk.Combobox(roc_frame, textvariable=self.rate_unit_var, width=12,
                     state="readonly", font=self.LABEL_NORM,
                     values=["millisecond(s)", "second(s)"]).pack(
                         side="left", padx=4)

        # --- Column headers: PSU 1 / 2 / 3 ----------------------------------
        for j, axis in enumerate(["PSU 1 (X axis)", "PSU 2 (Y axis)",
                                   "PSU 3 (Z axis)"]):
            ttk.Label(frame, text=axis, style="Bold.TLabel").grid(
                row=1, column=j + 1, padx=8, pady=(10, 4))

        # --- Rows for Offset, B, Voltage, Current ----------------------------
        self._sim_vars = {}
        row_labels = [
            ("Offset (Gauss)", "offset"),
            ("Magnetic Field Strength (G)", "field"),
            ("Voltage (V)", "voltage"),
            ("Current (A)", "current"),
        ]
        axes = ["X", "Y", "Z"]

        for r, (label_text, key) in enumerate(row_labels, start=2):
            ttk.Label(frame, text=label_text, style="Bold.TLabel").grid(
                row=r, column=0, padx=5, pady=6, sticky="e")
            for j, ax in enumerate(axes):
                var = tk.StringVar(value="0")
                entry_state = "normal" if key == "offset" else "readonly"
                e = ttk.Entry(frame, textvariable=var, width=12,
                              font=("Consolas", 10), justify="center")
                if entry_state == "readonly":
                    e.configure(state="readonly")
                e.grid(row=r, column=j + 1, padx=8, pady=6)
                self._sim_vars[(key, ax)] = var

        # pre-fill offsets with baseline values
        self._sim_vars[("offset", "X")].set(f"{self.BASELINE['X']:.4f}")
        self._sim_vars[("offset", "Y")].set(f"{self.BASELINE['Y']:.4f}")
        self._sim_vars[("offset", "Z")].set(f"{self.BASELINE['Z']:.4f}")

        # --- Direction indicators --------------------------------------------
        ttk.Label(frame, text="Direction", style="Bold.TLabel").grid(
            row=6, column=0, padx=5, pady=6, sticky="e")
        self._dir_labels = {}
        for j, ax in enumerate(axes):
            var = tk.StringVar(value="—")
            lbl = ttk.Label(frame, textvariable=var,
                            font=("Consolas", 10), anchor="center", width=10)
            lbl.grid(row=6, column=j + 1, padx=8, pady=6)
            self._dir_labels[ax] = var

        # --- Duty Cycle display ----------------------------------------------
        ttk.Label(frame, text="Duty Cycle", style="Bold.TLabel").grid(
            row=7, column=0, padx=5, pady=6, sticky="e")
        self._dc_vars = {}
        for j, ax in enumerate(axes):
            var = tk.StringVar(value="0")
            e = ttk.Entry(frame, textvariable=var, width=12,
                          font=("Consolas", 10), justify="center",
                          state="readonly")
            e.grid(row=7, column=j + 1, padx=8, pady=6)
            self._dc_vars[ax] = var

    # --------------------------------------------------------------------- #
    # Information / Status Frame (bottom-right)
    # --------------------------------------------------------------------- #
    def _build_info_frame(self):
        frame = ttk.LabelFrame(self, text="Information Box", padding=10)
        frame.place(x=650, y=190, width=395, height=440)

        # Data points
        ttk.Label(frame, text="Number of Data Points",
                  style="Bold.TLabel").grid(row=0, column=0, sticky="w", pady=4)
        self.dp_var = tk.StringVar(value="N/A")
        self._make_entry(frame, self.dp_var, width=10).grid(
            row=0, column=1, padx=10, pady=4)

        # Sim time
        ttk.Label(frame, text="Simulation Time (sec)",
                  style="Bold.TLabel").grid(row=1, column=0, sticky="w", pady=4)
        self.simtime_var = tk.StringVar(value="N/A")
        self._make_entry(frame, self.simtime_var, width=10).grid(
            row=1, column=1, padx=10, pady=4)

        # Current step
        ttk.Label(frame, text="Current Step",
                  style="Bold.TLabel").grid(row=2, column=0, sticky="w", pady=4)
        self.step_var = tk.StringVar(value="N/A")
        self._make_entry(frame, self.step_var, width=10).grid(
            row=2, column=1, padx=10, pady=4)

        # Progress
        ttk.Label(frame, text="Progress",
                  style="Bold.TLabel").grid(row=3, column=0, sticky="w", pady=4)
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            frame, variable=self.progress_var, maximum=100,
            length=180, mode="determinate")
        self.progress_bar.grid(row=3, column=1, padx=10, pady=4, sticky="ew")
        self.pct_var = tk.StringVar(value="0 %")
        ttk.Label(frame, textvariable=self.pct_var).grid(
            row=3, column=2, padx=2)

        # Status & Error log
        ttk.Label(frame, text="Status && Error Information",
                  style="Bold.TLabel").grid(
                      row=4, column=0, columnspan=3, sticky="w", pady=(14, 4))

        log_frame = ttk.Frame(frame)
        log_frame.grid(row=5, column=0, columnspan=3, sticky="nsew")
        frame.rowconfigure(5, weight=1)
        frame.columnconfigure(1, weight=1)

        self.log_text = tk.Text(log_frame, height=12, width=42, wrap="word",
                                bg=self.ENTRY_BG, fg="#B0E0B0",
                                font=("Consolas", 9), insertbackground="white",
                                state="disabled", relief="flat", padx=6, pady=4)
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # --------------------------------------------------------------------- #
    # Logging helper
    # --------------------------------------------------------------------- #
    def _log(self, msg):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    # --------------------------------------------------------------------- #
    # Button callbacks
    # --------------------------------------------------------------------- #
    def _browse_file(self):
        path = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if path:
            self.file_var.set(os.path.basename(path))
            try:
                self.csv_data.load(path)
                n = len(self.csv_data.mag490m1s)
                self._log(f"Loaded {os.path.basename(path)} — {n} rows per dataset.")
            except Exception as exc:
                self._log(f"ERROR loading CSV: {exc}")
                messagebox.showerror("CSV Load Error", str(exc))

    def _extract_data(self):
        if not self.csv_data.loaded:
            self._log("No CSV file loaded. Browse for a file first.")
            messagebox.showwarning("No Data", "Load a CSV file first.")
            return
        choice = self.dataset_var.get()
        ds = self.csv_data.dataset(choice)
        label = self.csv_data.dataset_label(choice)
        self.dp_var.set(str(len(ds)))

        rate_ms = self._get_rate_ms()
        total_sec = len(ds) * rate_ms / 1000.0
        self.simtime_var.set(f"{total_sec:.1f}")
        self._log(f"Extracted dataset: {label} ({len(ds)} points, "
                  f"~{total_sec:.1f} s total).")

    def _stk_extraction(self):
        self._log("STK Extraction: not yet implemented.")
        messagebox.showinfo("STK", "STK extraction is not yet implemented.")

    def _connect_ports(self):
        ports = {k: v.get() for k, v in self.port_vars.items()}
        self._log(f"Connecting ports: {ports}")
        # Hardware connection would go here (I2C / serial)
        self._log("Port connection — hardware not attached (simulation mode).")

    def _disconnect_ports(self):
        self._log("Ports disconnected.")

    def _open_settings(self):
        """Open a dialog to edit coil parameters."""
        win = tk.Toplevel(self)
        win.title("Coil Parameters")
        win.configure(bg=self.FRAME_BG)
        win.resizable(False, False)
        win.geometry("360x200")

        entries = {}
        for i, ax in enumerate(["X", "Y", "Z"]):
            ttk.Label(win, text=f"{ax} Axis", style="Bold.TLabel").grid(
                row=0, column=i + 1, padx=10, pady=4)
        for r, param in enumerate(["N", "a", "gamma"]):
            ttk.Label(win, text=param, style="Bold.TLabel").grid(
                row=r + 1, column=0, padx=10, pady=4, sticky="e")
            for j, ax in enumerate(["X", "Y", "Z"]):
                var = tk.StringVar(value=str(self.COIL_PARAMS[ax][param]))
                ttk.Entry(win, textvariable=var, width=8,
                          font=self.LABEL_NORM, justify="center").grid(
                              row=r + 1, column=j + 1, padx=10, pady=4)
                entries[(ax, param)] = var

        def apply():
            for ax in ["X", "Y", "Z"]:
                for param in ["N", "a", "gamma"]:
                    try:
                        self.COIL_PARAMS[ax][param] = float(
                            entries[(ax, param)].get())
                    except ValueError:
                        pass
            self._log("Coil parameters updated.")
            win.destroy()

        ttk.Button(win, text="Apply", command=apply,
                   style="Accent.TButton").grid(
                       row=4, column=0, columnspan=4, pady=12)

    # --------------------------------------------------------------------- #
    # Simulation engine
    # --------------------------------------------------------------------- #
    def _get_rate_ms(self):
        try:
            val = float(self.rate_var.get())
        except ValueError:
            val = 1000
        if self.rate_unit_var.get().startswith("second"):
            val *= 1000
        return max(val, 10)  # floor at 10 ms

    def _calculate_step(self, bX, bY, bZ):
        """Calculate currents + duty cycles for a single B-field vector."""
        offsets = {
            ax: float(self._sim_vars[("offset", ax)].get() or 0)
            for ax in ["X", "Y", "Z"]
        }
        targets = {"X": bX, "Y": bY, "Z": bZ}
        currents = {}
        for ax in ["X", "Y", "Z"]:
            p = self.COIL_PARAMS[ax]
            coil = Coil(ax, targets[ax] - offsets[ax],
                        p["N"], p["a"], p["gamma"])
            currents[ax] = coil.single_current()
        return currents

    def _update_displays(self, bX, bY, bZ, currents, step, total):
        """Push values into the GUI (must be called from main thread)."""
        fields = {"X": bX, "Y": bY, "Z": bZ}
        for ax in ["X", "Y", "Z"]:
            self._sim_vars[("field", ax)].set(f"{fields[ax]:.6f}")
            self._sim_vars[("current", ax)].set(f"{currents[ax]:.4f}")
            self._sim_vars[("voltage", ax)].set(
                f"{abs(currents[ax]) * 2.0:.3f}")  # placeholder R≈2 Ω
            direction = "FWD (+)" if currents[ax] >= 0 else "REV (−)"
            self._dir_labels[ax].set(direction)
            dc = DutyCycleCalc.to_duty(currents[ax])
            self._dc_vars[ax].set(str(dc))

        pct = (step + 1) / total * 100 if total else 0
        self.progress_var.set(pct)
        self.pct_var.set(f"{pct:.1f} %")
        self.step_var.set(f"{step + 1} / {total}")

    def _sim_loop(self, dataset):
        total = len(dataset)
        rate_s = self._get_rate_ms() / 1000.0

        for idx, entry in enumerate(dataset):
            if not self._sim_running:
                break
            while self._sim_paused and self._sim_running:
                time.sleep(0.05)

            bX, bY, bZ = entry[0], entry[1], entry[2]
            currents = self._calculate_step(bX, bY, bZ)

            # schedule GUI update on main thread
            self.after(0, self._update_displays,
                       bX, bY, bZ, currents, idx, total)

            time.sleep(rate_s)

        self._sim_running = False
        self.after(0, lambda: self._log("Simulation finished." if idx == total - 1
                                         else "Simulation stopped."))

    def _run_simulation(self):
        if self._sim_running:
            self._log("Simulation already running.")
            return
        if not self.csv_data.loaded:
            self._log("No data loaded — cannot run simulation.")
            messagebox.showwarning("No Data", "Load and extract a CSV first.")
            return

        choice = self.dataset_var.get()
        ds = self.csv_data.dataset(choice)
        if not ds:
            self._log("Selected dataset is empty.")
            return

        self.dp_var.set(str(len(ds)))
        rate_ms = self._get_rate_ms()
        self.simtime_var.set(f"{len(ds) * rate_ms / 1000:.1f}")

        self._sim_running = True
        self._sim_paused = False
        self._log(f"▶ Running {self.csv_data.dataset_label(choice)} "
                  f"@ {rate_ms:.0f} ms/step …")
        self._sim_thread = threading.Thread(target=self._sim_loop,
                                            args=(ds,), daemon=True)
        self._sim_thread.start()

    def _stop_simulation(self):
        if self._sim_running:
            self._sim_running = False
            self._sim_paused = False
            self._log("■ Simulation stopped.")
        else:
            self._log("No simulation to stop.")

    def _pause_simulation(self):
        if self._sim_running and not self._sim_paused:
            self._sim_paused = True
            self._log("⏸ Simulation paused.")
        elif self._sim_paused:
            self._sim_paused = False
            self._log("▶ Simulation resumed.")
        else:
            self._log("No simulation is running.")


# ===========================================================================
# Entry point
# ===========================================================================
if __name__ == "__main__":
    app = HelmholtzCageApp()
    app.mainloop()
