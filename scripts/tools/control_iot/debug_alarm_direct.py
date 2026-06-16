# debug_alarm_direct.py
import tinytuya
import os
from dotenv import load_dotenv

load_dotenv()

# Kết nối Tuya Cloud
cloud = tinytuya.Cloud(
    apiRegion="sg",
    apiKey=os.getenv("TUYA_KEY"),
    apiSecret=os.getenv("TUYA_SECRET"),
)

DEVICE_ID = "a359df88938e2a2223xdwx"

# Cách 1: Gửi từng lệnh riêng
print("=== Cách 1: Gửi AlarmSwitch = True ===")
result1 = cloud.sendcommand(DEVICE_ID, {"commands": [{"code": "AlarmSwitch", "value": True}]})
print(f"Kết quả: {result1}")

# Cách 2: Gửi boolean dạng chuỗi
print("\n=== Cách 2: Gửi AlarmSwitch = 'true' ===")
result2 = cloud.sendcommand(DEVICE_ID, {"commands": [{"code": "AlarmSwitch", "value": "true"}]})
print(f"Kết quả: {result2}")

# Cách 3: Gửi đủ 3 tham số
print("\n=== Cách 3: Gửi AlarmType, AlarmPeriod, AlarmSwitch ===")
result3 = cloud.sendcommand(DEVICE_ID, {
    "commands": [
        {"code": "AlarmType", "value": 10},
        {"code": "AlarmPeriod", "value": 10},
        {"code": "AlarmSwitch", "value": True}
    ]
})
print(f"Kết quả: {result3}")

# Kiểm tra trạng thái sau khi gửi
print("\n=== Kiểm tra trạng thái ===")
status = cloud.getstatus(DEVICE_ID)
print("Status:", status)