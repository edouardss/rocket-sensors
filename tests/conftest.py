"""Shared test fixtures and mocks for rocket-sensors testing framework."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, Mapping
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import ResourceName
from viam.resource.base import ResourceBase
from viam.utils import struct_to_dict

# Session-scoped fixture to register all models once per test session
@pytest.fixture(scope="session", autouse=True)
def register_all_models():
    """Register all models once at the start of the test session."""
    try:
        from viam.resource.registry import Registry
        # Clear any existing registrations
        Registry._RESOURCES.clear()
        Registry._APIS.clear()
        
        # Import and register all models once
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
        
        # Mock board module before importing models
        from unittest.mock import Mock
        sys.modules['board'] = Mock()
        
        # Import all models to register them once
        from models.loadcell import LoadCell
        from models.mpu import Mpu
        from models.bmp import BmpSensor
        
        # Make models available globally for test files
        import builtins
        builtins.LoadCell = LoadCell
        builtins.Mpu = Mpu
        builtins.BmpSensor = BmpSensor
        
        print(f"✅ Registered all models: {len(Registry._APIS)} APIs, {len(Registry._RESOURCES)} resources")
        
    except Exception as e:
        print(f"⚠️  Could not register models: {e}")
    
    yield
    
    # Clean up after session
    try:
        from viam.resource.registry import Registry
        Registry._RESOURCES.clear()
        Registry._APIS.clear()
    except Exception:
        pass


@pytest.fixture
def loadcell_class():
    """Provide LoadCell class for testing."""
    from models.loadcell import LoadCell
    return LoadCell

@pytest.fixture
def mpu_class():
    """Provide Mpu class for testing."""
    from models.mpu import Mpu
    return Mpu

@pytest.fixture
def bmp_class():
    """Provide BmpSensor class for testing."""
    from models.bmp import BmpSensor
    return BmpSensor

@pytest.fixture
def mock_component_config():
    """Create a mock ComponentConfig for testing."""
    config = Mock(spec=ComponentConfig)
    config.name = "test-sensor"
    config.namespace = "edss"
    config.type = "sensor"
    config.model = "test-model"
    config.api = "sensor"
    config.attributes = Mock()
    config.attributes.fields = {}
    return config


@pytest.fixture
def mock_resource_name():
    """Create a mock ResourceName for testing."""
    from viam.proto.common import ResourceName
    name = Mock(spec=ResourceName)
    name.namespace = "edss"
    name.type = "sensor"
    name.subtype = "loadcell"
    name.name = "test-sensor"
    return name


@pytest.fixture
def mock_dependencies():
    """Create mock dependencies for testing."""
    return {}


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    logger = Mock()
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    return logger


@pytest.fixture
def mock_gpio():
    """Mock GPIO module for testing without Raspberry Pi hardware."""
    gpio = Mock()
    gpio.OUT = 0
    gpio.IN = 1
    gpio.HIGH = 1
    gpio.LOW = 0
    gpio.BCM = 11
    gpio.BOARD = 10
    gpio.cleanup = Mock()
    gpio.setup = Mock()
    gpio.output = Mock()
    gpio.input = Mock(return_value=0)
    gpio.setmode = Mock()
    gpio.setwarnings = Mock()
    gpio.getmode = Mock(return_value=11)
    return gpio


@pytest.fixture
def mock_hx711():
    """Mock HX711 sensor for testing."""
    hx711 = Mock()
    hx711.reset = Mock()
    hx711.get_raw_data = Mock(return_value=[1000, 1005, 995])  # Mock raw readings
    return hx711


@pytest.fixture
def mock_mpu_sensor():
    """Mock MPU6050 sensor for testing."""
    sensor = Mock()
    sensor.acceleration = (0.1, 0.2, 9.8)  # Mock acceleration in m/s²
    sensor.gyro = (0.01, 0.02, 0.03)  # Mock gyro in rad/s
    sensor.temperature = 25.0  # Mock temperature in Celsius
    sensor.accelerometer_range = Mock()
    sensor.gyro_range = Mock()
    return sensor


@pytest.fixture
def mock_bmp_sensor():
    """Mock BMP085 sensor for testing."""
    sensor = Mock()
    sensor.read_temperature = Mock(return_value=25.0)  # Celsius
    sensor.read_pressure = Mock(return_value=101325.0)  # Pa
    sensor.read_altitude = Mock(return_value=100.0)  # meters
    return sensor


@pytest.fixture
def mock_i2c():
    """Mock I2C bus for testing."""
    i2c = Mock()
    return i2c


@pytest.fixture
def mock_board():
    """Mock board module for testing."""
    board = Mock()
    board.SCL = 3
    board.SDA = 2
    return board


@pytest.fixture
def loadcell_config_data():
    """Sample configuration data for LoadCell testing."""
    return {
        "gain": 64,
        "doutPin": 5,
        "sckPin": 6,
        "numberOfReadings": 3,
        "tare_offset": 0.0
    }


@pytest.fixture
def mpu_config_data():
    """Sample configuration data for MPU testing."""
    return {
        "i2c_address": 0x68,
        "units": "metric",
        "sample_rate": 100,
        "accel_x_offset": 0.0,
        "accel_y_offset": 0.0,
        "accel_z_offset": 0.0,
        "gyro_x_offset": 0.0,
        "gyro_y_offset": 0.0,
        "gyro_z_offset": 0.0
    }


@pytest.fixture
def bmp_config_data():
    """Sample configuration data for BMP testing."""
    return {
        "sea_level_pressure": 101325,
        "units": "metric"
    }


@pytest.fixture
def create_config_with_attributes():
    """Factory function to create ComponentConfig with specific attributes."""
    def _create_config(attributes: Dict[str, Any]) -> ComponentConfig:
        config = Mock(spec=ComponentConfig)
        config.name = "test-sensor"
        config.namespace = "edss"
        config.type = "sensor"
        config.model = "test-model"
        config.api = "sensor"
        config.attributes = Mock()
        
        # Convert attributes to protobuf field format
        fields = {}
        for key, value in attributes.items():
            field = Mock()
            if isinstance(value, str):
                field.HasField = Mock(return_value=True)
                field.string_value = value
                field.list_value = Mock()
                field.list_value.values = []
            elif isinstance(value, (int, float)):
                field.HasField = Mock(return_value=True)
                field.number_value = value
                field.list_value = Mock()
                field.list_value.values = []
            elif isinstance(value, bool):
                field.HasField = Mock(return_value=True)
                field.bool_value = value
                field.list_value = Mock()
                field.list_value.values = []
            else:
                field.HasField = Mock(return_value=False)
                field.list_value = Mock()
                field.list_value.values = []
            fields[key] = field
        
        config.attributes.fields = fields
        
        # Mock struct_to_dict to return the original attributes
        def mock_struct_to_dict(attrs):
            return attributes
        config.attributes.struct_to_dict = mock_struct_to_dict
        
        return config
    return _create_config


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "hardware: marks tests that require hardware (deselect with '-m \"not hardware\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
