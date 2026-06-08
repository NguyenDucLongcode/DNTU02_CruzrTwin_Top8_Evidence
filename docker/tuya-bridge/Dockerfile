FROM makuuu2903/tuya-2-mqtt:latest

# tinytuya < 1.17.2 does not map region "sg" to openapi-sg.iotbing.com
RUN pip install --no-cache-dir "tinytuya>=1.17.2"

# Map Tuya device id -> IoT Agent device_id and publish filtered attrs
COPY entrypoint.py /app/entrypoint.py