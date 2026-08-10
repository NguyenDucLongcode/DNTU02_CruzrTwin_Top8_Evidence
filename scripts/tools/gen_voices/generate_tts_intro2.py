import os
import sys

try:
    from gtts import gTTS
    from mutagen.mp3 import MP3
except ImportError:
    print("Vui lòng cài đặt gTTS và mutagen")
    sys.exit(1)

START_TEXT_EN = (
    "Ladies and Gentlemen, dear judges and all the audience. "
    "The DNTU CruzTwin team would like to begin our presentation now."
)

INTRO_TEXT_EN = (
    "In many ASEAN public buildings, digital systems can detect danger—"
    "but they cannot reach the people who need help. "
)

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
process_text(START_TEXT_EN, "start_speech.mp3")
process_text(INTRO_TEXT_EN, "intro_speech2.mp3")
print("="*50)
