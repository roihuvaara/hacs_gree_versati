# Project Status

## Current Task: Options Flow (Polling Interval)

### Problem Statement
Users need to change key settings (first: polling interval) after setup without re-adding the integration.

### Root Cause Analysis
No options flow exists; coordinator interval is fixed.

### TDD Progress

#### Step 1: Write Failing Test 🚧 NEXT
- Add `tests/test_options_flow.py` covering:
  - Opening options flow shows current polling interval
  - Submitting new interval updates `entry.options` and coordinator interval
  - Invalid input is handled (error shown, no change applied)

#### Step 2: Implement Code Fix 🔄 PENDING
- Add `OptionsFlowHandler` in `config_flow.py`
- Add `update_listener` in `__init__.py` to apply `entry.options`
- Persist chosen interval in `entry.options`

#### Step 3: Verify Test Passes 🔄 PENDING
- Run new options flow tests; fix until green

#### Step 4: Fix Consequential Failures 🔄 PENDING
- Run full test suite; adjust mocks/fixtures as needed

### Next Steps
1. Write failing options flow tests
2. Implement options flow + update listener
3. Make tests pass; run full suite
4. Update this status with results

---

## Recently Completed (for history)

### Device Grouping and Naming (Done)
- Entities now inherit from `GreeVersatiEntity` and share `DeviceInfo`
- Naming cleaned: friendly names, no full MAC in labels
- Added `naming.get_entry_name(entry)` helper
- All tests pass (136/136)