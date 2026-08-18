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
from src.utils.translator_utils import translate_to_vietnamese

# Cấu hình UTF-8 cho Windows console
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Đoạn xin phép bắt đầu (Greeting / Start Text)
START_TEXT_EN = (
    "Ladies and Gentlemen, dear judges and all the audience. The DNTU CruzTwin team would like to begin our presentation now. In many ASEAN public buildings, digital systems can detect danger but they cannot reach the people who need help."
)


def speak_intro(language: str = "en", emotion: str = "emotion://va/techface_happy"):
    client = CruzrRobotClient()


    try:
        # START ACTIONS--------------------
        client.play_emotion("emotion://va/face_default")
        client.move(distance=4.5, speed=0.45)
        time.sleep(1)
        client.play_action("action://ubtrobot/goodbye")
        client.move_and_wait(turningAngle=-84, turningSpeed=45)
        client.play_emotion("emotion://va/face_happy")
        # client.move_and_wait(distance=0.5, speed=0.45)

        client.speak(text=START_TEXT_EN, language="en")

        print("\n✅ Đã hoàn thành bài giới thiệu CruzrTwin ASEAN với tay di chuyển liên tục suốt bài nói!")
        return True

    except Exception as e:
        print(f"❌ Lỗi trong quá trình phát giọng nói: {e}")
        return False
    finally:
        if client.is_connected():
            client.disconnect()
            print("🔌 Đã ngắt kết nối với Robot.")


def main():
    parser = argparse.ArgumentParser(description="Script giới thiệu Robot CruzrTwin ASEAN kèm tay di chuyển liên tục")
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

    speak_intro(language=args.lang, emotion=args.emotion)


if __name__ == "__main__":
    main()
