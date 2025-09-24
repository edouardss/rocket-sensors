# Testing Framework for Rocket Sensors

This directory contains a comprehensive, modular testing framework for the rocket-sensors project. The framework provides thorough testing with proper mocking, designed to be easily extensible for testing all sensor modules (LoadCell, MPU, BMP) and future modules.

## Framework Structure

```
tests/
├── conftest.py                  # Shared fixtures and mocks
├── pytest.ini                  # Pytest configuration
├── README.md                   # This file
├── loadcell/                   # LoadCell module tests
│   ├── __init__.py
│   └── test_loadcell.py         # Comprehensive tests with mocking
├── mpu/                        # MPU module tests
│   ├── __init__.py
│   └── test_mpu.py              # Comprehensive tests with mocking
└── bmp/                        # BMP module tests
    ├── __init__.py
    └── test_bmp.py              # Comprehensive tests with mocking
```

## Testing Approach

This framework uses a **single, comprehensive testing approach** that includes:

- **Proper mocking** of hardware dependencies and Viam SDK
- **Async handling** for all async methods
- **Multiple test classes** per module for organized testing
- **Complete coverage** of all functionality
- **Error handling** with proper exception testing
- **Integration tests** for full workflows

## Test Categories

### Unit Tests (`@pytest.mark.unit`)
- Test individual functions and methods in isolation
- Use mocks to simulate hardware dependencies
- Fast execution, no hardware required
- Run by default

### Integration Tests (`@pytest.mark.integration`)
- Test complete workflows and module interactions
- May use real hardware or more realistic mocks
- Slower execution
- Run with `-m integration`

### Hardware Tests (`@pytest.mark.hardware`)
- Tests that require actual hardware
- Not run in CI by default
- Run with `--hardware` flag

## Running Tests

### Using the Test Runner

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
python test_runner.py

# Run specific module tests
python test_runner.py --module loadcell
python test_runner.py --module mpu
python test_runner.py --module bmp

# Run specific test types
python test_runner.py --type unit
python test_runner.py --type integration
python test_runner.py --hardware

# Run with coverage
python test_runner.py --coverage
```

### Using pytest directly

```bash
# Run all tests
pytest

# Run specific module tests
pytest tests/loadcell/
pytest tests/mpu/
pytest tests/bmp/

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test types
pytest -m unit
pytest -m integration
pytest -m "not hardware"

# Run specific test function
pytest tests/loadcell/test_loadcell.py::TestLoadCell::test_validation_valid_config
```

## Test Coverage

The framework includes comprehensive test coverage for:

### LoadCell Module
- Configuration validation
- Initialization and reconfiguration
- HX711 sensor management
- GPIO pin handling
- Sensor readings and tare functionality
- Command handling
- Error handling and cleanup

### MPU Module
- Configuration validation
- Initialization and reconfiguration
- Sensor readings (acceleration, gyroscope, temperature)
- Tare functionality and offset management
- Command handling
- Error handling

### BMP Module
- Configuration validation
- Initialization and reconfiguration
- Sensor readings (temperature, pressure, altitude)
- Tare functionality and offset management
- Command handling
- Error handling

## Mocking Strategy

The framework uses comprehensive mocking to test without hardware:

### Hardware Mocks
- **GPIO**: Mock RPi.GPIO for LoadCell testing
- **HX711**: Mock HX711 sensor for LoadCell testing
- **MPU6050**: Mock MPU6050 sensor for MPU testing
- **BMP085**: Mock BMP085 sensor for BMP testing
- **I2C**: Mock I2C bus for sensor communication

### Viam SDK Mocks
- **ComponentConfig**: Mock configuration objects with proper protobuf structure
- **Dependencies**: Mock resource dependencies
- **Loggers**: Mock logging functionality

## Fixtures

### Shared Fixtures (conftest.py)
- `mock_component_config`: Mock ComponentConfig for testing
- `mock_dependencies`: Mock dependencies for testing
- `mock_logger`: Mock logger for testing
- `mock_gpio`: Mock GPIO module
- `mock_hx711_class`: Mock HX711 sensor class
- `mock_mpu6050_class`: Mock MPU6050 sensor class
- `mock_adafruit_bmp_class`: Mock BMP085 sensor class
- `mock_busio`: Mock I2C bus
- `mock_board`: Mock board module
- `create_config_with_attributes`: Factory for creating configs with attributes

### Module-Specific Fixtures
- `loadcell_config_data`: Sample LoadCell configuration
- `mpu_config_data`: Sample MPU configuration
- `bmp_config_data`: Sample BMP configuration

## Adding New Module Tests

To add tests for a new sensor module:

### 1. Create Module Directory
```bash
mkdir tests/new_module/
touch tests/new_module/__init__.py
```

### 2. Create Test File
Create `tests/new_module/test_new_module.py` with test classes:
```python
@pytest.mark.unit
class TestNewModule:
    """Comprehensive NewModule tests with proper mocking."""
    
    def test_validation_valid_config(self, create_config_with_attributes):
        """Test validation with valid configuration"""
        
    def test_initialization_defaults(self, mock_component_config, mock_dependencies):
        """Test initialization with default values"""
        
    def test_readings_success(self, mock_component_config, mock_dependencies):
        """Test successful sensor readings"""
        
    def test_tare_success(self, mock_component_config, mock_dependencies):
        """Test successful tare operation"""
        
    @pytest.mark.integration
    def test_full_workflow(self, create_config_with_attributes, mock_dependencies):
        """Test complete workflow: configure, tare, read"""
```

### 3. Add Module-Specific Fixtures
Add any module-specific fixtures to `conftest.py`

### 4. Update Test Runner
The test runner automatically discovers new modules - no updates needed!

## Continuous Integration

The framework includes GitHub Actions workflows for:
- Automated testing on multiple Python versions
- Coverage reporting
- Linting and code quality checks
- Module-specific test jobs

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Descriptive Names**: Use clear, descriptive test names
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Mock External Dependencies**: Don't rely on real hardware
5. **Test Edge Cases**: Include boundary conditions and error cases
6. **Use Fixtures**: Reuse common setup code
7. **Mark Tests Appropriately**: Use markers for test categorization
8. **Document Complex Tests**: Add docstrings for complex test logic
9. **Async Handling**: Always await async methods in tests
10. **Proper Mocking**: Use appropriate mocks for Viam SDK components

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `src/` is in Python path
2. **Mock Issues**: Check that mocks are properly configured
3. **Async Issues**: Always await async methods in tests
4. **Hardware Tests**: Use `--hardware` flag for hardware-dependent tests
5. **Coverage**: Run with `--coverage` to see coverage reports

### Debug Mode

```bash
# Run with debug output
pytest -v -s --tb=long

# Run single test with debug
pytest tests/loadcell/test_loadcell.py::TestLoadCell::test_validation_valid_config -v -s
```

## Contributing

When adding new tests:
1. Follow the existing naming conventions
2. Add appropriate test markers
3. Include both positive and negative test cases
4. Update this README if adding new features
5. Ensure tests pass in CI environment
6. Use proper async handling for async methods
7. Mock all external dependencies appropriately