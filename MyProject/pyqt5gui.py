import sys
import psutil
import subprocess
from collections import deque

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QGridLayout, QScrollArea
)
from PyQt5.QtCore import QTimer

import pyqtgraph as pg

class SystemMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced System Monitor")
        self.setGeometry(200, 100, 800, 600)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # ==== Basic Info Labels ====
        self.cpu_label = QLabel("Total CPU: --%")
        self.ram_label = QLabel("RAM: --")
        self.temp_label = QLabel("Temp: --")
        self.fan_label = QLabel("Fan: --")
        self.gpu_label = QLabel("GPU: --")

        for label in [self.cpu_label, self.ram_label, self.temp_label, self.fan_label, self.gpu_label]:
            label.setStyleSheet("font-weight: bold; font-size: 14px;")
            self.layout.addWidget(label)

        # ==== Per-core CPU charts ====
        self.core_charts_layout = QGridLayout()
        self.core_charts = []
        self.core_data = []
        self.num_cores = psutil.cpu_count(logical=True)

        for i in range(self.num_cores):
            plot = pg.PlotWidget()
            plot.setYRange(0, 100)
            plot.setTitle(f"Core {i}")
            curve = plot.plot()
            self.core_charts.append(curve)
            self.core_data.append(deque([0] * 60, maxlen=60))
            self.core_charts_layout.addWidget(plot, i // 2, i % 2)

        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_widget.setLayout(self.core_charts_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        self.layout.addWidget(scroll_area)

        # ==== Timer ====
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)

    def update_stats(self):
        # ==== CPU ====
        cpu_percent = psutil.cpu_percent()
        self.cpu_label.setText(f"Total CPU: {cpu_percent}%")

        per_core = psutil.cpu_percent(percpu=True)
        for i, usage in enumerate(per_core):
            self.core_data[i].append(usage)
            self.core_charts[i].setData(list(self.core_data[i]))

        # ==== RAM ====
        ram = psutil.virtual_memory()
        self.ram_label.setText(
            f"RAM: {ram.used // (1024**2)}MB / {ram.total // (1024**2)}MB ({ram.percent}%)"
        )

        # ==== Temperature ====
        try:
            output = subprocess.check_output("sensors", text=True).splitlines()
            temp_line = next((line for line in output if "Package id 0" in line or "temp" in line.lower()), "Temp: ?")
            self.temp_label.setText(f"Temp: {temp_line.strip()}")
        except Exception:
            self.temp_label.setText("Temp: [Unavailable]")

        # ==== Fan ====
        try:
            output = subprocess.check_output("sensors", text=True).splitlines()
            fan_lines = [line for line in output if "fan" in line.lower()]
            self.fan_label.setText("Fan: " + " | ".join(fan_lines) if fan_lines else "Fan: [Not Detected]")
        except Exception:
            self.fan_label.setText("Fan: [Unavailable]")

        # ==== GPU ====
        self.gpu_label.setText(self.get_gpu_info())

    def get_gpu_info(self):
        try:
            # Try NVIDIA
            output = subprocess.check_output(["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"], text=True)
            usage, mem_used, mem_total = output.strip().split(", ")
            return f"GPU: {usage}% | {mem_used}MB / {mem_total}MB (NVIDIA)"
        except:
            try:
                # Try Intel
                output = subprocess.check_output("glxinfo | grep 'Device'", shell=True, text=True)
                return "GPU: " + output.strip()
            except:
                return "GPU: [Unavailable]"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    pg.setConfigOptions(antialias=True)
    window = SystemMonitor()
    window.show()
    sys.exit(app.exec_())
