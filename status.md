# Project Status

## Current Task: Fix Device Grouping Issue

### Problem Statement
Climate and water_heater entities are appearing as separate devices in Home Assistant instead of being grouped under a single Gree Versati device.

### Root Cause Analysis
Both `GreeVersatiClimate` and `GreeVersatiWaterHeater` entities inherit from `CoordinatorEntity` directly instead of `GreeVersatiEntity`, which means they don't have the shared `device_info` property needed for device grouping.

### TDD Progress

#### Step 1: Write Failing Test ✅ COMPLETED
- **Test Created**: `tests/test_device_registry.py::test_device_info_comparison`
- **Test Status**: ✅ **ACCEPTED**
- **Failure Mode**: Test fails predictably with `assert 0 == 1`
- **What it tests**:
  - Creates both climate and water_heater entities as they currently exist
  - Checks their `device_info` properties (currently both return `None`)
  - Counts unique device identifier sets (currently 0)
  - Asserts that there should be exactly 1 unique device identifier set
- **Expected behavior after fix**: Both entities will inherit from `GreeVersatiEntity` and provide the same device identifiers, making device_count = 1

#### Step 2: Implement Code Fix 🔄 PENDING
- **Status**: Waiting for permission to implement
- **Required Changes**:
  1. Update `GreeVersatiClimate` to inherit from `GreeVersatiEntity` instead of `CoordinatorEntity`
  2. Update `GreeVersatiWaterHeater` to inherit from `GreeVersatiEntity` instead of `CoordinatorEntity`
  3. Adjust constructors to work with new inheritance

#### Step 3: Verify Test Passes 🔄 PENDING
- **Status**: Not started - waiting for code implementation

#### Step 4: Fix Consequential Failures 🔄 PENDING
- **Status**: Not started - will run full test suite after implementation

### Next Steps
1. Get permission to implement the code changes
2. Make entities inherit from `GreeVersatiEntity`
3. Run the test to confirm it passes
4. Run full test suite to catch any regressions
5. Update this status document with results