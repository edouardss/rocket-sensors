"""Comprehensive BMP tests with proper mocking and async handling."""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from typing import Mapping, Any

# Import the BmpSensor class
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from models.bmp import BmpSensor


@pytest.mark.unit
class TestBmpSensor:
    """Comprehensive BMP tests with proper mocking."""
    
    def test_validation_valid_config(self, create_config_with_attributes):
        """Test validation with valid configuration."""
        config = create_config_with_attributes({
            "i2c_bus": 1,
            "i2c_address": 0x77,
            "oversampling": 3,
            "sea_level_pressure": 101325,
            "units": "metric"
        })
        required, optional = BmpSensor.validate_config(config)
        assert required == []
        assert set(optional) == {"i2c_bus", "i2c_address", "oversampling", "sea_level_pressure", "units"}
    
    def test_validation_invalid_oversampling(self, create_config_with_attributes):
        """Test validation with invalid oversampling."""
        config = create_config_with_attributes({"oversampling": 5})  # Invalid oversampling
        with pytest.raises(Exception, match="Oversampling must be 0, 1, 2, or 3"):
            BmpSensor.validate_config(config)
    
    def test_validation_invalid_i2c_address(self, create_config_with_attributes):
        """Test validation with invalid I2C address."""
        config = create_config_with_attributes({"i2c_address": 0x100})  # Invalid address
        with pytest.raises(Exception, match="I2C address must be 0x76 or 0x77"):
            BmpSensor.validate_config(config)
    
    def test_validation_invalid_units(self, create_config_with_attributes):
        """Test validation with invalid units."""
        config = create_config_with_attributes({"units": "fahrenheit"})  # Invalid units
        with pytest.raises(Exception, match="Units must be 'metric' or 'imperial'"):
            BmpSensor.validate_config(config)
    
    @patch('models.bmp.busio')
    @patch('models.bmp.board')
    @patch('models.bmp.Adafruit_BMP')
    def test_initialization_defaults(self, mock_bmp_class, mock_board, mock_busio, mock_component_config, mock_dependencies):
        """Test initialization with default values."""
        mock_i2c = Mock()
        mock_busio.I2C.return_value = mock_i2c
        mock_bmp_instance = Mock()
        mock_bmp_class.BMP085.return_value = mock_bmp_instance
        
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(mock_component_config, mock_dependencies)
        
        assert bmp.i2c_bus == 1
        assert bmp.i2c_address == 0x77
        assert bmp.oversampling == 3
        assert bmp.sea_level_pressure == 101325
        assert bmp.units == "metric"
    
    @patch('models.bmp.busio')
    @patch('models.bmp.board')
    @patch('models.bmp.Adafruit_BMP')
    def test_initialization_custom_values(self, mock_bmp_class, mock_board, mock_busio, create_config_with_attributes, mock_dependencies):
        """Test initialization with custom values."""
        config = create_config_with_attributes({
            "i2c_bus": 0,
            "i2c_address": 0x76,
            "oversampling": 1,
            "sea_level_pressure": 100000,
            "units": "imperial"
        })
        
        mock_i2c = Mock()
        mock_busio.I2C.return_value = mock_i2c
        mock_bmp_instance = Mock()
        mock_bmp_class.BMP085.return_value = mock_bmp_instance
        
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(config, mock_dependencies)
        
        assert bmp.i2c_bus == 0
        assert bmp.i2c_address == 0x76
        assert bmp.oversampling == 1
        assert bmp.sea_level_pressure == 100000
        assert bmp.units == "imperial"
    
    @patch('models.bmp.busio')
    @patch('models.bmp.board')
    @patch('models.bmp.Adafruit_BMP')
    def test_bmp_creation(self, mock_bmp_class, mock_board, mock_busio, mock_component_config, mock_dependencies):
        """Test BMP085 sensor creation."""
        mock_i2c = Mock()
        mock_busio.I2C.return_value = mock_i2c
        mock_bmp_instance = Mock()
        mock_bmp_class.BMP085.return_value = mock_bmp_instance
        
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(mock_component_config, mock_dependencies)
        
        # Check I2C was created correctly
        mock_busio.I2C.assert_called_once_with(mock_board.SCL, mock_board.SDA)
        
        # Check BMP085 was created correctly
        mock_bmp_class.BMP085.assert_called_once_with(mock_i2c, address=0x77)
    
    @patch('models.bmp.busio')
    @patch('models.bmp.board')
    @patch('models.bmp.Adafruit_BMP')
    def test_bmp_initialization_error(self, mock_bmp_class, mock_board, mock_busio, mock_component_config, mock_dependencies):
        """Test BMP085 initialization error handling."""
        mock_busio.I2C.side_effect = Exception("I2C not available")
        
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(mock_component_config, mock_dependencies)
        
        with pytest.raises(Exception, match="I2C not available"):
            bmp.get_bmp()
        
        assert bmp.bmp is None
    
    @patch('models.bmp.busio')
    @patch('models.bmp.board')
    @patch('models.bmp.Adafruit_BMP')
    def test_readings_success_metric(self, mock_bmp_class, mock_board, mock_busio, mock_component_config, mock_dependencies):
        """Test successful sensor readings in metric units."""
        mock_i2c = Mock()
        mock_busio.I2C.return_value = mock_i2c
        mock_bmp_instance = Mock()
        mock_bmp_instance.temperature = 25.0  # °C
        mock_bmp_instance.pressure = 101325.0  # Pa
        mock_bmp_instance.altitude = 100.0  # m
        mock_bmp_class.BMP085.return_value = mock_bmp_instance
        
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(mock_component_config, mock_dependencies)
        
        readings = asyncio.run(bmp.get_readings())
        
        assert "temperature" in readings
        assert "pressure" in readings
        assert "altitude" in readings
        assert "i2c_bus" in readings
        assert "i2c_address" in readings
        assert "oversampling" in readings
        assert "sea_level_pressure" in readings
        assert "units" in readings
        
        # Check values in metric units
        assert readings["temperature"] == 25.0
        assert readings["pressure"] == 101325.0
        assert readings["altitude"] == 100.0
        assert readings["units"] == "metric"
    
    @patch('models.bmp.busio')
    @patch('models.bmp.board')
    @patch('models.bmp.Adafruit_BMP')
    def test_readings_success_imperial(self, mock_bmp_class, mock_board, mock_busio, create_config_with_attributes, mock_dependencies):
        """Test successful sensor readings in imperial units."""
        config = create_config_with_attributes({"units": "imperial"})
        
        mock_i2c = Mock()
        mock_busio.I2C.return_value = mock_i2c
        mock_bmp_instance = Mock()
        mock_bmp_instance.temperature = 25.0  # °C (will be converted)
        mock_bmp_instance.pressure = 101325.0  # Pa (will be converted)
        mock_bmp_instance.altitude = 100.0  # m (will be converted)
        mock_bmp_class.BMP085.return_value = mock_bmp_instance
        
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(config, mock_dependencies)
        
        readings = asyncio.run(bmp.get_readings())
        
        # Check values in imperial units
        assert readings["temperature"] == 77.0  # 25°C = 77°F
        assert readings["pressure"] == 14.7  # 101325 Pa ≈ 14.7 PSI
        assert readings["altitude"] == 328.0  # 100m ≈ 328ft
        assert readings["units"] == "imperial"
    
    @patch('models.bmp.busio')
    @patch('models.bmp.board')
    @patch('models.bmp.Adafruit_BMP')
    def test_readings_error_handling(self, mock_bmp_class, mock_board, mock_busio, mock_component_config, mock_dependencies):
        """Test readings error handling."""
        mock_i2c = Mock()
        mock_busio.I2C.return_value = mock_i2c
        mock_bmp_instance = Mock()
        mock_bmp_instance.temperature = Mock(side_effect=Exception("Sensor error"))
        mock_bmp_class.BMP085.return_value = mock_bmp_instance
        
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(mock_component_config, mock_dependencies)
        
        with pytest.raises(Exception, match="Sensor error"):
            asyncio.run(bmp.get_readings())
        
        # BMP should be cleaned up after error
        assert bmp.bmp is None
    
    @patch('models.bmp.busio')
    @patch('models.bmp.board')
    @patch('models.bmp.Adafruit_BMP')
    def test_tare_success(self, mock_bmp_class, mock_board, mock_busio, mock_component_config, mock_dependencies):
        """Test successful tare operation."""
        mock_i2c = Mock()
        mock_busio.I2C.return_value = mock_i2c
        mock_bmp_instance = Mock()
        mock_bmp_instance.altitude = 100.0  # Current altitude
        mock_bmp_class.BMP085.return_value = mock_bmp_instance
        
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(mock_component_config, mock_dependencies)
        
        asyncio.run(bmp.tare())
        
        # Tare offset should be set to current altitude
        assert bmp.altitude_tare_offset == 100.0
    
    @patch('models.bmp.busio')
    @patch('models.bmp.board')
    @patch('models.bmp.Adafruit_BMP')
    def test_tare_error_handling(self, mock_bmp_class, mock_board, mock_busio, mock_component_config, mock_dependencies):
        """Test tare error handling."""
        mock_i2c = Mock()
        mock_busio.I2C.return_value = mock_i2c
        mock_bmp_instance = Mock()
        mock_bmp_instance.altitude = Mock(side_effect=Exception("Tare error"))
        mock_bmp_class.BMP085.return_value = mock_bmp_instance
        
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(mock_component_config, mock_dependencies)
        
        with pytest.raises(Exception, match="Tare error"):
            asyncio.run(bmp.tare())
        
        # BMP should be cleaned up after error
        assert bmp.bmp is None
    
    @patch('models.bmp.busio')
    @patch('models.bmp.board')
    @patch('models.bmp.Adafruit_BMP')
    def test_reset_tare(self, mock_bmp_class, mock_board, mock_busio, mock_component_config, mock_dependencies):
        """Test reset tare operation."""
        mock_i2c = Mock()
        mock_busio.I2C.return_value = mock_i2c
        mock_bmp_instance = Mock()
        mock_bmp_instance.altitude = 100.0
        mock_bmp_class.BMP085.return_value = mock_bmp_instance
        
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(mock_component_config, mock_dependencies)
        
        # Set some tare offset first
        bmp.altitude_tare_offset = 100.0
        
        asyncio.run(bmp.reset_tare())
        
        # Tare offset should be reset
        assert bmp.altitude_tare_offset == 0.0
    
    @patch('models.bmp.busio')
    @patch('models.bmp.board')
    @patch('models.bmp.Adafruit_BMP')
    def test_commands_tare(self, mock_bmp_class, mock_board, mock_busio, mock_component_config, mock_dependencies):
        """Test tare command execution."""
        mock_i2c = Mock()
        mock_busio.I2C.return_value = mock_i2c
        mock_bmp_instance = Mock()
        mock_bmp_instance.altitude = 100.0
        mock_bmp_class.BMP085.return_value = mock_bmp_instance
        
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(mock_component_config, mock_dependencies)
        
        command = {"tare": []}
        result = asyncio.run(bmp.do_command(command))
        
        assert "tare" in result
        assert "altitude_offset" in result["tare"]
        assert result["tare"]["altitude_offset"] == 100.0
    
    @patch('models.bmp.busio')
    @patch('models.bmp.board')
    @patch('models.bmp.Adafruit_BMP')
    def test_commands_reset_tare(self, mock_bmp_class, mock_board, mock_busio, mock_component_config, mock_dependencies):
        """Test reset tare command execution."""
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(mock_component_config, mock_dependencies)
        
        # Set some tare offset first
        bmp.altitude_tare_offset = 100.0
        
        command = {"reset_tare": []}
        result = asyncio.run(bmp.do_command(command))
        
        assert "reset_tare" in result
        assert result["reset_tare"]["altitude_offset"] == 0.0
    
    @patch('models.bmp.busio')
    @patch('models.bmp.board')
    @patch('models.bmp.Adafruit_BMP')
    def test_commands_unknown(self, mock_bmp_class, mock_board, mock_busio, mock_component_config, mock_dependencies):
        """Test handling of unknown commands."""
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(mock_component_config, mock_dependencies)
        
        command = {"unknown_command": []}
        result = asyncio.run(bmp.do_command(command))
        
        assert "unknown_command" in result
        assert "error" in result["unknown_command"]
        assert "available_commands" in result["unknown_command"]
    
    @pytest.mark.integration
    @patch('models.bmp.busio')
    @patch('models.bmp.board')
    @patch('models.bmp.Adafruit_BMP')
    def test_full_workflow(self, mock_bmp_class, mock_board, mock_busio, create_config_with_attributes, mock_dependencies):
        """Test complete BMP workflow: configure, tare, read."""
        config = create_config_with_attributes({
            "i2c_bus": 0,
            "i2c_address": 0x76,
            "oversampling": 1,
            "sea_level_pressure": 100000,
            "units": "imperial"
        })
        
        mock_i2c = Mock()
        mock_busio.I2C.return_value = mock_i2c
        mock_bmp_instance = Mock()
        mock_bmp_instance.temperature = 25.0
        mock_bmp_instance.pressure = 101325.0
        mock_bmp_instance.altitude = 100.0
        mock_bmp_class.BMP085.return_value = mock_bmp_instance
        
        # Initialize and configure
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(config, mock_dependencies)
        
        # Perform tare
        asyncio.run(bmp.tare())
        assert bmp.altitude_tare_offset == 100.0
        
        # Get readings
        readings = asyncio.run(bmp.get_readings())
        assert "temperature" in readings
        assert "pressure" in readings
        assert "altitude" in readings
        assert readings["units"] == "imperial"
        
        # Reset tare
        asyncio.run(bmp.reset_tare())
        assert bmp.altitude_tare_offset == 0.0
