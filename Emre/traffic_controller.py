"""
Traffic light controller module.
"""
from serial_comm import SerialComm


class TrafficLightController:
    """Controls the traffic light system and handles communication."""
    
    def __init__(self, gui_callback, port=None, baudrate=115200):
        """
        Initialize the traffic light controller.
        
        Args:
            gui_callback: Function to call when events occur
            port: COM port for serial communication
            baudrate: Baud rate for serial communication
        """
        self.gui_callback = gui_callback
        self.serial = SerialComm(self.handle_packet, port=port, baudrate=baudrate)
        self.current_state = 'RED'  # RED, GREEN

    def handle_packet(self, direction, light, data):
        """
        Handle incoming/outgoing packets from serial communication.
        
        Args:
            direction: 'IN' or 'OUT'
            light: Light state ('RED', 'GREEN', etc.)
            data: Raw packet data
        """
        if direction == 'IN':
            self.current_state = light
        self.gui_callback(direction, light, data)

    def manual_override(self, light):
        """
        Send manual override command.
        
        Args:
            light: 'RED' or 'GREEN' to override to
        """
        self.serial.send_override(light)

    def close(self):
        """Close the controller and serial connection."""
        if hasattr(self, 'serial'):
            self.serial.close()
