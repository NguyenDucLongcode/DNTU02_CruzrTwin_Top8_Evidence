from gtts import gTTS
import os

try:
    from mutagen.mp3 import MP3
except ImportError:
    import sys
    print("Vui lòng cài đặt mutagen: pip install mutagen")
    sys.exit(1)

text = "CruzTwin ASEAN — closing the last meter of smart-city response."

print("="*50)
print(f"Xử lý: {text}")
print(f"Số lượng từ: {len(text.split())}")
print(f"Số lượng ký tự: {len(text)}")

tts = gTTS(text, lang='en', tld='com') # Default google US female voice
output_file = "outro_en_google_female.mp3"
tts.save(output_file)

audio = MP3(output_file)
print(f"Saved to {output_file}")
print(f"Thời lượng (Time Sleep): {audio.info.length:.2f} giây")
print("="*50)
