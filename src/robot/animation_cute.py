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

# def play_gestures_continuously(client, duration_sec: float, actions: list, stop_event: threading.Event):
#     """
#     Phát cử chỉ tay liên tục lặp lại trong suốt thời gian Robot đang phát thoại
#     """
#     end_time = time.time() + duration_sec
#     idx = 0
#     while time.time() < end_time and not stop_event.is_set():
#         act = actions[idx % len(actions)]
#         try:
#             client.play_action(act)
#         except Exception:
#             pass
#         idx += 1
#         # Chờ 3.2 giây rồi chuyển sang động tác tay tiếp theo để tay di chuyển liên tục
#         stop_event.wait(3.2)


# def speak_with_continuous_gestures(client, text: str, language: str, actions: list):
#     """
#     Phát giọng nói TTS trước, phát cử chỉ tay song song, rồi chờ speech xong.
#     """
#     import queue as _queue

#     print(f"📢 Robot phát giọng nói: \"{text[:50]}...\"")
#     client.speak(text, language=language)
#     time.sleep(0.3)  # Buffer nhỏ để robot bắt đầu TTS trước khi nhận lệnh cử chỉ


def speak_intro(language: str = "en", emotion: str = "emotion://va/techface_happy"):
    # """
    # Kết nối và điều khiển Robot Cruzr phát câu giới thiệu ASEAN kèm cử chỉ tay di chuyển liên tục
    # """
    # print("\n" + "=" * 60)
    # print("🤖 CRUZR ROBOT INTRO SPEECH SCRIPT (CONTINUOUS HAND GESTURES)")
    # print("=" * 60)

    client = CruzrRobotClient()
    # print(f"📡 Đang kết nối tới Robot Cruzr ({client.ip}:{client.port})...")

    connected = client.connect(timeout=1.0)
    # if not connected:
    #     print("❌ Không thể kết nối tới Robot. Vui lòng kiểm tra địa chỉ IP và mạng!")
    #     print("💡 Text giới thiệu sẽ được in ra màn hình dưới dạng Demo:")
    #     print(f"\n[EN]: {START_TEXT_EN} {INTRO_TEXT_EN}")
    #     # print(f"[VI]: {start_vi} {intro_vi}\n")
    #     return False

    try:
        if language in ["en", "both"]:

            # Mở biểu cảm thẹn thùng & động tác dễ thương
            print("🎭 Đang mở biểu cảm: emotion://va/face_love")
            client.play_emotion("emotion://va/face_love")
            time.sleep(2)
            print("👋 Robot thực hiện cử chỉ: action://ubtech/cute")
            client.play_action("action://ubtrobot/cute")
            time.sleep(23)


        client.move(turningAngle=-176.3, turningSpeed=45)
        time.sleep(3.7)
        client.move(distance=0.6, speed=0.45)
        time.sleep(4.3)
        client.move(turningAngle=86.3, turningSpeed=45)
        time.sleep(3.5)
        client.move(distance=0.4, speed=0.45)
        time.sleep(4)
        client.move(turningAngle=-86.3, turningSpeed=45)


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
    # parser = argparse.ArgumentParser(description="Script giới thiệu Robot CruzrTwin ASEAN kèm tay di chuyển liên tục")
    # parser.add_argument(
    #     "--lang",
    #     choices=["en", "vi", "both"],
    #     default="en",
    #     help="Ngôn ngữ phát thoại: en (Tiếng Anh), vi (Tiếng Việt), both (Cả hai). Mặc định: en"
    # )
    parser.add_argument(
        "--emotion",
        default="emotion://va/face_amazing",
        help="Mã biểu cảm khuôn mặt của Robot (mặc định: face_amazing)"
    )
    args = parser.parse_args()

    speak_intro(language=args.lang, emotion=args.emotion)


if __name__ == "__main__":
    main()
