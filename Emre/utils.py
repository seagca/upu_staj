"""
Utility functions for the traffic light simulator.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from serial.tools import list_ports
import sys


def check_modbus_crc(data: bytes) -> bool:
    """
    Check if the Modbus CRC is valid for the given data.
    
    Args:
        data: The data bytes including CRC
        
    Returns:
        bool: True if CRC is valid, False otherwise
    """
    if len(data) < 3:
        return False  # min. 1 byte data + 2 byte CRC
    received_crc = data[-2] | (data[-1] << 8)  # LSB + MSB
    calculated_crc = modbus_crc16(data[:-2])
    return received_crc == calculated_crc


def modbus_crc16(data: bytes) -> int:
    """
    Calculate Modbus CRC16 for the given data.
    
    Args:
        data: The data bytes to calculate CRC for
        
    Returns:
        int: The calculated CRC16 value
    """
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
    """
    Show a dialog to select a COM port.
    
    Args:
        parent: The parent window
        
    Returns:
        str: The selected COM port
    """
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
