# Gree Versati Integration for Home Assistant

> **Note: Early Development Stage**
> This integration is in its early development stages. It's functional but may contain bugs or limitations. Use at your own risk and please report any issues you encounter to help improve the integration.

[![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This integration enables connection with Gree Versati Air to Water Heat Pumps in Home Assistant.

## Functionality

- Climate entity for heating and cooling control
- Water heater entity for domestic hot water control
- Device mode select exposing all six device modes
- Network auto-discovery of compatible devices
- Fully self-contained: the local UDP protocol is implemented inside the
  integration (MIT licensed), no external Python dependencies

## Supported Entities

| Entity Type | Capabilities |
|------------|----------|
| Climate | Water-out setpoint (heating 20–60 °C, cooling 7–25 °C), Mode selection (Heat/Cool/Off) |
| Water Heater | Tank setpoint (40–80 °C), Operation (Off/Heat pump/Performance boost) |
| Select | Direct device mode: off, heat, cool, hot water, heat+hot water, cool+hot water |
| Sensors | Hot water, water outlet/inlet and heat-exchanger temperatures (with long-term statistics for history graphs) |
| Binary sensors | Tank heater, auxiliary heaters 1/2, defrosting and frost protection running states (diagnostic) |

Mode changes follow the device's requirement of switching power off
before changing mode (the official app does the same), so a brief
off/on cycle during mode changes is expected.

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

### Temperature limits

The device itself accepts wide setpoint ranges (heating 20–60 °C, cooling
7–25 °C, hot water 40–80 °C). To guard against accidental extreme setpoints,
you can tighten these ranges: open the integration's **Configure** dialog
(Settings → Devices & Services → Gree Versati → Configure) and set your own
minimum/maximum for heating, cooling, and hot water. The climate and water
heater entities then refuse setpoints outside your configured range. Limits
can only be tightened — values outside the device's own range are ignored.

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

The local protocol implementation in `custom_components/gree_versati/protocol/`
is a clean-room MIT implementation written from publicly documented protocol
facts and packet captures. Earlier versions depended on a fork of the
[GreeClimate](https://github.com/cmroche/greeclimate) project.
