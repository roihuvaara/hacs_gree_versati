# Gree Versati Integration for Home Assistant

> **Note: Early Development Stage**
> This integration is in its early development stages. It's functional but may contain bugs or limitations. Use at your own risk and please report any issues you encounter to help improve the integration.

[![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This integration enables connection with Gree Versati Air to Water Heat Pumps in Home Assistant.

## Functionality

- Climate entity for heating and cooling control
- Water heater entity for domestic hot water control
- Network auto-discovery of compatible devices
- Support for multiple operation modes

## Supported Entities

| Entity Type | Capabilities |
|------------|----------|
| Climate | Temperature control, Mode selection (Heat/Cool/Off) |
| Water Heater | Temperature control, Mode selection (Normal/Performance) |

## Installation

### HACS Installation

1. Have [HACS](https://hacs.xyz) installed
2. Add as a custom repository:
   - Go to HACS → Integrations → "..." menu → Custom repositories
   - URL: `https://github.com/roihuvaara/hacs_gree_versati`
   - Category: Integration
3. Install the integration
4. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/gree_versati` folder to your `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to Settings → Devices & Services
2. Click "+ Add Integration" and search for "Gree Versati"
3. The integration will scan your network for devices
4. Select your device to complete setup

## Troubleshooting

Enable debug logging by adding to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.gree_versati: debug
```

### Common Issues

- **Device Not Found**: Check network connectivity and ensure the device is online
- **Connection Issues**: Verify UDP port 7000 is not blocked by your firewall
- **Binding Failed**: May indicate protocol incompatibility with your device model

## Development

### Development Environment

This project uses DevContainers for development:

1. Clone this repository
2. Open in VS Code with the Remote Containers extension
3. Run tests with `pytest tests/`

### Code Quality

Run linting checks before submitting changes:

```bash
# Run checks
ruff check .

# Apply automatic fixes
ruff check . --fix
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

This integration builds upon work from the [GreeClimate](https://github.com/cmroche/greeclimate) project and adapts it specifically for Gree Versati Air to Water Heat Pumps.
