import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import random
import serial
from serial.tools import list_ports
import sys


# --- Serial Communication ---
class SerialComm:
    def __init__(self, callback, port=None, baudrate=115200):
        self.callback = callback
        self.running = True
        self.ser = serial.Serial(port, baudrate, timeout=1)
        self.thread = threading.Thread(target=self.read_serial, daemon=True)
        self.thread.start()

    def read_serial(self):
        buffer = bytearray()
        ack = bytes([0xAC])
        while self.running:
            incoming = self.ser.read(self.ser.in_waiting)
            buffer.extend(incoming)
            if len(buffer) >= 8:
                data = buffer[:8]
                del buffer[:8]

                byte_array = list(data)
                if check_modbus_crc(data):
                    
                    if data[:6] == b'\x01\x02\x03\x04\x05\x06':
                        light = 'RED'
                        self.ser.write(ack)
                    elif data[:6] == b'\x06\x05\x04\x03\x02\x01':
                        light = 'GREEN'
                        self.ser.write(ack)
                    else:
                        light = 'UNKNOWN'
                    self.callback('IN', light, data)
                    self.callback('OUT', 'ACK', bytes(ack))

    def send_override(self, light):
        # Compose an 8-byte packet with the 3rd byte as the override request
        # 0x00 for RED, 0x01 for GREEN
        data = bytes([0x00]) if light == 'RED' else bytes([0x01])
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
    def __init__(self, root, baudrate=115200):
        self.root = root
        self.root.title("STM32 Traffic Light Simulator")
        self.controller = None
        self.baudrate = baudrate
        self.com_port = None
        self.connected = False
        self.setup_ui()
        self.current_state = 'RED'
        self.log_entries = []
        self.timer_id = None
        self.timer_remaining = 0
        self.previous_light = None
        self._last_ports = []
        self.refresh_ports()  # Start periodic port refresh

    def setup_ui(self):
        # Port selection UI
        port_frame = tk.Frame(self.root)
        port_frame.pack(pady=5)
        tk.Label(port_frame, text="Select COM Port:").pack(side='left', padx=5)
        ports = list(list_ports.comports())
        port_list = [port.device for port in ports]
        self.selected_port = tk.StringVar(value=port_list[0] if port_list else "")
        self.port_combo = ttk.Combobox(port_frame, textvariable=self.selected_port, values=port_list, state="readonly", width=10)
        self.port_combo.pack(side='left', padx=5)
        self.connect_btn = tk.Button(port_frame, text="Connect", command=self.connect_port)
        self.connect_btn.pack(side='left', padx=5)

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
            car_canvas = tk.Canvas(frame, width=120, height=30, bg='white', highlightthickness=1, relief='ridge')
            car_canvas.pack(side='left', padx=20)
            self.car_canvases[label] = car_canvas
            self.draw_cars(label, stopped=True)
        self.timer_label = tk.Label(main_frame, text="", font=("Arial", 14, "bold"), fg="blue")
        self.timer_label.grid(row=2, column=0, pady=10)
        log_frame = tk.Frame(self.root)
        log_frame.pack(pady=10, fill='x')
        tk.Label(log_frame, text="Log:").pack(side='left')
        self.log_box = scrolledtext.ScrolledText(log_frame, width=80, height=16, state='disabled')
        self.log_box.pack(pady=5)

    def refresh_ports(self):
        if not self.connected:
            ports = list(list_ports.comports())
            port_list = [port.device for port in ports]
            if port_list != self._last_ports:
                self.port_combo['values'] = port_list
                # If the currently selected port is gone, select the first available
                if self.selected_port.get() not in port_list:
                    self.selected_port.set(port_list[0] if port_list else "")
                self._last_ports = port_list
            self.root.after(1000, self.refresh_ports)

    def connect_port(self):
        port = self.selected_port.get()
        if not port:
            messagebox.showerror("No Port Selected", "Please select a COM port.")
            return
        self.com_port = port
        self.controller = TrafficLightController(self.log_event, port=port, baudrate=self.baudrate)
        self.update_lights('RED', None)
        self.animate_cars('Main')
        self.animate_cars('Side')
        self.connect_btn.config(state='disabled')
        self.port_combo.config(state='disabled')
        self.connected = True

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
            self.current_state = light
            self.update_lights(light, data)
            self.reset_timer_on_signal(light)
            self.reset_car_positions_on_signal()
            self.previous_light = light

    def reset_timer_on_signal(self, light):
        # Always reset timer to 15 on every signal (if RED or GREEN)
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
        self.timer_label.config(text="")
        if light == 'RED':
            self.timer_remaining = 10
            self.update_timer_label(light)
        elif light == 'GREEN' :
            self.timer_remaining = 6
            self.update_timer_label(light)
        else:
            self.timer_remaining = 0
            self.timer_label.config(text="")

    def reset_car_positions_on_signal(self):
        # Reset car positions so speed does not increase with every signal
        self.car_positions = {'Main': 0, 'Side': 0}

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
        if self.controller:
            self.controller.close()
        self.root.destroy()

def check_modbus_crc(data: bytes) -> bool:
    if len(data) < 3:
        return False  # min. 1 byte data + 2 byte CRC
    received_crc = data[-2] | (data[-1] << 8)  # LSB + MSB
    calculated_crc = modbus_crc16(data[:-2])
    return received_crc == calculated_crc


def modbus_crc16(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc

def select_port_dialog(parent):
    ports = list(list_ports.comports())
    port_list = [port.device for port in ports]
    if not port_list:
        messagebox.showerror("No Ports", "No serial ports found!", parent=parent)
        parent.destroy()
        sys.exit(1)
    dialog = tk.Toplevel(parent)
    dialog.title("Select COM Port")
    dialog.grab_set()
    tk.Label(dialog, text="Select COM Port:").pack(padx=10, pady=10)
    selected_port = tk.StringVar(value=port_list[0])
    combo = ttk.Combobox(dialog, textvariable=selected_port, values=port_list, state="readonly")
    combo.pack(padx=10, pady=5)
    def on_ok():
        dialog.destroy()
    tk.Button(dialog, text="OK", command=on_ok).pack(pady=10)
    dialog.protocol("WM_DELETE_WINDOW", lambda: None)  # Disable close button
    parent.wait_window(dialog)
    return selected_port.get()
        
if __name__ == "__main__":
    root = tk.Tk()
    app = TrafficLightGUI(root, baudrate=115200)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()

