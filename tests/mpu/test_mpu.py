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
        with pytest.raises(Exception, match="I2C address must be between 0x68 and 0x69"):
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
        
        assert mpu.i2c_bus == 1
        assert mpu.i2c_address == 0x68
        assert mpu.accel_range == 2
        assert mpu.gyro_range == 250
        assert mpu.filter_bandwidth == 5
    
    @patch('models.mpu.busio')
    @patch('models.mpu.board')
    @patch('models.mpu.adafruit_mpu6050')
    def test_initialization_custom_values(self, mock_mpu6050_class, mock_board, mock_busio, create_config_with_attributes, mock_dependencies):
        """Test initialization with custom values."""
        config = create_config_with_attributes({
            "i2c_bus": 0,
            "i2c_address": 0x69,
            "accel_range": 4,
            "gyro_range": 500,
            "filter_bandwidth": 10
        })
        
        mock_i2c = Mock()
        mock_busio.I2C.return_value = mock_i2c
        mock_mpu_instance = Mock()
        mock_mpu6050_class.MPU6050.return_value = mock_mpu_instance
        
        mpu = Mpu("test-mpu")
        mpu.reconfigure(config, mock_dependencies)
        
        assert mpu.i2c_bus == 0
        assert mpu.i2c_address == 0x69
        assert mpu.accel_range == 4
        assert mpu.gyro_range == 500
        assert mpu.filter_bandwidth == 10
    
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
        
        assert "acceleration" in readings
        assert "gyro" in readings
        assert "temperature" in readings
        assert "i2c_bus" in readings
        assert "i2c_address" in readings
        assert "accel_range" in readings
        assert "gyro_range" in readings
        assert "filter_bandwidth" in readings
        
        # Check acceleration values
        accel = readings["acceleration"]
        assert "x" in accel
        assert "y" in accel
        assert "z" in accel
        assert accel["x"] == 1.0
        assert accel["y"] == 2.0
        assert accel["z"] == 9.8
        
        # Check gyroscope values
        gyro = readings["gyro"]
        assert "x" in gyro
        assert "y" in gyro
        assert "z" in gyro
        assert gyro["x"] == 0.1
        assert gyro["y"] == 0.2
        assert gyro["z"] == 0.3
        
        # Check temperature
        assert readings["temperature"] == 25.0
    
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
        assert mpu.accel_tare_offset is not None
        assert mpu.gyro_tare_offset is not None
        assert len(mpu.accel_tare_offset) == 3
        assert len(mpu.gyro_tare_offset) == 3
    
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
        mpu.accel_tare_offset = (0.1, 0.2, 0.0)
        mpu.gyro_tare_offset = (0.01, 0.02, 0.0)
        
        asyncio.run(mpu.reset_tare())
        
        # Tare offsets should be reset
        assert mpu.accel_tare_offset == (0.0, 0.0, 0.0)
        assert mpu.gyro_tare_offset == (0.0, 0.0, 0.0)
    
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
        assert "accel_offset" in result["tare"]
        assert "gyro_offset" in result["tare"]
        assert len(result["tare"]["accel_offset"]) == 3
        assert len(result["tare"]["gyro_offset"]) == 3
    
    @patch('models.mpu.busio')
    @patch('models.mpu.board')
    @patch('models.mpu.adafruit_mpu6050')
    def test_commands_reset_tare(self, mock_mpu6050_class, mock_board, mock_busio, mock_component_config, mock_dependencies):
        """Test reset tare command execution."""
        mpu = Mpu("test-mpu")
        mpu.reconfigure(mock_component_config, mock_dependencies)
        
        # Set some tare offsets first
        mpu.accel_tare_offset = (0.1, 0.2, 0.0)
        mpu.gyro_tare_offset = (0.01, 0.02, 0.0)
        
        command = {"reset_tare": []}
        result = asyncio.run(mpu.do_command(command))
        
        assert "reset_tare" in result
        assert result["reset_tare"]["accel_offset"] == (0.0, 0.0, 0.0)
        assert result["reset_tare"]["gyro_offset"] == (0.0, 0.0, 0.0)
    
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
            "i2c_bus": 0,
            "i2c_address": 0x69,
            "accel_range": 4,
            "gyro_range": 500,
            "filter_bandwidth": 10
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
