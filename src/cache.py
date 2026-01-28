import datetime
from csv import writer

from configuration_generator import ConfigurationGenerator


class CacheError(Exception):
    """Exception for cache errors"""


class CarCache:
    def __init__(self, car_config: ConfigurationGenerator):
        self._data_file_name = datetime.datetime.now().strftime(
            "Data/%Y-%m-%d_%H-%M-%S_car_data.csv"
        )
        with open(self._data_file_name, "w") as file:
            csv_writer = writer(file)
            hardcoded_sensors = ["speed", "airspeed", "engine_temp", "rad_temp"]
            dynamic_sensors = [
                sensor.name for _, sensor in car_config.get_sensors().items()
            ]
            derived_sensors = ["distance_traveled", "time"]
            csv_writer.writerow(hardcoded_sensors + dynamic_sensors + derived_sensors)

    def add_record(self, data: dict):
        """Add data record to the cache"""
        with open(self._data_file_name, "a") as file:
            try:
                csv_writer = writer(file)
                data_list = [data[key] for key in data]
                csv_writer.writerow(data_list)
            except OSError as exc:
                raise CacheError(
                    f"Problem writing to CSV file, file cannot be opened and/or written: {exc}"
                )
            except (KeyError, TypeError) as exc:
                raise CacheError(
                    f"Invalid data being written to cache, received: {data}\n{exc}"
                )
