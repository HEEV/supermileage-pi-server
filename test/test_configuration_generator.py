import json
import shutil
from unittest.mock import patch

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

    def test_from_dict(self):
        sensor = Sensor.from_dict(
            {
                "name": "speed",
                "input_type": "analog",
                "unit": "km/h",
                "conversion_factor": 1.5,
                "limits": {"min": 0, "max": 300},
            }
        )
        assert sensor == Sensor(
            name="speed",
            input_type="analog",
            unit="km/h",
            conversion_factor=1.5,
            limit_min=0,
            limit_max=300,
        )

    def test_digital_allows_none_fields(self):
        sensor = Sensor(
            name="btn", input_type="digital", unit=None, conversion_factor=None
        )
        assert sensor.unit is None and sensor.conversion_factor is None

    def test_analog_requires_unit_and_conversion(self):
        with pytest.raises(ValueError):
            Sensor(name="temp", input_type="analog", unit=None, conversion_factor=None)
        with pytest.raises(ValueError):
            Sensor(name="temp", input_type="analog", unit="F", conversion_factor=None)


class TestConfigurationGenerator:
    """Test ConfigurationGenerator class"""

    @pytest.fixture
    def config_gen(self):
        return ConfigurationGenerator("test/testfiles/car_config.json")

    def test_initialization(self, config_gen):
        assert config_gen.config == CONFIG_LIST

    def test_initialization_missing_path(self, monkeypatch):
        monkeypatch.delenv("CONFIG_FILE_PATH", raising=False)
        with pytest.raises(ConfigurationGeneratorError):
            ConfigurationGenerator()

    @pytest.mark.parametrize(
        "path",
        [
            "test/testfiles/invalid_config.json",
            "test/testfiles/no_sensor.json",
            "test/testfiles/no_meta.json",
        ],
    )
    def test_initialization_bad_files(self, path):
        with pytest.raises(ConfigurationGeneratorError):
            ConfigurationGenerator(path)

    def test_get_sensors(self, config_gen):
        assert set(config_gen.get_sensors()) == {"channelA0", "channel2"}
        assert config_gen.get_sensors("car1") == config_gen.get_sensors()
        assert config_gen.get_sensors("car2") == {}

    def test_get_sensors_errors(self, config_gen):
        with pytest.raises(ConfigurationGeneratorError):
            config_gen.get_sensors("nonexistent_car")
        for car in config_gen.config:
            car.active = False
        with pytest.raises(ConfigurationGeneratorError):
            config_gen.get_sensors()

    def test_get_metadata(self, config_gen):
        meta = config_gen.get_metadata()
        assert meta.weight == 200 and meta.power_plant == "gasoline"
        assert isinstance(config_gen.get_metadata("car2"), Metadata)

    def test_get_metadata_errors(self, config_gen):
        with pytest.raises(ConfigurationGeneratorError):
            config_gen.get_metadata("nonexistent_car")
        for car in config_gen.config:
            car.active = False
        with pytest.raises(ConfigurationGeneratorError):
            config_gen.get_metadata()

    @pytest.fixture
    def tmp_config_gen(self, tmp_path):
        tmp_config = tmp_path / "car_config.json"
        shutil.copy("test/testfiles/car_config.json", tmp_config)
        return ConfigurationGenerator(str(tmp_config))

    def test_update_config_success(self, tmp_config_gen):
        tmp_config_gen.update_config(
            json.dumps(
                {
                    "cars": {
                        "car3": {
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
        )
        assert len(tmp_config_gen.config) == 3
        car3 = tmp_config_gen.config[2]
        assert (
            car3.name == "car3" and car3.active is True and "channelA1" in car3.sensors
        )

    def test_update_config_invalid_json(self, tmp_config_gen):
        with pytest.raises(ConfigurationGeneratorError):
            tmp_config_gen.update_config("invalid_json")

    def test_update_config_os_error(self, tmp_config_gen):
        with patch("builtins.open", side_effect=OSError("disk full")):
            with pytest.raises(ConfigurationGeneratorError, match="Problem writing"):
                tmp_config_gen.update_config('{"cars": {}}')
