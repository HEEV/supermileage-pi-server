import struct
from unittest.mock import MagicMock, patch

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

    @pytest.fixture
    def sm_serial_live(self, mock_serial, monkeypatch):
        monkeypatch.setenv("TESTING", "False")
        return SmSerial()

    def test_initialization_default(self, default_env):
        with patch("glob.glob", return_value=["/dev/ttyUSB0"]):
            sm_serial = SmSerial()
        assert sm_serial._baudrate == 9600
        assert sm_serial._timeout == 1
        assert sm_serial._testing is True
        assert sm_serial._port == "/dev/ttyUSB0"

    def test_initialization_full(self, mock_serial, monkeypatch):
        monkeypatch.setenv("TESTING", "False")
        sm_serial = SmSerial(port="/dev/ttyUSB2", baudrate=115200, timeout=0.5)
        assert sm_serial._port == "/dev/ttyUSB2"
        assert sm_serial._baudrate == 115200
        assert sm_serial._timeout == 0.5
        assert sm_serial._testing is False
        assert sm_serial._ser is not None

    def test_initialization_failed_connection(self, mock_serial, monkeypatch):
        monkeypatch.setenv("TESTING", "False")
        mock_serial.side_effect = serial.SerialException(
            "PermissionError: Access denied"
        )
        with pytest.raises(SmSerialError, match="Permission Error"):
            SmSerial(port="/dev/ttyUSB3")
        mock_serial.side_effect = serial.SerialException("Other serial error")
        with pytest.raises(SmSerialError):
            SmSerial(port="/dev/ttyUSB4")

    def test_reconnect(self, sm_serial_live, capsys):
        sm_serial_live._ser.is_open = False
        sm_serial_live.reconnect()
        sm_serial_live._ser.open.assert_called_once()

        sm_serial_live._ser.is_open = False
        sm_serial_live._ser.open.side_effect = serial.SerialException(
            "Failed to open port"
        )
        sm_serial_live.reconnect()
        assert "Failed to reconnect to serial" in capsys.readouterr().out

    def test_read_response(self, sm_serial_live, mock_serial):
        assert sm_serial_live.read_response(23) == DEFAULT_PACKET
        assert mock_serial.return_value.read.call_count == 3

    def test_read_response_testing_mode(self, mock_serial, monkeypatch):
        monkeypatch.setenv("TESTING", "True")
        sm_serial = SmSerial()
        assert sm_serial.read_response(23) == DEFAULT_PACKET
        assert sm_serial.read_response(23) == b""  # second call returns empty bytes
        mock_serial.return_value.read.assert_not_called()

    def test_crashloop_retry(self, monkeypatch):
        monkeypatch.setenv("TESTING", "False")
        with (
            patch("sm_serial.sleep") as mock_sleep,
            patch(
                "serial.Serial",
                side_effect=[serial.SerialException("Other error"), MagicMock()],
            ),
        ):
            SmSerial(crashloop=True)
            mock_sleep.assert_called_once_with(3)

    def test_read_response_failure(self, sm_serial_live, mock_serial):
        mock_serial.return_value.read.side_effect = serial.SerialException("Read error")
        with pytest.raises(SmSerialError, match="Error reading from serial"):
            sm_serial_live.read_response(23)

    def test_is_open_testing_mode(self, monkeypatch):
        monkeypatch.setenv("TESTING", "True")
        assert SmSerial().is_open() is True

    def test_close(self, sm_serial_live, mock_serial):
        sm_serial_live.close()
        mock_serial.return_value.close.assert_called_once()
