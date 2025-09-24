"""Unified test file that imports all models once and runs all tests together."""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from typing import Mapping, Any

# Clear Viam registry at the very beginning
try:
    from viam.resource.registry import Registry
    Registry._resources.clear()
    Registry._apis.clear()
except Exception:
    pass

# Mock board module before importing any models
with patch.dict('sys.modules', {'board': Mock()}):
    # Import all models at once to register Viam components only once
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
    
    from models.loadcell import LoadCell
    from models.mpu import Mpu
    from models.bmp import BmpSensor

# Import shared fixtures from conftest
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Import fixtures directly
from conftest import (
    mock_component_config,
    mock_resource_name,
    mock_dependencies,
    mock_gpio,
    mock_hx711,
    mock_mpu_sensor,
    mock_bmp_sensor,
    mock_i2c,
    mock_board,
    create_config_with_attributes
)


@pytest.mark.unit
class TestLoadCell:
    """LoadCell tests from the original test file."""
    
    def test_validation_valid_config(self, create_config_with_attributes):
        """Test validation with valid configuration."""
        config = create_config_with_attributes({
            "dout_pin": 5,
            "sck_pin": 6,
            "gain": 64,
            "offset": 0.0
        })
        required, optional = LoadCell.validate_config(config)
        assert required == []
        assert set(optional) == {"dout_pin", "sck_pin", "gain", "offset"}
    
    def test_validation_invalid_pins(self, create_config_with_attributes):
        """Test validation with invalid pin configuration."""
        config = create_config_with_attributes({
            "dout_pin": -1,  # Invalid pin
            "sck_pin": 6
        })
        with pytest.raises(Exception, match="dout_pin must be a valid GPIO pin"):
            LoadCell.validate_config(config)
    
    def test_initialization_defaults(self, mock_component_config, mock_dependencies):
        """Test LoadCell initialization with default values."""
        with patch('models.loadcell.HX711') as mock_hx711_class:
            mock_hx711 = Mock()
            mock_hx711_class.return_value = mock_hx711
            
            loadcell = LoadCell("test-loadcell")
            loadcell.reconfigure(mock_component_config, mock_dependencies)
            
            assert loadcell.dout_pin == 5
            assert loadcell.sck_pin == 6
            assert loadcell.gain == 64
            assert loadcell.offset == 0.0
            assert loadcell.tare_offset == 0.0
    
    def test_initialization_custom_values(self, create_config_with_attributes, mock_dependencies):
        """Test LoadCell initialization with custom values."""
        config = create_config_with_attributes({
            "dout_pin": 7,
            "sck_pin": 8,
            "gain": 128,
            "offset": 100.0
        })
        
        with patch('models.loadcell.HX711') as mock_hx711_class:
            mock_hx711 = Mock()
            mock_hx711_class.return_value = mock_hx711
            
            loadcell = LoadCell("test-loadcell")
            loadcell.reconfigure(config, mock_dependencies)
            
            assert loadcell.dout_pin == 7
            assert loadcell.sck_pin == 8
            assert loadcell.gain == 128
            assert loadcell.offset == 100.0
    
    def test_hx711_creation(self, mock_component_config, mock_dependencies):
        """Test HX711 sensor creation."""
        with patch('models.loadcell.HX711') as mock_hx711_class:
            mock_hx711 = Mock()
            mock_hx711_class.return_value = mock_hx711
            
            loadcell = LoadCell("test-loadcell")
            loadcell.reconfigure(mock_component_config, mock_dependencies)
            
            hx711 = loadcell.get_hx711()
            assert hx711 == mock_hx711
            mock_hx711_class.assert_called_once_with(5, 6, gain=64)
    
    def test_readings_success(self, mock_component_config, mock_dependencies):
        """Test successful readings."""
        with patch('models.loadcell.HX711') as mock_hx711_class:
            mock_hx711 = Mock()
            mock_hx711.get_raw_data.return_value = 1000
            mock_hx711_class.return_value = mock_hx711
            
            loadcell = LoadCell("test-loadcell")
            loadcell.reconfigure(mock_component_config, mock_dependencies)
            
            readings = asyncio.run(loadcell.get_readings())
            assert "weight" in readings
            assert readings["weight"] == 1000.0
    
    def test_tare_success(self, mock_component_config, mock_dependencies):
        """Test successful tare operation."""
        with patch('models.loadcell.HX711') as mock_hx711_class:
            mock_hx711 = Mock()
            mock_hx711.get_raw_data.return_value = 1000
            mock_hx711_class.return_value = mock_hx711
            
            loadcell = LoadCell("test-loadcell")
            loadcell.reconfigure(mock_component_config, mock_dependencies)
            
            asyncio.run(loadcell.tare())
            assert loadcell.tare_offset == 1000.0
    
    def test_commands_tare(self, mock_component_config, mock_dependencies):
        """Test tare command."""
        with patch('models.loadcell.HX711') as mock_hx711_class:
            mock_hx711 = Mock()
            mock_hx711.get_raw_data.return_value = 1000
            mock_hx711_class.return_value = mock_hx711
            
            loadcell = LoadCell("test-loadcell")
            loadcell.reconfigure(mock_component_config, mock_dependencies)
            
            result = asyncio.run(loadcell.do_command("tare", {}))
            assert result["tare"] is True
            assert loadcell.tare_offset == 1000.0
    
    def test_commands_unknown(self, mock_component_config, mock_dependencies):
        """Test unknown command handling."""
        loadcell = LoadCell("test-loadcell")
        loadcell.reconfigure(mock_component_config, mock_dependencies)
        
        result = asyncio.run(loadcell.do_command("unknown_command", {}))
        assert result["unknown_command"] is False


@pytest.mark.unit
class TestMpu:
    """MPU tests from the original test file."""
    
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
        # Note: The actual optional fields may include more than what we expect
        assert "i2c_bus" in optional
        assert "i2c_address" in optional
    
    def test_validation_invalid_i2c_address(self, create_config_with_attributes):
        """Test validation with invalid I2C address."""
        config = create_config_with_attributes({"i2c_address": 0x100})  # Invalid address
        with pytest.raises(Exception, match="i2c_address must be a valid I2C address"):
            Mpu.validate_config(config)
    
    def test_initialization_defaults(self, mock_component_config, mock_dependencies):
        """Test MPU initialization with default values."""
        with patch('models.mpu.MPU6050') as mock_mpu_class:
            mock_mpu = Mock()
            mock_mpu_class.return_value = mock_mpu
            
            mpu = Mpu("test-mpu")
            mpu.reconfigure(mock_component_config, mock_dependencies)
            
            assert mpu.i2c_bus == 1
            assert mpu.i2c_address == 0x68
    
    def test_readings_success(self, mock_component_config, mock_dependencies):
        """Test successful readings."""
        with patch('models.mpu.MPU6050') as mock_mpu_class:
            mock_mpu = Mock()
            mock_mpu.acceleration = (1.0, 2.0, 3.0)
            mock_mpu.gyro = (0.1, 0.2, 0.3)
            mock_mpu_class.return_value = mock_mpu
            
            mpu = Mpu("test-mpu")
            mpu.reconfigure(mock_component_config, mock_dependencies)
            
            readings = asyncio.run(mpu.get_readings())
            assert "accel_x" in readings
            assert "accel_y" in readings
            assert "accel_z" in readings
            assert "gyro_x" in readings
            assert "gyro_y" in readings
            assert "gyro_z" in readings
    
    def test_tare_success(self, mock_component_config, mock_dependencies):
        """Test successful tare operation."""
        with patch('models.mpu.MPU6050') as mock_mpu_class:
            mock_mpu = Mock()
            mock_mpu.acceleration = (1.0, 2.0, 3.0)
            mock_mpu.gyro = (0.1, 0.2, 0.3)
            mock_mpu_class.return_value = mock_mpu
            
            mpu = Mpu("test-mpu")
            mpu.reconfigure(mock_component_config, mock_dependencies)
            
            asyncio.run(mpu.tare())
            assert mpu.accel_x_offset == 1.0
            assert mpu.accel_y_offset == 2.0
            assert mpu.accel_z_offset == 3.0
    
    def test_commands_tare(self, mock_component_config, mock_dependencies):
        """Test tare command."""
        with patch('models.mpu.MPU6050') as mock_mpu_class:
            mock_mpu = Mock()
            mock_mpu.acceleration = (1.0, 2.0, 3.0)
            mock_mpu.gyro = (0.1, 0.2, 0.3)
            mock_mpu_class.return_value = mock_mpu
            
            mpu = Mpu("test-mpu")
            mpu.reconfigure(mock_component_config, mock_dependencies)
            
            result = asyncio.run(mpu.do_command("tare", {}))
            assert result["tare"] is True
    
    def test_commands_unknown(self, mock_component_config, mock_dependencies):
        """Test unknown command handling."""
        mpu = Mpu("test-mpu")
        mpu.reconfigure(mock_component_config, mock_dependencies)
        
        result = asyncio.run(mpu.do_command("unknown_command", {}))
        assert result["unknown_command"] is False


@pytest.mark.unit
class TestBmpSensor:
    """BMP tests from the original test file."""
    
    def test_validation_valid_config(self, create_config_with_attributes):
        """Test validation with valid configuration."""
        config = create_config_with_attributes({
            "i2c_bus": 1,
            "i2c_address": 0x77
        })
        required, optional = BmpSensor.validate_config(config)
        assert required == []
        assert "i2c_bus" in optional
        assert "i2c_address" in optional
    
    def test_validation_invalid_i2c_address(self, create_config_with_attributes):
        """Test validation with invalid I2C address."""
        config = create_config_with_attributes({"i2c_address": 0x100})  # Invalid address
        with pytest.raises(Exception, match="i2c_address must be a valid I2C address"):
            BmpSensor.validate_config(config)
    
    def test_initialization_defaults(self, mock_component_config, mock_dependencies):
        """Test BMP initialization with default values."""
        with patch('models.bmp.BMP085') as mock_bmp_class:
            mock_bmp = Mock()
            mock_bmp_class.return_value = mock_bmp
            
            bmp = BmpSensor("test-bmp")
            bmp.reconfigure(mock_component_config, mock_dependencies)
            
            assert bmp.i2c_bus == 1
            assert bmp.i2c_address == 0x77
    
    def test_readings_success(self, mock_component_config, mock_dependencies):
        """Test successful readings."""
        with patch('models.bmp.BMP085') as mock_bmp_class:
            mock_bmp = Mock()
            mock_bmp.temperature = 25.0
            mock_bmp.pressure = 101325.0
            mock_bmp.altitude = 100.0
            mock_bmp_class.return_value = mock_bmp
            
            bmp = BmpSensor("test-bmp")
            bmp.reconfigure(mock_component_config, mock_dependencies)
            
            readings = asyncio.run(bmp.get_readings())
            assert "temperature" in readings
            assert "pressure" in readings
            assert "altitude" in readings
    
    def test_tare_success(self, mock_component_config, mock_dependencies):
        """Test successful tare operation."""
        with patch('models.bmp.BMP085') as mock_bmp_class:
            mock_bmp = Mock()
            mock_bmp.pressure = 101325.0
            mock_bmp_class.return_value = mock_bmp
            
            bmp = BmpSensor("test-bmp")
            bmp.reconfigure(mock_component_config, mock_dependencies)
            
            asyncio.run(bmp.tare())
            assert bmp.pressure_offset == 101325.0
    
    def test_commands_tare(self, mock_component_config, mock_dependencies):
        """Test tare command."""
        with patch('models.bmp.BMP085') as mock_bmp_class:
            mock_bmp = Mock()
            mock_bmp.pressure = 101325.0
            mock_bmp_class.return_value = mock_bmp
            
            bmp = BmpSensor("test-bmp")
            bmp.reconfigure(mock_component_config, mock_dependencies)
            
            result = asyncio.run(bmp.do_command("tare", {}))
            assert result["tare"] is True
    
    def test_commands_unknown(self, mock_component_config, mock_dependencies):
        """Test unknown command handling."""
        bmp = BmpSensor("test-bmp")
        bmp.reconfigure(mock_component_config, mock_dependencies)
        
        result = asyncio.run(bmp.do_command("unknown_command", {}))
        assert result["unknown_command"] is False
