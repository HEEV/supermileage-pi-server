import datetime
from abc import ABC, abstractmethod
from csv import writer
from os import getenv

import paho.mqtt.client as mqtt

from configuration_generator import ConfigurationGenerator, Sensor


class TransmitterError(Exception):
    """Exception for transmitter errors"""


class DataTransmitter(ABC):  # pragma: no cover
    """Base class for data transmission"""

    def __init__():
        pass

    @abstractmethod
    def handle_record(data: dict):
        """
        send a data record to the relevant endpoint.

        Args:
            data (dict): the data record to be sent
        """
        pass


class LocalTransmitter(DataTransmitter):
    """
    A transmitter to save data records to a local file cache for posterity.

    A new CSV file is create for each instantiation of this class. In the context of running this on
    a car telemetry computer, it would make sense to instantiate this once per power cycle of the computer.

    Args:
        car_sensors (dict[str, Sensor])): the set of sensors for the car being written to
        data_dir (str, optional): the directory to write the CSV file to. Defaults to "Data".
    """

    def __init__(self, car_sensors: dict[str, Sensor], data_dir: str = "Data"):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self._data_file_name = f"{data_dir}/{timestamp}_car_data.csv"

        hardcoded_sensors = ["speed", "airspeed", "engine_temp", "rad_temp"]
        dynamic_sensors = [sensor.name for _, sensor in car_sensors.items()]
        derived_sensors = ["distance_traveled", "time"]
        self._write_to_csv(
            self._data_file_name, hardcoded_sensors + dynamic_sensors + derived_sensors
        )

    def handle_record(self, data: dict):
        """
        Write the data record to a local CSV cache file.

        Args:
            data(dict): the data record to be saved.

        Raises:
            TransmitterError: If an error occurs while trying to write to the CSV.
                Errors can be due to OS or data formatting.
        """
        try:
            data_list = [data[key] for key in data]
            self._write_to_csv(self._data_file_name, data_list)
        except OSError as exc:
            raise TransmitterError(
                f"Problem writing to CSV file, file cannot be opened and/or written: {exc}"
            ) from exc
        except (KeyError, TypeError) as exc:
            raise TransmitterError(
                f"Invalid data being written, received: {data}\n{exc}"
            ) from exc

    def _write_to_csv(self, file_name: str, line: dict):
        """Helper function to write line to CSV, with error handling"""
        with open(file_name, "a") as file:
            csv_writer = writer(file)
            csv_writer.writerow(line)

# TODO: Investigate why connection is dropping after a time period on prod
class RemoteTransmitter(DataTransmitter):
    """
    A transmitter to send data over MQTT to the cloud server.
    """

    def __init__(self, config_gen: ConfigurationGenerator = None):
        self._broker_address = getenv("MQTT_HOST", None)
        self._port = getenv("MQTT_PORT", None)
        self._publish_topic = getenv("MQTT_PUBLISH_TOPIC", None)
        self._subscribe_topic = getenv("MQTT_SUBSCRIBE_TOPIC", None)
        self._username = getenv("MQTT_USERNAME", None)
        self._password = getenv("MQTT_PASSWORD", None)
        self._config_gen = config_gen
        if (
            not self._broker_address
            or not self._port
            or not self._publish_topic
            or not self._username
            or not self._password
        ):
            raise TransmitterError(
                "MQTT broker address, port, publish topic, username, or password not set in environment variables."
            )
        self._port = int(self._port)

        self._client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            f"{self._username}_python_publisher",
            reconnect_on_failure=True,
            transport="websockets",
        )
        self._client.username_pw_set(self._username, self._password)
        try:
            self._client.connect(self._broker_address, self._port)
            print(
                f"Connected to MQTT broker at {self._broker_address}:{self._port} as {self._username}"
            )
            # Subscribe to config topic
            self._client.subscribe(self._subscribe_topic)
            self._client.on_message = self._receive_message
            self._client.loop_start()
        except ConnectionRefusedError as exc:
            raise TransmitterError(
                f"Could not connect to MQTT broker at {self._broker_address}:{self._port} as {self._username}: {exc}"
            ) from exc

    def handle_record(self, data: dict):
        """
        Send the data record to the remote cloud client.

        Args:
            data(dict): the data record to be sent
        """
        try:
            result = self._client.publish(
                self._publish_topic, str(data), qos=0
            )  # QoS 0 = fire and forget
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                raise TransmitterError(
                    f"Failed to publish to MQTT broker at {self._broker_address}:{self._port} on topic {self._publish_topic}, return code: {result.rc}"
                )
        except ValueError as exc:
            raise TransmitterError(
                f"Problem publishing to MQTT broker at on topic {self._publish_topic}: Topic or QoS is invalid. {exc}"
            ) from exc
        
    def _receive_message(self, client, userdata, msg):
        """
        Receive a message from the MQTT broker on the specified topic.

        Args:
            topic (str): the topic to subscribe to for receiving messages
        """
        try:
            if msg.topic == self._subscribe_topic:
                message = msg.payload.decode()
                self._config_gen.update_config(message)  # Attempt to update configuration on any message received, regardless of content. If message is invalid, config remains unchanged.
        except ValueError as exc:
            raise TransmitterError(
                f"Problem receiving message from MQTT broker on topic {msg.topic}: Topic is invalid. {exc}"
            ) from exc

    def disconnect(self):
        """Disconnect the MQTT client cleanly."""
        self._client.disconnect()
