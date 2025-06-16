# Gree Versati Integration Improvement Plan

This document outlines a plan to enhance the Gree Versati integration by incorporating best practices from other mature, local-first Home Assistant integrations.

## 1. Fix Device & Entity Grouping (Highest Priority)
**Goal:** Ensure `climate` and `water_heater` entities are correctly grouped under a single device in Home Assistant, reflecting that they are part of the same physical unit.

**Detailed TDD Steps:**

1.  **Write a Failing and PREDICTABLE Test:**
    -   **Goal:** Create a new, high-level integration test that proves the device grouping is currently broken in a predictable way.
    -   **Action:** Create a new test file, `tests/test_device_registry.py`.
    -   **Test Implementation:**
        -   The test will perform a full setup of the integration by calling `async_setup_entry` from the root `__init__.py`. This will load all platforms associated with the integration.
        -   It will then get the `device_registry` from `hass`.
        -   The key assertion will be: `assert len(dr.async_entries_for_config_entry(config_entry.entry_id)) == 1`.
    -   **Confirming the Test's Correctness (Crucial Step):**
        -   Before any code changes, run this new test.
        -   It **must fail with a specific, predicted `AssertionError`**: `assert 2 == 1`.
        -   This confirms two things:
            1.  The problem exists as we understand it (the `climate` and `water_heater` entities are each creating their own device).
            2.  Our test is correctly capturing this specific failure mode.
        -   **If the test fails differently (e.g., `assert 3 == 1` or with some other error), we must STOP.** A different failure means our initial analysis is wrong, and we need to re-investigate before proceeding.

2.  **Implement the Code Changes:**
    -   **Goal:** Refactor the entity classes to make the test pass.
    -   **Action (Refactor `climate.py`):**
        -   Import `GreeVersatiEntity`.
        -   Change the class to inherit from `GreeVersatiEntity` instead of `CoordinatorEntity`.
        -   Update the constructor signature to accept only the `coordinator`.
        -   Update the `async_setup_entry` call to match the new constructor.
        -   Adjust the `unique_id` to be derived from the parent (`f"{super().unique_id}_climate"`).
    -   **Action (Refactor `water_heater.py`):**
        -   Apply the exact same refactoring logic as in `climate.py`.

3.  **Verify the Primary Fix:**
    -   **Goal:** Ensure the new test now passes.
    -   **Action:** Run the new test from `tests/test_device_registry.py` again. It should now pass, proving that the entities are correctly grouped under a single device.

4.  **Fix Consequential Test Failures:**
    -   **Goal:** The refactoring in step 2 will have broken the old unit tests for climate and water heater. We must now fix them.
    -   **Action:** Run the full `pytest` suite. It will show failures in `tests/test_climate_entity.py` and `tests/test_water_heater.py` due to the changed constructor. Update the test setup in these files to instantiate the entities correctly with only the `coordinator`.

5.  **Final Verification:**
    -   **Goal:** Confirm that the entire integration is healthy after all changes.
    -   **Action:** Run the full `pytest` suite one last time. All tests—the new device registry test and all the updated unit tests—must now pass.

## 2. Implement a Robust Options Flow (High Priority)
**Goal:** Allow users to modify settings after initial setup without re-adding the integration. This is a critical feature for usability and the foundation for other improvements.
**Tasks:**
- Create an `OptionsFlowHandler` in `config_flow.py`.
- Define a schema for user-configurable options, with the **polling interval** as the most important first option.
- Implement an `update_listener` in `__init__.py` to dynamically apply changes made in the options flow.

## 3. Enhance Climate and Water Heater Entities (Medium Priority)
**Goal:** Provide a better user experience by restoring state on restart and giving more detailed status feedback.
**Tasks:**
- Inherit from `RestoreEntity` in `climate.py` and `water_heater.py`.
- Implement `async_added_to_hass` to restore the last known state from Home Assistant's state restoration mechanism.
- Add the `hvac_action` property to the `GreeVersatiClimate` entity to show if the unit is actively heating, cooling, or idle, based on available sensor data like `tank_heater_status`.

## 4. Verify Brand Logo Display (Low Priority)
**Goal:** Ensure the correct "Gree" brand and logo are always shown for the device.
**Tasks:**
- Confirm that setting `manufacturer="Gree"` in the `device_info` property correctly and reliably displays the Gree logo in Home Assistant. No code changes are anticipated as this appears to be correctly implemented already.

## 5. Add Support for Custom Services (Low Priority)
**Goal:** Expose advanced device-specific features to users through Home Assistant services.
**Tasks:**
- Create a `services.yaml` file to define the custom services.
- A prime candidate is a `send_raw_command` service, similar to the one in the Midea integration. This would allow advanced users to call functions from the underlying `greeclimate_versati_fork` library directly for features not exposed in the UI.

## 6. Create a Diagnostics Platform (Low Priority)
**Goal:** Help users and developers troubleshoot issues by providing key diagnostic information.
**Tasks:**
- Create a `diagnostics.py` file.
- Implement `async_get_config_entry_diagnostics` to gather relevant data like connection status, coordinator state, and redacted device info.

## 7. Re-evaluate Data Update Strategy (Long-Term Goal)
**Goal:** Improve efficiency and responsiveness by potentially moving away from a fixed-interval polling model.
**Tasks:**
- Investigate if the underlying Gree protocol supports a push-based or subscription model.
- If so, a future architectural change could be to remove the `DataUpdateCoordinator` and have the device manage its own connection, pushing state updates to Home Assistant directly. For now, making the polling interval configurable (Item #2) is the immediate goal.