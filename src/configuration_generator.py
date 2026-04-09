import json
from dataclasses import dataclass
from os import getenv
from typing import List, Literal


@dataclass
class Sensor:
    """Class representing a sensor configuration

    Attributes:
        name(str):
        unit(str | None):
        conversion_factor(float | None):
        input_type(Literal["analog", "digital"]):
        limit_min(float | None):
        limit_max(float | None):
    """

    name: str
    unit: str | None
    conversion_factor: float | None
    input_type: Literal["analog", "digital"]
    limit_min: float | None = None
    limit_max: float | None = None

    def __post_init__(self):
        # Field Validation
        if self.input_type == "analog":
            if self.unit is None:
                raise ValueError("Unit must be specified for analog sensors")
            if self.conversion_factor is None:
                raise ValueError(
                    "Conversion factor must be specified for analog sensors"
                )

    @classmethod
    def from_dict(cls, data: dict) -> "Sensor":
        """Create a Sensor instance from a dictionary"""
        return cls(
            name=data.get("name"),
            input_type=data.get("input_type"),
            unit=data.get("unit", None),
            conversion_factor=data.get("conversion_factor", None),
            limit_min=data.get("limits", None).get("min", None)
            if data.get("limits", None)
            else None,
            limit_max=data.get("limits", None).get("max", None)
            if data.get("limits", None)
            else None,
        )


@dataclass
class Metadata:
    """Class representing metadata for a car

    Attributes:
        weight(int | None):
        power_plant(Literal["gasoline", "electric", "hydrogen"]):
        drag_coefficient(float | None):
    """

    weight: int | None = None
    power_plant: Literal["gasoline", "electric", "hydrogen"] | None = None
    drag_coefficient: float | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "Metadata":
        """Create a Metadata instance from a dictionary"""
        return cls(
            weight=data.get("weight", None),
            power_plant=data.get("power_plant", None),
            drag_coefficient=data.get("drag_coefficient", None),
        )


@dataclass
class Car:
    """Class representing a car configuration

    Attributes:
        name(str): name of the car
        active(bool): True if the car is the active configuration
        theme(str): the name of the color profile for the display
        sensors(dict[str, Sensor]): dictionary of sensors for the car
        metadata(Metadata): collection of misc. metadata for the car
    """

    name: str
    active: bool
    theme: str
    sensors: dict[str, Sensor]
    metadata: Metadata


class ConfigurationGeneratorError(Exception):
    """ConfigurationGenerator error class"""


class ConfigurationGenerator:
    """
    Class to generate configuration from a JSON file.

    This information is parsed based on the JSON schema defined in the team documentation.
    The data coming from the Arduino cannot be properly parsed without this class being properly
    initialized with the JSON config file.

    The path to this file is required and can be set in the arguments, or in the environment
    variables.

    Attributes:
        config (List[Car]): List of Car configurations parsed from the configuration file.
    """

    def __init__(self, config_file_path: str | None = None):
        self._config_file_path = (
            getenv("CONFIG_FILE_PATH") if config_file_path is None else config_file_path
        )
        if self._config_file_path is None:
            raise ConfigurationGeneratorError(
                "CONFIG_FILE_PATH must be provided in the environment or passed to the generator."
            )
        self.config: List[Car] = []
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from a JSON file"""
        with open(self._config_file_path, "r") as config_file:
            config: dict = json.load(config_file)
            cars: dict = config.get("cars", None)
            if not cars:
                raise ConfigurationGeneratorError(
                    "No cars defined in configuration file"
                )

            # Loop through each car and populate configuration
            for car_name, car in cars.items():
                sensor_list: dict[str, Sensor] = {}
                metadata_obj: Metadata = None
                # Load sensors
                sensors = car.get("sensors", None)
                if sensors is None:
                    raise ConfigurationGeneratorError(
                        f"Sensors not defined for car: {car_name}"
                    )
                for sensor_name, sensor in sensors.items():
                    sensor_list[sensor_name] = Sensor.from_dict(sensor)

                # Load metadata
                metadata: dict = car.get("metadata", None)
                if metadata is None:
                    raise ConfigurationGeneratorError(
                        f"Metadata not defined for car: {car_name}"
                    )
                metadata_obj = Metadata.from_dict(metadata)

                # Create Car object
                car_obj: Car = Car(
                    name=car_name,
                    active=car.get("active", False),
                    theme=car.get("theme", "default"),
                    sensors=sensor_list,
                    metadata=metadata_obj,
                )
                self.config.append(car_obj)

    def get_sensors(self, car_name: str | None = None) -> dict[str, Sensor]:
        """
        Get the sensor configuration for a specified car. This does not include any hardcoded sensors.

        Args:
            car_name(str | None): Optional, name of the car to get information for

        Returns:
            (dict[str, Sensor]): a dictionary of sensors for the requested car

        Raises:
            ConfigurationGeneratorError: If the requested car is not found in the configuration.
        """
        # Return active car if no name provided
        if car_name is None:
            for car in self.config:
                if car.active:
                    return car.sensors
        # Otherwise, return specified car
        for car in self.config:
            if car.name == car_name:
                return car.sensors
        raise ConfigurationGeneratorError(f"Car not found: {car_name}")

    def get_metadata(self, car_name: str | None = None) -> Metadata:
        """
        Get the metadata for a specified car

        Args:
            car_name(str | None): Optional, name of the car to get information for

        Returns:
            Metadata: a collection of the metadata for the requested car

        Raises:
            ConfigurationGeneratorError: If the requested car is not found in the configuration.
        """
        # Return active car if no name provided
        if car_name is None:
            for car in self.config:
                if car.active:
                    return car.metadata
        # Otherwise, return specified car
        for car in self.config:
            if car.name == car_name:
                return car.metadata
        raise ConfigurationGeneratorError(f"Car not found: {car_name}")

    def update_config(self, config_string: str) -> None:
        """
        Update the configuration stored in the JSON and reload it into the generator.

        Args:
            config_string(str): the new configuration as a JSON string
        """
        try:
            config_dict = json.loads(config_string)
            with open(self._config_file_path, "w") as config_file:
                json.dump(config_dict, config_file, indent=4)
            self._load_config()
            print("Configuration updated successfully")
        except json.JSONDecodeError as exc:
            raise ConfigurationGeneratorError(
                f"Invalid JSON string provided for configuration update: {exc}"
            ) from exc
        except OSError as exc:
            raise ConfigurationGeneratorError(
                f"Problem writing updated configuration to file: {exc}"
            ) from exc