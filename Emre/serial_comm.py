"""
Serial communication module for the traffic light simulator.
"""
import threading
import serial
from utils import check_modbus_crc


class SerialComm:
    """Handles serial communication with the STM32 device."""
    
    def __init__(self, callback, port=None, baudrate=115200):
        """
        Initialize serial communication.
        
        Args:
            callback: Function to call when data is received
            port: COM port to use
            baudrate: Baud rate for communication
        """
        self.callback = callback
        self.running = True
        self.ser = serial.Serial(port, baudrate, timeout=1)
        self.thread = threading.Thread(target=self.read_serial, daemon=True)
        self.thread.start()

    def read_serial(self):
        """
        Continuously read data from the serial port in a separate thread.
        """
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
        """
        Send manual override command to the device.
        
        Args:
            light: 'RED' or 'GREEN' light to override to
        """
        # Compose an 8-byte packet with the 3rd byte as the override request
        # 0x00 for RED, 0x01 for GREEN
        data = bytes([0x00]) if light == 'RED' else bytes([0x01])
        self.ser.write(data)
        self.callback('OUT', light, bytes(data))

    def close(self):
        """Close the serial connection and stop the reading thread."""
        self.running = False
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.close()

    def ack_check(self, mode):
       if mode == 0: #check if the sender got the ack
           while(1):
            self.ser.write(bytes([0xAC]))
            self.callback('OUT', 'CHECK', bytes(bytes([0xAC])))
            

