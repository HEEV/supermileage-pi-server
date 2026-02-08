import struct
from unittest.mock import patch

import pytest
import serial

from sm_serial import SmSerial, SmSerialError

DEFAULT_PACKET = struct.pack(
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
    100,  # analog channel
)


class TestSmSerial:
    """Tests for the SmSerial class."""

    def test_initialization_default(self, default_env):
        """Test default initialization of SmSerial."""
        with patch("glob.glob", return_value=["/dev/ttyUSB0"]):
            sm_serial = SmSerial()
        assert sm_serial._baudrate == 9600
        assert sm_serial._timeout == 1
        assert sm_serial._testing == True
        assert sm_serial._port == "/dev/ttyUSB0"

    def test_initialization_full(self, mock_serial, monkeypatch):
        """Test full initialization of SmSerial with parameters."""
        monkeypatch.setenv("TESTING", "False")
        sm_serial = SmSerial(port="/dev/ttyUSB2", baudrate=115200, timeout=0.5)
        assert sm_serial._port == "/dev/ttyUSB2"
        assert sm_serial._baudrate == 115200
        assert sm_serial._timeout == 0.5
        assert sm_serial._testing == False
        assert (
            sm_serial._ser is not None
        )  # Serial connection should be established in non-testing mode

    def test_initialization_failed_connection(self, mock_serial, monkeypatch):
        """Test initialization when serial connection fails."""
        monkeypatch.setenv("TESTING", "False")
        mock_serial.side_effect = serial.SerialException(
            "PermissionError: Access denied"
        )
        with pytest.raises(SmSerialError) as excinfo:
            SmSerial(port="/dev/ttyUSB3")
        assert "Permission Error" in str(excinfo.value)

        mock_serial.side_effect = serial.SerialException("Other serial error")
        with pytest.raises(SmSerialError):
            SmSerial(port="/dev/ttyUSB4")

    def test_reconnect_success(self, mock_serial, monkeypatch):
        """Test successful reconnection of SmSerial."""
        monkeypatch.setenv("TESTING", "False")
        sm_serial = SmSerial()
        sm_serial._ser.is_open = False  # Simulate disconnected state
        sm_serial.reconnect()
        sm_serial._ser.open.assert_called_once()
        assert sm_serial._ser is not None

    def test_reconnect_failure(self, mock_serial, monkeypatch, capsys):
        """Test reconnection failure of SmSerial."""
        monkeypatch.setenv("TESTING", "False")
        sm_serial = SmSerial()
        sm_serial._ser.is_open = False  # Simulate disconnected state
        sm_serial._ser.open.side_effect = serial.SerialException("Failed to open port")
        sm_serial.reconnect()
        assert "Failed to reconnect to serial" in capsys.readouterr().out

    def test_read_response(self, mock_serial, monkeypatch):
        """Test reading response from SmSerial."""
        monkeypatch.setenv("TESTING", "False")
        sm_serial = SmSerial()
        response = sm_serial.read_response(23)
        assert isinstance(response, bytes)
        assert len(response) == 23
        assert response == DEFAULT_PACKET
        assert (
            mock_serial.return_value.read.call_count == 3
        )  # Ensure multiple reads were made

    def test_read_response_testing_mode(self, mock_serial, monkeypatch):
        """Test reading response in testing mode."""
        monkeypatch.setenv("TESTING", "True")
        sm_serial = SmSerial()
        response = sm_serial.read_response(23)
        assert isinstance(response, bytes)
        assert len(response) == 23
        assert response == DEFAULT_PACKET
        mock_serial.return_value.read.assert_not_called()  # No reads should be made in testing mode

    def test_read_response_failure(self, mock_serial, monkeypatch):
        """Test reading response failure from SmSerial."""
        monkeypatch.setenv("TESTING", "False")
        sm_serial = SmSerial()
        mock_serial.return_value.read.side_effect = serial.SerialException("Read error")
        with pytest.raises(SmSerialError) as excinfo:
            sm_serial.read_response(23)
        assert "Error reading from serial, most likely a disconnect." in str(
            excinfo.value
        )

    def test_is_open_testing_mode(self, monkeypatch):
        """Test is_open method in testing mode."""
        monkeypatch.setenv("TESTING", "True")
        sm_serial = SmSerial()
        assert sm_serial.is_open() == True

    def test_close(self, mock_serial, monkeypatch):
        """Test closing the SmSerial connection."""
        monkeypatch.setenv("TESTING", "False")
        sm_serial = SmSerial()
        sm_serial.close()
        mock_serial.return_value.close.assert_called_once()
