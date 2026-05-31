# Scripts Layout

Use the grouped folders below as the canonical entrypoints for future maintenance. The legacy top-level files are kept for compatibility.

## Setup

- `scripts/setup/setup_subscription.py`
- `scripts/setup/reset_subscriptions.py`

## Scenarios

- `scripts/scenarios/run_normal.py`
- `scripts/scenarios/run_warning.py`
- `scripts/scenarios/run_critical.py`

## Replay

- `scripts/replay/replay_tests.py`

## Tools

- `scripts/tools/send_test_notification.py`
- `scripts/tools/show_demo_trace.py`

## Legacy Compatibility

Top-level scripts still exist in `scripts/` so existing commands keep working. Prefer the grouped paths above for new work.
