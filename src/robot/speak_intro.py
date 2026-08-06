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
# START_TEXT_VI = "Đội DNTU CruzrTwin xin được phép bắt đầu."
START_TEXT_EN = "Ladies and Gentlemen, dear judges and all the audience. The DNTU CruzrTwin team would like to begin our presentation now."

# Đoạn văn bản giới thiệu bằng Tiếng Anh (English Intro Text)
INTRO_TEXT_EN = (
    "In many ASEAN public buildings, digital systems can detect danger—"
    "but they cannot reach the people who need help. "
)

# Bản dịch Tiếng Việt chuẩn (Vietnamese Intro Text)
# INTRO_TEXT_VI = (
#     "Tại nhiều tòa nhà công cộng tại khu vực ASEAN, hệ thống kỹ thuật số có thể phát hiện nguy hiểm—"
#     "nhưng lại không thể tiếp cận trực tiếp những người đang cần hỗ trợ. "

# )


def play_gestures_continuously(client, duration_sec: float, actions: list, stop_event: threading.Event):
    """
    Phát cử chỉ tay liên tục lặp lại trong suốt thời gian Robot đang phát thoại
    """
    end_time = time.time() + duration_sec
    idx = 0
    while time.time() < end_time and not stop_event.is_set():
        act = actions[idx % len(actions)]
        try:
            client.play_action(act)
        except Exception:
            pass
        idx += 1
        # Chờ 3.2 giây rồi chuyển sang động tác tay tiếp theo để tay di chuyển liên tục
        stop_event.wait(3.2)


def speak_with_continuous_gestures(client, text: str, language: str, duration_sec: float, actions: list):
    """
    Phát âm thanh đồng thời kích hoạt luồng cử chỉ tay di chuyển liên tục
    """
    stop_event = threading.Event()
    t = threading.Thread(
        target=play_gestures_continuously,
        args=(client, duration_sec, actions, stop_event),
        daemon=True
    )
    t.start()
    client.speak(text, language=language)
    time.sleep(duration_sec)
    stop_event.set()
    t.join(timeout=0.5)


def speak_intro(language: str = "en", emotion: str = "emotion://va/techface_happy"):
    """
    Kết nối và điều khiển Robot Cruzr phát câu giới thiệu ASEAN kèm cử chỉ tay di chuyển liên tục
    """
    print("\n" + "=" * 60)
    print("🤖 CRUZR ROBOT INTRO SPEECH SCRIPT (CONTINUOUS HAND GESTURES)")
    print("=" * 60)

    client = CruzrRobotClient()
    print(f"📡 Đang kết nối tới Robot Cruzr ({client.ip}:{client.port})...")

    connected = client.connect(timeout=1.0)
    if not connected:
        print("❌ Không thể kết nối tới Robot. Vui lòng kiểm tra địa chỉ IP và mạng!")
        print("💡 Text giới thiệu sẽ được in ra màn hình dưới dạng Demo:")
        print(f"\n[EN]: {START_TEXT_EN} {INTRO_TEXT_EN}")
        print(f"[VI]: {START_TEXT_VI} {INTRO_TEXT_VI}\n")
        return False

    try:
        # 1. Phát biểu cảm khuôn mặt + Cử chỉ giơ tay chào (Greeting Action)
        if emotion:
            print(f"🎭 Đang mở biểu cảm: {emotion}")
            client.play_emotion(emotion)

        print("👋 Robot giơ tay chào mở đầu...")
        client.play_action("action://ubtech/greeting")
        time.sleep(1.5)

        # Danh sách các động tác cử chỉ tay thay đổi liên tục khi thuyết trình
        greeting_actions = ["action://ubtech/wave", "action://ubtech/greeting"]
        presentation_actions = [
            "action://ubtech/presentation",
            "action://ubtech/explain",
            "action://ubtech/gesture_right",
            "action://ubtech/gesture_left",
            "action://ubtech/wave"
        ]

        # 2. Phát giọng nói kết hợp cử chỉ tay di chuyển liên tục
        if language in ["en", "both"]:
            # Bước A: Xin phép bắt đầu + Động tác vẫy tay chào (Wave gestures)
            print(f"\n📢 Robot chào xin phép bắt đầu (EN):\n\"{START_TEXT_EN}\"")
            speak_with_continuous_gestures(
                client=client,
                text=START_TEXT_EN,
                language="en",
                duration_sec=7.0,
                actions=greeting_actions
            )

            # Bước B: Nói bài giới thiệu + Động tác tay thuyết trình liên tục suốt bài nói (Continuous Presentation)
            print(f"\n📢 Robot phát bài giới thiệu (EN) + Tay di chuyển liên tục:\n\"{INTRO_TEXT_EN}\"")
            speak_with_continuous_gestures(
                client=client,
                text=INTRO_TEXT_EN,
                language="en",
                duration_sec=12.0,
                actions=presentation_actions
            )

        if language in ["vi", "both"]:
            # Bước A: Xin phép bắt đầu (VI) + Động tác tay chào
            print(f"\n📢 Robot chào xin phép bắt đầu (VI):\n\"{START_TEXT_VI}\"")
            speak_with_continuous_gestures(
                client=client,
                text=START_TEXT_VI,
                language="vi",
                duration_sec=4.5,
                actions=greeting_actions
            )

            # Bước B: Nói bài giới thiệu (VI) + Động tác tay thuyết trình liên tục suốt bài nói
            print(f"\n📢 Robot phát bài giới thiệu (VI) + Tay di chuyển liên tục:\n\"{INTRO_TEXT_VI}\"")
            speak_with_continuous_gestures(
                client=client,
                text=INTRO_TEXT_VI,
                language="vi",
                duration_sec=14.0,
                actions=presentation_actions
            )

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
        default="emotion://va/techface_happy",
        help="Mã biểu cảm khuôn mặt của Robot (mặc định: techface_happy)"
    )
    args = parser.parse_args()

    speak_intro(language=args.lang, emotion=args.emotion)


if __name__ == "__main__":
    main()
