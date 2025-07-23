"""
Main entry point for the STM32 Traffic Light Simulator.

This modular application consists of:
- utils.py: Utility functions (CRC, port selection)
- serial_comm.py: Serial communication handling
- traffic_controller.py: Traffic light control logic
- gui.py: User interface components
"""
import tkinter as tk
from gui import TrafficLightGUI


def main():
    """Main application entry point."""
    root = tk.Tk()
    app = TrafficLightGUI(root, baudrate=115200)
    
    # Handle window close event
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    
    # Start the main event loop
    root.mainloop()


if __name__ == "__main__":
    main()
