import os
import sys
import time
import argparse
import threading
from pathlib import Path

# Thêm đường dẫn gốc dự án
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

from src.robot.cruzr_client import CruzrRobotClient

# Cấu hình UTF-8 cho Windows console
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


# Đoạn văn bản Outro chuẩn (Tập trung 1 câu duy nhất theo yêu cầu)
OUTRO_TEXT_EN = "CruzTwin ASEAN — closing the last meter of smart-city response."

def speak_outro(language: str = "en", emotion: str = "emotion://va/techface_happy"):

    client = CruzrRobotClient()

    try:
        # Di chuyển theo hành trình Outro
        client.move_and_wait(turningAngle=-84.6, turningSpeed=45)
        client.move_and_wait(distance=3.10, speed=0.45)
        client.move_and_wait(turningAngle=86.3, turningSpeed=45)
        client.move_and_wait(distance=1.50, speed=0.45)

        client.speak_and_wait(OUTRO_TEXT_EN, language="en")
        time.sleep(3)
        client.play_action("action://ubtrobot/goodbye")


        print("\n✅ Đã hoàn thành phát thoại Outro: CruzrTwin ASEAN — closing the last meter of smart-city response.")
        return True

    except Exception as e:
        print(f"❌ Lỗi trong quá trình phát giọng nói Outro: {e}")
        return False
    finally:
        if client.is_connected():
            client.disconnect()
            print("🔌 Đã ngắt kết nối với Robot.")


def main():
    parser = argparse.ArgumentParser(description="Script phát thoại Outro của Robot CruzrTwin ASEAN")
    parser.add_argument(
        "--lang",
        choices=["en", "vi", "both"],
        default="en",
        help="Ngôn ngữ phát thoại: en (Tiếng Anh), vi (Tiếng Việt), both (Cả hai). Mặc định: en"
    )
    parser.add_argument(
        "--emotion",
        default="emotion://va/face_amazing",
        help="Mã biểu cảm khuôn mặt của Robot (mặc định: face_amazing)"
    )
    args = parser.parse_args()

    speak_outro(language=args.lang, emotion=args.emotion)


if __name__ == "__main__":
    main()
