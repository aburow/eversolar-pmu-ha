# Contributing to Eversolar PMU Home Assistant Integration

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Issues

### Reporting Bugs

Before creating a bug report, please check the issue list to see if the problem has already been reported.

When creating a bug report, please include:
- Home Assistant version
- Python version
- Integration version
- Steps to reproduce the issue
- Expected behavior vs. actual behavior
- Relevant logs (enable debug logging if applicable)
- Inverter model and firmware version (if known)

**Enable debug logging:**
```yaml
logger:
  logs:
    custom_components.eversolar_pmu: debug
```

### Feature Requests

When suggesting a feature or improvement, please:
- Describe the feature and its use case
- Explain why it would be useful
- Provide examples of how it would be used

## Development

### Setup Development Environment

1. Clone the repository:
   ```bash
   git clone http://192.168.0.178:3000/aburow/eversolar-pmu-ha.git
   cd eversolar-pmu-ha
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install Home Assistant in development mode (optional):
   ```bash
   pip install homeassistant
   ```

### Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep lines under 100 characters
- Use type hints where possible

### Making Changes

1. Create a new branch for your changes:
   ```bash
   git checkout -b feature/my-feature
   ```

2. Make your changes
3. Test thoroughly
4. Commit with clear, descriptive messages:
   ```bash
   git commit -m "Add feature: Description of what was added"
   ```

5. Push to your fork and create a Pull Request

### Pull Request Guidelines

- Use a clear, descriptive title
- Describe the changes and why they're needed
- Reference related issues (e.g., "Fixes #123")
- Include any breaking changes
- Ensure all tests pass

## Testing

### Protocol Tests

Run protocol validation tests:
```bash
python3 test_protocol.py
```

All tests should pass before submitting a PR.

### Manual Testing

When adding or modifying sensors:
1. Configure the integration with your inverter
2. Verify sensor entities are created
3. Check that values update regularly
4. Compare values with original script output
5. Verify error handling works correctly

## Documentation

When adding new features:
- Update README.md with new functionality
- Add examples if applicable
- Update QUICK_START.md if relevant
- Add UI strings to strings.json

## File Structure

```
custom_components/eversolar_pmu/
├── __init__.py                # Integration setup
├── config_flow.py             # UI configuration
├── const.py                   # Constants
├── coordinator.py             # Data polling
├── eversolar_protocol.py      # Protocol implementation
├── sensor.py                  # Sensor platform
├── manifest.json              # Metadata
├── strings.json               # UI strings
├── services.yaml              # Service definitions
├── translations/
│   └── en.json                # English translations
└── services.yaml              # Service documentation
```

## Adding a New Sensor

1. **Add constant to `const.py`:**
   ```python
   SENSOR_MY_VALUE = "my_value"
   SENSOR_DATA_KEYS = {
       SENSOR_MY_VALUE: "my_value_json_key",
   }
   ```

2. **Add entity to `sensor.py`:**
   ```python
   EversolarSensor(
       coordinator,
       SENSOR_MY_VALUE,
       "My Value Name",
       "my_value_json_key",
       SensorDeviceClass.POWER,
       "unit",
       SensorStateClass.MEASUREMENT,
   ),
   ```

3. **Test the integration:**
   - Restart Home Assistant
   - Verify sensor is created
   - Check that values update correctly
   - Verify it appears in the device

## Commit Message Guidelines

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Reference issues and pull requests when relevant
- Example: `Add temperature sensor support (Fixes #42)`

## Code Review

All pull requests will be reviewed for:
- Code quality and style
- Adherence to Home Assistant best practices
- Test coverage
- Documentation completeness
- No breaking changes

## Questions?

- Check the main project documentation: http://192.168.0.178:3000/aburow/eversolar-pmu-ha
- Review Home Assistant integration docs: https://developers.home-assistant.io/
- Open an issue to discuss

Thank you for contributing! 🎉
