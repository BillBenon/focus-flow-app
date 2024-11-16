import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class WellnessMonitorGUI:
    def __init__(self, config, database):
        self.config = config
        self.database = database
        self.setup_main_window()

    def setup_main_window(self):
        self.root = tk.Tk()
        self.root.title("Wellness Monitor")
        self.root.iconbitmap('icon.ico')  # You'll need to create an icon

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)

        # Create tabs
        self.dashboard_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)
        self.stats_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.dashboard_tab, text="Dashboard")
        self.notebook.add(self.settings_tab, text="Settings")
        self.notebook.add(self.stats_tab, text="Statistics")

        self.notebook.pack(expand=True, fill='both')

        self.setup_dashboard()
        self.setup_settings()
        self.setup_stats()

    def setup_dashboard(self):
        # Current status frame
        status_frame = ttk.LabelFrame(self.dashboard_tab, text="Current Status")
        status_frame.pack(padx=5, pady=5, fill='x')

        self.status_labels = {
            'last_break': ttk.Label(status_frame, text="Last break: Never"),
            'activity_level': ttk.Label(status_frame, text="Activity level: Normal"),
            'fatigue_level': ttk.Label(status_frame, text="Fatigue level: Low")
        }

        for label in self.status_labels.values():
            label.pack(padx=5, pady=2)

    def setup_settings(self):
        # Break intervals
        intervals_frame = ttk.LabelFrame(self.settings_tab, text="Break Intervals")
        intervals_frame.pack(padx=5, pady=5, fill='x')

        self.interval_vars = {}
        for break_type, seconds in self.config.settings['break_intervals'].items():
            var = tk.StringVar(value=str(seconds // 60))
            ttk.Label(intervals_frame, text=break_type.replace('_', ' ').title()).pack()
            ttk.Entry(intervals_frame, textvariable=var).pack()
            self.interval_vars[break_type] = var

        # Detection settings
        detection_frame = ttk.LabelFrame(self.settings_tab, text="Detection Settings")
        detection_frame.pack(padx=5, pady=5, fill='x')

        self.detection_vars = {}
        for setting, value in self.config.settings['detection_settings'].items():
            var = tk.DoubleVar(value=value)
            ttk.Label(detection_frame, text=setting.replace('_', ' ').title()).pack()
            ttk.Scale(detection_frame, from_=0, to=1, variable=var).pack()
            self.detection_vars[setting] = var

        # Save button
        ttk.Button(self.settings_tab, text="Save Settings",
                   command=self.save_settings).pack(pady=10)

    def setup_stats(self):
        # Create figure for plots
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(6, 8))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.stats_tab)
        self.canvas.get_tk_widget().pack()

        # Time range selector
        time_frame = ttk.Frame(self.stats_tab)
        time_frame.pack(pady=5)

        self.time_var = tk.StringVar(value="day")
        ttk.Radiobutton(time_frame, text="Day", variable=self.time_var,
                        value="day", command=self.update_stats).pack(side=tk.LEFT)
        ttk.Radiobutton(time_frame, text="Week", variable=self.time_var,
                        value="week", command=self.update_stats).pack(side=tk.LEFT)
        ttk.Radiobutton(time_frame, text="Month", variable=self.time_var,
                        value="month", command=self.update_stats).pack(side=tk.LEFT)

    def save_settings(self):
        # Update config with new values
        for break_type, var in self.interval_vars.items():
            self.config.settings['break_intervals'][break_type] = int(var.get()) * 60

        for setting, var in self.detection_vars.items():
            self.config.settings['detection_settings'][setting] = var.get()

        self.config.save_settings(self.config.settings)

    def update_stats(self):
        # Clear previous plots
        self.ax1.clear()
        self.ax2.clear()

        # Get data from database based on time range
        # Plot activity levels
        self.ax1.set_title("Activity Levels")
        # Add plotting code here

        # Plot fatigue events
        self.ax2.set_title("Fatigue Events")
        # Add plotting code here

        self.canvas.draw()

    def show(self):
        self.root.mainloop()
