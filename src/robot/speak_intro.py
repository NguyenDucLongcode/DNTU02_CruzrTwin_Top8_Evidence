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
START_TEXT_EN = (
    "Ladies and Gentlemen, dear judges and all the audience."
    "The DNTU CruzTwin team would like to begin our presentation now."
)

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
    Phát giọng nói TTS trước, phát cử chỉ tay song song, rồi chờ speech xong.
    """
    import queue as _queue

    print(f"📢 Robot phát giọng nói: \"{text[:50]}...\"")
    client.speak(text, language=language)
    time.sleep(0.3)  # Buffer nhỏ để robot bắt đầu TTS trước khi nhận lệnh cử chỉ

    # Phát cử chỉ tay song song với speech
    gesture_start = time.monotonic()
    for act in actions:
        try:
            client.play_action(act)
            time.sleep(2.5)
        except Exception as e:
            print(f"   ⚠️ Lỗi phát cử chỉ {act}: {e}")
    gesture_elapsed = time.monotonic() - gesture_start

    # Sau khi cử chỉ xong, chờ speech hoàn thành (nếu robot vẫn đang nói)
    estimated = client._estimate_speak_duration(text, language)
    remaining = max(0, estimated - gesture_elapsed)

    if remaining > 0:
        print(f"   ⏳ [SPEAK] Chờ speech còn lại ({remaining:.1f}s)...")
        deadline = time.monotonic() + remaining
        while time.monotonic() < deadline:
            rem = deadline - time.monotonic()
            if rem <= 0:
                break
            try:
                resp = client._response_queue.get(timeout=min(rem, 0.5))
                if resp.get("status") == "completed":
                    print(f"   ✅ [SPEAK] Robot nói xong!")
                    time.sleep(0.3)
                    return
            except _queue.Empty:
                continue
        print(f"   ⏱️ [SPEAK] Đã chờ hết {remaining:.1f}s (fallback)")



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
        # print(f"[VI]: {start_vi} {intro_vi}\n")
        return False

    try:
        # Danh sách các động tác cử chỉ tay thay đổi liên tục khi thuyết trình

        greeting_actions = ["action://ubtech/wave", "action://ubtech/greeting"]
        presentation_actions = [
            "action://ubtech/presentation",
            "action://ubtech/explain",
            "action://ubtech/gesture_right",
            "action://ubtech/gesture_left",
            "action://ubtech/wave"
        ]

        # START ACTIONS--------------------

        client.move(distance=1.46, speed=0.45)
        client.play_action("action://ubtech/goodbye")
        time.sleep(5)
        client.move(turningAngle=-86.3, turningSpeed=45)
        time.sleep(3.7)
        client.move(distance=0.5, speed=0.45)
        time.sleep(2)

        # 2. Phát giọng nói kết hợp cử chỉ tay di chuyển liên tục
        if language in ["en", "both"]:
            # Bước A: Xin phép bắt đầu + Động tác vẫy tay chào (Wave gestures)
            print(f"\n📢 Robot chào xin phép bắt đầu (EN):\n\"{START_TEXT_EN}\"")
            speak_with_continuous_gestures(
                client=client,
                text=START_TEXT_EN,
                language="en",
                duration_sec=20,
                actions=greeting_actions
            )
            time.sleep(4)
            # Bước B: Nói bài giới thiệu + Động tác tay thuyết trình liên tục suốt bài nói (Continuous Presentation)
            print(f"\n📢 Robot phát bài giới thiệu (EN) + Tay di chuyển liên tục:\n\"{INTRO_TEXT_EN}\"")
            speak_with_continuous_gestures(
                client=client,
                text=INTRO_TEXT_EN,
                language="en",
                duration_sec=12.0,
                actions=presentation_actions
            )
            time.sleep(20)

            # Mở biểu cảm thẹn thùng & động tác dễ thương
            print("🎭 Đang mở biểu cảm: emotion://va/face_love")
            client.play_emotion("emotion://va/face_love")
            time.sleep(2)
            print("👋 Robot thực hiện cử chỉ: action://ubtech/cute")
            client.play_action("action://ubtrobot/cute")
            time.sleep(23)


        client.move(turningAngle=-176.3, turningSpeed=45)
        time.sleep(5)
        client.move(distance=0.6, speed=0.45)
        time.sleep(5)
        client.move(turningAngle=86.3, turningSpeed=45)
        time.sleep(5)
        client.move(distance=0.4, speed=0.45)
        time.sleep(5)
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
