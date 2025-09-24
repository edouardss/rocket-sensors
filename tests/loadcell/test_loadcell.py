"""Comprehensive tests for LoadCell module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Mapping, Any

# Import the LoadCell class
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from models.loadcell import LoadCell


@pytest.mark.unit
class TestLoadCellValidation:
    """Test LoadCell configuration validation."""
    
    def test_validate_config_valid_defaults(self, create_config_with_attributes):
        """Test validation with valid default configuration."""
        config = create_config_with_attributes({})
        required, optional = LoadCell.validate_config(config)
        assert required == []
        assert set(optional) == {"gain", "doutPin", "sckPin", "numberOfReadings", "tare_offset"}
    
    def test_validate_config_valid_custom(self, create_config_with_attributes):
        """Test validation with valid custom configuration."""
        config = create_config_with_attributes({
            "gain": 128,
            "doutPin": 7,
            "sckPin": 8,
            "numberOfReadings": 5,
            "tare_offset": -100.0
        })
        required, optional = LoadCell.validate_config(config)
        assert required == []
        assert set(optional) == {"gain", "doutPin", "sckPin", "numberOfReadings", "tare_offset"}
    
    def test_validate_config_invalid_gain(self, create_config_with_attributes):
        """Test validation with invalid gain value."""
        config = create_config_with_attributes({"gain": 64.5})  # Invalid gain
        with pytest.raises(Exception, match="Gain must be 32, 64, or 128"):
            LoadCell.validate_config(config)
    
    def test_validate_config_invalid_dout_pin(self, create_config_with_attributes):
        """Test validation with invalid doutPin value."""
        config = create_config_with_attributes({"doutPin": 50})  # Invalid pin
        with pytest.raises(Exception, match="Data Out pin must be a valid GPIO pin number"):
            LoadCell.validate_config(config)
    
    def test_validate_config_invalid_sck_pin(self, create_config_with_attributes):
        """Test validation with invalid sckPin value."""
        config = create_config_with_attributes({"sckPin": 0})  # Invalid pin
        with pytest.raises(Exception, match="Clock pin must be a valid GPIO pin number"):
            LoadCell.validate_config(config)
    
    def test_validate_config_invalid_number_of_readings(self, create_config_with_attributes):
        """Test validation with invalid numberOfReadings value."""
        config = create_config_with_attributes({"numberOfReadings": 150})  # Too many readings
        with pytest.raises(Exception, match="Number of readings must be a positive integer less than 100"):
            LoadCell.validate_config(config)
    
    def test_validate_config_invalid_tare_offset(self, create_config_with_attributes):
        """Test validation with invalid tare_offset value."""
        config = create_config_with_attributes({"tare_offset": 100.0})  # Positive offset
        with pytest.raises(Exception, match="Tare offset must be a non-positive floating point value"):
            LoadCell.validate_config(config)


@pytest.mark.unit
class TestLoadCellInitialization:
    """Test LoadCell initialization and configuration."""
    
    @patch('models.loadcell.GPIO')
    @patch('models.loadcell.HX711')
    def test_new_creates_instance(self, mock_hx711_class, mock_gpio, mock_component_config, mock_dependencies):
        """Test that new() creates a LoadCell instance."""
        loadcell = LoadCell.new(mock_component_config, mock_dependencies)
        assert isinstance(loadcell, LoadCell)
    
    @patch('models.loadcell.GPIO')
    @patch('models.loadcell.HX711')
    def test_reconfigure_sets_default_values(self, mock_hx711_class, mock_gpio, mock_component_config, mock_dependencies):
        """Test that reconfigure sets default configuration values."""
        loadcell = LoadCell("test-loadcell")
        loadcell.reconfigure(mock_component_config, mock_dependencies)
        
        assert loadcell.gain == 64
        assert loadcell.doutPin == 5
        assert loadcell.sckPin == 6
        assert loadcell.numberOfReadings == 3
        assert loadcell.tare_offset == 0.0
    
    @patch('models.loadcell.GPIO')
    @patch('models.loadcell.HX711')
    def test_reconfigure_sets_custom_values(self, mock_hx711_class, mock_gpio, create_config_with_attributes, mock_dependencies):
        """Test that reconfigure sets custom configuration values."""
        config = create_config_with_attributes({
            "gain": 128,
            "doutPin": 7,
            "sckPin": 8,
            "numberOfReadings": 5,
            "tare_offset": -50.0
        })
        
        loadcell = LoadCell("test-loadcell")
        loadcell.reconfigure(config, mock_dependencies)
        
        assert loadcell.gain == 128
        assert loadcell.doutPin == 7
        assert loadcell.sckPin == 8
        assert loadcell.numberOfReadings == 5
        assert loadcell.tare_offset == -50.0


@pytest.mark.unit
class TestLoadCellHX711Management:
    """Test HX711 sensor management."""
    
    @patch('models.loadcell.GPIO')
    @patch('models.loadcell.HX711')
    def test_get_hx711_creates_instance(self, mock_hx711_class, mock_gpio, mock_component_config, mock_dependencies):
        """Test that get_hx711 creates HX711 instance when needed."""
        mock_hx711_instance = Mock()
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
    def test_get_hx711_handles_initialization_error(self, mock_hx711_class, mock_gpio, mock_component_config, mock_dependencies):
        """Test that get_hx711 handles initialization errors gracefully."""
        mock_hx711_class.side_effect = Exception("Hardware not available")
        
        loadcell = LoadCell("test-loadcell")
        loadcell.reconfigure(mock_component_config, mock_dependencies)
        
        with pytest.raises(Exception, match="Hardware not available"):
            loadcell.get_hx711()
        
        assert loadcell.hx711 is None
    
    @patch('models.loadcell.GPIO')
    @patch('models.loadcell.HX711')
    def test_cleanup_gpio_pins(self, mock_gpio, mock_hx711_class, mock_component_config, mock_dependencies):
        """Test GPIO pin cleanup."""
        loadcell = LoadCell("test-loadcell")
        loadcell.reconfigure(mock_component_config, mock_dependencies)
        
        loadcell.cleanup_gpio_pins()
        mock_gpio.cleanup.assert_called_once_with((5, 6))
    
    @patch('models.loadcell.GPIO')
    @patch('models.loadcell.HX711')
    def test_close_cleans_up_resources(self, mock_gpio, mock_hx711_class, mock_component_config, mock_dependencies):
        """Test that close() cleans up resources properly."""
        mock_hx711_instance = Mock()
        mock_hx711_class.return_value = mock_hx711_instance
        
        loadcell = LoadCell("test-loadcell")
        loadcell.reconfigure(mock_component_config, mock_dependencies)
        loadcell.get_hx711()  # Initialize HX711
        
        loadcell.close()
        
        assert loadcell.hx711 is None
        mock_gpio.cleanup.assert_called_once_with((5, 6))


@pytest.mark.unit
class TestLoadCellReadings:
    """Test LoadCell sensor readings."""
    
    @patch('models.loadcell.GPIO')
    @patch('models.loadcell.HX711')
    def test_get_readings_success(self, mock_hx711_class, mock_gpio, mock_component_config, mock_dependencies):
        """Test successful sensor readings."""
        mock_hx711_instance = Mock()
        mock_hx711_instance.get_raw_data.return_value = [8200, 8205, 8195]  # ~1kg readings
        mock_hx711_class.return_value = mock_hx711_instance
        
        loadcell = LoadCell("test-loadcell")
        loadcell.reconfigure(mock_component_config, mock_dependencies)
        
        readings = loadcell.get_readings()
        
        assert "weight" in readings
        assert "measures" in readings
        assert "doutPin" in readings
        assert "sckPin" in readings
        assert "gain" in readings
        assert "numberOfReadings" in readings
        assert "tare_offset" in readings
        
        # Check that weight is calculated correctly (average of measures)
        expected_weight = sum([1.0, 1.0006, 0.9994]) / 3  # Converted from raw values
        assert abs(readings["weight"] - expected_weight) < 0.001
    
    @patch('models.loadcell.GPIO')
    @patch('models.loadcell.HX711')
    def test_get_readings_with_tare_offset(self, mock_hx711_class, mock_gpio, create_config_with_attributes, mock_dependencies):
        """Test sensor readings with tare offset applied."""
        config = create_config_with_attributes({"tare_offset": -8200})  # -1kg offset
        mock_hx711_instance = Mock()
        mock_hx711_instance.get_raw_data.return_value = [8200, 8205, 8195]  # ~1kg readings
        mock_hx711_class.return_value = mock_hx711_instance
        
        loadcell = LoadCell("test-loadcell")
        loadcell.reconfigure(config, mock_dependencies)
        
        readings = loadcell.get_readings()
        
        # With -1kg tare offset, readings should be ~2kg
        expected_weight = sum([2.0, 2.0006, 1.9994]) / 3
        assert abs(readings["weight"] - expected_weight) < 0.001
    
    @patch('models.loadcell.GPIO')
    @patch('models.loadcell.HX711')
    def test_get_readings_handles_error(self, mock_hx711_class, mock_gpio, mock_component_config, mock_dependencies):
        """Test that get_readings handles errors gracefully."""
        mock_hx711_instance = Mock()
        mock_hx711_instance.get_raw_data.side_effect = Exception("Sensor error")
        mock_hx711_class.return_value = mock_hx711_instance
        
        loadcell = LoadCell("test-loadcell")
        loadcell.reconfigure(mock_component_config, mock_dependencies)
        
        with pytest.raises(Exception, match="Sensor error"):
            loadcell.get_readings()
        
        # HX711 should be cleaned up after error
        assert loadcell.hx711 is None


@pytest.mark.unit
class TestLoadCellTare:
    """Test LoadCell tare functionality."""
    
    @patch('models.loadcell.GPIO')
    @patch('models.loadcell.HX711')
    def test_tare_success(self, mock_hx711_class, mock_gpio, mock_component_config, mock_dependencies):
        """Test successful tare operation."""
        mock_hx711_instance = Mock()
        mock_hx711_instance.get_raw_data.return_value = [1000, 1005, 995]
        mock_hx711_class.return_value = mock_hx711_instance
        
        loadcell = LoadCell("test-loadcell")
        loadcell.reconfigure(mock_component_config, mock_dependencies)
        
        loadcell.tare()
        
        # Tare offset should be set to average of raw readings
        expected_offset = (1000 + 1005 + 995) / 3
        assert loadcell.tare_offset == expected_offset
    
    @patch('models.loadcell.GPIO')
    @patch('models.loadcell.HX711')
    def test_tare_handles_error(self, mock_hx711_class, mock_gpio, mock_component_config, mock_dependencies):
        """Test that tare handles errors gracefully."""
        mock_hx711_instance = Mock()
        mock_hx711_instance.get_raw_data.side_effect = Exception("Tare error")
        mock_hx711_class.return_value = mock_hx711_instance
        
        loadcell = LoadCell("test-loadcell")
        loadcell.reconfigure(mock_component_config, mock_dependencies)
        
        with pytest.raises(Exception, match="Tare error"):
            loadcell.tare()
        
        # HX711 should be cleaned up after error
        assert loadcell.hx711 is None


@pytest.mark.unit
class TestLoadCellCommands:
    """Test LoadCell command handling."""
    
    @patch('models.loadcell.GPIO')
    @patch('models.loadcell.HX711')
    def test_do_command_tare(self, mock_hx711_class, mock_gpio, mock_component_config, mock_dependencies):
        """Test tare command execution."""
        mock_hx711_instance = Mock()
        mock_hx711_instance.get_raw_data.return_value = [1000, 1005, 995]
        mock_hx711_class.return_value = mock_hx711_instance
        
        loadcell = LoadCell("test-loadcell")
        loadcell.reconfigure(mock_component_config, mock_dependencies)
        
        command = {"tare": []}
        result = loadcell.do_command(command)
        
        assert "tare" in result
        assert isinstance(result["tare"], float)
        assert result["tare"] > 0  # Should be positive tare offset in kg
    
    @patch('models.loadcell.GPIO')
    @patch('models.loadcell.HX711')
    def test_do_command_unknown(self, mock_hx711_class, mock_gpio, mock_component_config, mock_dependencies):
        """Test handling of unknown commands."""
        loadcell = LoadCell("test-loadcell")
        loadcell.reconfigure(mock_component_config, mock_dependencies)
        
        command = {"unknown_command": []}
        result = loadcell.do_command(command)
        
        assert "unknown_command" in result
        assert "error" in result["unknown_command"]
        assert "available_commands" in result["unknown_command"]


class TestLoadCellIntegration:
    """Integration tests for LoadCell module."""
    
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
        loadcell.tare()
        assert loadcell.tare_offset > 0
        
        # Get readings
        readings = loadcell.get_readings()
        assert "weight" in readings
        assert readings["weight"] > 0
        
        # Clean up
        loadcell.close()
        assert loadcell.hx711 is None


# Test markers for different test types
@pytest.mark.unit
class TestLoadCellUnit:
    """Unit tests for LoadCell module."""
    pass  # All tests above are unit tests


@pytest.mark.hardware
class TestLoadCellHardware:
    """Hardware-dependent tests for LoadCell module."""
    # These tests would require actual hardware
    pass
