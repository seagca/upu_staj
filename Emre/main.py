import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
import random
import serial

# --- Serial Communication ---
class SerialComm:
    def __init__(self, callback, port=None, baudrate=115200):
        self.callback = callback
        self.running = True
        self.ser = serial.Serial(port, baudrate, timeout=1)
        self.thread = threading.Thread(target=self.read_serial, daemon=True)
        self.thread.start()

    def read_serial(self):
        while self.running:
            if self.ser.in_waiting >= 8:
                data = self.ser.read(8)
                if data:
                    light_code = data[2]
                    if light_code == 0x00:
                        light = 'RED'
                    elif light_code == 0x01:
                        light = 'GREEN'
                    else:
                        light = 'UNKNOWN'
                    self.callback('IN', light, data)
            time.sleep(0.01)

    def send_override(self, light):
        # Compose an 8-byte packet with the 3rd byte as the override request
        # 0x00 for RED, 0x01 for GREEN
        data = bytearray(8)
        data[2] = 0x00 if light == 'RED' else 0x01
        self.ser.write(data)
        self.callback('OUT', light, bytes(data))

    def close(self):
        self.running = False
        self.ser.close()

# --- Traffic Light Controller ---
class TrafficLightController:
    def __init__(self, gui_callback, port=None, baudrate=115200):
        self.gui_callback = gui_callback
        self.serial = SerialComm(self.handle_packet, port=port, baudrate=baudrate)
        self.current_state = 'RED'  # RED, GREEN

    def handle_packet(self, direction, light, data):
        if direction == 'IN':
            self.current_state = light
        self.gui_callback(direction, light, data)

    def manual_override(self, light):
        self.serial.send_override(light)

    def close(self):
        self.serial.close()

# --- GUI ---
class TrafficLightGUI:
    def __init__(self, root, port=None, baudrate=115200):
        self.root = root
        self.root.title("STM32 Traffic Light Simulator")
        self.controller = TrafficLightController(self.log_event, port=port, baudrate=baudrate)
        self.setup_ui()
        self.current_state = 'RED'
        self.update_lights('RED', None)
        self.log_entries = []
        self.timer_id = None
        self.timer_remaining = 0
        # self.timer_label = None  # Removed, set in setup_ui
        self.previous_light = None # Added for assumptional timer logic

    def setup_ui(self):
        main_frame = tk.Frame(self.root)
        main_frame.pack(pady=10)
        self.lights = {'Main': {}, 'Side': {}}
        self.car_canvases = {'Main': None, 'Side': None}
        self.car_positions = {'Main': 0, 'Side': 0}
        colors = {'RED': 'red', 'GREEN': 'green'}
        for row, label in enumerate(['Main', 'Side']):
            frame = tk.Frame(main_frame)
            frame.grid(row=row, column=0, pady=5)
            tk.Label(frame, text=f"{label} Road", font=("Arial", 12, "bold")).pack(side='left', padx=10)
            for idx, light in enumerate(['RED', 'GREEN']):
                col = tk.Frame(frame)
                col.pack(side='left', padx=10)
                canvas = tk.Canvas(col, width=40, height=40, bg='black', highlightthickness=0)
                oval = canvas.create_oval(5, 5, 35, 35, fill='gray')
                canvas.pack()
                btn = tk.Button(col, text=f"Override {light}", command=lambda l=light, road=label: self.manual_override(l, road))
                btn.pack(pady=2)
                self.lights[label][light] = {'canvas': canvas, 'oval': oval}
            # Add car canvas to the right of the lights
            car_canvas = tk.Canvas(frame, width=120, height=30, bg='white', highlightthickness=1, relief='ridge')
            car_canvas.pack(side='left', padx=20)
            self.car_canvases[label] = car_canvas
            self.draw_cars(label, stopped=True)
        # Timer label (for user visual aid)
        self.timer_label = tk.Label(main_frame, text="", font=("Arial", 14, "bold"), fg="blue")
        self.timer_label.grid(row=2, column=0, pady=10)

        # Log box (make it wider and keep it tall)
        log_frame = tk.Frame(self.root)
        log_frame.pack(pady=10, fill='x')
        tk.Label(log_frame, text="Log:").pack(side='left')
        self.log_box = scrolledtext.ScrolledText(log_frame, width=80, height=16, state='disabled')
        self.log_box.pack(pady=5)

    def draw_cars(self, road, stopped):
        car_canvas = self.car_canvases[road]
        car_canvas.delete('all')
        # Draw 3 cars
        for i in range(3):
            if stopped:
                x = 10 + i * 30
            else:
                # Animate cars moving from left to right
                pos = self.car_positions[road]
                x = 10 + ((i * 30 + pos) % 90)
            car_canvas.create_rectangle(x, 10, x+18, 28, fill='blue', outline='black')

    def animate_cars(self, road):
        # Move cars if green, else keep them stopped
        if (road == 'Main' and self.current_state == 'GREEN') or (road == 'Side' and self.current_state == 'RED'):
            self.car_positions[road] = (self.car_positions[road] + 5) % 90
            self.draw_cars(road, stopped=False)
        else:
            self.draw_cars(road, stopped=True)
        self.root.after(150, lambda: self.animate_cars(road))

    def update_lights(self, active_light, data):
        # Main and Side are always opposite
        for road in ['Main', 'Side']:
            for light, info in self.lights[road].items():
                color = {'RED': 'red', 'GREEN': 'green'}[light]
                if road == 'Main':
                    fill = color if light == active_light else 'gray'
                else:  # Side road
                    fill = color if light != active_light else 'gray'
                info['canvas'].itemconfig(info['oval'], fill=fill)
        # Animate cars for both roads
        self.animate_cars('Main')
        self.animate_cars('Side')

    def log_event(self, direction, light, data):
        entry = {
            'direction': direction,
            'light': light,
            'data': ' '.join(f'{b:02X}' for b in data[:8]) if data else '',
            'time': time.strftime('%H:%M:%S')
        }
        self.log_entries.append(entry)
        self.update_log_box()
        if direction == 'IN':
            previous_light = getattr(self, 'previous_light', None)
            self.current_state = light
            self.update_lights(light, data)
            self.handle_assumptional_timer(light, previous_light)
            self.previous_light = light

    def handle_assumptional_timer(self, light, previous_light):
        # Only reset timer if light changes (RED<->GREEN)
        if previous_light != light:
            if self.timer_id:
                self.root.after_cancel(self.timer_id)
                self.timer_id = None
            self.timer_label.config(text="")
            if light == 'RED' or light == 'GREEN':
                self.timer_remaining = 15
                self.update_timer_label(light)
            else:
                self.timer_remaining = 0
                self.timer_label.config(text="")
        # If timer ended and same color keeps coming, reset to 15
        elif self.timer_remaining == 0 and (light == 'RED' or light == 'GREEN'):
            if self.timer_id:
                self.root.after_cancel(self.timer_id)
                self.timer_id = None
            self.timer_remaining = 15
            self.update_timer_label(light)

    def update_timer_label(self, light):
        if self.timer_remaining > 0:
            self.timer_label.config(text=f"{self.timer_remaining}")
            self.timer_remaining -= 1
            self.timer_id = self.root.after(1000, lambda: self.update_timer_label(light))
        else:
            self.timer_label.config(text="0")
            self.timer_id = None

    def update_log_box(self):
        self.log_box.config(state='normal')
        self.log_box.delete(1.0, tk.END)
        for entry in self.log_entries[-100:]:  # Show last 100 entries
            self.log_box.insert(tk.END, f"[{entry['time']}] {entry['direction']} | Light: {entry['light']} | Data: {entry['data']}\n")
        self.log_box.config(state='disabled')
        self.log_box.see(tk.END)

    def manual_override(self, light, road):
        # For Side road, send the opposite light to Main road
        if road == 'Side':
            main_light = 'GREEN' if light == 'RED' else 'RED'
            self.controller.manual_override(main_light)
        else:
            self.controller.manual_override(light)

    def on_close(self):
        self.controller.close()
        self.root.destroy()

if __name__ == "__main__":
    COM_PORT = "COM3"
    BAUDRATE = 115200
    root = tk.Tk()
    app = TrafficLightGUI(root, port=COM_PORT, baudrate=BAUDRATE)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
