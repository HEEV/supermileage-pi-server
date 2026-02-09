from unittest.mock import patch

import freezegun
import pytest

from data_transmitter import LocalTransmitter, RemoteTransmitter, TransmitterError

import paho.mqtt.client as mqtt


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

    def test_initialization(self, default_env, mock_config_generator, mock_mqtt_client):
        """Test that RemoteTransmitter initializes without error
        Note: this test does not test functionality due to lack of implementation.
        """
        remote_transmitter = RemoteTransmitter(config_gen=mock_config_generator)

        assert remote_transmitter is not None

    def test_initialization_missing_env_vars(self, mock_config_generator, monkeypatch):
        """Test that initialization raises TransmitterError when env vars are missing"""
        monkeypatch.delenv("MQTT_HOST", raising=False)
        with pytest.raises(TransmitterError) as exc_info:
            RemoteTransmitter(config_gen=mock_config_generator)
        assert "not set in environment variables" in str(exc_info.value)

    def test_initialization_connection_refused(self, default_env, mock_config_generator, mock_mqtt_client):
        """Test that initialization raises TransmitterError on connection failure"""
        mock_mqtt_client.return_value.connect.side_effect=ConnectionRefusedError("Connection refused")
        with pytest.raises(TransmitterError) as exc_info:
            RemoteTransmitter(config_gen=mock_config_generator)
        assert "Could not connect to MQTT broker" in str(exc_info.value)

    def test_handle_record_publishes_data(self, default_env, mock_config_generator, mock_mqtt_client):
        """Test that handle_record publishes data to MQTT broker"""
        remote_transmitter = RemoteTransmitter(config_gen=mock_config_generator)
        data_record = {"speed": 30.0}
        
        with patch.object(remote_transmitter._client, 'publish') as mock_publish:
            mock_publish.return_value.rc = mqtt.MQTT_ERR_SUCCESS
            remote_transmitter.handle_record(data_record)
            
            mock_publish.assert_called_once_with(
                remote_transmitter._publish_topic,
                str(data_record),
                qos=0
            )

    def test_handle_record_publish_failure(self, default_env, mock_config_generator, mock_mqtt_client):
        """Test that handle_record raises TransmitterError on publish failure"""
        remote_transmitter = RemoteTransmitter(config_gen=mock_config_generator)
        data_record = {"speed": 30.0}
        
        with patch.object(remote_transmitter._client, 'publish') as mock_publish:
            mock_publish.return_value.rc = mqtt.MQTT_ERR_NO_CONN
            with pytest.raises(TransmitterError) as exc_info:
                remote_transmitter.handle_record(data_record)
            assert "Failed to publish" in str(exc_info.value)

    def test_handle_record_value_error(self, default_env, mock_config_generator, mock_mqtt_client):
        """Test that handle_record raises TransmitterError on ValueError"""
        remote_transmitter = RemoteTransmitter(config_gen=mock_config_generator)
        data_record = {"speed": 30.0}
        
        with patch.object(remote_transmitter._client, 'publish', side_effect=ValueError("Invalid topic")):
            with pytest.raises(TransmitterError) as exc_info:
                remote_transmitter.handle_record(data_record)
            assert "Topic or QoS is invalid" in str(exc_info.value)

    def test_receive_message_updates_config(self, default_env, mock_config_generator, mock_mqtt_client):
        """Test that _receive_message calls update_config on the config generator"""
        remote_transmitter = RemoteTransmitter(config_gen=mock_config_generator)
        
        # Create a mock message
        mock_msg = type('obj', (object,), {
            'topic': 'cars/user/config',
            'payload': b'{"new": "config"}'
        })()
        
        with patch.object(mock_config_generator, 'update_config') as mock_update:
            remote_transmitter._receive_message(None, None, mock_msg)
            mock_update.assert_called_once_with('{"new": "config"}')

    def test_receive_message_wrong_topic(self, default_env, mock_config_generator, mock_mqtt_client):
        """Test that _receive_message ignores messages on wrong topic"""
        remote_transmitter = RemoteTransmitter(config_gen=mock_config_generator)
        
        mock_msg = type('obj', (object,), {
            'topic': 'wrong/topic',
            'payload': b'{"new": "config"}'
        })()
        
        with patch.object(mock_config_generator, 'update_config') as mock_update:
            remote_transmitter._receive_message(None, None, mock_msg)
            mock_update.assert_not_called()

    def test_disconnect(self, default_env, mock_config_generator, mock_mqtt_client):
        """Test that disconnect calls client.disconnect"""
        remote_transmitter = RemoteTransmitter(config_gen=mock_config_generator)
        
        with patch.object(remote_transmitter._client, 'disconnect') as mock_disconnect:
            remote_transmitter.disconnect()
            mock_disconnect.assert_called_once()
