"""Comprehensive tests for BMP module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Mapping, Any

# Import the BmpSensor class
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from models.bmp import BmpSensor


class TestBmpValidation:
    """Test BMP configuration validation."""
    
    def test_validate_config_valid_defaults(self, create_config_with_attributes):
        """Test validation with valid default configuration."""
        config = create_config_with_attributes({})
        dependencies = BmpSensor.validate_config(config)
        assert dependencies == []
    
    def test_validate_config_valid_custom(self, create_config_with_attributes):
        """Test validation with valid custom configuration."""
        config = create_config_with_attributes({
            "sea_level_pressure": 101325,
            "units": "imperial"
        })
        dependencies = BmpSensor.validate_config(config)
        assert dependencies == []
    
    def test_validate_config_invalid_sea_level_pressure(self, create_config_with_attributes):
        """Test validation with invalid sea level pressure."""
        config = create_config_with_attributes({"sea_level_pressure": -100})  # Invalid pressure
        with pytest.raises(ValueError, match="sea_level_pressure must be a positive number"):
            BmpSensor.validate_config(config)
    
    def test_validate_config_invalid_units(self, create_config_with_attributes):
        """Test validation with invalid units."""
        config = create_config_with_attributes({"units": "celsius"})  # Invalid units
        with pytest.raises(ValueError, match="units must be either 'metric' or 'imperial'"):
            BmpSensor.validate_config(config)
    
    def test_validate_config_invalid_sea_level_pressure_type(self, create_config_with_attributes):
        """Test validation with invalid sea level pressure type."""
        config = create_config_with_attributes({"sea_level_pressure": "invalid"})  # Invalid type
        with pytest.raises(ValueError, match="sea_level_pressure must be a valid number"):
            BmpSensor.validate_config(config)
    
    def test_validate_config_invalid_units_type(self, create_config_with_attributes):
        """Test validation with invalid units type."""
        config = create_config_with_attributes({"units": 123})  # Invalid type
        with pytest.raises(ValueError, match="units must be a valid string"):
            BmpSensor.validate_config(config)


class TestBmpInitialization:
    """Test BMP initialization and configuration."""
    
    @patch('models.bmp.busio.I2C')
    @patch('models.bmp.board')
    @patch('models.bmp.BMP085.BMP085')
    def test_new_creates_instance(self, mock_bmp_class, mock_board, mock_i2c, mock_component_config, mock_dependencies):
        """Test that new() creates a BmpSensor instance."""
        bmp = BmpSensor.new(mock_component_config, mock_dependencies)
        assert isinstance(bmp, BmpSensor)
    
    @patch('models.bmp.busio.I2C')
    @patch('models.bmp.board')
    @patch('models.bmp.BMP085.BMP085')
    def test_reconfigure_sets_default_values(self, mock_bmp_class, mock_board, mock_i2c, mock_component_config, mock_dependencies):
        """Test that reconfigure sets default configuration values."""
        mock_bmp_instance = Mock()
        mock_bmp_class.return_value = mock_bmp_instance
        
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(mock_component_config, mock_dependencies)
        
        assert bmp.sea_level_pressure == 101325
        assert bmp.units == "metric"
        assert bmp.pressure_offset == 0.0
        assert bmp.altitude_offset == 0.0
    
    @patch('models.bmp.busio.I2C')
    @patch('models.bmp.board')
    @patch('models.bmp.BMP085.BMP085')
    def test_reconfigure_sets_custom_values(self, mock_bmp_class, mock_board, mock_i2c, create_config_with_attributes, mock_dependencies):
        """Test that reconfigure sets custom configuration values."""
        config = create_config_with_attributes({
            "sea_level_pressure": 100000,
            "units": "imperial"
        })
        
        mock_bmp_instance = Mock()
        mock_bmp_class.return_value = mock_bmp_instance
        
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(config, mock_dependencies)
        
        assert bmp.sea_level_pressure == 100000
        assert bmp.units == "imperial"
        assert bmp.pressure_offset == 0.0
        assert bmp.altitude_offset == 0.0
    
    @patch('models.bmp.busio.I2C')
    @patch('models.bmp.board')
    @patch('models.bmp.BMP085.BMP085')
    def test_reconfigure_handles_initialization_error(self, mock_bmp_class, mock_board, mock_i2c, mock_component_config, mock_dependencies):
        """Test that reconfigure handles initialization errors gracefully."""
        mock_bmp_class.side_effect = Exception("Hardware not available")
        
        bmp = BmpSensor("test-bmp")
        
        with pytest.raises(Exception, match="Hardware not available"):
            bmp.reconfigure(mock_component_config, mock_dependencies)
        
        assert bmp.sensor is None


class TestBmpReadings:
    """Test BMP sensor readings."""
    
    @patch('models.bmp.busio.I2C')
    @patch('models.bmp.board')
    @patch('models.bmp.BMP085.BMP085')
    def test_get_readings_metric_units(self, mock_bmp_class, mock_board, mock_i2c, mock_component_config, mock_dependencies):
        """Test sensor readings in metric units."""
        mock_bmp_instance = Mock()
        mock_bmp_instance.read_temperature.return_value = 25.0  # Celsius
        mock_bmp_instance.read_pressure.return_value = 101325.0  # Pa
        mock_bmp_instance.read_altitude.return_value = 100.0  # meters
        mock_bmp_class.return_value = mock_bmp_instance
        
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(mock_component_config, mock_dependencies)
        
        readings = bmp.get_readings()
        
        # Check that all expected readings are present
        expected_keys = [
            "temperature - C", "pressure - Pa", "altitude - m",
            "sea_level_pressure - Pa", "raw_pressure - Pa", "raw_altitude - m",
            "pressure_offset - Pa", "altitude_offset - m"
        ]
        
        for key in expected_keys:
            assert key in readings
            assert isinstance(readings[key], float)
        
        # Check specific values (with offsets applied)
        assert readings["temperature - C"] == 25.0
        assert readings["pressure - Pa"] == 101325.0  # No offset applied
        assert readings["altitude - m"] == 100.0  # No offset applied
        assert readings["sea_level_pressure - Pa"] == 101325.0
        assert readings["raw_pressure - Pa"] == 101325.0
        assert readings["raw_altitude - m"] == 100.0
        assert readings["pressure_offset - Pa"] == 0.0
        assert readings["altitude_offset - m"] == 0.0
    
    @patch('models.bmp.busio.I2C')
    @patch('models.bmp.board')
    @patch('models.bmp.BMP085.BMP085')
    def test_get_readings_imperial_units(self, mock_bmp_class, mock_board, mock_i2c, create_config_with_attributes, mock_dependencies):
        """Test sensor readings in imperial units."""
        config = create_config_with_attributes({"units": "imperial"})
        
        mock_bmp_instance = Mock()
        mock_bmp_instance.read_temperature.return_value = 25.0  # Celsius
        mock_bmp_instance.read_pressure.return_value = 101325.0  # Pa
        mock_bmp_instance.read_altitude.return_value = 100.0  # meters
        mock_bmp_class.return_value = mock_bmp_instance
        
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(config, mock_dependencies)
        
        readings = bmp.get_readings()
        
        # Check that all expected readings are present with imperial units
        expected_keys = [
            "temperature - F", "pressure - inHg", "altitude - ft",
            "sea_level_pressure - inHg", "raw_pressure - inHg", "raw_altitude - ft",
            "pressure_offset - inHg", "altitude_offset - ft"
        ]
        
        for key in expected_keys:
            assert key in readings
            assert isinstance(readings[key], float)
        
        # Check unit conversions
        assert abs(readings["temperature - F"] - ((25.0 * 9/5) + 32)) < 0.001
        assert abs(readings["pressure - inHg"] - (101325.0 * 0.0002953)) < 0.001
        assert abs(readings["altitude - ft"] - (100.0 * 3.28084)) < 0.001
    
    @patch('models.bmp.busio.I2C')
    @patch('models.bmp.board')
    @patch('models.bmp.BMP085.BMP085')
    def test_get_readings_with_offsets(self, mock_bmp_class, mock_board, mock_i2c, create_config_with_attributes, mock_dependencies):
        """Test sensor readings with tare offsets applied."""
        config = create_config_with_attributes({})
        
        mock_bmp_instance = Mock()
        mock_bmp_instance.read_temperature.return_value = 25.0
        mock_bmp_instance.read_pressure.return_value = 101325.0
        mock_bmp_instance.read_altitude.return_value = 100.0
        mock_bmp_class.return_value = mock_bmp_instance
        
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(config, mock_dependencies)
        
        # Set custom offsets
        bmp.pressure_offset = 1000.0
        bmp.altitude_offset = 10.0
        
        readings = bmp.get_readings()
        
        # Check that offsets are applied
        assert readings["pressure - Pa"] == 100325.0  # 101325 - 1000
        assert readings["altitude - m"] == 90.0  # 100 - 10
        assert readings["pressure_offset - Pa"] == 1000.0
        assert readings["altitude_offset - m"] == 10.0
    
    @patch('models.bmp.busio.I2C')
    @patch('models.bmp.board')
    @patch('models.bmp.BMP085.BMP085')
    def test_get_readings_handles_error(self, mock_bmp_class, mock_board, mock_i2c, mock_component_config, mock_dependencies):
        """Test that get_readings handles errors gracefully."""
        mock_bmp_instance = Mock()
        mock_bmp_instance.read_temperature = Mock(side_effect=Exception("Sensor error"))
        mock_bmp_class.return_value = mock_bmp_instance
        
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(mock_component_config, mock_dependencies)
        
        readings = bmp.get_readings()
        assert readings == {}
    
    @patch('models.bmp.busio.I2C')
    @patch('models.bmp.board')
    @patch('models.bmp.BMP085.BMP085')
    def test_get_readings_no_sensor(self, mock_bmp_class, mock_board, mock_i2c, mock_component_config, mock_dependencies):
        """Test get_readings when sensor is not initialized."""
        bmp = BmpSensor("test-bmp")
        bmp.sensor = None
        
        readings = bmp.get_readings()
        assert readings == {}


class TestBmpTare:
    """Test BMP tare functionality."""
    
    @patch('models.bmp.busio.I2C')
    @patch('models.bmp.board')
    @patch('models.bmp.BMP085.BMP085')
    def test_tare_success(self, mock_bmp_class, mock_board, mock_i2c, mock_component_config, mock_dependencies):
        """Test successful tare operation."""
        mock_bmp_instance = Mock()
        mock_bmp_instance.read_pressure.return_value = 101325.0
        mock_bmp_instance.read_altitude.return_value = 100.0
        mock_bmp_class.return_value = mock_bmp_instance
        
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(mock_component_config, mock_dependencies)
        
        bmp.tare()
        
        # Check that offsets are set to current readings
        assert bmp.pressure_offset == 101325.0
        assert bmp.altitude_offset == 100.0
    
    @patch('models.bmp.busio.I2C')
    @patch('models.bmp.board')
    @patch('models.bmp.BMP085.BMP085')
    def test_tare_handles_error(self, mock_bmp_class, mock_board, mock_i2c, mock_component_config, mock_dependencies):
        """Test that tare handles errors gracefully."""
        mock_bmp_instance = Mock()
        mock_bmp_instance.read_pressure = Mock(side_effect=Exception("Tare error"))
        mock_bmp_class.return_value = mock_bmp_instance
        
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(mock_component_config, mock_dependencies)
        
        with pytest.raises(Exception, match="Tare error"):
            bmp.tare()
    
    @patch('models.bmp.busio.I2C')
    @patch('models.bmp.board')
    @patch('models.bmp.BMP085.BMP085')
    def test_tare_no_sensor(self, mock_bmp_class, mock_board, mock_i2c, mock_component_config, mock_dependencies):
        """Test tare when sensor is not initialized."""
        bmp = BmpSensor("test-bmp")
        bmp.sensor = None
        
        with pytest.raises(RuntimeError, match="Sensor not initialized"):
            bmp.tare()
    
    def test_reset_tare_success(self, mock_component_config, mock_dependencies):
        """Test successful reset tare operation."""
        bmp = BmpSensor("test-bmp")
        bmp.pressure_offset = 1000.0
        bmp.altitude_offset = 10.0
        
        bmp.reset_tare()
        
        # Check that all offsets are reset to zero
        assert bmp.pressure_offset == 0.0
        assert bmp.altitude_offset == 0.0


class TestBmpCommands:
    """Test BMP command handling."""
    
    @patch('models.bmp.busio.I2C')
    @patch('models.bmp.board')
    @patch('models.bmp.BMP085.BMP085')
    def test_do_command_tare(self, mock_bmp_class, mock_board, mock_i2c, mock_component_config, mock_dependencies):
        """Test tare command execution."""
        mock_bmp_instance = Mock()
        mock_bmp_instance.read_pressure.return_value = 101325.0
        mock_bmp_instance.read_altitude.return_value = 100.0
        mock_bmp_class.return_value = mock_bmp_instance
        
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(mock_component_config, mock_dependencies)
        
        command = {"tare": []}
        result = bmp.do_command(command)
        
        assert "tare" in result
        assert isinstance(result["tare"], dict)
        assert "pressure_offset" in result["tare"]
        assert "altitude_offset" in result["tare"]
        assert result["tare"]["pressure_offset"] == 101325.0
        assert result["tare"]["altitude_offset"] == 100.0
    
    @patch('models.bmp.busio.I2C')
    @patch('models.bmp.board')
    @patch('models.bmp.BMP085.BMP085')
    def test_do_command_reset_tare(self, mock_bmp_class, mock_board, mock_i2c, mock_component_config, mock_dependencies):
        """Test reset_tare command execution."""
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(mock_component_config, mock_dependencies)
        
        command = {"reset_tare": []}
        result = bmp.do_command(command)
        
        assert "reset_tare" in result
        assert result["reset_tare"] is True
    
    @patch('models.bmp.busio.I2C')
    @patch('models.bmp.board')
    @patch('models.bmp.BMP085.BMP085')
    def test_do_command_unknown(self, mock_bmp_class, mock_board, mock_i2c, mock_component_config, mock_dependencies):
        """Test handling of unknown commands."""
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(mock_component_config, mock_dependencies)
        
        command = {"unknown_command": []}
        result = bmp.do_command(command)
        
        assert "unknown_command" in result
        assert "error" in result["unknown_command"]
        assert "available_commands" in result["unknown_command"]


class TestBmpIntegration:
    """Integration tests for BMP module."""
    
    @pytest.mark.integration
    @patch('models.bmp.busio.I2C')
    @patch('models.bmp.board')
    @patch('models.bmp.BMP085.BMP085')
    def test_full_workflow(self, mock_bmp_class, mock_board, mock_i2c, create_config_with_attributes, mock_dependencies):
        """Test complete BMP workflow: configure, tare, read."""
        config = create_config_with_attributes({
            "sea_level_pressure": 100000,
            "units": "imperial"
        })
        
        mock_bmp_instance = Mock()
        mock_bmp_instance.read_temperature.return_value = 25.0
        mock_bmp_instance.read_pressure.return_value = 101325.0
        mock_bmp_instance.read_altitude.return_value = 100.0
        mock_bmp_class.return_value = mock_bmp_instance
        
        # Initialize and configure
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(config, mock_dependencies)
        
        # Perform tare
        bmp.tare()
        assert bmp.pressure_offset == 101325.0
        assert bmp.altitude_offset == 100.0
        
        # Get readings
        readings = bmp.get_readings()
        assert "temperature - F" in readings
        assert "pressure - inHg" in readings
        assert "altitude - ft" in readings
        
        # Reset tare
        bmp.reset_tare()
        assert bmp.pressure_offset == 0.0
        assert bmp.altitude_offset == 0.0


class TestBmpEdgeCases:
    """Test BMP edge cases and boundary conditions."""
    
    @patch('models.bmp.busio.I2C')
    @patch('models.bmp.board')
    @patch('models.bmp.BMP085.BMP085')
    def test_zero_sea_level_pressure(self, mock_bmp_class, mock_board, mock_i2c, create_config_with_attributes, mock_dependencies):
        """Test behavior with zero sea level pressure."""
        config = create_config_with_attributes({"sea_level_pressure": 0})
        
        mock_bmp_instance = Mock()
        mock_bmp_instance.read_temperature.return_value = 25.0
        mock_bmp_instance.read_pressure.return_value = 101325.0
        mock_bmp_instance.read_altitude.return_value = 100.0
        mock_bmp_class.return_value = mock_bmp_instance
        
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(config, mock_dependencies)
        
        readings = bmp.get_readings()
        assert "altitude - m" in readings
        assert readings["altitude - m"] == 100.0  # Should still work
    
    @patch('models.bmp.busio.I2C')
    @patch('models.bmp.board')
    @patch('models.bmp.BMP085.BMP085')
    def test_extreme_temperature_values(self, mock_bmp_class, mock_board, mock_i2c, mock_component_config, mock_dependencies):
        """Test behavior with extreme temperature values."""
        mock_bmp_instance = Mock()
        mock_bmp_instance.read_temperature.return_value = -40.0  # Very cold
        mock_bmp_instance.read_pressure.return_value = 101325.0
        mock_bmp_instance.read_altitude.return_value = 100.0
        mock_bmp_class.return_value = mock_bmp_instance
        
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(mock_component_config, mock_dependencies)
        
        readings = bmp.get_readings()
        assert readings["temperature - C"] == -40.0
    
    @patch('models.bmp.busio.I2C')
    @patch('models.bmp.board')
    @patch('models.bmp.BMP085.BMP085')
    def test_negative_altitude_after_offset(self, mock_bmp_class, mock_board, mock_i2c, mock_component_config, mock_dependencies):
        """Test behavior when altitude becomes negative after offset application."""
        mock_bmp_instance = Mock()
        mock_bmp_instance.read_temperature.return_value = 25.0
        mock_bmp_instance.read_pressure.return_value = 101325.0
        mock_bmp_instance.read_altitude.return_value = 50.0  # Low altitude
        mock_bmp_class.return_value = mock_bmp_instance
        
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(mock_component_config, mock_dependencies)
        
        # Set offset higher than current altitude
        bmp.altitude_offset = 100.0
        
        readings = bmp.get_readings()
        assert readings["altitude - m"] == -50.0  # 50 - 100


# Test markers for different test types
@pytest.mark.unit
class TestBmpUnit:
    """Unit tests for BMP module."""
    pass  # All tests above are unit tests


@pytest.mark.hardware
class TestBmpHardware:
    """Hardware-dependent tests for BMP module."""
    # These tests would require actual hardware
    pass
