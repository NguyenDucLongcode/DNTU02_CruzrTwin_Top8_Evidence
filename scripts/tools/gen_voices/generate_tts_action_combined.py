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
messageSmartPlug = "I will turn off all electrical devices. "
messageAlarm = "and activate the alarm. "
messageMoveOut = "Now, please follow me to the safe waiting area."

# Gom lại thành 1 đoạn
combined_text = messageCitical + messageSmartPlug + messageAlarm + messageMoveOut

print("="*50)
print(f"Xử lý đoạn GOM CHUNG: \n{combined_text}")
print(f"Số lượng từ: {len(combined_text.split())}")
print(f"Số lượng ký tự: {len(combined_text)}")

filename = "action_combined.mp3"
tts = gTTS(text=combined_text, lang='en', slow=False)
tts.save(filename)

audio = MP3(filename)
print(f"File: {filename}")
print(f"Thời lượng Tổng (Time Sleep): {audio.info.length:.2f} giây\n")
print("="*50)
