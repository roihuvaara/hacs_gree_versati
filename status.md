# Project Status

## Current Task: Mode Control Rework (Device 6-mode logic)

### Problem Statement
Device supports 6 real modes: off, cool, heat, hot water only, cool+hot water, heat+hot water. Current behavior is not logically correct across entities.

### Root Cause Analysis
Mode is a combined device concept. Independent climate/DHW toggles must be reconciled into a single device mode; today there’s no authoritative combiner and no direct way for users to pick the 6 modes.

### TDD Progress

#### Step 1: Write Failing Tests ✅ COMPLETED
- Added `tests/test_mode_control.py` with initial tests:
  - `test_client_has_set_device_mode_api` (fails predictably: method missing)
  - `test_hw_only_mapping_sets_flags_correctly` (placeholder expecting exception until implemented)
- Result: 1 failed, 1 passed. Failure matches expectation (missing `set_device_mode`).
- Awaiting approval to accept failing tests as the baseline for implementation.

#### Step 2: Implement Code ✅ COMPLETED
- Implemented client API `set_device_mode(mode: str)` to atomically set power/mode/DHW flag, including HW-only. Added unit tests.
- Next: Add `select.py` with `GreeVersatiDeviceModeSelect` exposing 6 modes.

#### Step 3: Write Failing Select Tests ✅ COMPLETED
- Added `tests/test_device_mode_select.py` covering:
  - Initialization/options expose 6 modes in stable order
  - Selecting an option calls `client.set_device_mode` and refreshes
  - Platform setup adds the Select entity
- Current result: All three tests fail predictably with `ModuleNotFoundError: custom_components.gree_versati.select` (implementation pending).

#### Step 4: Implement Select Entity ✅ COMPLETED
- Added `select.py` defining `GreeVersatiDeviceModeSelect` and `async_setup_entry`.
- Options expose 6 modes; selection calls client `set_device_mode` and refreshes.

#### Step 5: Wire Climate/DHW to Combiner ✅ COMPLETED
- Updated `climate.async_set_hvac_mode` to compute combined mode using `fast_heat_water` and call `set_device_mode`.
- Updated `water_heater.async_set_operation_mode` to compute combined mode using `power`/`mode` and call `set_device_mode`.

#### Step 6: Verify Tests Pass ✅ COMPLETED
- Added wiring tests in `tests/test_mode_wiring.py`; all pass.
- Full suite green: 153/153.

#### Step 3: Verify Tests Pass 🔄 PENDING
- Run new mode control tests; iterate until green.

#### Step 4: Fix Consequential Failures 🔄 PENDING
- Run full test suite; adjust mocks/fixtures if needed.

### Next Steps
1. Write failing mode control tests
2. Implement Select entity and client `set_device_mode`
3. Integrate combiner with climate/DHW
4. Make tests pass; run full suite

---

## Recently Completed (for history)

### Device Grouping and Naming (Done)
- Entities now inherit from `GreeVersatiEntity` and share `DeviceInfo`
- Naming cleaned: friendly names, no full MAC in labels
- Added `naming.get_entry_name(entry)` helper
- All tests pass (136/136)