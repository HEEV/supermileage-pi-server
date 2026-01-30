import datetime
from abc import ABC, abstractmethod
from csv import writer

from configuration_generator import Sensor


class TransmitterError(Exception):
    """Exception for transmitter errors"""


class DataTransmitter(ABC):
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
    """

    def __init__(self, car_sensors: dict[str, Sensor]):
        self._data_file_name = datetime.datetime.now().strftime(
            "Data/%Y-%m-%d_%H-%M-%S_car_data.csv"
        )
        with open(self._data_file_name, "w") as file:
            csv_writer = writer(file)
            hardcoded_sensors = ["speed", "airspeed", "engine_temp", "rad_temp"]
            dynamic_sensors = [sensor.name for _, sensor in car_sensors.items()]
            derived_sensors = ["distance_traveled", "time"]
            csv_writer.writerow(hardcoded_sensors + dynamic_sensors + derived_sensors)

    def handle_record(self, data: dict):
        """
        Write the data record to a local CSV cache file.

        Args:
            data(dict): the data record to be saved.

        Raises:
            TransmitterError: If an error occurs while trying to write to the CSV.
                Errors can be due to OS or data formatting.
        """
        with open(self._data_file_name, "a") as file:
            try:
                csv_writer = writer(file)
                data_list = [data[key] for key in data]
                csv_writer.writerow(data_list)
            except OSError as exc:
                raise TransmitterError(
                    f"Problem writing to CSV file, file cannot be opened and/or written: {exc}"
                ) from exc
            except (KeyError, TypeError) as exc:
                raise TransmitterError(
                    f"Invalid data being written to cache, received: {data}\n{exc}"
                ) from exc


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
        print("Warning: handle_record is unimplemented for RemoveTransmitter.")
