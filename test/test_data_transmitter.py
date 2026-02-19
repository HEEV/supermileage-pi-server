from unittest.mock import MagicMock, patch

import freezegun
import paho.mqtt.client as mqtt
import pytest

from data_transmitter import LocalTransmitter, RemoteTransmitter, TransmitterError

DATA_RECORD = {
    "speed": 30.0,
    "airspeed": 5.0,
    "engine_temp": 80.0,
    "rad_temp": 70.0,
    "sensor1": 1,
    "sensor2": 12.5,
    "distance_traveled": 100.0,
    "time": 10.0,
}


@freezegun.freeze_time("2024-01-01 12:00:00")
class TestLocalTransmitter:
    """Tests for the LocalTransmitter class"""

    @pytest.fixture
    def loc_transmitter(self, tmp_path, mock_config_generator):
        return LocalTransmitter(
            car_sensors=mock_config_generator.get_sensors(), data_dir=str(tmp_path)
        )

    def test_initialization_creates_file(self, loc_transmitter, tmp_path):
        expected_file = tmp_path / "2024-01-01_12-00-00_car_data.csv"
        assert expected_file.exists()
        assert loc_transmitter._data_file_name == str(expected_file)

    def test_handle_record_success(self, loc_transmitter):
        loc_transmitter.handle_record(DATA_RECORD)
        with open(loc_transmitter._data_file_name) as f:
            lines = f.readlines()
        assert len(lines) == 2
        assert "30.0,5.0,80.0,70.0,1,12.5,100.0,10.0" in lines[1]

    def test_handle_record_errors(self, loc_transmitter):
        with patch("builtins.open", side_effect=OSError("Disk full")):
            with pytest.raises(TransmitterError, match="Disk full"):
                loc_transmitter.handle_record(DATA_RECORD)
        with pytest.raises(TransmitterError, match="Invalid data being written"):
            loc_transmitter.handle_record(0)


class TestRemoteTransmitter:
    """Tests for the RemoteTransmitter class"""

    @pytest.fixture
    def remote_transmitter(self, default_env, mock_config_generator, mock_mqtt_client):
        return RemoteTransmitter(config_gen=mock_config_generator)

    def test_initialization(self, remote_transmitter):
        assert remote_transmitter is not None

    def test_initialization_missing_env_vars(self, mock_config_generator, monkeypatch):
        monkeypatch.delenv("MQTT_HOST", raising=False)
        with pytest.raises(TransmitterError, match="not set in environment variables"):
            RemoteTransmitter(config_gen=mock_config_generator)

    def test_initialization_connection_refused(
        self, default_env, mock_config_generator, mock_mqtt_client
    ):
        mock_mqtt_client.return_value.connect.side_effect = ConnectionRefusedError
        with pytest.raises(TransmitterError, match="Could not connect to MQTT broker"):
            RemoteTransmitter(config_gen=mock_config_generator)

    def test_handle_record_publishes_data(self, remote_transmitter):
        with patch.object(remote_transmitter._client, "publish") as mock_publish:
            mock_publish.return_value.rc = mqtt.MQTT_ERR_SUCCESS
            remote_transmitter.handle_record({"speed": 30.0})
            mock_publish.assert_called_once_with(
                remote_transmitter._publish_topic, str({"speed": 30.0}), qos=0
            )

    def test_handle_record_errors(self, remote_transmitter):
        with patch.object(remote_transmitter._client, "publish") as mock_publish:
            mock_publish.return_value.rc = mqtt.MQTT_ERR_NO_CONN
            with pytest.raises(TransmitterError, match="Failed to publish"):
                remote_transmitter.handle_record({"speed": 30.0})
        with patch.object(
            remote_transmitter._client,
            "publish",
            side_effect=ValueError("Invalid topic"),
        ):
            with pytest.raises(TransmitterError, match="Topic or QoS is invalid"):
                remote_transmitter.handle_record({"speed": 30.0})

    def test_receive_message(self, remote_transmitter, mock_config_generator):
        correct_msg = MagicMock(topic="cars/user/config", payload=b'{"new": "config"}')
        wrong_msg = MagicMock(topic="wrong/topic", payload=b'{"new": "config"}')
        bad_msg = MagicMock(topic="cars/user/config")
        bad_msg.payload.decode.side_effect = ValueError("bad encoding")

        remote_transmitter._receive_message(None, None, correct_msg)
        mock_config_generator.update_config.assert_called_once_with('{"new": "config"}')

        remote_transmitter._receive_message(None, None, wrong_msg)
        mock_config_generator.update_config.assert_called_once()  # still only once

        with pytest.raises(TransmitterError, match="Topic is invalid"):
            remote_transmitter._receive_message(None, None, bad_msg)

    def test_disconnect(self, remote_transmitter):
        with patch.object(remote_transmitter._client, "disconnect") as mock_disconnect:
            remote_transmitter.disconnect()
            mock_disconnect.assert_called_once()
