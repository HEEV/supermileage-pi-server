import glob
from os import getenv
import struct
from typing import Optional

import serial

class SmSerial:
    def __init__(self, port: str | None = None, baudrate: int = 9600, timeout: float = 1):
        """
        Initialize serial connection to Arduino.
        
        Args:
            port: Serial port name (e.g., 'COM6' or '/dev/ttyUSB0')
            baudrate: Communication speed (default: 9600)
            timeout: Read timeout in seconds (default: 1)
        """
        self.port: str = ''
        self.baudrate: int = baudrate
        self.timeout: float = timeout
        self._testing: bool = getenv('TESTING', 'False') == 'True'
        self._test_data_sent: bool = False
        self._ser: Optional[serial.Serial] = None
        
        # Determine port if not provided
        if port:
            self.port = port
        else:
            usb_devices = glob.glob("/dev/ttyUSB*")
            if usb_devices:
                self.port = usb_devices[0]
            else:
                self.port = '/dev/ttyUSB1'

        # Initialize serial connection or mock for testing
        if self._testing:
            print("Running in testing mode, no serial connection will be made.")
        else:
            try:
                self._ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
                print(f"Serial connection established on {self.port} at {self.baudrate} baud")
            except serial.SerialException as e:
                print(f"Failed to open serial port {port}: {e}")
                raise

    def read_response(self, size: int = 32) -> str:
        """
        Read a line of data from the Arduino.
        
        Args:
            size: Number of bytes to read from the serial port.
        
        Returns:
            Decoded string response from Arduino
        """
        response = ""
        # Mock a response if in testing mode
        # Responses alternate between valid data and an empty string, since the arduino will not have data on every read.
        if self._testing:
            if not self._test_data_sent:
                self._test_data_sent = True
                response = struct.pack('<ffffBBBBBH', 
                                25.3,  # speed
                                5.2,   # airspeed
                                78.2,  # engineTemp
                                65.4,  # radTemp
                                0, 1, 0, 1, 0,  # digital channels
                                100)  # analog channel
                return response
            else:
                self._test_data_sent = False
                return response
        
        # Actual read from serial port
        try:
            response = self._ser.read(size)
            return response
        except serial.SerialException as e:
            print(f"Error reading from serial: {e}")
            raise
        
    def is_open(self) -> bool:
        """Check if the serial connection is open."""
        if self._testing:
            return True
        return self._ser.is_open if self._ser else False

    def close(self) -> None:
        """Close the serial connection."""
        if not self._testing:
            self._ser.close()