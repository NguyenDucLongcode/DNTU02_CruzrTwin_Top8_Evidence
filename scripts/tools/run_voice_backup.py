import sys
import os
import time

def play_audio(filename):
    # Xác định đường dẫn file âm thanh dự phòng
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    voice_dir = os.path.join(root_dir, "VoiceBackup")
    file_path = os.path.join(voice_dir, filename)

    if not os.path.exists(file_path):
        print(f"[ERROR] Khong tim thay file am thanh: {file_path}")
        return

    print(f"[INFO] Dang phat am thanh du phong tren may tinh: {filename}")
    
    # Ưu tiên sử dụng pygame để phát ngầm mà không mở cửa sổ (không giật màn hình)
    try:
        import pygame
        pygame.mixer.init()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        
        # Chờ phát xong
        while pygame.mixer.music.get_busy():
            time.sleep(1)
        print("[INFO] Phat xong!")
    except ImportError:
        print("[WARNING] Chua cai thu vien pygame. Dang dung trinh phat mac dinh cua Windows...")
        print("   (Goi y: chay lenh 'pip install pygame' de am thanh phat ngam tot hon)")
        if os.name == 'nt':
            os.startfile(file_path)
        else:
            print("Không thể tự động phát trên hệ điều hành này nếu không có pygame.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        play_audio(sys.argv[1])
    else:
        print("Vui lòng cung cấp tên file mp3. Ví dụ: python run_voice_backup.py vi_speak_intro.mp3")
