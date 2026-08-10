import os
import sys

try:
    from gtts import gTTS
    from mutagen.mp3 import MP3
except ImportError:
    print("Vui lòng cài đặt gTTS và mutagen")
    sys.exit(1)

room_name = "A101"

segments = [
    {
        "lang": "en",
        "text": f"Critical indoor-environment anomaly detected in Room {room_name}. Please follow me guidance and move calmly to the safe waiting area. "
    },
    {
        "lang": "vi",
        "text": f"Đã phát hiện sự cố bất thường nghiêm trọng trong môi trường trong nhà tại Phòng {room_name}. Vui lòng làm theo hướng dẫn của tôi và di chuyển bình tĩnh đến khu vực chờ an toàn. "
    },
    {
        "lang": "en",
        "text": "I will turn off all electrical devices. "
    },
    {
        "lang": "vi",
        "text": "Tôi sẽ tiến hành tắt tất cả các thiết bị điện. "
    },
    {
        "lang": "en",
        "text": "and activate the alarm.. "
    },
    {
        "lang": "vi",
        "text": "Và bật còi báo động. "
    },
    {
        "lang": "en",
        "text": "Now, please follow me to the safe waiting area.. "
    },
    {
        "lang": "vi",
        "text": "Bây giờ, xin hãy đi theo tôi đến khu vực chờ an toàn."
    }
]

temp_files = []

for i, seg in enumerate(segments):
    tmp_name = f"temp_{i}.mp3"
    tts = gTTS(text=seg["text"], lang=seg["lang"], slow=False)
    tts.save(tmp_name)
    temp_files.append(tmp_name)

output_file = "full_action_multilingual.mp3"

# Gom tất cả các file mp3 thành 1 bằng cách nối byte (binary append)
with open(output_file, "wb") as outfile:
    for f in temp_files:
        with open(f, "rb") as infile:
            outfile.write(infile.read())

# Đo thời lượng file tổng
audio = MP3(output_file)

# Dọn dẹp file tạm
for f in temp_files:
    os.remove(f)

print("="*50)
print(f"Đã gộp toàn bộ text (cả Tiếng Anh & Tiếng Việt) thành 1 file MP3.")
print(f"File: {output_file}")
print(f"Thời lượng (Time Sleep): {audio.info.length:.2f} giây")
print("="*50)
