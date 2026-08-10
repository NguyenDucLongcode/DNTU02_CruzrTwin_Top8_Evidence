import os
import sys

try:
    from gtts import gTTS
    from mutagen.mp3 import MP3
except ImportError:
    print("Vui lòng cài đặt gTTS và mutagen: pip install gTTS mutagen")
    sys.exit(1)

START_TEXT_EN = (
    "Ladies and Gentlemen, dear judges and all the audience. "
    "The DNTU CruzTwin team would like to begin our presentation now. "
)

INTRO_TEXT_EN = (
    "In many ASEAN public buildings, digital systems can detect danger—"
    "but they cannot reach the people who need help. "
)

# Thêm dấu cách ở giữa 2 đoạn nếu cần
full_text = START_TEXT_EN + INTRO_TEXT_EN

print("="*50)
print("ĐANG XỬ LÝ TEXT:")
print(f"START_TEXT: {START_TEXT_EN}")
print(f"INTRO_TEXT: {INTRO_TEXT_EN}")
print("="*50)

# Đếm
word_count = len(full_text.split())
char_count = len(full_text)
print(f"Số lượng từ (Word count): {word_count}")
print(f"Số lượng ký tự (Character count): {char_count}")

# Tạo audio
output_file = "intro_speech.mp3"
tts = gTTS(text=full_text, lang='en', slow=False)
tts.save(output_file)
print(f"Đã tạo file MP3 thành công: {os.path.abspath(output_file)}")

# Đo thời lượng
audio = MP3(output_file)
duration = audio.info.length

print("="*50)
print(f"Thời lượng Audio (Time Sleep khuyến nghị): {duration:.2f} giây")
print("="*50)
