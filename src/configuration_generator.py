import json
from os import getenv
from typing import List, Literal

type InputType = Literal['analog', 'digital']
type PowerPlant = Literal['gasoline', 'electric', 'hydrogen']

class Sensor:
    """Class representing a sensor configuration"""
    name: str
    unit: str | None
    conversion_factor: float | None
    input_type: InputType
    limit_min: float | None = None
    limit_max: float | None = None

    def __init__(self, name: str, input_type: InputType, unit: str | None = None,
                 conversion_factor: float | None = None, limit_min: float | None = None,
                 limit_max: float | None = None):
        self.name = name
        self.unit = unit
        self.conversion_factor = conversion_factor
        self.input_type = input_type
        self.limit_min = limit_min
        self.limit_max = limit_max

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
            limit_min=data.get("limit_min", None),
            limit_max=data.get("limit_max", None)
        )

class Metadata:
    """Class representing metadata for a car"""
    weight: int | None = None
    power_plant: PowerPlant | None = None
    drag_coefficient: float | None = None

    def __init__(self, weight: int | None = None, 
                 power_plant: PowerPlant | None = None,
                 drag_coefficient: float | None = None):
        self.weight = weight
        self.power_plant = power_plant
        self.drag_coefficient = drag_coefficient

    @classmethod
    def from_dict(cls, data: dict) -> 'Metadata':
        """Create a Metadata instance from a dictionary"""
        return cls(
            weight=data.get("weight", None),
            power_plant=data.get("power_plant", None),
            drag_coefficient=data.get("drag_coefficient", None)
        )

class Car:
    """Class representing a car configuration"""
    name: str
    active: bool
    theme: str
    sensors: dict[str, Sensor]
    metadata: Metadata


class ConfigurationGenerator:
    """Class to generate configuration from a JSON file"""

    def __init__(self, config_file_path: str | None = None):
        self._config_file_path = getenv('CONFIG_FILE_PATH') if config_file_path is None else config_file_path
        self.config: List[Car] = []
        self._load_config()

    def _load_config(self):
        """Load configuration from a JSON file"""
        sensor_list: dict[str, Sensor] = {}
        metadata_obj: Metadata = None

        with open(self._config_file_path, 'r') as config_file:
            config: dict = json.load(config_file)
            cars: dict = config.get("cars", None)
            if not cars:
                raise ValueError('No cars defined in configuration file')
            
            # Loop through each car and populate configuration
            for car_name, car in cars.items():
                # Load sensors
                sensors = car.get("sensors", None)
                if sensors is None:
                    raise ValueError(f'Sensors not defined for car: {car_name}')
                for sensor_name, sensor in sensors.items():
                    sensor_list[sensor_name] = Sensor.from_dict(sensor)
                
                # Load metadata
                metadata: dict = car.get("metadata", None)
                if metadata is None:
                    raise ValueError(f'Metadata not defined for car: {car_name}')
                metadata_obj = Metadata.from_dict(metadata)

                # Create Car object
                car_obj: Car = Car()
                car_obj.name = car_name
                car_obj.active = car.get("active", False)
                car_obj.theme = car.get("theme", "default")
                car_obj.sensors = sensor_list
                car_obj.metadata = metadata_obj
                self.config.append(car_obj)

    def get_sensors(self, car_name):
        """Get the sensor configuration for a specified car"""
        for car in self.config:
            if car.name == car_name:
                return car.sensors
        raise ValueError(f'Car not found: {car_name}')
    
    def get_metadata(self, car_name):
        """Get the metadata for a specified car"""
        for car in self.config:
            if car.name == car_name:
                return car.metadata
        raise ValueError(f'Car not found: {car_name}')