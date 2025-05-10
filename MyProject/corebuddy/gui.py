import tkinter as tk
import psutil

def update_stats():
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    label.config(text=f"CPU: {cpu}%\nRAM: {ram}%")
    root.after(2000, update_stats)

root = tk.Tk()
root.title("Simple System Monitor")
root.geometry("200x100")

label = tk.Label(root, text="Loading...", font=("Helvetica", 14))
label.pack(pady=20)

update_stats()
root.mainloop()
