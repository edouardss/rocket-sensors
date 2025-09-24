"""Working LoadCell tests with proper mocking and async handling."""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from typing import Mapping, Any

# LoadCell is imported by the session-scoped fixture in conftest.py
# No need to import here to avoid duplicate registration


@pytest.mark.unit
class TestLoadCell:
    """Working LoadCell tests with proper mocking."""
    
    def test_validation_valid_config(self, create_config_with_attributes):
        """Test validation with valid configuration."""
        config = create_config_with_attributes({
            "gain": 64,
            "doutPin": 5,
            "sckPin": 6,
            "numberOfReadings": 3,
            "tare_offset": 0.0
        })
        required, optional = LoadCell.validate_config(config)
        assert required == []
        assert set(optional) == {"gain", "doutPin", "sckPin", "numberOfReadings", "tare_offset"}
    
    def test_validation_invalid_gain(self, create_config_with_attributes):
        """Test validation with invalid gain."""
        config = create_config_with_attributes({"gain": 50})  # Invalid gain
        with pytest.raises(Exception, match="Gain must be 32, 64, or 128"):
            LoadCell.validate_config(config)
    
    def test_validation_invalid_pin(self, create_config_with_attributes):
        """Test validation with invalid pin numbers."""
        config = create_config_with_attributes({"doutPin": 50})  # Invalid pin
        with pytest.raises(Exception, match="Data Out pin must be a valid GPIO pin number"):
            LoadCell.validate_config(config)
    
    def test_validation_invalid_tare_offset(self, create_config_with_attributes):
        """Test validation with invalid tare offset."""
        config = create_config_with_attributes({"tare_offset": 100.0})  # Positive offset
        with pytest.raises(Exception, match="Tare offset must be a non-positive floating point value"):
            LoadCell.validate_config(config)
    
    @patch('models.loadcell.GPIO')
    @patch('models.loadcell.HX711')
    def test_initialization_defaults(self, mock_hx711_class, mock_gpio, mock_component_config, mock_dependencies):
        """Test initialization with default values."""
        
        loadcell = LoadCell("test-loadcell")
        loadcell.reconfigure(mock_component_config, mock_dependencies)
        
        assert loadcell.gain == 64
        assert loadcell.doutPin == 5
        assert loadcell.sckPin == 6
        assert loadcell.numberOfReadings == 3
        assert loadcell.tare_offset == 0.0
    
    @patch('models.loadcell.GPIO')
    @patch('models.loadcell.HX711')
    def test_initialization_custom_values(self, mock_hx711_class, mock_gpio, create_config_with_attributes, mock_dependencies):
        """Test initialization with custom values."""
        config = create_config_with_attributes({
            "gain": 128,
            "doutPin": 7,
            "sckPin": 8,
            "numberOfReadings": 5,
            "tare_offset": -100.0
        })
        
        loadcell = LoadCell("test-loadcell")
        loadcell.reconfigure(config, mock_dependencies)
        
        assert loadcell.gain == 128
        assert loadcell.doutPin == 7
        assert loadcell.sckPin == 8
        assert loadcell.numberOfReadings == 5
        assert loadcell.tare_offset == -100.0
    
    @patch('models.loadcell.GPIO')
    @patch('models.loadcell.HX711')
    def test_hx711_creation(self, mock_hx711_class, mock_gpio, mock_component_config, mock_dependencies):
        """Test HX711 sensor creation."""
        mock_hx711_instance = Mock()
        mock_hx711_instance.reset = Mock()
        mock_hx711_class.return_value = mock_hx711_instance
        
        loadcell = LoadCell("test-loadcell")
        loadcell.reconfigure(mock_component_config, mock_dependencies)
        
        hx711 = loadcell.get_hx711()
        assert hx711 == mock_hx711_instance
        mock_hx711_class.assert_called_once_with(
            dout_pin=5,
            pd_sck_pin=6,
            channel="A",
            gain=64
        )
        mock_hx711_instance.reset.assert_called_once()
    
    @patch('models.loadcell.GPIO')
    @patch('models.loadcell.HX711')
    def test_hx711_initialization_error(self, mock_hx711_class, mock_gpio, mock_component_config, mock_dependencies):
        """Test HX711 initialization error handling."""
        
        # Create a mock that raises an exception when called
        def mock_hx711_constructor(*args, **kwargs):
            raise Exception("Hardware not available")
        
        mock_hx711_class.side_effect = mock_hx711_constructor
        
        loadcell = LoadCell("test-loadcell")
        
        # The error should be raised during reconfigure when get_hx711() is called
        with pytest.raises(Exception, match="Hardware not available"):
            loadcell.reconfigure(mock_component_config, mock_dependencies)
        
        # The error should be caught and logged, hx711 should remain None
        assert loadcell.hx711 is None
    
    @patch('models.loadcell.GPIO')
    @patch('models.loadcell.HX711')
    def test_readings_success(self, mock_hx711_class, mock_gpio, mock_component_config, mock_dependencies):
        """Test successful sensor readings."""
        mock_hx711_instance = Mock()
        mock_hx711_instance.get_raw_data.return_value = [8200, 8205, 8195]  # ~1kg readings
        mock_hx711_class.return_value = mock_hx711_instance
        
        loadcell = LoadCell("test-loadcell")
        loadcell.reconfigure(mock_component_config, mock_dependencies)
        
        readings = asyncio.run(loadcell.get_readings())
        
        assert "weight" in readings
        assert "measures" in readings
        assert "doutPin" in readings
        assert "sckPin" in readings
        assert "gain" in readings
        assert "numberOfReadings" in readings
        assert "tare_offset" in readings
        
        # Check that weight is calculated correctly
        expected_weight = sum([1.0, 1.0006, 0.9994]) / 3  # Converted from raw values
        assert abs(readings["weight"] - expected_weight) < 0.001
    
    @patch('models.loadcell.GPIO')
    @patch('models.loadcell.HX711')
    def test_readings_with_tare_offset(self, mock_hx711_class, mock_gpio, create_config_with_attributes, mock_dependencies):
        """Test readings with tare offset applied."""
        config = create_config_with_attributes({"tare_offset": -8200})  # -1kg offset
        mock_hx711_instance = Mock()
        mock_hx711_instance.get_raw_data.return_value = [8200, 8205, 8195]  # ~1kg readings
        mock_hx711_class.return_value = mock_hx711_instance
        
        loadcell = LoadCell("test-loadcell")
        loadcell.reconfigure(config, mock_dependencies)
        
        readings = asyncio.run(loadcell.get_readings())
        
        # With -1kg tare offset, readings should be ~2kg
        expected_weight = sum([2.0, 2.0006, 1.9994]) / 3
        assert abs(readings["weight"] - expected_weight) < 0.001
    
    @patch('models.loadcell.GPIO')
    @patch('models.loadcell.HX711')
    def test_readings_error_handling(self, mock_hx711_class, mock_gpio, mock_component_config, mock_dependencies):
        """Test readings error handling."""
        mock_hx711_instance = Mock()
        mock_hx711_instance.get_raw_data.side_effect = Exception("Sensor error")
        mock_hx711_class.return_value = mock_hx711_instance
        
        loadcell = LoadCell("test-loadcell")
        loadcell.reconfigure(mock_component_config, mock_dependencies)
        
        with pytest.raises(Exception, match="Sensor error"):
            asyncio.run(loadcell.get_readings())
        
        # HX711 should be cleaned up after error
        assert loadcell.hx711 is None
    
    @patch('models.loadcell.GPIO')
    @patch('models.loadcell.HX711')
    def test_tare_success(self, mock_hx711_class, mock_gpio, mock_component_config, mock_dependencies):
        """Test successful tare operation."""
        mock_hx711_instance = Mock()
        mock_hx711_instance.get_raw_data.return_value = [1000, 1005, 995]
        mock_hx711_class.return_value = mock_hx711_instance
        
        loadcell = LoadCell("test-loadcell")
        loadcell.reconfigure(mock_component_config, mock_dependencies)
        
        asyncio.run(loadcell.tare())
        
        # Tare offset should be set to average of raw readings
        expected_offset = (1000 + 1005 + 995) / 3
        assert loadcell.tare_offset == expected_offset
    
    @patch('models.loadcell.GPIO')
    @patch('models.loadcell.HX711')
    def test_tare_error_handling(self, mock_hx711_class, mock_gpio, mock_component_config, mock_dependencies):
        """Test tare error handling."""
        mock_hx711_instance = Mock()
        mock_hx711_instance.get_raw_data.side_effect = Exception("Tare error")
        mock_hx711_class.return_value = mock_hx711_instance
        
        loadcell = LoadCell("test-loadcell")
        loadcell.reconfigure(mock_component_config, mock_dependencies)
        
        with pytest.raises(Exception, match="Tare error"):
            asyncio.run(loadcell.tare())
        
        # HX711 should be cleaned up after error
        assert loadcell.hx711 is None
    
    @patch('models.loadcell.GPIO')
    @patch('models.loadcell.HX711')
    def test_commands_tare(self, mock_hx711_class, mock_gpio, mock_component_config, mock_dependencies):
        """Test tare command execution."""
        mock_hx711_instance = Mock()
        mock_hx711_instance.get_raw_data.return_value = [1000, 1005, 995]
        mock_hx711_class.return_value = mock_hx711_instance
        
        loadcell = LoadCell("test-loadcell")
        loadcell.reconfigure(mock_component_config, mock_dependencies)
        
        command = {"tare": []}
        result = asyncio.run(loadcell.do_command(command))
        
        assert "tare" in result
        assert isinstance(result["tare"], float)
        assert result["tare"] > 0  # Should be positive tare offset in kg
    
    @patch('models.loadcell.GPIO')
    @patch('models.loadcell.HX711')
    def test_commands_unknown(self, mock_hx711_class, mock_gpio, mock_component_config, mock_dependencies):
        """Test handling of unknown commands."""
        
        loadcell = LoadCell("test-loadcell")
        loadcell.reconfigure(mock_component_config, mock_dependencies)
        
        command = {"unknown_command": []}
        result = asyncio.run(loadcell.do_command(command))
        
        assert "unknown_command" in result
        # Unknown commands return False
        assert result["unknown_command"] is False
    
    @patch('models.loadcell.GPIO')
    @patch('models.loadcell.HX711')
    def test_cleanup(self, mock_hx711_class, mock_gpio, mock_component_config, mock_dependencies):
        """Test resource cleanup."""
        mock_hx711_instance = Mock()
        mock_hx711_class.return_value = mock_hx711_instance
        
        loadcell = LoadCell("test-loadcell")
        loadcell.reconfigure(mock_component_config, mock_dependencies)
        loadcell.get_hx711()  # Initialize HX711
        
        loadcell.close()
        
        assert loadcell.hx711 is None
        mock_gpio.cleanup.assert_called_once_with((5, 6))
    
    @pytest.mark.integration
    @patch('models.loadcell.GPIO')
    @patch('models.loadcell.HX711')
    def test_full_workflow(self, mock_hx711_class, mock_gpio, create_config_with_attributes, mock_dependencies):
        """Test complete LoadCell workflow: configure, tare, read."""
        config = create_config_with_attributes({
            "gain": 128,
            "doutPin": 7,
            "sckPin": 8,
            "numberOfReadings": 5,
            "tare_offset": 0.0
        })
        
        
        mock_hx711_instance = Mock()
        mock_hx711_instance.get_raw_data.return_value = [8200, 8205, 8195, 8202, 8198]
        mock_hx711_class.return_value = mock_hx711_instance
        
        # Initialize and configure
        loadcell = LoadCell("test-loadcell")
        loadcell.reconfigure(config, mock_dependencies)
        
        # Perform tare
        asyncio.run(loadcell.tare())
        assert loadcell.tare_offset > 0
        
        # Get readings
        readings = asyncio.run(loadcell.get_readings())
        assert "weight" in readings
        # Weight should be close to 0 after tare (since we're subtracting the tare offset)
        assert abs(readings["weight"]) < 0.1
        
        # Clean up
        loadcell.close()
        assert loadcell.hx711 is None
