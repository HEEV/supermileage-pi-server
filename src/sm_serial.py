import glob
import struct
from os import getenv
from typing import Optional

import serial


class SmSerialError(Exception):
    """SM Serial error class"""


class SmSerial:
    """
    Encapsulates and maintains a serial connection with an Arduino.

    Args:
        port: Serial port name (e.g., 'COM6' or '/dev/ttyUSB0')
        baudrate: Communication speed (default: 9600)
        timeout: Read timeout in seconds (default: 1)
    """

    def __init__(
        self, port: str | None = None, baudrate: int = 9600, timeout: float = 1
    ):
        self._port: str = ""
        self._baudrate: int = baudrate
        self._timeout: float = timeout
        self._testing: bool = getenv("TESTING", "False") == "True"
        self._test_data_sent: bool = False
        self._ser: Optional[serial.Serial] = None

        # Determine port if not provided
        if port:
            self._port = port
        else:
            usb_devices = glob.glob("/dev/ttyUSB*")
            if usb_devices:
                self._port = usb_devices[0]
            else:
                self._port = "/dev/ttyUSB1"

        # Initialize serial connection or mock for testing
        if self._testing:
            print("Running in testing mode, no serial connection will be made.")
        else:
            try:
                self._ser = serial.Serial(
                    self._port, self._baudrate, timeout=self._timeout
                )
                print(
                    f"Serial connection established on {self._port} at {self._baudrate} baud"
                )
            except serial.SerialException as exc:
                print(f"Failed to open serial port {port}: {exc}")
                if "PermissionError" in str(exc):
                    raise SmSerialError(
                        "Permission Error, try unplugging and replugging arduino. Retrying in 3 seconds..."
                    ) from exc
                else:
                    raise SmSerialError(
                        f"Arduino is missing, please connect the arduino. Retrying in 3 seconds... \n {exc}"
                    ) from exc

    def reconnect(self):
        """
        Reinitialize the serial connection if it is not open currently.
        """
        if not self.is_open():
            try:
                self._ser.open()
                print(f"Connection to {self._port} re-established.")
            except serial.SerialException as exc:
                print(f"Failed to reconnect to serial. {exc}")

    def read_response(self, size: int = 32) -> bytes:
        """
        Read a packet of data from the Arduino.

        Args:
            size(int): Number of bytes to read from the serial port.

        Returns:
            bytes: data packet from Arduino
        """
        response = b""
        # Mock a response if in testing mode
        # Responses alternate between valid data and an empty string, since the arduino will not have data on every read.
        if self._testing:
            if not self._test_data_sent:
                self._test_data_sent = True
                response = struct.pack(
                    "<ffffBBBBBH",
                    25.3,  # speed
                    5.1,  # airspeed
                    78.2,  # engineTemp
                    65.4,  # radTemp
                    0,
                    1,
                    0,
                    1,
                    0,  # digital channels
                    100,
                )  # analog channel
                return response
            else:
                self._test_data_sent = False
                return response

        # Actual read from serial port
        try:
            last_line = self._ser.read(size)
            next_line = self._ser.read(size)
            while next_line != b"":
                last_line = next_line
                next_line = self._ser.read(size)
            return last_line
        except serial.SerialException as exc:
            raise SmSerialError(
                "Error reading from serial, most likely a disconnect."
            ) from exc

    def is_open(self) -> bool:
        """Check if the serial connection is open."""
        if self._testing:
            return True
        return self._ser.is_open if self._ser else False

    def close(self) -> None:
        """Close the serial connection."""
        if not self._testing:
            self._ser.close()
