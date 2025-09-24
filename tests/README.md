# Testing Framework for Rocket Sensors

This directory contains a unified, modular testing framework for the rocket-sensors project. The framework provides both comprehensive and simplified testing approaches, designed to be easily extensible for testing all sensor modules (LoadCell, MPU, BMP) and future modules.

## Framework Structure

```
tests/
├── conftest.py                  # Shared fixtures and mocks
├── pytest.ini                  # Pytest configuration
├── README.md                   # This file
├── loadcell/                   # LoadCell module tests
│   ├── __init__.py
│   ├── test_loadcell.py         # Comprehensive tests
│   └── test_loadcell_simple.py  # Simplified tests
├── mpu/                        # MPU module tests
│   ├── __init__.py
│   ├── test_mpu.py              # Comprehensive tests
│   └── test_mpu_simple.py       # Simplified tests (to be created)
└── bmp/                        # BMP module tests
    ├── __init__.py
    ├── test_bmp.py              # Comprehensive tests
    └── test_bmp_simple.py       # Simplified tests (to be created)
```

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

### Using the Unified Test Runner

```bash
# Activate virtual environment
source venv/bin/activate

# Run comprehensive tests (default)
python test_runner.py --module loadcell
python test_runner.py --module loadcell --type unit
python test_runner.py --module loadcell --coverage

# Run simplified tests
python test_runner.py --module loadcell --simple
python test_runner.py --module loadcell --simple --type unit
python test_runner.py --module loadcell --simple --coverage

# Run all tests
python test_runner.py                    # All comprehensive tests
python test_runner.py --simple          # All simplified tests
python test_runner.py --type unit       # All unit tests
python test_runner.py --hardware        # Include hardware tests
```

### Using pytest directly

```bash
# Run all tests
pytest

# Run specific module tests
pytest tests/loadcell/
pytest tests/mpu/
pytest tests/bmp/

# Run specific test files
pytest tests/loadcell/test_loadcell.py              # Comprehensive tests
pytest tests/loadcell/test_loadcell_simple.py       # Simplified tests

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test types
pytest -m unit
pytest -m integration
pytest -m "not hardware"

# Run specific test function
pytest tests/loadcell/test_loadcell.py::TestLoadCellValidation::test_validate_config_valid_defaults
```

## Testing Approaches

### Comprehensive Tests (`test_*.py`)
- **Multiple test classes** per module (Validation, Initialization, Readings, etc.)
- **Detailed mocking** with extensive fixtures
- **Complete coverage** of all functionality
- **Best for**: CI/CD, thorough testing, debugging complex issues

### Simplified Tests (`test_*_simple.py`)
- **Single test class** per module
- **Essential fixtures** only
- **Focused testing** on core functionality
- **Best for**: Development, quick testing, learning the codebase

### When to Use Which

**Use Comprehensive Tests when:**
- Running CI/CD pipelines
- Need thorough validation
- Debugging complex issues
- Preparing for production

**Use Simplified Tests when:**
- Developing new features
- Quick validation during development
- Learning how the code works
- Fast feedback loops

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
- Sensor readings in metric/imperial units
- Tare functionality and offset management
- Command handling
- Error handling

### BMP Module
- Configuration validation
- Initialization and reconfiguration
- Sensor readings in metric/imperial units
- Tare functionality and offset management
- Command handling
- Error handling
- Edge cases and boundary conditions

## Mocking Strategy

The framework uses comprehensive mocking to test without hardware:

### Hardware Mocks
- **GPIO**: Mock RPi.GPIO for LoadCell testing
- **HX711**: Mock HX711 sensor for LoadCell testing
- **MPU6050**: Mock MPU6050 sensor for MPU testing
- **BMP085**: Mock BMP085 sensor for BMP testing
- **I2C**: Mock I2C bus for sensor communication

### Viam SDK Mocks
- **ComponentConfig**: Mock configuration objects
- **Dependencies**: Mock resource dependencies
- **Loggers**: Mock logging functionality

## Fixtures

### Shared Fixtures (conftest.py)
- `mock_component_config`: Mock ComponentConfig for testing
- `mock_dependencies`: Mock dependencies for testing
- `mock_logger`: Mock logger for testing
- `mock_gpio`: Mock GPIO module
- `mock_hx711`: Mock HX711 sensor
- `mock_mpu_sensor`: Mock MPU6050 sensor
- `mock_bmp_sensor`: Mock BMP085 sensor
- `mock_i2c`: Mock I2C bus
- `mock_board`: Mock board module
- `create_config_with_attributes`: Factory for creating configs

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

### 2. Create Comprehensive Tests
Create `tests/new_module/test_new_module.py` with test classes:
```python
@pytest.mark.unit
class TestNewModuleValidation:
    """Test configuration validation"""

@pytest.mark.unit  
class TestNewModuleInitialization:
    """Test initialization and configuration"""

@pytest.mark.unit
class TestNewModuleReadings:
    """Test sensor readings"""

@pytest.mark.unit
class TestNewModuleTare:
    """Test tare functionality (if applicable)"""

@pytest.mark.unit
class TestNewModuleCommands:
    """Test command handling"""

@pytest.mark.integration
class TestNewModuleIntegration:
    """Test complete workflows"""
```

### 3. Create Simplified Tests
Create `tests/new_module/test_new_module_simple.py`:
```python
@pytest.mark.unit
class TestNewModule:
    """All NewModule tests in one class"""
    
    def test_validation_valid_config(self):
        """Test validation with valid configuration"""
        
    def test_initialization_defaults(self):
        """Test initialization with default values"""
        
    def test_readings_success(self):
        """Test successful sensor readings"""
        
    def test_tare_success(self):
        """Test successful tare operation"""
        
    # ... other test methods
```

### 4. Add Module-Specific Fixtures
Add any module-specific fixtures to `conftest.py`

### 5. Update Test Runner
The unified test runner automatically discovers new modules - no updates needed!

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

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `src/` is in Python path
2. **Mock Issues**: Check that mocks are properly configured
3. **Hardware Tests**: Use `--hardware` flag for hardware-dependent tests
4. **Coverage**: Run with `--coverage` to see coverage reports

### Debug Mode

```bash
# Run with debug output
pytest -v -s --tb=long

# Run single test with debug
pytest tests/loadcell/test_loadcell.py::TestLoadCellValidation::test_validate_config_valid_defaults -v -s
```

## Contributing

When adding new tests:
1. Follow the existing naming conventions
2. Add appropriate test markers
3. Include both positive and negative test cases
4. Update this README if adding new features
5. Ensure tests pass in CI environment
