import requests
import pathlib

p = {
  "data": [
    {
      "id": "Device:test-1",
      "temperature": {"type":"Number","value": 24.2},
      "humidity": {"type":"Number","value": 42},
      "co2": {"type":"Number","value": 600},
      "smoke_status": {"type":"Text","value": "CLEAR"}
    }
  ],
  "subscriptionId": "test",
  "timestamp": "2026-05-31T00:00:00Z"
}

resp = requests.post('http://127.0.0.1:5000/webhook/notify', json=p, timeout=5)
print('status', resp.status_code)
print(resp.text)

log = pathlib.Path('logs/orion_state.jsonl')
if log.exists():
    lines = log.read_text(encoding='utf-8').strip().splitlines()
    print('\nlog lines:', len(lines))
    if lines:
        print('LAST:', lines[-1])
else:
    print('log file not found')
