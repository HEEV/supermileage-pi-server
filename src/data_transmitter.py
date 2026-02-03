import datetime
from abc import ABC, abstractmethod
from csv import writer

from configuration_generator import Sensor


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


class RemoteTransmitter(DataTransmitter):
    """
    A transmitter to send data over MQTT to the cloud server.
    TODO: This is unimplemented.
    """

    def __init__(self):
        pass

    def handle_record(self, data: dict):
        """
        Send the data record to the remote cloud client.

        Args:
            data(dict): the data record to be sent
        """
        raise NotImplementedError(
            "RemoteTransmitter.handle_record is not yet implemented."
        )
