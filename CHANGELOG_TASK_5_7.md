# Changelog - Tasks 5-7

All notable changes to the AI detection, AlertEvent, and RobotAction closed-loop implementation are documented here.

## [1.0.0] - 2026-06-07

### Added
- Created global in-memory `offline_cache` registry inside the FIWARE Orion client `src/fiware/client.py`. If Orion is down/offline, all state transitions degrade gracefully using the local registry fallback instead of crashing with `CRITICAL_ORCHESTRATION_ERROR`.
- Added ASCII-safe console print fallbacks in `scripts/tools/show_demo_trace.py` to support printing Vietnamese accents (e.g. voice evac messages) on standard CP1252 Windows consoles without raising `UnicodeEncodeError`.
- Added project root path configuration to all scripts inside `scripts/tools/` to prevent `ModuleNotFoundError: No module named 'src'` when executed from the project root directory.
- Created `docs/` folder containing implementation blueprints, schemas, runbooks, and known limitations.

### Fixed
- Fixed **Rule Engine Classification Bug** in `src/ai/feature_extractor.py`: Updated warning telemetry thresholds mapped to `multi_signal_risk_count` calculation so that warning-level signals (such as CO2 around 900-1000 ppm or energy around 500-600W) do not accumulate to trigger critical actions.
- Fixed mock behavior for `mock_al_get` in `tests/integration/test_closed_loop_task_5_7.py`: Configured `mock_al_get.side_effect` to return `None` on the first call (creation check) and a mock entity dictionary on subsequent calls (status updates check). This fixed the integration test.
- Fixed `scripts/tools/assert_task_5_7_acceptance.py` verification logic: Grouped AI records by scenario ID and asserted on the *final* record of each scenario to correctly support multi-step replayed telemetry sequences transitioning from warning to critical.

### Changed
- Reduced Orion and Local Bridge network connection timeouts to 1 second in `.env` to speed up offline demo execution runs.
