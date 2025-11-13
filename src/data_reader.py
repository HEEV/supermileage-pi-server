
import datetime
import math
import struct
from configuration_generator import ConfigurationGenerator


class DataReader:
    def __init__(self, config: ConfigurationGenerator):
        self._config = config
        self._packet_format = '<ffffBBBBBH'
        self._packet_size = struct.calcsize(self._packet_format)
        self._distance_traveled = 0
        self._last_update = 0
    
    def read_sensor_data(self, raw_data: bytes) -> dict:
        """
        Reads raw sensor data and converts it based on the configuration.

        Args:
            raw_data (bytes): Raw bytes of sensor values.
        Returns:
            dict: A dictionary with sensor names as keys and converted values.
        """
        # Validate and unpack the raw data
        if len(raw_data) != self._packet_size:
            raise ValueError(f"Invalid data size: expected {self._packet_size}, got {len(raw_data)}")
        
        unpacked_data = struct.unpack(self._packet_format, raw_data)

        sensor_data = {}

        # Handle the hardcoded sensors first
        sensor_data["speed"] = unpacked_data[0]
        sensor_data["airspeed"] = unpacked_data[1]
        sensor_data["engine_temp"] = unpacked_data[2]
        sensor_data["rad_temp"] = unpacked_data[3]
        
        # Handle configuration-defined sensor channels
        cars = self._config.config
        for car in cars:
            if car.active:
                sensors = car.sensors
                for sensor_name, sensor in sensors.items():
                    match sensor_name:
                        case "channel0":
                            sensor_data[sensor.name] = unpacked_data[4] * sensor.conversion_factor
                        case "channel1":
                            sensor_data[sensor.name] = unpacked_data[5] * sensor.conversion_factor
                        case "channel2":
                            sensor_data[sensor.name] = unpacked_data[6] * sensor.conversion_factor
                        case "channel3":
                            sensor_data[sensor.name] = unpacked_data[7] * sensor.conversion_factor
                        case "channel4":
                            sensor_data[sensor.name] = unpacked_data[8] * sensor.conversion_factor
                        case "channelA0":
                            sensor_data[sensor.name] = unpacked_data[9] * sensor.conversion_factor
                        case _:
                            continue # TODO: investigate whether an unknown sensor should raise an error, or if ignore is okay
        
        # Calculate the information derived from speed, and return the full data set
        return self._parse_speed_derivative_data(sensor_data)
    
    def reset_distance(self):
        """Resets the distance traveled to zero."""
        self._distance_traveled = 0
        self._last_update = 0

    def _parse_speed_derivative_data(self, data: dict) -> dict:
        """
        Parses data derived from the speed from the speed data dictionary.

        Args:
            data (dict): Dictionary containing speed data.

        Returns:
            dict: Dictionary containing speed derivative data.
        """

        if self._distance_traveled > 100000000:
            self._distance_traveled = 0

        utc_dt_aware = datetime.datetime.now(datetime.timezone.utc)
        timestamp = math.floor(utc_dt_aware.timestamp() * 1000)

        if self._last_update > 0:
            delta = timestamp - self._last_update

            # mph -> Ft/ms
            speedFtms = 0.00146667 * data["speed"]
            self._distance_traveled += speedFtms * delta
        self._last_update = timestamp

        data["distance_traveled"] = self._distance_traveled
        data["time"] = timestamp
        return data
    