# Gree Versati Integration Improvement Plan

This plan is written to be easy to follow. Each item says what to do, how to test it, and when it is done.

## Completed Work (keep for reference)

1) Fix device and entity grouping
- What we did:
  - `climate` and `water_heater` now inherit from `GreeVersatiEntity`.
  - Both share a single `DeviceInfo` (same identifiers), so HA groups them as one device.
  - Tests were added/updated to prove grouping works.
- Status: Done. Full test suite passes.

2) Clean naming and labels (UX)
- What we did:
  - Entry title and `DeviceInfo.name` now use a friendly name (from `CONF_NAME`).
  - Config-flow device selection shows "Name · XXXX" (only last-4 of MAC). No full MAC in labels.
  - Added `naming.get_entry_name(entry)` to centralize name resolution.
  - Tests updated to assert semantics, not exact hardcoded strings.
- Status: Done. Full test suite passes.

3) Test environment and dependencies
- What we did:
  - Aligned HA and pytest plugin versions to avoid josepy/acme issues.
  - Fixed mocks and brittle title assertions.
- Status: Done.

## Next Work (prioritized)

### 1. Mode Control Rework (High Priority)
- Goal: Make mode control correct and intuitive across the device’s 6 real modes: off, cool, heat, hot water only, cool+hot water, heat+hot water.
- Approach:
  - Add a dedicated mode select entity (Select) that exposes the 6 device modes explicitly.
  - Keep existing `climate` and `water_heater` entities; map their state changes into the correct combined device mode in the background.
  - Mapping rules (source of truth):
    - climate=OFF, dhw=OFF -> device=OFF
    - climate=COOL, dhw=OFF -> device=COOL
    - climate=HEAT, dhw=OFF -> device=HEAT
    - climate=OFF, dhw=ON   -> device=HOT_WATER
    - climate=COOL, dhw=ON  -> device=COOL+HW
    - climate=HEAT, dhw=ON  -> device=HEAT+HW
- How to test (TDD):
  1) Add failing tests `tests/test_mode_control.py` covering:
     - Selecting each of the 6 modes via the new Select updates the client’s MODE/POWER (and any DHW flags) correctly and updates coordinator state.
     - Toggling climate hvac_mode + water heater hvac_mode results in the correct combined device mode (per mapping above).
     - climate OFF + dhw ON maps to HOT_WATER; verify entities reflect states consistently (climate may show OFF/idle while device is in HW-only mode).
  2) Implement:
     - New platform `select.py` with `GreeVersatiDeviceModeSelect` exposing the 6 options.
     - Client API `set_device_mode(mode: str)` to set power/mode (+ any supporting flags) atomically, including HOT_WATER only.
     - Update climate/water_heater to call a shared combiner when their mode toggles change.
  3) Make tests pass; run full suite.
  4) Document behavior in README and entity docstrings.

### 2. Add Options Flow (High Priority)
- Goal: Let users change settings after setup (first: polling interval).
- How to test (TDD):
  1) Add failing tests in `tests/test_options_flow.py`:
     - Opening options flow shows current interval.
     - Submitting new interval updates `entry.options` and coordinator interval.
  2) Implement `OptionsFlowHandler` in `config_flow.py`.
  3) Add `update_listener` in `__init__.py` to apply options on change.
  4) Make tests pass; run full suite.

### 3. Entity Enhancements (Medium)
- Goal: Better UX on restart and richer feedback.
- Tasks:
  - Inherit from `RestoreEntity` in `climate.py` and `water_heater.py`.
  - Implement `async_added_to_hass` to restore last state.
  - Add `hvac_action` to climate (uses available status fields).
- Tests:
  - Add/extend tests to verify state restore and `hvac_action` values.

### 4. Diagnostics (Low)
- Goal: Help users troubleshoot.
- Tasks: Add `diagnostics.py` and implement `async_get_config_entry_diagnostics`.
- Tests: Snapshot minimal redacted data.

### 5. Custom Services (Low)
- Goal: Expose advanced calls (e.g., `send_raw_command`).
- Tasks: Add `services.yaml` and service handler.
- Tests: Unit test service handler input/output and errors.

### 6. Test Hardening and CI (Ongoing)
- Replace exact-string checks with semantic assertions.
- Use shared fixtures/factories for entries/coordinators.
- Ensure config-flow tests always set `flow.hass` and stub unique-id where needed.
- Add CI to run lint + tests on PRs.

## How We Work (short TDD guide)
1) Write a failing test that proves the problem or missing feature.
2) Confirm the failure is the exact expected one.
3) Implement the smallest change to pass the test.
4) Fix any consequential failures and refactor.
5) Ensure the full test suite is green.

## Quick commands
- Lint: `ruff check .`
- Tests: `pytest`

## Notes
- Use `naming.get_entry_name(entry)` wherever you need a device name.
- Do not show full MAC addresses in UI labels.