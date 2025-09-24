# GitHub Actions Workflows

This directory contains GitHub Actions workflows for automated testing, linting, and quality assurance.

## Workflows

### 1. `test.yml` - Comprehensive Test Suite

**Triggers:**
- Push to `main` or `add-unit-testing` branches
- Pull requests to `main` or `add-unit-testing` branches

**Jobs:**

#### `test-all`
- **Purpose**: Main test job that runs all tests together for efficiency
- **Python Versions**: 3.11, 3.12
- **Features**:
  - Runs all unit tests with coverage
  - Runs all integration tests
  - Includes linting
  - Uploads coverage to Codecov
  - Uses pip caching for faster builds

#### `test-modules`
- **Purpose**: Individual module tests for detailed reporting
- **Modules**: loadcell, mpu, bmp
- **Features**:
  - Runs tests for each module separately
  - Generates individual coverage reports
  - Uploads module-specific coverage to Codecov

#### `lint`
- **Purpose**: Comprehensive code quality checks
- **Python Versions**: 3.11, 3.12
- **Tools**:
  - **flake8**: Syntax and style checking
  - **black**: Code formatting validation
  - **isort**: Import sorting validation
  - **mypy**: Type checking
  - **bandit**: Security linting
  - **safety**: Dependency vulnerability checking

#### `test-hardware`
- **Purpose**: Hardware-specific tests
- **Triggers**: Only on pull requests
- **Features**:
  - Runs hardware tests when available
  - Continues on error (hardware may not be available in CI)

#### `test-performance`
- **Purpose**: Performance and load testing
- **Triggers**: Only on pull requests
- **Features**:
  - Runs performance benchmarks
  - Continues on error (optional)

### 2. `quick-test.yml` - Fast Development Testing

**Triggers:**
- Push to `add-unit-testing` branch (only when test files change)
- Pull requests to `add-unit-testing` branch (only when test files change)

**Features:**
- Quick unit test execution
- Basic linting
- Fast feedback for development

## Usage

### Running Tests Locally

```bash
# Run all unit tests
python test_runner.py --module all --type unit --coverage --verbose

# Run specific module tests
python test_runner.py --module loadcell --type unit --coverage --verbose

# Run integration tests
python test_runner.py --module all --type integration --verbose

# Run linting
python test_runner.py --lint --verbose

# Run hardware tests
python test_runner.py --hardware --verbose
```

### Test Runner Options

The `test_runner.py` script supports various options:

- `--module {loadcell,mpu,bmp,all}`: Specify which module to test
- `--type {unit,integration,hardware}`: Specify test type
- `--coverage`: Generate coverage reports
- `--verbose`: Verbose output
- `--lint`: Run linting checks
- `--benchmark`: Run performance benchmarks

### Coverage Reports

Coverage reports are automatically generated and uploaded to Codecov:
- **Main coverage**: Combined coverage from all modules
- **Module coverage**: Individual coverage for each module (loadcell, mpu, bmp)

### Branch Protection

To enable branch protection with these workflows:

1. Go to your repository settings
2. Navigate to "Branches"
3. Add a branch protection rule for `main`
4. Enable "Require status checks to pass before merging"
5. Select the following required status checks:
   - `test-all` (Python 3.11)
   - `test-all` (Python 3.12)
   - `lint` (Python 3.11)
   - `lint` (Python 3.12)

### Customization

#### Adding New Test Types

To add new test types (e.g., `performance`):

1. Add the test type to `test_runner.py`
2. Update the workflow to include the new test type
3. Add appropriate markers to your test files

#### Adding New Modules

To add new sensor modules:

1. Create test files in `tests/{module_name}/`
2. Add the module to the matrix in `test-modules` job
3. Update `test_runner.py` if needed

#### Modifying Linting Rules

To customize linting:

1. Create configuration files (e.g., `.flake8`, `pyproject.toml`)
2. Update the linting commands in the workflow
3. Add new linting tools as needed

## Troubleshooting

### Common Issues

1. **Tests failing due to missing dependencies**: Ensure all dependencies are in `requirements.txt`
2. **Coverage not uploading**: Check that `coverage.xml` is being generated
3. **Hardware tests failing**: This is expected in CI - hardware tests are optional
4. **Linting failures**: Fix code style issues or update linting configuration

### Debugging

To debug workflow issues:

1. Check the Actions tab in your GitHub repository
2. Click on the failed workflow run
3. Expand the failed step to see detailed logs
4. Use the "Re-run jobs" button to retry after fixes

### Local Testing

Before pushing, run tests locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
python test_runner.py --module all --type unit --coverage --verbose

# Check linting
python test_runner.py --lint --verbose
```

## Best Practices

1. **Keep tests fast**: Unit tests should run quickly
2. **Use appropriate test types**: Unit tests for logic, integration tests for workflows
3. **Maintain good coverage**: Aim for >80% code coverage
4. **Fix linting issues**: Keep code clean and consistent
5. **Test locally first**: Run tests before pushing
6. **Use meaningful test names**: Make test failures easy to understand
7. **Mock external dependencies**: Don't rely on external services in tests
