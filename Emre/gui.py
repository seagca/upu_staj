"""
GUI module for the traffic light simulator.
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import time
from serial.tools import list_ports
from traffic_controller import TrafficLightController


class TrafficLightGUI:
    """Main GUI application for the traffic light simulator."""
    
    def __init__(self, root, baudrate=115200):
        """
        Initialize the GUI application.
        
        Args:
            root: Tkinter root window
            baudrate: Serial communication baud rate
        """
        self.root = root
        self.root.title("STM32 Traffic Light Simulator")
        self.controller = None
        self.baudrate = baudrate
        self.com_port = None
        self.connected = False
        
        # Initialize GUI state variables
        self.current_state = 'RED'
        self.log_entries = []
        self.timer_id = None
        self.timer_remaining = 0
        self.previous_light = None
        self._last_ports = []
        
        # Initialize GUI elements containers
        self.lights = {'Main': {}, 'Side': {}}
        self.car_canvases = {'Main': None, 'Side': None}
        self.car_positions = {'Main': 0, 'Side': 0}
        
        # Setup the user interface
        self.setup_ui()
        self.refresh_ports()  # Start periodic port refresh

    def setup_ui(self):
        """Setup the user interface components."""
        self._setup_port_selection()
        self._setup_main_interface()
        self._setup_log_interface()

    def _setup_port_selection(self):
        """Setup the COM port selection interface."""
        port_frame = tk.Frame(self.root)
        port_frame.pack(pady=5)
        
        tk.Label(port_frame, text="Select COM Port:").pack(side='left', padx=5)
        
        ports = list(list_ports.comports())
        port_list = [port.device for port in ports]
        self.selected_port = tk.StringVar(value=port_list[0] if port_list else "")
        
        self.port_combo = ttk.Combobox(
            port_frame, 
            textvariable=self.selected_port, 
            values=port_list, 
            state="readonly", 
            width=10
        )
        self.port_combo.pack(side='left', padx=5)
        
        self.connect_btn = tk.Button(port_frame, text="Connect", command=self.connect_port)
        self.connect_btn.pack(side='left', padx=5)

    def _setup_main_interface(self):
        """Setup the main traffic light and car animation interface."""
        main_frame = tk.Frame(self.root)
        main_frame.pack(pady=10)
        
        # Create traffic lights and car canvases for each road
        for row, label in enumerate(['Main', 'Side']):
            frame = tk.Frame(main_frame)
            frame.grid(row=row, column=0, pady=5)
            
            tk.Label(frame, text=f"{label} Road", font=("Arial", 12, "bold")).pack(side='left', padx=10)
            
            # Create traffic light controls
            for light in ['RED', 'GREEN']:
                col = tk.Frame(frame)
                col.pack(side='left', padx=10)
                
                canvas = tk.Canvas(col, width=40, height=40, bg='black', highlightthickness=0)
                oval = canvas.create_oval(5, 5, 35, 35, fill='gray')
                canvas.pack()
                
                btn = tk.Button(
                    col, 
                    text=f"Override {light}", 
                    command=lambda l=light, road=label: self.manual_override(l, road)
                )
                btn.pack(pady=2)
                
                self.lights[label][light] = {'canvas': canvas, 'oval': oval}
            
            # Create car animation canvas
            car_canvas = tk.Canvas(
                frame, 
                width=120, 
                height=30, 
                bg='white', 
                highlightthickness=1, 
                relief='ridge'
            )
            car_canvas.pack(side='left', padx=20)
            self.car_canvases[label] = car_canvas
            self.draw_cars(label, stopped=True)
        
        # Create timer label
        self.timer_label = tk.Label(main_frame, text="", font=("Arial", 14, "bold"), fg="blue")
        self.timer_label.grid(row=2, column=0, pady=10)

    def _setup_log_interface(self):
        """Setup the log display interface."""
        log_frame = tk.Frame(self.root)
        log_frame.pack(pady=10, fill='x')
        
        tk.Label(log_frame, text="Log:").pack(side='left')
        self.log_box = scrolledtext.ScrolledText(log_frame, width=80, height=16, state='disabled')
        self.log_box.pack(pady=5)

    def refresh_ports(self):
        """Periodically refresh the list of available COM ports."""
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
        """Connect to the selected COM port."""
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
        """
        Draw cars on the specified road canvas.
        
        Args:
            road: 'Main' or 'Side' road
            stopped: Whether cars should be drawn as stopped
        """
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
        """
        Animate cars on the specified road.
        
        Args:
            road: 'Main' or 'Side' road
        """
        # Move cars if green, else keep them stopped
        if (road == 'Main' and self.current_state == 'GREEN') or (road == 'Side' and self.current_state == 'RED'):
            self.car_positions[road] = (self.car_positions[road] + 5) % 90
            self.draw_cars(road, stopped=False)
        else:
            self.draw_cars(road, stopped=True)
        
        self.root.after(150, lambda: self.animate_cars(road))

    def update_lights(self, active_light, data):
        """
        Update the traffic light display.
        
        Args:
            active_light: Currently active light ('RED' or 'GREEN')
            data: Associated data (unused)
        """
        # Main and Side are always opposite
        for road in ['Main', 'Side']:
            for light, info in self.lights[road].items():
                color = {'RED': 'red', 'GREEN': 'green'}[light]
                if road == 'Main':
                    fill = color if light == active_light else 'gray'
                else:  # Side road
                    fill = color if light != active_light else 'gray'
                info['canvas'].itemconfig(info['oval'], fill=fill)

    def log_event(self, direction, light, data):
        """
        Log an event and update the GUI accordingly.
        
        Args:
            direction: 'IN' or 'OUT'
            light: Light state
            data: Raw packet data
        """
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
        """
        Reset and start the timer based on the current light.
        
        Args:
            light: Current light state
        """
        # Always reset timer to 15 on every signal (if RED or GREEN)
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
        self.timer_label.config(text="")
        
        if light == 'RED':
            self.timer_remaining = 10
            self.update_timer_label(light)
        elif light == 'GREEN':
            self.timer_remaining = 6
            self.update_timer_label(light)
        else:
            self.timer_remaining = 0
            self.timer_label.config(text="")

    def reset_car_positions_on_signal(self):
        """Reset car positions so speed does not increase with every signal."""
        self.car_positions = {'Main': 0, 'Side': 0}

    def update_timer_label(self, light):
        """
        Update the timer display.
        
        Args:
            light: Current light state
        """
        if self.timer_remaining > 0:
            self.timer_label.config(text=f"{self.timer_remaining}")
            self.timer_remaining -= 1
            self.timer_id = self.root.after(1000, lambda: self.update_timer_label(light))
        else:
            self.timer_label.config(text="0")
            self.timer_id = None

    def update_log_box(self):
        """Update the log display with recent entries."""
        self.log_box.config(state='normal')
        self.log_box.delete(1.0, tk.END)
        
        # Show last 100 entries
        for entry in self.log_entries[-100:]:
            log_line = f"[{entry['time']}] {entry['direction']} | Light: {entry['light']} | Data: {entry['data']}\n"
            self.log_box.insert(tk.END, log_line)
        
        self.log_box.config(state='disabled')
        self.log_box.see(tk.END)

    def manual_override(self, light, road):
        """
        Handle manual override button press.
        
        Args:
            light: Light to override to ('RED' or 'GREEN')
            road: Road that was clicked ('Main' or 'Side')
        """
        if not self.controller:
            return
        
        # For Side road, send the opposite light to Main road
        if road == 'Side':
            main_light = 'GREEN' if light == 'RED' else 'RED'
            self.controller.manual_override(main_light)
        else:
            self.controller.manual_override(light)

    def on_close(self):
        """Handle application close event."""
        if self.controller:
            self.controller.close()
        self.root.destroy()
