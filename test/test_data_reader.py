import pytest
import struct
import datetime
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
                "channel0": Sensor(
                    name="voltage",
                    unit="volts",
                    conversion_factor=0.1,
                    input_type="digital"
                ),
                "channel1": Sensor(
                    name="current",
                    unit="amps",
                    conversion_factor=0.01,
                    input_type="digital"
                ),
                "channel2": Sensor(
                    name="button1",
                    unit="",
                    conversion_factor=1.0,
                    input_type="digital"
                ),
                "channel3": Sensor(
                    name="button2",
                    unit="",
                    conversion_factor=1.0,
                    input_type="digital"
                ),
                "channel4": Sensor(
                    name="switch",
                    unit="",
                    conversion_factor=1.0,
                    input_type="digital"
                ),
                "channelA0": Sensor(
                    name="analog_sensor",
                    unit="units",
                    conversion_factor=0.5,
                    input_type="analog"
                )
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
    # Format: '<ffffBBBBBH'
    # 4 floats (speed, airspeed, engine_temp, rad_temp)
    # 5 bytes (channel0-4) - digital channels can only be 0 or 1
    # 1 unsigned short (channelA0)
    return struct.pack('<ffffBBBBBH', 
                       25.5,   # speed
                       28.0,   # airspeed
                       180.0,  # engine_temp
                       160.0,  # rad_temp
                       1,      # channel0 (digital: 0 or 1)
                       0,      # channel1 (digital: 0 or 1)
                       1,      # channel2 (digital: 0 or 1)
                       0,      # channel3 (digital: 0 or 1)
                       1,      # channel4 (digital: 0 or 1)
                       1000)   # channelA0 (analog)


class TestDataReaderInitialization:
    """Test DataReader initialization"""
    
    def test_initialization(self, mock_config):
        reader = DataReader(mock_config)
        assert reader._config == mock_config
        assert reader._distance_traveled == 0
        assert reader._last_update == 0
        assert reader._packet_size == struct.calcsize('<ffffBBBBBH')


class TestReadSensorData:
    """Test read_sensor_data method"""
    
    def test_read_sensor_data_valid(self, data_reader, sample_raw_data):
        result = data_reader.read_sensor_data(sample_raw_data)
        
        # Check hardcoded sensors
        assert result["speed"] == 25.5
        assert result["airspeed"] == 28.0
        assert result["engine_temp"] == 180.0
        assert result["rad_temp"] == 160.0
        
        # Check configured sensors with conversion factors
        assert result["voltage"] == 1 * 0.1  # 0.1
        assert result["current"] == 0 * 0.01  # 0.0
        assert result["button1"] == 1 * 1.0    # 1.0
        assert result["button2"] == 0 * 1.0    # 0.0
        assert result["switch"] == 1 * 1.0     # 1.0
        assert result["analog_sensor"] == 1000 * 0.5  # 500.0
        
        # Check derived data
        assert "distance_traveled" in result
        assert "time" in result
    
    def test_read_sensor_data_invalid_size(self, data_reader):
        invalid_data = b'\x00' * 10  # Wrong size
        
        with pytest.raises(ValueError) as excinfo:
            data_reader.read_sensor_data(invalid_data)
        
        assert "Invalid data size" in str(excinfo.value)
    
    def test_read_sensor_data_empty(self, data_reader):
        with pytest.raises(ValueError):
            data_reader.read_sensor_data(b'')
    
    def test_read_sensor_data_no_active_car(self, sample_raw_data):
        config = Mock(spec=ConfigurationGenerator)
        config.config = [
            Car(name="inactive", active=False, theme="", sensors={}, metadata=Metadata())
        ]
        reader = DataReader(config)
        
        result = reader.read_sensor_data(sample_raw_data)
        
        # Should still have hardcoded sensors
        assert "speed" in result
        assert "airspeed" in result
        assert "engine_temp" in result
        assert "rad_temp" in result
    
    def test_read_sensor_data_unknown_channel(self):
        config = Mock(spec=ConfigurationGenerator)
        config.config = [
            Car(
                name="test",
                active=True,
                theme="",
                sensors={
                    "unknown_channel": Sensor(
                        name="unknown",
                        unit="",
                        conversion_factor=1.0,
                        input_type="digital"
                    )
                },
                metadata=Metadata()
            )
        ]
        reader = DataReader(config)
        raw_data = struct.pack('<ffffBBBBBH', 10.0, 10.0, 10.0, 10.0, 0, 0, 0, 0, 0, 0)
        
        result = reader.read_sensor_data(raw_data)
        
        # Unknown channel should be ignored
        assert "unknown" not in result


class TestSpeedDerivativeData:
    """Test speed derivative data calculations"""
    
    @patch('data_reader.datetime')
    def test_distance_calculation_first_call(self, mock_datetime, data_reader, sample_raw_data):
        # Mock timestamp
        mock_dt = Mock()
        mock_dt.timestamp.return_value = 1000.0
        mock_datetime.datetime.now.return_value = mock_dt
        
        result = data_reader.read_sensor_data(sample_raw_data)
        
        # First call should not calculate distance (no previous timestamp)
        assert result["distance_traveled"] == 0
        assert result["time"] == 1000000  # 1000.0 * 1000
        assert data_reader._last_update == 1000000
    
    @patch('data_reader.datetime')
    def test_distance_calculation_subsequent_call(self, mock_datetime, data_reader, sample_raw_data):
        # First call
        mock_dt1 = Mock()
        mock_dt1.timestamp.return_value = 1000.0
        mock_datetime.datetime.now.return_value = mock_dt1
        
        data_reader.read_sensor_data(sample_raw_data)
        
        # Second call - 1 second later
        mock_dt2 = Mock()
        mock_dt2.timestamp.return_value = 1001.0
        mock_datetime.datetime.now.return_value = mock_dt2
        
        result = data_reader.read_sensor_data(sample_raw_data)
        
        # Should calculate distance: speed (25.5 mph) * 0.00146667 * 1000ms
        expected_distance = 25.5 * 0.00146667 * 1000
        assert result["distance_traveled"] == pytest.approx(expected_distance, rel=0.01)
        assert data_reader._last_update == 1001000
    
    @patch('data_reader.datetime')
    def test_distance_accumulation(self, mock_datetime, data_reader, sample_raw_data):
        # Multiple reads to accumulate distance
        timestamps = [1000.0, 1001.0, 1002.0, 1003.0]
        
        for i, ts in enumerate(timestamps):
            mock_dt = Mock()
            mock_dt.timestamp.return_value = ts
            mock_datetime.datetime.now.return_value = mock_dt
            
            result = data_reader.read_sensor_data(sample_raw_data)
            
            if i > 0:
                # Distance should be accumulating
                assert result["distance_traveled"] > 0
    
    @patch('data_reader.datetime')
    def test_distance_reset_on_overflow(self, mock_datetime, data_reader, sample_raw_data):
        # Set distance close to overflow threshold
        data_reader._distance_traveled = 100000001
        
        mock_dt = Mock()
        mock_dt.timestamp.return_value = 1000.0
        mock_datetime.datetime.now.return_value = mock_dt
        
        result = data_reader.read_sensor_data(sample_raw_data)
        
        # Should reset to 0 when over 100000000
        assert result["distance_traveled"] == 0


class TestResetDistance:
    """Test reset_distance method"""
    
    def test_reset_distance(self, data_reader):
        # Set some values
        data_reader._distance_traveled = 1234.5
        data_reader._last_update = 5678
        
        # Reset
        data_reader.reset_distance()
        
        assert data_reader._distance_traveled == 0
        assert data_reader._last_update == 0
    
    @patch('data_reader.datetime')
    def test_reset_distance_between_reads(self, mock_datetime, data_reader, sample_raw_data):
        # First read
        mock_dt1 = Mock()
        mock_dt1.timestamp.return_value = 1000.0
        mock_datetime.datetime.now.return_value = mock_dt1
        data_reader.read_sensor_data(sample_raw_data)
        
        # Second read to accumulate distance
        mock_dt2 = Mock()
        mock_dt2.timestamp.return_value = 1001.0
        mock_datetime.datetime.now.return_value = mock_dt2
        result1 = data_reader.read_sensor_data(sample_raw_data)
        assert result1["distance_traveled"] > 0
        
        # Reset
        data_reader.reset_distance()
        
        # Third read
        mock_dt3 = Mock()
        mock_dt3.timestamp.return_value = 1002.0
        mock_datetime.datetime.now.return_value = mock_dt3
        result2 = data_reader.read_sensor_data(sample_raw_data)
        
        # Distance should be 0 (no previous timestamp after reset)
        assert result2["distance_traveled"] == 0


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_zero_speed(self, data_reader):
        raw_data = struct.pack('<ffffBBBBBH', 0.0, 0.0, 0.0, 0.0, 0, 0, 0, 0, 0, 0)
        result = data_reader.read_sensor_data(raw_data)
        
        assert result["speed"] == 0.0
        assert result["distance_traveled"] == 0.0
    
    def test_negative_speed(self, data_reader):
        raw_data = struct.pack('<ffffBBBBBH', -10.0, 0.0, 0.0, 0.0, 0, 0, 0, 0, 0, 0)
        result = data_reader.read_sensor_data(raw_data)
        
        assert result["speed"] == -10.0
    
    def test_max_values(self, data_reader):
        raw_data = struct.pack('<ffffBBBBBH',
                               999.9, 999.9, 999.9, 999.9,
                               1, 1, 1, 1, 1, 65535)  # Digital channels: 0 or 1 only
        result = data_reader.read_sensor_data(raw_data)
        
        assert result["speed"] == 999.9
        assert result["voltage"] == 1 * 0.1  # 0.1
        assert result["analog_sensor"] == 65535 * 0.5
    
    def test_conversion_factor_zero(self):
        config = Mock(spec=ConfigurationGenerator)
        config.config = [
            Car(
                name="test",
                active=True,
                theme="",
                sensors={
                    "channel0": Sensor(
                        name="zero_factor",
                        unit="",
                        conversion_factor=0.0,
                        input_type="digital"
                    )
                },
                metadata=Metadata()
            )
        ]
        reader = DataReader(config)
        raw_data = struct.pack('<ffffBBBBBH', 10.0, 10.0, 10.0, 10.0, 100, 0, 0, 0, 0, 0)
        
        result = reader.read_sensor_data(raw_data)
        
        assert result["zero_factor"] == 100 * 1.0  # Defaults to 1.0 (no conversion) if conversion factor is 0.0
