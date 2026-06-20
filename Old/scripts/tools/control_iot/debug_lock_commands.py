import sys
from pathlib import Path

# Thêm đường dẫn
ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT_DIR))

from src.tuya import TuyaCloudClient

DEVICE_ID = "a3400b0f1o3q5kji"
client = TuyaCloudClient(DEVICE_ID)

# Kiểm tra trạng thái hiện tại
print("=== TRẠNG THÁI HIỆN TẠI ===")
status = client.get_status()
print(f"manual_lock: {status.get('manual_lock')}")
print(f"lock_motor_state: {status.get('lock_motor_state')}")
print(f"alarm_lock: {status.get('alarm_lock')}")

print("\n=== TEST CÁC CÁCH KHÓA/MỞ ===")

# Cách 1: manual_lock = False (mở)
print("\n1. Gửi manual_lock = False (mở khóa)")
result1 = client.send_command("manual_lock", False)
print(f"Kết quả: {result1}")

# Cách 2: manual_lock = True (khóa)
print("\n2. Gửi manual_lock = True (khóa)")
result2 = client.send_command("manual_lock", True)
print(f"Kết quả: {result2}")

# Kiểm tra lại trạng thái sau khi test
print("\n=== TRẠNG THÁI SAU KHI TEST ===")
status = client.get_status()
print(f"manual_lock: {status.get('manual_lock')}")

# Cách 3: Thử với lock_motor_state
print("\n3. Thử với lock_motor_state = True")
result3 = client.send_command("lock_motor_state", True)
print(f"Kết quả: {result3}")