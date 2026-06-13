# Known Limitations - Task 5 and Task 6

Here are the limitations of the current implementation:

- **Simulated Data**: The dataset in `data/sensor_data.csv` is generated simulation data. It is not real building telemetry.
- **Privacy and PII**: The dataset contains no Personally Identifiable Information (PII). It has no names, email addresses, phone numbers, face recognition data, or person IDs.
- **Local Logs Only**: Alert events are written to local JSONL logs in the `logs/` folder.
- **Orion Integration**: The Orion Context Broker integration is not active for Task 5 and Task 6. This can be added in future updates.
