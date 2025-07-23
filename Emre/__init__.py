"""
STM32 Traffic Light Simulator Package

A modular traffic light simulation application with STM32 communication support.
"""

__version__ = "1.0.0"
__author__ = "Traffic Light Simulator Team"

# Import main components for easy access
from .gui import TrafficLightGUI
from .traffic_controller import TrafficLightController
from .serial_comm import SerialComm
from .utils import check_modbus_crc, modbus_crc16, select_port_dialog

__all__ = [
    'TrafficLightGUI',
    'TrafficLightController', 
    'SerialComm',
    'check_modbus_crc',
    'modbus_crc16',
    'select_port_dialog'
]
