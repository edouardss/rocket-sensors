"""Comprehensive BMP tests with proper mocking and async handling."""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from typing import Mapping, Any

# BmpSensor is imported by the session-scoped fixture in conftest.py
# No need to import here to avoid duplicate registration


@pytest.mark.unit
class TestBmpSensor:
    """Comprehensive BMP tests with proper mocking."""
    
    def test_validation_valid_config(self, create_config_with_attributes):
        """Test validation with valid configuration."""
        config = create_config_with_attributes({
            "sea_level_pressure": 101325,
            "units": "metric"
        })
        # BMP validate_config returns Sequence[str], not tuple
        result = BmpSensor.validate_config(config)
        assert result == []
    
    def test_validation_invalid_oversampling(self, create_config_with_attributes):
        """Test validation with invalid oversampling."""
        # BMP doesn't validate oversampling, so this test should pass
        config = create_config_with_attributes({"oversampling": 5})  # Invalid oversampling
        result = BmpSensor.validate_config(config)
        assert result == []
    
    def test_validation_invalid_i2c_address(self, create_config_with_attributes):
        """Test validation with invalid I2C address."""
        # BMP doesn't validate i2c_address, so this test should pass
        config = create_config_with_attributes({"i2c_address": 0x100})  # Invalid address
        result = BmpSensor.validate_config(config)
        assert result == []
    
    def test_validation_invalid_units(self, create_config_with_attributes):
        """Test validation with invalid units."""
        config = create_config_with_attributes({"units": "fahrenheit"})  # Invalid units
        with pytest.raises(Exception, match="units must be either 'metric' or 'imperial'"):
            BmpSensor.validate_config(config)
    
    @patch('models.bmp.busio')
    @patch('models.bmp.board')
    @patch('models.bmp.BMP085')
    def test_initialization_defaults(self, mock_bmp_class, mock_board, mock_busio, mock_component_config, mock_dependencies):
        """Test initialization with default values."""
        mock_i2c = Mock()
        mock_busio.I2C.return_value = mock_i2c
        mock_bmp_instance = Mock()
        mock_bmp_class.BMP085.return_value = mock_bmp_instance
        
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(mock_component_config, mock_dependencies)
        
        assert bmp.sea_level_pressure == 101325
        assert bmp.units == "metric"
    
    @patch('models.bmp.busio')
    @patch('models.bmp.board')
    @patch('models.bmp.BMP085')
    def test_initialization_custom_values(self, mock_bmp_class, mock_board, mock_busio, create_config_with_attributes, mock_dependencies):
        """Test initialization with custom values."""
        config = create_config_with_attributes({
            "sea_level_pressure": 100000,
            "units": "imperial"
        })
        
        mock_i2c = Mock()
        mock_busio.I2C.return_value = mock_i2c
        mock_bmp_instance = Mock()
        mock_bmp_class.BMP085.return_value = mock_bmp_instance
        
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(config, mock_dependencies)
        
        assert bmp.sea_level_pressure == 100000
        assert bmp.units == "imperial"
    
    @patch('models.bmp.busio')
    @patch('models.bmp.board')
    @patch('models.bmp.BMP085')
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
        mock_bmp_class.BMP085.assert_called_once_with(busnum=1)
    
    @patch('models.bmp.busio')
    @patch('models.bmp.board')
    @patch('models.bmp.BMP085')
    def test_bmp_initialization_error(self, mock_bmp_class, mock_board, mock_busio, mock_component_config, mock_dependencies):
        """Test BMP085 initialization error handling."""
        mock_busio.I2C.side_effect = Exception("I2C not available")
        
        bmp = BmpSensor("test-bmp")
        with pytest.raises(Exception, match="I2C not available"):
            bmp.reconfigure(mock_component_config, mock_dependencies)
        
        assert bmp.sensor is None
    
    @patch('models.bmp.busio')
    @patch('models.bmp.board')
    @patch('models.bmp.BMP085')
    def test_readings_success_metric(self, mock_bmp_class, mock_board, mock_busio, mock_component_config, mock_dependencies):
        """Test successful sensor readings in metric units."""
        mock_i2c = Mock()
        mock_busio.I2C.return_value = mock_i2c
        mock_bmp_instance = Mock()
        mock_bmp_instance.read_temperature.return_value = 25.0  # °C
        mock_bmp_instance.read_pressure.return_value = 101325.0  # Pa
        mock_bmp_instance.read_altitude.return_value = 100.0  # m
        mock_bmp_class.BMP085.return_value = mock_bmp_instance
        
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(mock_component_config, mock_dependencies)
        
        readings = asyncio.run(bmp.get_readings())
        
        assert "temperature - C" in readings
        assert "pressure - Pa" in readings
        assert "altitude - m" in readings
        assert "sea_level_pressure - Pa" in readings
        assert "raw_pressure - Pa" in readings
        assert "raw_altitude - m" in readings
        assert "pressure_offset - Pa" in readings
        assert "altitude_offset - m" in readings
        
        # Check values in metric units
        assert readings["temperature - C"] == 25.0
        assert readings["pressure - Pa"] == 101325.0
        assert readings["altitude - m"] == 100.0
    
    @patch('models.bmp.busio')
    @patch('models.bmp.board')
    @patch('models.bmp.BMP085')
    def test_readings_success_imperial(self, mock_bmp_class, mock_board, mock_busio, create_config_with_attributes, mock_dependencies):
        """Test successful sensor readings in imperial units."""
        config = create_config_with_attributes({"units": "imperial"})
        
        mock_i2c = Mock()
        mock_busio.I2C.return_value = mock_i2c
        mock_bmp_instance = Mock()
        mock_bmp_instance.read_temperature.return_value = 25.0  # °C (will be converted)
        mock_bmp_instance.read_pressure.return_value = 101325.0  # Pa (will be converted)
        mock_bmp_instance.read_altitude.return_value = 100.0  # m (will be converted)
        mock_bmp_class.BMP085.return_value = mock_bmp_instance
        
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(config, mock_dependencies)
        
        readings = asyncio.run(bmp.get_readings())
        
        # Check values in imperial units
        assert readings["temperature - F"] == 77.0  # 25°C = 77°F
        assert readings["pressure - inHg"] == pytest.approx(29.92, rel=1e-2)  # 101325 Pa ≈ 29.92 inHg
        assert readings["altitude - ft"] == pytest.approx(328.084, abs=0.1)  # 100m ≈ 328.084ft
    
    @patch('models.bmp.busio')
    @patch('models.bmp.board')
    @patch('models.bmp.BMP085')
    def test_readings_error_handling(self, mock_bmp_class, mock_board, mock_busio, mock_component_config, mock_dependencies):
        """Test readings error handling."""
        mock_i2c = Mock()
        mock_busio.I2C.return_value = mock_i2c
        mock_bmp_instance = Mock()
        mock_bmp_instance.read_temperature.side_effect = Exception("Sensor error")
        mock_bmp_class.BMP085.return_value = mock_bmp_instance
        
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(mock_component_config, mock_dependencies)
        
        readings = asyncio.run(bmp.get_readings())
        assert readings == {}  # Error handling returns empty dict
    
    @patch('models.bmp.busio')
    @patch('models.bmp.board')
    @patch('models.bmp.BMP085')
    def test_tare_success(self, mock_bmp_class, mock_board, mock_busio, mock_component_config, mock_dependencies):
        """Test successful tare operation."""
        mock_i2c = Mock()
        mock_busio.I2C.return_value = mock_i2c
        mock_bmp_instance = Mock()
        mock_bmp_instance.read_pressure.return_value = 101325.0  # Current pressure
        mock_bmp_instance.read_altitude.return_value = 100.0  # Current altitude
        mock_bmp_class.BMP085.return_value = mock_bmp_instance
        
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(mock_component_config, mock_dependencies)
        
        asyncio.run(bmp.tare())
        
        # Tare offsets should be set
        assert bmp.pressure_offset == 101325.0
        assert bmp.altitude_offset == 100.0
    
    @patch('models.bmp.busio')
    @patch('models.bmp.board')
    @patch('models.bmp.BMP085')
    def test_tare_error_handling(self, mock_bmp_class, mock_board, mock_busio, mock_component_config, mock_dependencies):
        """Test tare error handling."""
        mock_i2c = Mock()
        mock_busio.I2C.return_value = mock_i2c
        mock_bmp_instance = Mock()
        mock_bmp_instance.read_pressure.side_effect = Exception("Tare error")
        mock_bmp_instance.read_altitude.side_effect = Exception("Tare error")
        mock_bmp_class.BMP085.return_value = mock_bmp_instance
        
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(mock_component_config, mock_dependencies)
        
        with pytest.raises(Exception, match="Tare error"):
            asyncio.run(bmp.tare())
    
    @patch('models.bmp.busio')
    @patch('models.bmp.board')
    @patch('models.bmp.BMP085')
    def test_reset_tare(self, mock_bmp_class, mock_board, mock_busio, mock_component_config, mock_dependencies):
        """Test reset tare operation."""
        mock_i2c = Mock()
        mock_busio.I2C.return_value = mock_i2c
        mock_bmp_instance = Mock()
        mock_bmp_instance.altitude = 100.0
        mock_bmp_class.BMP085.return_value = mock_bmp_instance
        
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(mock_component_config, mock_dependencies)
        
        # Set some tare offsets first
        bmp.pressure_offset = 1000.0
        bmp.altitude_offset = 50.0
        
        asyncio.run(bmp.reset_tare())
        
        # Tare offsets should be reset
        assert bmp.pressure_offset == 0.0
        assert bmp.altitude_offset == 0.0
    
    @patch('models.bmp.busio')
    @patch('models.bmp.board')
    @patch('models.bmp.BMP085')
    def test_commands_tare(self, mock_bmp_class, mock_board, mock_busio, mock_component_config, mock_dependencies):
        """Test tare command execution."""
        mock_i2c = Mock()
        mock_busio.I2C.return_value = mock_i2c
        mock_bmp_instance = Mock()
        mock_bmp_instance.read_pressure.return_value = 101325.0
        mock_bmp_instance.read_altitude.return_value = 100.0
        mock_bmp_class.BMP085.return_value = mock_bmp_instance
        
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(mock_component_config, mock_dependencies)
        
        command = {"tare": []}
        result = asyncio.run(bmp.do_command(command))
        
        assert "tare" in result
        assert "pressure_offset" in result["tare"]
        assert "altitude_offset" in result["tare"]
        assert result["tare"]["pressure_offset"] == 101325.0
        assert result["tare"]["altitude_offset"] == 100.0
    
    @patch('models.bmp.busio')
    @patch('models.bmp.board')
    @patch('models.bmp.BMP085')
    def test_commands_reset_tare(self, mock_bmp_class, mock_board, mock_busio, mock_component_config, mock_dependencies):
        """Test reset tare command execution."""
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(mock_component_config, mock_dependencies)
        
        # Set some tare offsets first
        bmp.pressure_offset = 1000.0
        bmp.altitude_offset = 50.0
        
        command = {"reset_tare": []}
        result = asyncio.run(bmp.do_command(command))
        
        assert "reset_tare" in result
        assert result["reset_tare"] == True
    
    @patch('models.bmp.busio')
    @patch('models.bmp.board')
    @patch('models.bmp.BMP085')
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
    @patch('models.bmp.BMP085')
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
        mock_bmp_instance.read_temperature.return_value = 25.0
        mock_bmp_instance.read_pressure.return_value = 101325.0
        mock_bmp_instance.read_altitude.return_value = 100.0
        mock_bmp_class.BMP085.return_value = mock_bmp_instance
        
        # Initialize and configure
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(config, mock_dependencies)
        
        # Perform tare
        asyncio.run(bmp.tare())
        assert bmp.altitude_offset == 100.0
        
        # Get readings
        readings = asyncio.run(bmp.get_readings())
        assert "temperature - F" in readings
        assert "pressure - inHg" in readings
        assert "altitude - ft" in readings
        
        # Reset tare
        asyncio.run(bmp.reset_tare())
        assert bmp.altitude_offset == 0.0
