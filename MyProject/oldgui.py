import sys
import psutil
import subprocess
from collections import deque

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QStackedLayout, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import QTimer, Qt
import pyqtgraph as pg
from PyQt5.QtWidgets import QScrollArea, QSizePolicy, QWidget

class RGBDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Neon RGB System Dashboard")
        self.setGeometry(100, 100, 1000, 700)
        self.setStyleSheet("background-color: #121212;")

        # Main Layout
        main_layout = QHBoxLayout(self)

        # Sidebar
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(180)
        self.sidebar.setStyleSheet("""
            QListWidget {
                background-color: #1c1c1c;
                color: white;
                font-size: 16px;
                border-right: 2px solid #333;
            }
            QListWidget::item:hover {
                background-color: #333;
                color: cyan;
            }
            QListWidget::item:selected {
                background-color: #292929;
                border-left: 4px solid cyan;
                color: magenta;
            }
        """)
        for item in ["Overview", "CPU", "RAM", "GPU", "Temp/Fan"]:
            QListWidgetItem(item, self.sidebar)
        self.sidebar.currentRowChanged.connect(self.switch_page)
        main_layout.addWidget(self.sidebar)

        # Pages
        self.pages = QStackedLayout()
        main_layout.addLayout(self.pages)

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

    def neon_card(self, title):
        label = QLabel(title)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 18px;
                padding: 15px;
                margin: 10px;
                border: 2px solid #00ffff;
                border-radius: 10px;
                background-color: #1a1a1a;
                box-shadow: 0 0 10px #00ffff;
            }
        """)
        return label

    def create_overview_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.label_overview = self.neon_card("System Overview")
        layout.addWidget(self.label_overview)
        return page
    
    def create_cpu_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        self.cpu_label = self.neon_card("Total CPU Usage:")
        layout.addWidget(self.cpu_label)

    # Scroll area for graphs
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: none;")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        self.cpu_graphs = []
        self.cpu_data = []
        self.num_cores = psutil.cpu_count(logical=True)

        for i in range(self.num_cores):
            graph = pg.PlotWidget()
            graph.setYRange(0, 100)
            graph.setBackground('#121212')
            graph.setTitle(f"Core {i}", color='w')
            graph.getAxis('left').setPen(pg.mkPen(color='w'))
            graph.getAxis('bottom').setPen(pg.mkPen(color='w'))
            curve = graph.plot(pen=pg.mkPen(color='magenta'))
            self.cpu_graphs.append(curve)
            self.cpu_data.append(deque([0]*60, maxlen=60))
            scroll_layout.addWidget(graph)

        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        return page


   

    def create_ram_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.ram_label = self.neon_card("RAM:")
        layout.addWidget(self.ram_label)
        return page

    def create_gpu_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.gpu_label = self.neon_card("GPU Info:")
        layout.addWidget(self.gpu_label)
        return page

    def create_temp_fan_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.temp_label = self.neon_card("Temperature:")
        self.fan_label = self.neon_card("Fan Speed:")
        layout.addWidget(self.temp_label)
        layout.addWidget(self.fan_label)
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
    window = RGBDashboard()
    window.show()
    sys.exit(app.exec_())
