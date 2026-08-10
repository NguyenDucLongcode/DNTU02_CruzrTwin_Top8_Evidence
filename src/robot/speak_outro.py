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
OUTRO_TEXT_EN = "CruzrTwin ASEAN — closing the last meter of smart-city response."
OUTRO_TEXT_VI = "CruzrTwin ASEAN — giải pháp rút ngắn mét cuối cùng trong ứng phó đô thị thông minh."


def speak_with_continuous_gestures(client, text: str, language: str, duration_sec: float, actions: list):
    """
    Phát giọng nói TTS trước, phát cử chỉ tay song song, rồi chờ speech xong.
    """
    import queue as _queue

    print(f"📢 Robot phát giọng nói Outro ({language.upper()}): \"{text}\"")
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



def speak_outro(language: str = "en", emotion: str = "emotion://va/techface_happy"):
    """
    Kết nối và điều khiển Robot Cruzr phát câu Outro chốt kịch bản
    """
    print("\n" + "=" * 60)
    print("🤖 CRUZR ROBOT OUTRO SPEECH SCRIPT")
    print("=" * 60)

    client = CruzrRobotClient()
    print(f"📡 Đang kết nối tới Robot Cruzr ({client.ip}:{client.port})...")

    connected = client.connect(timeout=1.0)
    if not connected:
        print("❌ Không thể kết nối tới Robot. Vui lòng kiểm tra địa chỉ IP và mạng!")
        print("💡 Text Outro sẽ được in ra màn hình dưới dạng Demo:")
        print(f"\n[EN]: {OUTRO_TEXT_EN}")
        print(f"[VI]: {OUTRO_TEXT_VI}\n")
        return False

    try:
        # 1. Phát biểu cảm khuôn mặt + Cử chỉ giơ tay chào
        if emotion:
            print(f"🎭 Đang mở biểu cảm: {emotion}")
            client.play_emotion(emotion)

        print("👋 Robot giơ tay chào Outro...")
        client.play_action("action://ubtech/greeting")
        time.sleep(1.5)

        # Di chuyển theo hành trình Outro
        client.move(turningAngle=-81.5, turningSpeed=60)
        time.sleep(3.7)
        client.move(distance=1.1, speed=0.5)
        time.sleep(4.4)
        client.move(turningAngle=81.5, turningSpeed=60)
        time.sleep(3.7)
        client.move(distance=2.2, speed=0.45)
        time.sleep(5)

        # Danh sách các động tác cử chỉ tay chào kết thúc Outro
        closing_actions = [
            "action://ubtech/presentation",
            "action://ubtech/wave",
            "action://ubtech/greeting"
        ]

        # 2. Phát duy nhất câu slogan Outro
        if language in ["en", "both"]:
            print(f"\n📢 Robot phát Outro (EN):\n\"{OUTRO_TEXT_EN}\"")
            speak_with_continuous_gestures(
                client=client,
                text=OUTRO_TEXT_EN,
                language="en",
                duration_sec=7.0,
                actions=closing_actions
            )


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
