from unittest.mock import patch

import freezegun
import pytest

from data_transmitter import LocalTransmitter, RemoteTransmitter, TransmitterError


@freezegun.freeze_time("2024-01-01 12:00:00")
class TestLocalTransmitter:
    """Tests for the LocalTransmitter class"""

    def test_initialization_creates_file(self, tmp_path, mock_config_generator):
        """Test that initialization creates a CSV file with the correct header"""
        loc_transmitter = LocalTransmitter(
            car_sensors=mock_config_generator.get_sensors(), data_dir=str(tmp_path)
        )
        expected_file = tmp_path / "2024-01-01_12-00-00_car_data.csv"
        assert (
            loc_transmitter._data_file_name
            == f"{tmp_path}/2024-01-01_12-00-00_car_data.csv"
        )
        assert expected_file.exists()

    def test_handle_record_success(self, tmp_path, mock_config_generator):
        """Test that handle_record writes data correctly to the CSV file"""
        loc_transmitter = LocalTransmitter(
            car_sensors=mock_config_generator.get_sensors(), data_dir=str(tmp_path)
        )
        data_record = {
            "speed": 30.0,
            "airspeed": 5.0,
            "engine_temp": 80.0,
            "rad_temp": 70.0,
            "sensor1": 1,
            "sensor2": 12.5,
            "distance_traveled": 100.0,
            "time": 10.0,
        }
        loc_transmitter.handle_record(data_record)

        # Read the file and verify the data was written
        with open(loc_transmitter._data_file_name, "r") as file:
            lines = file.readlines()
            assert len(lines) == 2  # header + data row
            assert "30.0,5.0,80.0,70.0,1,12.5,100.0,10.0" in lines[1]

    def test_handle_record_fail_os(self, tmp_path, mock_config_generator):
        """Test that handle_record raises TransmitterError on OS error"""
        loc_transmitter = LocalTransmitter(
            car_sensors=mock_config_generator.get_sensors(), data_dir=str(tmp_path)
        )
        data_record = {
            "speed": 30.0,
            "airspeed": 5.0,
            "engine_temp": 80.0,
            "rad_temp": 70.0,
            "sensor1": 1,
            "sensor2": 12.5,
            "distance_traveled": 100.0,
            "time": 10.0,
        }
        with patch("builtins.open", side_effect=OSError("Disk full")):
            with pytest.raises(TransmitterError) as exc_info:
                loc_transmitter.handle_record(data_record)
            assert "Disk full" in str(exc_info.value)

    def test_handle_record_fail_typeerror(self, tmp_path, mock_config_generator):
        """Test that handle_record raises TransmitterError on KeyError"""
        loc_transmitter = LocalTransmitter(
            car_sensors=mock_config_generator.get_sensors(), data_dir=str(tmp_path)
        )
        with pytest.raises(TransmitterError) as exc_info:
            loc_transmitter.handle_record(0)
        assert "Invalid data being written" in str(exc_info.value)


class TestRemoteTransmitter:
    """Tests for the RemoteTransmitter class"""

    def test_initialization(self):
        """Test that RemoteTransmitter initializes without error
        Note: this test does not test functionality due to lack of implementation.
        """
        remote_transmitter = RemoteTransmitter()

        assert remote_transmitter is not None

    def test_handle_record_not_implemented(self):
        """Test that handle_record reports not implemented"""
        remote_transmitter = RemoteTransmitter()
        with pytest.raises(NotImplementedError):
            remote_transmitter.handle_record({"speed": 30.0})
