import json

import pytest

from configuration_generator import (
    Car,
    ConfigurationGenerator,
    ConfigurationGeneratorError,
    Metadata,
    Sensor,
)

CONFIG_LIST = [
    Car(
        name="car1",
        active=True,
        theme="color-theme",
        sensors={
            "channelA0": Sensor(
                name="voltage",
                unit="volts",
                conversion_factor=0.35,
                input_type="analog",
                limit_min=0.0,
                limit_max=36.0,
            ),
            "channel2": Sensor(
                name="button", unit="", conversion_factor=0.0, input_type="digital"
            ),
        },
        metadata=Metadata(weight=200, power_plant="gasoline"),
    ),
    Car(
        name="car2", active=False, theme="color-theme", sensors={}, metadata=Metadata()
    ),
]


class TestSensor:
    """Test Sensor dataclass"""

    def test_from_dict_complete(self):
        data = {
            "name": "speed",
            "input_type": "analog",
            "unit": "km/h",
            "conversion_factor": 1.5,
            "limits": {"min": 0, "max": 300},
        }
        sensor = Sensor.from_dict(data)
        assert sensor.name == "speed"
        assert sensor.input_type == "analog"
        assert sensor.unit == "km/h"
        assert sensor.conversion_factor == 1.5
        assert sensor.limit_min == 0
        assert sensor.limit_max == 300

    def test_digital_partial(self):
        sensor = Sensor(
            name="temperature", input_type="digital", unit=None, conversion_factor=None
        )
        assert sensor.name == "temperature"
        assert sensor.input_type == "digital"
        assert sensor.unit is None
        assert sensor.conversion_factor is None
        assert sensor.limit_min is None
        assert sensor.limit_max is None

    def test_analog_partial_fail(self):
        with pytest.raises(ValueError):
            Sensor(
                name="temperature",
                input_type="analog",
                unit=None,
                conversion_factor=None,
            )

        with pytest.raises(ValueError):
            Sensor(
                name="temperature",
                input_type="analog",
                unit="F",
                conversion_factor=None,
            )


class TestConfigurationGenerator:
    """Test ConfigurationGenerator class"""

    def test_initialization(self):
        config_gen = ConfigurationGenerator("test/testfiles/car_config.json")
        assert isinstance(config_gen, ConfigurationGenerator)
        assert len(config_gen.config) == 2
        assert config_gen.config == CONFIG_LIST
        assert isinstance(config_gen.config, list)
        assert all(isinstance(car, Car) for car in config_gen.config)

    def test_initialization_missing_path(self, monkeypatch):
        """Test initialization with no file path given"""
        with pytest.raises(ConfigurationGeneratorError):
            monkeypatch.delenv("CONFIG_FILE_PATH", raising=False)
            ConfigurationGenerator()

    def test_initialization_invalid_file(self):
        """Test initialization with invalid JSON file"""
        with pytest.raises(ConfigurationGeneratorError):
            ConfigurationGenerator("test/testfiles/invalid_config.json")

    def test_initialization_no_sensors(self):
        """Test initialization with no sensors in config"""
        with pytest.raises(ConfigurationGeneratorError):
            ConfigurationGenerator("test/testfiles/no_sensor.json")

    def test_initialization_no_metadata(self):
        """Test initialization with no metadata in config"""
        with pytest.raises(ConfigurationGeneratorError):
            ConfigurationGenerator("test/testfiles/no_meta.json")

    def test_get_sensors_active(self):
        """Test getting sensors from active car"""
        config_gen = ConfigurationGenerator("test/testfiles/car_config.json")
        sensors = config_gen.get_sensors()

        assert isinstance(sensors, dict)
        assert len(sensors) == 2
        assert "channelA0" in sensors
        assert "channel2" in sensors
        assert sensors["channelA0"].name == "voltage"
        assert sensors["channelA0"].unit == "volts"
        assert sensors["channelA0"].conversion_factor == 0.35
        assert sensors["channelA0"].input_type == "analog"
        assert sensors["channelA0"].limit_min == 0.0
        assert sensors["channelA0"].limit_max == 36.0

    def test_get_sensors_by_name(self):
        """Test getting sensors from specific cars by name"""
        config_gen = ConfigurationGenerator("test/testfiles/car_config.json")

        sensors_car1 = config_gen.get_sensors("car1")
        assert isinstance(sensors_car1, dict)
        assert len(sensors_car1) == 2

        sensors_car2 = config_gen.get_sensors("car2")
        assert isinstance(sensors_car2, dict)
        assert len(sensors_car2) == 0

    def test_get_sensors_no_active_car(self):
        """Test error when no car is active"""
        config_gen = ConfigurationGenerator("test/testfiles/car_config.json")
        for car in config_gen.config:
            car.active = False

        with pytest.raises(ConfigurationGeneratorError):
            config_gen.get_sensors()

    def test_get_sensors_nonexistent_car(self):
        """Test error when requesting nonexistent car"""
        config_gen = ConfigurationGenerator("test/testfiles/car_config.json")
        with pytest.raises(ConfigurationGeneratorError):
            config_gen.get_sensors("nonexistent_car")

    def test_get_metadata(self):
        """Test getting metadata from active and specific cars"""
        config_gen = ConfigurationGenerator("test/testfiles/car_config.json")

        # Active car metadata
        metadata_active = config_gen.get_metadata()
        assert isinstance(metadata_active, Metadata)
        assert metadata_active.weight == 200
        assert metadata_active.power_plant == "gasoline"

        # Specific car metadata
        metadata_car2 = config_gen.get_metadata("car2")
        assert isinstance(metadata_car2, Metadata)

    def test_get_metadata_no_active_car(self):
        """Test error when no car is active"""
        config_gen = ConfigurationGenerator("test/testfiles/car_config.json")
        for car in config_gen.config:
            car.active = False

        with pytest.raises(ConfigurationGeneratorError):
            config_gen.get_metadata()

    def test_get_metadata_nonexistent_car(self):
        """Test error when requesting metadata from nonexistent car"""
        config_gen = ConfigurationGenerator("test/testfiles/car_config.json")
        with pytest.raises(ConfigurationGeneratorError):
            config_gen.get_metadata("nonexistent_car")

    def test_sensor_zero_conversion_factor(self):
        """Test sensor with zero conversion factor"""
        config_gen = ConfigurationGenerator("test/testfiles/car_config.json")
        sensor = config_gen.config[0].sensors["channel2"]

        assert sensor.conversion_factor == 0.0
        assert sensor.name == "button"
        assert sensor.input_type == "digital"

    # TODO: fix this so it does not modify the actual config file
    def test_update_config_success(self):
        """Test successful config update"""
        # with mock.patch("builtins.open", mock.mock_open()) as mock_file:
        config_gen = ConfigurationGenerator("test/testfiles/car_config.json")
        new_config = json.dumps(
            {
                "cars": {
                    "car3": {
                        "name": "car3",
                        "active": True,
                        "theme": "new-theme",
                        "sensors": {
                            "channelA1": {
                                "name": "current",
                                "unit": "amps",
                                "conversion_factor": 0.5,
                                "input_type": "analog",
                                "limits": {"min": 0.0, "max": 100.0},
                            }
                        },
                        "metadata": {"weight": 150, "power_plant": "electric"},
                    }
                }
            }
        )
        config_gen.update_config(new_config)

        assert len(config_gen.config) == 3
        assert config_gen.config[2].name == "car3"
        assert config_gen.config[2].active is True
        assert config_gen.config[2].theme == "new-theme"
        assert "channelA1" in config_gen.config[2].sensors
        assert config_gen.config[2].metadata.weight == 150
        assert config_gen.config[2].metadata.power_plant == "electric"

    def test_update_config_error(self):
        """Test error when updating config with invalid JSON and OS Error"""
        config_gen = ConfigurationGenerator("test/testfiles/car_config.json")
        with pytest.raises(ConfigurationGeneratorError):
            config_gen.update_config("invalid_json")
