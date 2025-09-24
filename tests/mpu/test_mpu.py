"""Comprehensive MPU tests with proper mocking and async handling."""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from typing import Mapping, Any

# Mpu is imported by the session-scoped fixture in conftest.py
# No need to import here to avoid duplicate registration


@pytest.mark.unit
class TestMpu:
    """Comprehensive MPU tests with proper mocking."""
    
    def test_validation_valid_config(self, create_config_with_attributes):
        """Test validation with valid configuration."""
        config = create_config_with_attributes({
            "i2c_bus": 1,
            "i2c_address": 0x68,
            "accel_range": 2,
            "gyro_range": 250,
            "filter_bandwidth": 5
        })
        required, optional = Mpu.validate_config(config)
        assert required == []
        assert set(optional) == {"i2c_bus", "i2c_address", "accel_range", "gyro_range", "filter_bandwidth"}
    
    def test_validation_invalid_accel_range(self, create_config_with_attributes):
        """Test validation with invalid accelerometer range."""
        config = create_config_with_attributes({"accel_range": 8})  # Invalid range
        with pytest.raises(Exception, match="Accelerometer range must be 2, 4, 8, or 16"):
            Mpu.validate_config(config)
    
    def test_validation_invalid_gyro_range(self, create_config_with_attributes):
        """Test validation with invalid gyroscope range."""
        config = create_config_with_attributes({"gyro_range": 1000})  # Invalid range
        with pytest.raises(Exception, match="Gyroscope range must be 250, 500, 1000, or 2000"):
            Mpu.validate_config(config)
    
    def test_validation_invalid_i2c_address(self, create_config_with_attributes):
        """Test validation with invalid I2C address."""
        config = create_config_with_attributes({"i2c_address": 0x100})  # Invalid address
        with pytest.raises(Exception, match="i2c_address must be a valid I2C address \\(0x08-0x77\\)"):
            Mpu.validate_config(config)
    
    @patch('models.mpu.busio')
    @patch('models.mpu.board')
    @patch('models.mpu.adafruit_mpu6050')
    def test_initialization_defaults(self, mock_mpu6050_class, mock_board, mock_busio, mock_component_config, mock_dependencies):
        """Test initialization with default values."""
        mock_i2c = Mock()
        mock_busio.I2C.return_value = mock_i2c
        mock_mpu_instance = Mock()
        mock_mpu6050_class.MPU6050.return_value = mock_mpu_instance
        
        mpu = Mpu("test-mpu")
        mpu.reconfigure(mock_component_config, mock_dependencies)
        
        assert mpu.i2c_address == 0x68  # Default address
        assert mpu.units == "metric"  # Default units
        assert mpu.sample_rate == 100  # Default sample rate
    
    @patch('models.mpu.busio')
    @patch('models.mpu.board')
    @patch('models.mpu.adafruit_mpu6050')
    def test_initialization_custom_values(self, mock_mpu6050_class, mock_board, mock_busio, create_config_with_attributes, mock_dependencies):
        """Test initialization with custom values."""
        config = create_config_with_attributes({
            "i2c_address": 0x69,
            "units": "imperial",
            "sample_rate": 200
        })
        
        mock_i2c = Mock()
        mock_busio.I2C.return_value = mock_i2c
        mock_mpu_instance = Mock()
        mock_mpu6050_class.MPU6050.return_value = mock_mpu_instance
        
        mpu = Mpu("test-mpu")
        mpu.reconfigure(config, mock_dependencies)
        
        assert mpu.i2c_address == 0x69
        assert mpu.units == "imperial"
        assert mpu.sample_rate == 200
    
    @patch('models.mpu.busio')
    @patch('models.mpu.board')
    @patch('models.mpu.adafruit_mpu6050')
    def test_mpu_creation(self, mock_mpu6050_class, mock_board, mock_busio, mock_component_config, mock_dependencies):
        """Test MPU6050 sensor creation."""
        mock_i2c = Mock()
        mock_busio.I2C.return_value = mock_i2c
        mock_mpu_instance = Mock()
        mock_mpu6050_class.MPU6050.return_value = mock_mpu_instance
        
        mpu = Mpu("test-mpu")
        mpu.reconfigure(mock_component_config, mock_dependencies)
        
        # Check I2C was created correctly
        mock_busio.I2C.assert_called_once_with(mock_board.SCL, mock_board.SDA)
        
        # Check MPU6050 was created correctly
        mock_mpu6050_class.MPU6050.assert_called_once_with(mock_i2c, address=0x68)
    
    @patch('models.mpu.busio')
    @patch('models.mpu.board')
    @patch('models.mpu.adafruit_mpu6050')
    def test_mpu_initialization_error(self, mock_mpu6050_class, mock_board, mock_busio, mock_component_config, mock_dependencies):
        """Test MPU6050 initialization error handling."""
        mock_busio.I2C.side_effect = Exception("I2C not available")
        
        mpu = Mpu("test-mpu")
        mpu.reconfigure(mock_component_config, mock_dependencies)
        
        with pytest.raises(Exception, match="I2C not available"):
            mpu.get_mpu()
        
        assert mpu.mpu is None
    
    @patch('models.mpu.busio')
    @patch('models.mpu.board')
    @patch('models.mpu.adafruit_mpu6050')
    def test_readings_success(self, mock_mpu6050_class, mock_board, mock_busio, mock_component_config, mock_dependencies):
        """Test successful sensor readings."""
        mock_i2c = Mock()
        mock_busio.I2C.return_value = mock_i2c
        mock_mpu_instance = Mock()
        mock_mpu_instance.acceleration = (1.0, 2.0, 9.8)  # x, y, z in m/s²
        mock_mpu_instance.gyro = (0.1, 0.2, 0.3)  # x, y, z in rad/s
        mock_mpu_instance.temperature = 25.0  # °C
        mock_mpu6050_class.MPU6050.return_value = mock_mpu_instance
        
        mpu = Mpu("test-mpu")
        mpu.reconfigure(mock_component_config, mock_dependencies)
        
        readings = asyncio.run(mpu.get_readings())
        
        assert "acceleration_x - m/s²" in readings
        assert "acceleration_y - m/s²" in readings
        assert "acceleration_z - m/s²" in readings
        assert "gyro_x - rad/s" in readings
        assert "gyro_y - rad/s" in readings
        assert "gyro_z - rad/s" in readings
        assert "temperature - C" in readings
        
        # Check acceleration values
        assert readings["acceleration_x - m/s²"] == 1.0
        assert readings["acceleration_y - m/s²"] == 2.0
        assert readings["acceleration_z - m/s²"] == 9.8
        
        # Check gyroscope values
        assert readings["gyro_x - rad/s"] == 0.1
        assert readings["gyro_y - rad/s"] == 0.2
        assert readings["gyro_z - rad/s"] == 0.3
        
        # Check temperature
        assert readings["temperature - C"] == 25.0
    
    @patch('models.mpu.busio')
    @patch('models.mpu.board')
    @patch('models.mpu.adafruit_mpu6050')
    def test_readings_error_handling(self, mock_mpu6050_class, mock_board, mock_busio, mock_component_config, mock_dependencies):
        """Test readings error handling."""
        mock_i2c = Mock()
        mock_busio.I2C.return_value = mock_i2c
        mock_mpu_instance = Mock()
        mock_mpu_instance.acceleration = Mock(side_effect=Exception("Sensor error"))
        mock_mpu6050_class.MPU6050.return_value = mock_mpu_instance
        
        mpu = Mpu("test-mpu")
        mpu.reconfigure(mock_component_config, mock_dependencies)
        
        with pytest.raises(Exception, match="Sensor error"):
            asyncio.run(mpu.get_readings())
        
        # MPU should be cleaned up after error
        assert mpu.mpu is None
    
    @patch('models.mpu.busio')
    @patch('models.mpu.board')
    @patch('models.mpu.adafruit_mpu6050')
    def test_tare_success(self, mock_mpu6050_class, mock_board, mock_busio, mock_component_config, mock_dependencies):
        """Test successful tare operation."""
        mock_i2c = Mock()
        mock_busio.I2C.return_value = mock_i2c
        mock_mpu_instance = Mock()
        mock_mpu_instance.acceleration = (0.1, 0.2, 9.8)  # Small offset from zero
        mock_mpu_instance.gyro = (0.01, 0.02, 0.03)  # Small gyro offset
        mock_mpu6050_class.MPU6050.return_value = mock_mpu_instance
        
        mpu = Mpu("test-mpu")
        mpu.reconfigure(mock_component_config, mock_dependencies)
        
        asyncio.run(mpu.tare())
        
        # Tare offsets should be set
        assert mpu.accel_x_offset == 0.1
        assert mpu.accel_y_offset == 0.2
        assert mpu.accel_z_offset == 9.8
        assert mpu.gyro_x_offset == 0.01
        assert mpu.gyro_y_offset == 0.02
        assert mpu.gyro_z_offset == 0.03
    
    @patch('models.mpu.busio')
    @patch('models.mpu.board')
    @patch('models.mpu.adafruit_mpu6050')
    def test_tare_error_handling(self, mock_mpu6050_class, mock_board, mock_busio, mock_component_config, mock_dependencies):
        """Test tare error handling."""
        mock_i2c = Mock()
        mock_busio.I2C.return_value = mock_i2c
        mock_mpu_instance = Mock()
        mock_mpu_instance.acceleration = Mock(side_effect=Exception("Tare error"))
        mock_mpu6050_class.MPU6050.return_value = mock_mpu_instance
        
        mpu = Mpu("test-mpu")
        mpu.reconfigure(mock_component_config, mock_dependencies)
        
        with pytest.raises(Exception, match="Tare error"):
            asyncio.run(mpu.tare())
        
        # MPU should be cleaned up after error
        assert mpu.mpu is None
    
    @patch('models.mpu.busio')
    @patch('models.mpu.board')
    @patch('models.mpu.adafruit_mpu6050')
    def test_reset_tare(self, mock_mpu6050_class, mock_board, mock_busio, mock_component_config, mock_dependencies):
        """Test reset tare operation."""
        mock_i2c = Mock()
        mock_busio.I2C.return_value = mock_i2c
        mock_mpu_instance = Mock()
        mock_mpu_instance.acceleration = (0.1, 0.2, 9.8)
        mock_mpu_instance.gyro = (0.01, 0.02, 0.03)
        mock_mpu6050_class.MPU6050.return_value = mock_mpu_instance
        
        mpu = Mpu("test-mpu")
        mpu.reconfigure(mock_component_config, mock_dependencies)
        
        # Set some tare offsets first
        mpu.accel_x_offset = 0.1
        mpu.accel_y_offset = 0.2
        mpu.accel_z_offset = 0.0
        mpu.gyro_x_offset = 0.01
        mpu.gyro_y_offset = 0.02
        mpu.gyro_z_offset = 0.0
        
        asyncio.run(mpu.reset_tare())
        
        # Tare offsets should be reset
        assert mpu.accel_x_offset == 0.0
        assert mpu.accel_y_offset == 0.0
        assert mpu.accel_z_offset == 0.0
        assert mpu.gyro_x_offset == 0.0
        assert mpu.gyro_y_offset == 0.0
        assert mpu.gyro_z_offset == 0.0
    
    @patch('models.mpu.busio')
    @patch('models.mpu.board')
    @patch('models.mpu.adafruit_mpu6050')
    def test_commands_tare(self, mock_mpu6050_class, mock_board, mock_busio, mock_component_config, mock_dependencies):
        """Test tare command execution."""
        mock_i2c = Mock()
        mock_busio.I2C.return_value = mock_i2c
        mock_mpu_instance = Mock()
        mock_mpu_instance.acceleration = (0.1, 0.2, 9.8)
        mock_mpu_instance.gyro = (0.01, 0.02, 0.03)
        mock_mpu6050_class.MPU6050.return_value = mock_mpu_instance
        
        mpu = Mpu("test-mpu")
        mpu.reconfigure(mock_component_config, mock_dependencies)
        
        command = {"tare": []}
        result = asyncio.run(mpu.do_command(command))
        
        assert "tare" in result
        assert "accel_x_offset" in result["tare"]
        assert "accel_y_offset" in result["tare"]
        assert "accel_z_offset" in result["tare"]
        assert "gyro_x_offset" in result["tare"]
        assert "gyro_y_offset" in result["tare"]
        assert "gyro_z_offset" in result["tare"]
        assert result["tare"]["accel_x_offset"] == 0.1
        assert result["tare"]["accel_y_offset"] == 0.2
        assert result["tare"]["accel_z_offset"] == 9.8
        assert result["tare"]["gyro_x_offset"] == 0.01
        assert result["tare"]["gyro_y_offset"] == 0.02
        assert result["tare"]["gyro_z_offset"] == 0.03
    
    @patch('models.mpu.busio')
    @patch('models.mpu.board')
    @patch('models.mpu.adafruit_mpu6050')
    def test_commands_reset_tare(self, mock_mpu6050_class, mock_board, mock_busio, mock_component_config, mock_dependencies):
        """Test reset tare command execution."""
        mpu = Mpu("test-mpu")
        mpu.reconfigure(mock_component_config, mock_dependencies)
        
        # Set some tare offsets first
        mpu.accel_x_offset = 0.1
        mpu.accel_y_offset = 0.2
        mpu.accel_z_offset = 0.0
        mpu.gyro_x_offset = 0.01
        mpu.gyro_y_offset = 0.02
        mpu.gyro_z_offset = 0.0
        
        command = {"reset_tare": []}
        result = asyncio.run(mpu.do_command(command))
        
        assert "reset_tare" in result
        assert result["reset_tare"] == True
    
    @patch('models.mpu.busio')
    @patch('models.mpu.board')
    @patch('models.mpu.adafruit_mpu6050')
    def test_commands_unknown(self, mock_mpu6050_class, mock_board, mock_busio, mock_component_config, mock_dependencies):
        """Test handling of unknown commands."""
        mpu = Mpu("test-mpu")
        mpu.reconfigure(mock_component_config, mock_dependencies)
        
        command = {"unknown_command": []}
        result = asyncio.run(mpu.do_command(command))
        
        assert "unknown_command" in result
        assert "error" in result["unknown_command"]
        assert "available_commands" in result["unknown_command"]
    
    @pytest.mark.integration
    @patch('models.mpu.busio')
    @patch('models.mpu.board')
    @patch('models.mpu.adafruit_mpu6050')
    def test_full_workflow(self, mock_mpu6050_class, mock_board, mock_busio, create_config_with_attributes, mock_dependencies):
        """Test complete MPU workflow: configure, tare, read."""
        config = create_config_with_attributes({
            "i2c_address": 0x69,
            "units": "imperial",
            "sample_rate": 200
        })
        
        mock_i2c = Mock()
        mock_busio.I2C.return_value = mock_i2c
        mock_mpu_instance = Mock()
        mock_mpu_instance.acceleration = (0.1, 0.2, 9.8)
        mock_mpu_instance.gyro = (0.01, 0.02, 0.03)
        mock_mpu_instance.temperature = 25.0
        mock_mpu6050_class.MPU6050.return_value = mock_mpu_instance
        
        # Initialize and configure
        mpu = Mpu("test-mpu")
        mpu.reconfigure(config, mock_dependencies)
        
        # Perform tare
        asyncio.run(mpu.tare())
        assert mpu.accel_tare_offset is not None
        assert mpu.gyro_tare_offset is not None
        
        # Get readings
        readings = asyncio.run(mpu.get_readings())
        assert "acceleration" in readings
        assert "gyro" in readings
        assert "temperature" in readings
        
        # Reset tare
        asyncio.run(mpu.reset_tare())
        assert mpu.accel_tare_offset == (0.0, 0.0, 0.0)
        assert mpu.gyro_tare_offset == (0.0, 0.0, 0.0)
