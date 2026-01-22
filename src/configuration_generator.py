from dataclasses import dataclass
import json
from os import getenv
from typing import List, Literal

type InputType = Literal['analog', 'digital']
type PowerPlant = Literal['gasoline', 'electric', 'hydrogen']

@dataclass
class Sensor:
    """Class representing a sensor configuration"""
    name: str
    unit: str | None
    conversion_factor: float | None
    input_type: InputType
    limit_min: float | None = None
    limit_max: float | None = None

    def __post_init__(self):
        # Field Validation
        if self.input_type == 'analog':
            if self.unit is None:
                raise ValueError('Unit must be specified for analog sensors')
            if self.conversion_factor is None:
                raise ValueError('Conversion factor must be specified for analog sensors')
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Sensor':
        """Create a Sensor instance from a dictionary"""
        return cls(
            name=data.get("name"),
            input_type=data.get("input_type"),
            unit=data.get("unit", None),
            conversion_factor=data.get("conversion_factor", None),
            limit_min=data.get("limits", None).get("min", None) if data.get("limits", None) else None,
            limit_max=data.get("limits", None).get("max", None) if data.get("limits", None) else None
        )

@dataclass
class Metadata:
    """Class representing metadata for a car"""
    weight: int | None = None
    power_plant: PowerPlant | None = None
    drag_coefficient: float | None = None

    @classmethod
    def from_dict(cls, data: dict) -> 'Metadata':
        """Create a Metadata instance from a dictionary"""
        return cls(
            weight=data.get("weight", None),
            power_plant=data.get("power_plant", None),
            drag_coefficient=data.get("drag_coefficient", None)
        )

@dataclass
class Car:
    """Class representing a car configuration"""
    name: str
    active: bool
    theme: str
    sensors: dict[str, Sensor]
    metadata: Metadata

class ConfigurationGeneratorError(Exception):
    """ConfigurationGenerator error class"""


class ConfigurationGenerator:
    """Class to generate configuration from a JSON file"""

    def __init__(self, config_file_path: str | None = None):
        self._config_file_path = getenv('CONFIG_FILE_PATH') if config_file_path is None else config_file_path
        if self._config_file_path is None:
            raise ConfigurationGeneratorError("CONFIG_FILE_PATH must be provided in the environment or passed to the generator.")
        self.config: List[Car] = []
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from a JSON file"""
        with open(self._config_file_path, 'r') as config_file:
            config: dict = json.load(config_file)
            cars: dict = config.get("cars", None)
            if not cars:
                raise ConfigurationGeneratorError('No cars defined in configuration file')
            
            # Loop through each car and populate configuration
            for car_name, car in cars.items():
                sensor_list: dict[str, Sensor] = {}
                metadata_obj: Metadata = None
                # Load sensors
                sensors = car.get("sensors", None)
                if sensors is None:
                    raise ConfigurationGeneratorError(f'Sensors not defined for car: {car_name}')
                for sensor_name, sensor in sensors.items():
                    sensor_list[sensor_name] = Sensor.from_dict(sensor)
                
                # Load metadata
                metadata: dict = car.get("metadata", None)
                if metadata is None:
                    raise ConfigurationGeneratorError(f'Metadata not defined for car: {car_name}')
                metadata_obj = Metadata.from_dict(metadata)

                # Create Car object
                car_obj: Car = Car(
                    name=car_name,
                    active=car.get("active", False),
                    theme=car.get("theme", "default"),
                    sensors=sensor_list,
                    metadata=metadata_obj
                )
                self.config.append(car_obj)

    def get_sensors(self, car_name = None) -> dict[str, Sensor]:
        """Get the sensor configuration for a specified car. This does not include any hardcoded sensors."""
        # Return active car if no name provided
        if (car_name is None):
            for car in self.config:
                if car.active:
                    return car.sensors
        # Otherwise, return specified car
        for car in self.config:
            if car.name == car_name:
                return car.sensors
        raise ConfigurationGeneratorError(f'Car not found: {car_name}')
    
    def get_metadata(self, car_name = None) -> Metadata:
        """Get the metadata for a specified car"""
        # Return active car if no name provided
        if (car_name is None):
            for car in self.config:
                if car.active:
                    return car.metadata
        # Otherwise, return specified car
        for car in self.config:
            if car.name == car_name:
                return car.metadata
        raise ConfigurationGeneratorError(f'Car not found: {car_name}')