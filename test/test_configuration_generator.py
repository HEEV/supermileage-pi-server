import pytest
from configuration_generator import ConfigurationGenerator, Car, Metadata, Sensor

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
                limit_max=36.0
            ), 
            "channel2": Sensor(
                name="button", 
                unit="", 
                conversion_factor=0.0, 
                input_type="digital"
            )
        }, 
        metadata=Metadata(weight=200, power_plant="gasoline")
    ),
    Car(name="car2", active=False, theme="color-theme", sensors={}, metadata=Metadata()),
]

def test_initialization():
    config_gen = ConfigurationGenerator("test/testfiles/car_config.json")
    assert isinstance(config_gen, ConfigurationGenerator)
    assert len(config_gen.config) == 2
    assert config_gen.config == CONFIG_LIST
    assert isinstance(config_gen.config, list)
    assert all(isinstance(car, Car) for car in config_gen.config)

def test_initialization_invalid_file():
    """Test initialization with non-existent file"""
    with pytest.raises((FileNotFoundError, Exception)):
        ConfigurationGenerator("test/testfiles/nonexistent.json")

def test_get_sensors_active():
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

def test_get_sensors_by_name():
    """Test getting sensors from specific cars by name"""
    config_gen = ConfigurationGenerator("test/testfiles/car_config.json")
    
    sensors_car1 = config_gen.get_sensors("car1")
    assert isinstance(sensors_car1, dict)
    assert len(sensors_car1) == 2
    
    sensors_car2 = config_gen.get_sensors("car2")
    assert isinstance(sensors_car2, dict)
    assert len(sensors_car2) == 0

def test_get_sensors_no_active_car():
    """Test error when no car is active"""
    config_gen = ConfigurationGenerator("test/testfiles/car_config.json")
    for car in config_gen.config:
        car.active = False
    
    with pytest.raises(ValueError):
        config_gen.get_sensors()

def test_get_sensors_nonexistent_car():
    """Test error when requesting nonexistent car"""
    config_gen = ConfigurationGenerator("test/testfiles/car_config.json")
    with pytest.raises(ValueError):
        config_gen.get_sensors("nonexistent_car")

def test_get_metadata():
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

def test_get_metadata_no_active_car():
    """Test error when no car is active"""
    config_gen = ConfigurationGenerator("test/testfiles/car_config.json")
    for car in config_gen.config:
        car.active = False
    
    with pytest.raises(ValueError):
        config_gen.get_metadata()

def test_get_metadata_nonexistent_car():
    """Test error when requesting metadata from nonexistent car"""
    config_gen = ConfigurationGenerator("test/testfiles/car_config.json")
    with pytest.raises(ValueError):
        config_gen.get_metadata("nonexistent_car")

def test_sensor_zero_conversion_factor():
    """Test sensor with zero conversion factor"""
    config_gen = ConfigurationGenerator("test/testfiles/car_config.json")
    sensor = config_gen.config[0].sensors["channel2"]
    
    assert sensor.conversion_factor == 0.0
    assert sensor.name == "button"
    assert sensor.input_type == "digital"