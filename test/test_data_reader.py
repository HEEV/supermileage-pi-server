import pytest
import struct
from unittest.mock import Mock, patch
from data_reader import DataReader
from configuration_generator import ConfigurationGenerator, Car, Sensor, Metadata


@pytest.fixture
def mock_config():
    """Create a mock configuration with sensors"""
    config = Mock(spec=ConfigurationGenerator)
    config.config = [
        Car(
            name="test_car",
            active=True,
            theme="test-theme",
            sensors={
                "channel0": Sensor(name="voltage", unit="volts", conversion_factor=0.1, input_type="digital"),
                "channel1": Sensor(name="current", unit="amps", conversion_factor=0.01, input_type="digital"),
                "channel2": Sensor(name="button1", unit="", conversion_factor=1.0, input_type="digital"),
                "channel3": Sensor(name="button2", unit="", conversion_factor=1.0, input_type="digital"),
                "channel4": Sensor(name="switch", unit="", conversion_factor=1.0, input_type="digital"),
                "channelA0": Sensor(name="analog_sensor", unit="units", conversion_factor=0.5, input_type="analog")
            },
            metadata=Metadata(weight=200, power_plant="electric")
        )
    ]
    return config


@pytest.fixture
def data_reader(mock_config):
    """Create DataReader instance with mock config"""
    return DataReader(mock_config)


@pytest.fixture
def sample_raw_data():
    """Create sample raw data matching the packet format"""
    return struct.pack('<ffffBBBBBH', 25.5, 28.0, 180.0, 160.0, 1, 0, 1, 0, 1, 1000)


def test_initialization(mock_config):
    """Test DataReader initialization"""
    reader = DataReader(mock_config)
    assert reader._config == mock_config
    assert reader._distance_traveled == 0
    assert reader._last_update == 0
    assert reader._packet_size == struct.calcsize('<ffffBBBBBH')


def test_read_sensor_data_valid(data_reader, sample_raw_data):
    """Test reading valid sensor data with all channels"""
    result = data_reader.read_sensor_data(sample_raw_data)
    
    # Hardcoded sensors
    assert result["speed"] == 25.5
    assert result["airspeed"] == 28.0
    assert result["engine_temp"] == 180.0
    assert result["rad_temp"] == 160.0
    
    # Configured sensors with conversion factors
    assert result["voltage"] == 0.1
    assert result["current"] == 0.0
    assert result["button1"] == 1.0
    assert result["button2"] == 0.0
    assert result["switch"] == 1.0
    assert result["analog_sensor"] == 500.0
    
    # Derived data
    assert "distance_traveled" in result
    assert "time" in result


def test_read_sensor_data_invalid_size(data_reader):
    """Test error handling for invalid data size"""
    with pytest.raises(ValueError) as excinfo:
        data_reader.read_sensor_data(b'\x00' * 10)
    assert "Invalid data size" in str(excinfo.value)
    
    with pytest.raises(ValueError):
        data_reader.read_sensor_data(b'')


def test_read_sensor_data_no_active_car(sample_raw_data):
    """Test reading data when no car is active"""
    config = Mock(spec=ConfigurationGenerator)
    config.config = [Car(name="inactive", active=False, theme="", sensors={}, metadata=Metadata())]
    reader = DataReader(config)
    
    result = reader.read_sensor_data(sample_raw_data)
    
    # Should still have hardcoded sensors
    assert all(key in result for key in ["speed", "airspeed", "engine_temp", "rad_temp"])


def test_read_sensor_data_unknown_channel():
    """Test that unknown sensor channels are ignored"""
    config = Mock(spec=ConfigurationGenerator)
    config.config = [
        Car(
            name="test",
            active=True,
            theme="",
            sensors={"unknown_channel": Sensor(name="unknown", unit="", conversion_factor=1.0, input_type="digital")},
            metadata=Metadata()
        )
    ]
    reader = DataReader(config)
    raw_data = struct.pack('<ffffBBBBBH', 10.0, 10.0, 10.0, 10.0, 0, 0, 0, 0, 0, 0)
    
    result = reader.read_sensor_data(raw_data)
    assert "unknown" not in result


@patch('data_reader.datetime')
def test_distance_calculation(mock_datetime, data_reader, sample_raw_data):
    """Test distance calculation over multiple reads"""
    # First call - no distance calculated
    mock_dt1 = Mock()
    mock_dt1.timestamp.return_value = 1000.0
    mock_datetime.datetime.now.return_value = mock_dt1
    
    result1 = data_reader.read_sensor_data(sample_raw_data)
    assert result1["distance_traveled"] == 0
    assert result1["time"] == 1000000
    assert data_reader._last_update == 1000000
    
    # Second call - distance calculated
    mock_dt2 = Mock()
    mock_dt2.timestamp.return_value = 1001.0
    mock_datetime.datetime.now.return_value = mock_dt2
    
    result2 = data_reader.read_sensor_data(sample_raw_data)
    expected_distance = 25.5 * 0.00146667 * 1000
    assert result2["distance_traveled"] == pytest.approx(expected_distance, rel=0.01)
    assert data_reader._last_update == 1001000


@patch('data_reader.datetime')
def test_distance_reset_on_overflow(mock_datetime, data_reader, sample_raw_data):
    """Test that distance resets when exceeding threshold"""
    data_reader._distance_traveled = 100000001
    
    mock_dt = Mock()
    mock_dt.timestamp.return_value = 1000.0
    mock_datetime.datetime.now.return_value = mock_dt
    
    result = data_reader.read_sensor_data(sample_raw_data)
    assert result["distance_traveled"] == 0


def test_reset_distance(data_reader):
    """Test manual distance reset"""
    data_reader._distance_traveled = 1234.5
    data_reader._last_update = 5678
    
    data_reader.reset_distance()
    
    assert data_reader._distance_traveled == 0
    assert data_reader._last_update == 0


@patch('data_reader.datetime')
def test_reset_distance_between_reads(mock_datetime, data_reader, sample_raw_data):
    """Test that reset works correctly between reads"""
    # First read
    mock_dt1 = Mock()
    mock_dt1.timestamp.return_value = 1000.0
    mock_datetime.datetime.now.return_value = mock_dt1
    data_reader.read_sensor_data(sample_raw_data)
    
    # Second read - accumulate distance
    mock_dt2 = Mock()
    mock_dt2.timestamp.return_value = 1001.0
    mock_datetime.datetime.now.return_value = mock_dt2
    result1 = data_reader.read_sensor_data(sample_raw_data)
    assert result1["distance_traveled"] > 0
    
    # Reset
    data_reader.reset_distance()
    
    # Third read - distance should be 0
    mock_dt3 = Mock()
    mock_dt3.timestamp.return_value = 1002.0
    mock_datetime.datetime.now.return_value = mock_dt3
    result2 = data_reader.read_sensor_data(sample_raw_data)
    assert result2["distance_traveled"] == 0


def test_edge_cases(data_reader):
    """Test edge cases: zero speed, negative speed, max values"""
    # Zero speed
    raw_data_zero = struct.pack('<ffffBBBBBH', 0.0, 0.0, 0.0, 0.0, 0, 0, 0, 0, 0, 0)
    result_zero = data_reader.read_sensor_data(raw_data_zero)
    assert result_zero["speed"] == 0.0
    
    # Negative speed
    raw_data_neg = struct.pack('<ffffBBBBBH', -10.0, 0.0, 0.0, 0.0, 0, 0, 0, 0, 0, 0)
    result_neg = data_reader.read_sensor_data(raw_data_neg)
    assert result_neg["speed"] == -10.0
    
    # Max values
    raw_data_max = struct.pack('<ffffBBBBBH', 999.9, 999.9, 999.9, 999.9, 1, 1, 1, 1, 1, 65535)
    result_max = data_reader.read_sensor_data(raw_data_max)
    assert result_max["speed"] == 999.9
    assert result_max["voltage"] == 0.1
    assert result_max["analog_sensor"] == 32767.5


def test_conversion_factor_zero():
    """Test that zero conversion factor defaults to 1.0"""
    config = Mock(spec=ConfigurationGenerator)
    config.config = [
        Car(
            name="test",
            active=True,
            theme="",
            sensors={"channel0": Sensor(name="zero_factor", unit="", conversion_factor=0.0, input_type="digital")},
            metadata=Metadata()
        )
    ]
    reader = DataReader(config)
    raw_data = struct.pack('<ffffBBBBBH', 10.0, 10.0, 10.0, 10.0, 1, 0, 0, 0, 0, 0)
    
    result = reader.read_sensor_data(raw_data)
    assert result["zero_factor"] == 1.0  # Conversion factor set to 1.0 when 0.0
