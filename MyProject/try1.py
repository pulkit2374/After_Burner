import sys
import psutil
import subprocess
from collections import deque

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QStackedLayout, QListWidget, QListWidgetItem, QGraphicsView,
    QGraphicsScene, QGraphicsEllipseItem
)
from PyQt5.QtCore import QTimer, Qt, QRectF
from PyQt5.QtGui import QBrush, QColor, QPen
import pyqtgraph as pg

class RGBDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Neon RGB System Dashboard")
        self.setGeometry(200, 100, 1200, 800)
        self.setMinimumSize(800, 600)
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
            layout.addWidget(graph)

        return page

    def create_ram_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.ram_label = self.neon_card("RAM:")
        layout.addWidget(self.ram_label)

        self.ram_scene = QGraphicsScene()
        self.ram_view = QGraphicsView(self.ram_scene)
        self.ram_view.setStyleSheet("background-color: #121212;")
        layout.addWidget(self.ram_view)

        return page

    def create_gpu_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.gpu_label = self.neon_card("GPU Info:")
        layout.addWidget(self.gpu_label)

        self.gpu_scene = QGraphicsScene()
        self.gpu_view = QGraphicsView(self.gpu_scene)
        self.gpu_view.setStyleSheet("background-color: #121212;")
        layout.addWidget(self.gpu_view)

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

    def draw_pie_chart(self, scene, percent_used, used_color, free_color):
        scene.clear()
        size = min(self.width(), self.height()) // 6
        rect = QRectF(0, 0, size, size)

        used_item = QGraphicsEllipseItem(rect)
        used_item.setStartAngle(0)
        used_item.setSpanAngle(int(percent_used * 16 * 3.6))
        used_item.setBrush(QBrush(QColor(*used_color)))
        used_item.setPen(QPen(QColor(*used_color), 2))

        free_item = QGraphicsEllipseItem(rect)
        free_item.setStartAngle(int(percent_used * 16 * 3.6))
        free_item.setSpanAngle(5760 - int(percent_used * 16 * 3.6))
        free_item.setBrush(QBrush(QColor(*free_color)))
        free_item.setPen(QPen(QColor(*free_color), 2))

        scene.addItem(free_item)
        scene.addItem(used_item)

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
        self.draw_pie_chart(self.ram_scene, ram.percent, (255, 0, 255), (50, 50, 50))

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
        gpu_text = self.get_gpu_info()
        self.gpu_label.setText(gpu_text)

        try:
            if "NVIDIA" in gpu_text:
                usage, mem_used, mem_total = gpu_text.split("|")[1].strip().split(" ")[0], gpu_text.split("/")[0].split()[-1][:-2], gpu_text.split("/")[1].split("M")[0]
                mem_used = int(mem_used)
                mem_total = int(mem_total)
                percent_used = (mem_used / mem_total) * 100
                self.draw_pie_chart(self.gpu_scene, percent_used, (0, 255, 255), (50, 50, 50))
            else:
                self.draw_pie_chart(self.gpu_scene, 0, (100, 100, 100), (30, 30, 30))
        except:
            self.draw_pie_chart(self.gpu_scene, 0, (100, 100, 100), (30, 30, 30))

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
