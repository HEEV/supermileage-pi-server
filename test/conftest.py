import os
import struct
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def default_env(monkeypatch):
    """fixture providing basic environment for testing"""
    monkeypatch.setenv(
        "DISABLE_REMOTE", "True"
    )  # TODO: #22 Change to False when RemoteTrasmitter is implemented
    monkeypatch.setenv("DISABLE_LOCAL", "False")
    monkeypatch.setenv("DISABLE_DISPLAY", "False")
    monkeypatch.setenv("TESTING", "True")
    test_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(test_dir, "testfiles", "car_config.json")
    monkeypatch.setenv("CONFIG_FILE_PATH", config_path)
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_USER", "user")
    monkeypatch.setenv("DB_PASSWORD", "password")
    monkeypatch.setenv("DB_PORT", "27017")
    monkeypatch.setenv("DB", "database")
    yield


@pytest.fixture
def mock_config_generator():
    """Mock configuration generator fixture"""
    config_gen = MagicMock()
    config_gen.get_sensors.return_value = {
        "sensor1": MagicMock(name="sensor1", input_type="digital"),
        "sensor2": MagicMock(
            name="sensor2", input_type="analog", unit="V", conversion_factor=1.0
        ),
    }
    config_gen.get_metadata.return_value = MagicMock(
        weight=300, power_plant="gasoline", drag_coefficient=0.3
    )
    yield config_gen


@pytest.fixture
def mock_serial():
    """mock serial.Serial fixture"""
    with patch("serial.Serial") as mock_ser:
        # Configure the instance that Serial() returns
        instance = mock_ser.return_value
        instance.read.side_effect = [
            struct.pack(
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
        ] * 2 + [b""]  # empty string to signal end of data
        instance.is_open = True
        yield mock_ser
