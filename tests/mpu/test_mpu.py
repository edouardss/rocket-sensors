"""Comprehensive tests for MPU module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Mapping, Any

# Import the MPU class
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from models.mpu import Mpu


class TestMpuValidation:
    """Test MPU configuration validation."""
    
    def test_validate_config_valid_defaults(self, create_config_with_attributes):
        """Test validation with valid default configuration."""
        config = create_config_with_attributes({})
        required, optional = Mpu.validate_config(config)
        assert required == []
        assert set(optional) == {
            "i2c_address", "units", "sample_rate", 
            "accel_x_offset", "accel_y_offset", "accel_z_offset",
            "gyro_x_offset", "gyro_y_offset", "gyro_z_offset"
        }
    
    def test_validate_config_valid_custom(self, create_config_with_attributes):
        """Test validation with valid custom configuration."""
        config = create_config_with_attributes({
            "i2c_address": 0x69,
            "units": "imperial",
            "sample_rate": 200,
            "accel_x_offset": 0.1,
            "accel_y_offset": 0.2,
            "accel_z_offset": 0.3,
            "gyro_x_offset": 0.01,
            "gyro_y_offset": 0.02,
            "gyro_z_offset": 0.03
        })
        required, optional = Mpu.validate_config(config)
        assert required == []
        assert set(optional) == {
            "i2c_address", "units", "sample_rate", 
            "accel_x_offset", "accel_y_offset", "accel_z_offset",
            "gyro_x_offset", "gyro_y_offset", "gyro_z_offset"
        }
    
    def test_validate_config_invalid_i2c_address(self, create_config_with_attributes):
        """Test validation with invalid I2C address."""
        config = create_config_with_attributes({"i2c_address": 0x100})  # Invalid address
        with pytest.raises(Exception, match="i2c_address must be a valid I2C address"):
            Mpu.validate_config(config)
    
    def test_validate_config_invalid_units(self, create_config_with_attributes):
        """Test validation with invalid units."""
        config = create_config_with_attributes({"units": "celsius"})  # Invalid units
        with pytest.raises(Exception, match="units must be either 'metric' or 'imperial'"):
            Mpu.validate_config(config)
    
    def test_validate_config_invalid_sample_rate(self, create_config_with_attributes):
        """Test validation with invalid sample rate."""
        config = create_config_with_attributes({"sample_rate": -10})  # Invalid sample rate
        with pytest.raises(Exception, match="sample_rate must be a positive number"):
            Mpu.validate_config(config)
    
    def test_validate_config_invalid_offset(self, create_config_with_attributes):
        """Test validation with invalid offset value."""
        config = create_config_with_attributes({"accel_x_offset": "invalid"})  # Invalid offset
        with pytest.raises(Exception, match="accel_x_offset must be a valid number"):
            Mpu.validate_config(config)


class TestMpuInitialization:
    """Test MPU initialization and configuration."""
    
    @patch('models.mpu.busio.I2C')
    @patch('models.mpu.board')
    @patch('models.mpu.adafruit_mpu6050.MPU6050')
    def test_new_creates_instance(self, mock_mpu_class, mock_board, mock_i2c, mock_component_config, mock_dependencies):
        """Test that new() creates an MPU instance."""
        mpu = Mpu.new(mock_component_config, mock_dependencies)
        assert isinstance(mpu, Mpu)
    
    @patch('models.mpu.busio.I2C')
    @patch('models.mpu.board')
    @patch('models.mpu.adafruit_mpu6050.MPU6050')
    def test_reconfigure_sets_default_values(self, mock_mpu_class, mock_board, mock_i2c, mock_component_config, mock_dependencies):
        """Test that reconfigure sets default configuration values."""
        mock_mpu_instance = Mock()
        mock_mpu_class.return_value = mock_mpu_instance
        
        mpu = Mpu("test-mpu")
        mpu.reconfigure(mock_component_config, mock_dependencies)
        
        assert mpu.i2c_address == 0x68
        assert mpu.units == "metric"
        assert mpu.sample_rate == 100
        assert mpu.accel_x_offset == 0.0
        assert mpu.accel_y_offset == 0.0
        assert mpu.accel_z_offset == 0.0
        assert mpu.gyro_x_offset == 0.0
        assert mpu.gyro_y_offset == 0.0
        assert mpu.gyro_z_offset == 0.0
    
    @patch('models.mpu.busio.I2C')
    @patch('models.mpu.board')
    @patch('models.mpu.adafruit_mpu6050.MPU6050')
    def test_reconfigure_sets_custom_values(self, mock_mpu_class, mock_board, mock_i2c, create_config_with_attributes, mock_dependencies):
        """Test that reconfigure sets custom configuration values."""
        config = create_config_with_attributes({
            "i2c_address": 0x69,
            "units": "imperial",
            "sample_rate": 200,
            "accel_x_offset": 0.1,
            "accel_y_offset": 0.2,
            "accel_z_offset": 0.3,
            "gyro_x_offset": 0.01,
            "gyro_y_offset": 0.02,
            "gyro_z_offset": 0.03
        })
        
        mock_mpu_instance = Mock()
        mock_mpu_class.return_value = mock_mpu_instance
        
        mpu = Mpu("test-mpu")
        mpu.reconfigure(config, mock_dependencies)
        
        assert mpu.i2c_address == 0x69
        assert mpu.units == "imperial"
        assert mpu.sample_rate == 200
        assert mpu.accel_x_offset == 0.1
        assert mpu.accel_y_offset == 0.2
        assert mpu.accel_z_offset == 0.3
        assert mpu.gyro_x_offset == 0.01
        assert mpu.gyro_y_offset == 0.02
        assert mpu.gyro_z_offset == 0.03
    
    @patch('models.mpu.busio.I2C')
    @patch('models.mpu.board')
    @patch('models.mpu.adafruit_mpu6050.MPU6050')
    def test_reconfigure_handles_initialization_error(self, mock_mpu_class, mock_board, mock_i2c, mock_component_config, mock_dependencies):
        """Test that reconfigure handles initialization errors gracefully."""
        mock_mpu_class.side_effect = Exception("Hardware not available")
        
        mpu = Mpu("test-mpu")
        
        with pytest.raises(Exception, match="Hardware not available"):
            mpu.reconfigure(mock_component_config, mock_dependencies)
        
        assert mpu.sensor is None


class TestMpuReadings:
    """Test MPU sensor readings."""
    
    @patch('models.mpu.busio.I2C')
    @patch('models.mpu.board')
    @patch('models.mpu.adafruit_mpu6050.MPU6050')
    def test_get_readings_metric_units(self, mock_mpu_class, mock_board, mock_i2c, mock_component_config, mock_dependencies):
        """Test sensor readings in metric units."""
        mock_mpu_instance = Mock()
        mock_mpu_instance.acceleration = (0.1, 0.2, 9.8)  # m/s²
        mock_mpu_instance.gyro = (0.01, 0.02, 0.03)  # rad/s
        mock_mpu_instance.temperature = 25.0  # Celsius
        mock_mpu_class.return_value = mock_mpu_instance
        
        mpu = Mpu("test-mpu")
        mpu.reconfigure(mock_component_config, mock_dependencies)
        
        readings = mpu.get_readings()
        
        # Check that all expected readings are present
        expected_keys = [
            "acceleration_x - m/s²", "acceleration_y - m/s²", "acceleration_z - m/s²",
            "gyro_x - rad/s", "gyro_y - rad/s", "gyro_z - rad/s",
            "temperature - C"
        ]
        
        for key in expected_keys:
            assert key in readings
            assert isinstance(readings[key], float)
        
        # Check specific values (with offsets applied)
        assert readings["acceleration_x - m/s²"] == 0.1  # No offset applied
        assert readings["acceleration_y - m/s²"] == 0.2
        assert readings["acceleration_z - m/s²"] == 9.8
        assert readings["gyro_x - rad/s"] == 0.01
        assert readings["gyro_y - rad/s"] == 0.02
        assert readings["gyro_z - rad/s"] == 0.03
        assert readings["temperature - C"] == 25.0
    
    @patch('models.mpu.busio.I2C')
    @patch('models.mpu.board')
    @patch('models.mpu.adafruit_mpu6050.MPU6050')
    def test_get_readings_imperial_units(self, mock_mpu_class, mock_board, mock_i2c, create_config_with_attributes, mock_dependencies):
        """Test sensor readings in imperial units."""
        config = create_config_with_attributes({"units": "imperial"})
        
        mock_mpu_instance = Mock()
        mock_mpu_instance.acceleration = (0.1, 0.2, 9.8)  # m/s²
        mock_mpu_instance.gyro = (0.01, 0.02, 0.03)  # rad/s
        mock_mpu_instance.temperature = 25.0  # Celsius
        mock_mpu_class.return_value = mock_mpu_instance
        
        mpu = Mpu("test-mpu")
        mpu.reconfigure(config, mock_dependencies)
        
        readings = mpu.get_readings()
        
        # Check that all expected readings are present with imperial units
        expected_keys = [
            "acceleration_x - ft/s²", "acceleration_y - ft/s²", "acceleration_z - ft/s²",
            "gyro_x - deg/s", "gyro_y - deg/s", "gyro_z - deg/s",
            "temperature - F"
        ]
        
        for key in expected_keys:
            assert key in readings
            assert isinstance(readings[key], float)
        
        # Check unit conversions
        assert abs(readings["acceleration_x - ft/s²"] - (0.1 * 3.28084)) < 0.001
        assert abs(readings["gyro_x - deg/s"] - (0.01 * 57.2958)) < 0.001
        assert abs(readings["temperature - F"] - ((25.0 * 9/5) + 32)) < 0.001
    
    @patch('models.mpu.busio.I2C')
    @patch('models.mpu.board')
    @patch('models.mpu.adafruit_mpu6050.MPU6050')
    def test_get_readings_with_offsets(self, mock_mpu_class, mock_board, mock_i2c, create_config_with_attributes, mock_dependencies):
        """Test sensor readings with tare offsets applied."""
        config = create_config_with_attributes({
            "accel_x_offset": 0.05,
            "accel_y_offset": 0.1,
            "accel_z_offset": 0.15,
            "gyro_x_offset": 0.005,
            "gyro_y_offset": 0.01,
            "gyro_z_offset": 0.015
        })
        
        mock_mpu_instance = Mock()
        mock_mpu_instance.acceleration = (0.1, 0.2, 9.8)  # m/s²
        mock_mpu_instance.gyro = (0.01, 0.02, 0.03)  # rad/s
        mock_mpu_instance.temperature = 25.0  # Celsius
        mock_mpu_class.return_value = mock_mpu_instance
        
        mpu = Mpu("test-mpu")
        mpu.reconfigure(config, mock_dependencies)
        
        readings = mpu.get_readings()
        
        # Check that offsets are applied
        assert readings["acceleration_x - m/s²"] == 0.05  # 0.1 - 0.05
        assert readings["acceleration_y - m/s²"] == 0.1   # 0.2 - 0.1
        assert readings["acceleration_z - m/s²"] == 9.65  # 9.8 - 0.15
        assert readings["gyro_x - rad/s"] == 0.005  # 0.01 - 0.005
        assert readings["gyro_y - rad/s"] == 0.01   # 0.02 - 0.01
        assert readings["gyro_z - rad/s"] == 0.015  # 0.03 - 0.015
    
    @patch('models.mpu.busio.I2C')
    @patch('models.mpu.board')
    @patch('models.mpu.adafruit_mpu6050.MPU6050')
    def test_get_readings_handles_error(self, mock_mpu_class, mock_board, mock_i2c, mock_component_config, mock_dependencies):
        """Test that get_readings handles errors gracefully."""
        mock_mpu_instance = Mock()
        mock_mpu_instance.acceleration = Mock(side_effect=Exception("Sensor error"))
        mock_mpu_class.return_value = mock_mpu_instance
        
        mpu = Mpu("test-mpu")
        mpu.reconfigure(mock_component_config, mock_dependencies)
        
        readings = mpu.get_readings()
        assert readings == {}
    
    @patch('models.mpu.busio.I2C')
    @patch('models.mpu.board')
    @patch('models.mpu.adafruit_mpu6050.MPU6050')
    def test_get_readings_no_sensor(self, mock_mpu_class, mock_board, mock_i2c, mock_component_config, mock_dependencies):
        """Test get_readings when sensor is not initialized."""
        mpu = Mpu("test-mpu")
        mpu.sensor = None
        
        readings = mpu.get_readings()
        assert readings == {}


class TestMpuTare:
    """Test MPU tare functionality."""
    
    @patch('models.mpu.busio.I2C')
    @patch('models.mpu.board')
    @patch('models.mpu.adafruit_mpu6050.MPU6050')
    def test_tare_success(self, mock_mpu_class, mock_board, mock_i2c, mock_component_config, mock_dependencies):
        """Test successful tare operation."""
        mock_mpu_instance = Mock()
        mock_mpu_instance.acceleration = (0.1, 0.2, 9.8)
        mock_mpu_instance.gyro = (0.01, 0.02, 0.03)
        mock_mpu_class.return_value = mock_mpu_instance
        
        mpu = Mpu("test-mpu")
        mpu.reconfigure(mock_component_config, mock_dependencies)
        
        mpu.tare()
        
        # Check that offsets are set to current readings
        assert mpu.accel_x_offset == 0.1
        assert mpu.accel_y_offset == 0.2
        assert mpu.accel_z_offset == 9.8
        assert mpu.gyro_x_offset == 0.01
        assert mpu.gyro_y_offset == 0.02
        assert mpu.gyro_z_offset == 0.03
    
    @patch('models.mpu.busio.I2C')
    @patch('models.mpu.board')
    @patch('models.mpu.adafruit_mpu6050.MPU6050')
    def test_tare_handles_error(self, mock_mpu_class, mock_board, mock_i2c, mock_component_config, mock_dependencies):
        """Test that tare handles errors gracefully."""
        mock_mpu_instance = Mock()
        mock_mpu_instance.acceleration = Mock(side_effect=Exception("Tare error"))
        mock_mpu_class.return_value = mock_mpu_instance
        
        mpu = Mpu("test-mpu")
        mpu.reconfigure(mock_component_config, mock_dependencies)
        
        with pytest.raises(Exception, match="Tare error"):
            mpu.tare()
    
    @patch('models.mpu.busio.I2C')
    @patch('models.mpu.board')
    @patch('models.mpu.adafruit_mpu6050.MPU6050')
    def test_tare_no_sensor(self, mock_mpu_class, mock_board, mock_i2c, mock_component_config, mock_dependencies):
        """Test tare when sensor is not initialized."""
        mpu = Mpu("test-mpu")
        mpu.sensor = None
        
        with pytest.raises(RuntimeError, match="Sensor not initialized"):
            mpu.tare()
    
    def test_reset_tare_success(self, mock_component_config, mock_dependencies):
        """Test successful reset tare operation."""
        mpu = Mpu("test-mpu")
        mpu.accel_x_offset = 0.1
        mpu.accel_y_offset = 0.2
        mpu.accel_z_offset = 0.3
        mpu.gyro_x_offset = 0.01
        mpu.gyro_y_offset = 0.02
        mpu.gyro_z_offset = 0.03
        
        mpu.reset_tare()
        
        # Check that all offsets are reset to zero
        assert mpu.accel_x_offset == 0.0
        assert mpu.accel_y_offset == 0.0
        assert mpu.accel_z_offset == 0.0
        assert mpu.gyro_x_offset == 0.0
        assert mpu.gyro_y_offset == 0.0
        assert mpu.gyro_z_offset == 0.0


class TestMpuCommands:
    """Test MPU command handling."""
    
    @patch('models.mpu.busio.I2C')
    @patch('models.mpu.board')
    @patch('models.mpu.adafruit_mpu6050.MPU6050')
    def test_do_command_tare(self, mock_mpu_class, mock_board, mock_i2c, mock_component_config, mock_dependencies):
        """Test tare command execution."""
        mock_mpu_instance = Mock()
        mock_mpu_instance.acceleration = (0.1, 0.2, 9.8)
        mock_mpu_instance.gyro = (0.01, 0.02, 0.03)
        mock_mpu_class.return_value = mock_mpu_instance
        
        mpu = Mpu("test-mpu")
        mpu.reconfigure(mock_component_config, mock_dependencies)
        
        command = {"tare": []}
        result = mpu.do_command(command)
        
        assert "tare" in result
        assert isinstance(result["tare"], dict)
        assert "accel_x_offset" in result["tare"]
        assert "accel_y_offset" in result["tare"]
        assert "accel_z_offset" in result["tare"]
        assert "gyro_x_offset" in result["tare"]
        assert "gyro_y_offset" in result["tare"]
        assert "gyro_z_offset" in result["tare"]
    
    @patch('models.mpu.busio.I2C')
    @patch('models.mpu.board')
    @patch('models.mpu.adafruit_mpu6050.MPU6050')
    def test_do_command_reset_tare(self, mock_mpu_class, mock_board, mock_i2c, mock_component_config, mock_dependencies):
        """Test reset_tare command execution."""
        mpu = Mpu("test-mpu")
        mpu.reconfigure(mock_component_config, mock_dependencies)
        
        command = {"reset_tare": []}
        result = mpu.do_command(command)
        
        assert "reset_tare" in result
        assert result["reset_tare"] is True
    
    @patch('models.mpu.busio.I2C')
    @patch('models.mpu.board')
    @patch('models.mpu.adafruit_mpu6050.MPU6050')
    def test_do_command_unknown(self, mock_mpu_class, mock_board, mock_i2c, mock_component_config, mock_dependencies):
        """Test handling of unknown commands."""
        mpu = Mpu("test-mpu")
        mpu.reconfigure(mock_component_config, mock_dependencies)
        
        command = {"unknown_command": []}
        result = mpu.do_command(command)
        
        assert "unknown_command" in result
        assert "error" in result["unknown_command"]
        assert "available_commands" in result["unknown_command"]


class TestMpuIntegration:
    """Integration tests for MPU module."""
    
    @pytest.mark.integration
    @patch('models.mpu.busio.I2C')
    @patch('models.mpu.board')
    @patch('models.mpu.adafruit_mpu6050.MPU6050')
    def test_full_workflow(self, mock_mpu_class, mock_board, mock_i2c, create_config_with_attributes, mock_dependencies):
        """Test complete MPU workflow: configure, tare, read."""
        config = create_config_with_attributes({
            "i2c_address": 0x69,
            "units": "imperial",
            "sample_rate": 200
        })
        
        mock_mpu_instance = Mock()
        mock_mpu_instance.acceleration = (0.1, 0.2, 9.8)
        mock_mpu_instance.gyro = (0.01, 0.02, 0.03)
        mock_mpu_instance.temperature = 25.0
        mock_mpu_class.return_value = mock_mpu_instance
        
        # Initialize and configure
        mpu = Mpu("test-mpu")
        mpu.reconfigure(config, mock_dependencies)
        
        # Perform tare
        mpu.tare()
        assert mpu.accel_x_offset == 0.1
        assert mpu.gyro_x_offset == 0.01
        
        # Get readings
        readings = mpu.get_readings()
        assert "acceleration_x - ft/s²" in readings
        assert "gyro_x - deg/s" in readings
        assert "temperature - F" in readings
        
        # Reset tare
        mpu.reset_tare()
        assert mpu.accel_x_offset == 0.0
        assert mpu.gyro_x_offset == 0.0


# Test markers for different test types
@pytest.mark.unit
class TestMpuUnit:
    """Unit tests for MPU module."""
    pass  # All tests above are unit tests


@pytest.mark.hardware
class TestMpuHardware:
    """Hardware-dependent tests for MPU module."""
    # These tests would require actual hardware
    pass
