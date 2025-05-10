import psutil
import subprocess
import time
import os

def get_cpu_usage():
    return psutil.cpu_percent(interval=1, percpu=True)

def get_ram_usage():
    return psutil.virtual_memory().percent

def get_temperatures():
    try:
        output = subprocess.check_output("sensors", text=True)
        return output
    except subprocess.CalledProcessError:
        return "Error reading sensors"

def clear_screen():
    os.system("clear")  # use 'cls' on Windows

if __name__ == "__main__":
    while True:
        clear_screen()
        print("=== System Monitor ===")
        print("CPU Usage:", get_cpu_usage())
        print("RAM Usage:", get_ram_usage())
        print("Temperatures:\n", get_temperatures())
        time.sleep(2)
