import os
import sys

try:
    from gtts import gTTS
    from mutagen.mp3 import MP3
except ImportError:
    print("Vui lòng cài đặt gTTS và mutagen")
    sys.exit(1)

room_name = "A101"
messageCitical = (
    f"Critical indoor-environment anomaly detected in "
    f"Room {room_name}. Please follow me guidance and move calmly to the safe waiting area. "
)
messageSmartPlug = "I will turn off all electrical devices."
messageAlarm = "and activate the alarm.."
messageMoveOut = "Now, please follow me to the safe waiting area.."

def process_text(text, filename):
    print(f"Xử lý: {text}")
    print(f"Số lượng từ: {len(text.split())}")
    print(f"Số lượng ký tự: {len(text)}")
    
    tts = gTTS(text=text, lang='en', slow=False)
    tts.save(filename)
    audio = MP3(filename)
    print(f"File: {filename}")
    print(f"Thời lượng (Time Sleep): {audio.info.length:.2f} giây\n")

print("="*50)
process_text(messageCitical, "action_critical.mp3")
process_text(messageSmartPlug, "action_smartplug.mp3")
process_text(messageAlarm, "action_alarm.mp3")
process_text(messageMoveOut, "action_moveout.mp3")
print("="*50)
