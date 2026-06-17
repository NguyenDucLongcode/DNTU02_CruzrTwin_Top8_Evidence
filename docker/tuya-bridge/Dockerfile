FROM makuuu2903/tuya-2-mqtt:latest

# tinytuya < 1.17.2 does not map region "sg" to openapi-sg.iotbing.com
# entrypoint.py uses: yaml, jinja2, paho.mqtt
RUN pip install --no-cache-dir \
    "tinytuya>=1.17.2" \
    "pyyaml>=6.0" \
    "jinja2>=3.0" \
    "paho-mqtt>=2.0"

# Map Tuya device id -> IoT Agent device_id and publish filtered attrs
COPY entrypoint.py /app/entrypoint.py