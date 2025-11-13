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
    assert len(config_gen.config) == 2  # Assuming car_config.json has 2 car configurations
    assert config_gen.config == CONFIG_LIST

# TODO: finish writing these tests
def test_get_sensors_active():
    assert True

def test_get_sensors_manual_car():
    assert True

def test_get_metadata():
    assert True