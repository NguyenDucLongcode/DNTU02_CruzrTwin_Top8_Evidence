# AI and Rule Layer Design

The system uses AI and rules to find problems in the room.

## AI Model Learning

The model learns normal data only. Normal data has label 0. Anomaly data has label 1. The model does not learn label 1. It only uses label 1 for test. This is called normal-only boundary learning. We use an Isolation Forest model to do this.

## Rule Layer

If new data is outside the normal area, the rule layer says warning or critical.

- **Warning**: High temperature, elevated smoke, or elevated CO2.
- **Critical**: Very high temperature, very high smoke, very high CO2, or multiple risk signs at the same time.
