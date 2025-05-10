import sys
import psutil
import subprocess
from collections import deque

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QStackedLayout, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import QTimer, Qt
import pyqtgraph as pg

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Linux System Dashboard")
        self.setGeometry(200, 100, 1000, 600)

        # ==== MAIN LAYOUT ====
        main_layout = QHBoxLayout(self)

        # ==== SIDEBAR ====
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(150)
        self.sidebar.setStyleSheet("background-color: #2c2c2c; color: white; font-size: 14px;")
        for item in ["Overview", "CPU", "RAM", "GPU", "Temp/Fan"]:
            QListWidgetItem(item, self.sidebar)
        self.sidebar.currentRowChanged.connect(self.switch_page)
        main_layout.addWidget(self.sidebar)

        # ==== STACKED PAGES ====
        self.pages = QStackedLayout()
        main_layout.addLayout(self.pages)

        # Add Pages
        self.pages.addWidget(self.create_overview_page())
        self.pages.addWidget(self.create_cpu_page())
        self.pages.addWidget(self.create_ram_page())
        self.pages.addWidget(self.create_gpu_page())
        self.pages.addWidget(self.create_temp_fan_page())

        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_all_stats)
        self.timer.start(1000)

        pg.setConfigOptions(antialias=True)

    def create_overview_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.label_overview = QLabel("System Overview")
        self.label_overview.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        layout.addWidget(self.label_overview)
        page.setStyleSheet("background-color: #1e1e1e;")
        return page

    def create_cpu_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.cpu_label = QLabel("Total CPU Usage:")
        self.cpu_label.setStyleSheet("color: white; font-size: 14px;")
        layout.addWidget(self.cpu_label)

        self.cpu_graphs = []
        self.cpu_data = []
        self.num_cores = psutil.cpu_count(logical=True)

        for i in range(self.num_cores):
            graph = pg.PlotWidget()
            graph.setYRange(0, 100)
            graph.setBackground('#1e1e1e')
            graph.setTitle(f"Core {i}", color='w')
            graph.getAxis('left').setPen(pg.mkPen(color='w'))
            graph.getAxis('bottom').setPen(pg.mkPen(color='w'))
            curve = graph.plot(pen=pg.mkPen(color='cyan'))
            self.cpu_graphs.append(curve)
            self.cpu_data.append(deque([0]*60, maxlen=60))
            layout.addWidget(graph)

        page.setStyleSheet("background-color: #1e1e1e;")
        return page

    def create_ram_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.ram_label = QLabel("RAM:")
        self.ram_label.setStyleSheet("color: white; font-size: 14px;")
        layout.addWidget(self.ram_label)
        page.setStyleSheet("background-color: #1e1e1e;")
        return page

    def create_gpu_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.gpu_label = QLabel("GPU Info:")
        self.gpu_label.setStyleSheet("color: white; font-size: 14px;")
        layout.addWidget(self.gpu_label)
        page.setStyleSheet("background-color: #1e1e1e;")
        return page

    def create_temp_fan_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.temp_label = QLabel("Temperature:")
        self.fan_label = QLabel("Fan Speed:")
        for lbl in [self.temp_label, self.fan_label]:
            lbl.setStyleSheet("color: white; font-size: 14px;")
            layout.addWidget(lbl)
        page.setStyleSheet("background-color: #1e1e1e;")
        return page

    def switch_page(self, index):
        self.pages.setCurrentIndex(index)

    def update_all_stats(self):
        # CPU
        total = psutil.cpu_percent()
        self.cpu_label.setText(f"Total CPU Usage: {total}%")

        per_core = psutil.cpu_percent(percpu=True)
        for i, usage in enumerate(per_core):
            self.cpu_data[i].append(usage)
            self.cpu_graphs[i].setData(self.cpu_data[i])

        # RAM
        ram = psutil.virtual_memory()
        self.ram_label.setText(
            f"RAM Usage: {ram.used // (1024**2)}MB / {ram.total // (1024**2)}MB ({ram.percent}%)"
        )

        # Temp
        try:
            output = subprocess.check_output("sensors", text=True).splitlines()
            temp_line = next((line for line in output if "Package id 0" in line or "temp" in line.lower()), "Temp: ?")
            self.temp_label.setText(f"Temperature: {temp_line.strip()}")
        except:
            self.temp_label.setText("Temperature: [Unavailable]")

        # Fan
        try:
            output = subprocess.check_output("sensors", text=True).splitlines()
            fan_lines = [line for line in output if "fan" in line.lower()]
            self.fan_label.setText("Fan: " + " | ".join(fan_lines) if fan_lines else "Fan: [Not Detected]")
        except:
            self.fan_label.setText("Fan: [Unavailable]")

        # GPU
        self.gpu_label.setText(self.get_gpu_info())

    def get_gpu_info(self):
        try:
            output = subprocess.check_output([
                "nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits"
            ], text=True)
            usage, mem_used, mem_total = output.strip().split(", ")
            return f"GPU: {usage}% | {mem_used}MB / {mem_total}MB (NVIDIA)"
        except:
            try:
                output = subprocess.check_output("glxinfo | grep 'Device'", shell=True, text=True)
                return "GPU: " + output.strip()
            except:
                return "GPU: [Unavailable]"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Dashboard()
    window.show()
    sys.exit(app.exec_())
