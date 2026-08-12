import os
import sys
import logging
from flask import Flask, jsonify
from flask_cors import CORS
import win32com.client
import win32gui
import win32con
import win32api
import pythoncom

app = Flask(__name__)
CORS(app)  # Cho phép gọi chéo từ giao diện React (CORS)

# ĐƯỜNG DẪN TỚI FILE PPT CỦA BẠN (Sửa dòng này thành đường dẫn thật của bạn, nhớ giữ chữ r ở trước)
PPT_FILE_PATH = r"C:\Users\Ngoc Tan\Downloads\DNTU02_CruzrTwin_Top8_Evidence\PPT_final.pptx"

def get_ppt_app():
    """Lấy kết nối tới phần mềm PowerPoint đang mở"""
    try:
        # Sử dụng Dispatch để bắt vào ứng dụng PowerPoint đã mở sẵn
        ppt = win32com.client.Dispatch("PowerPoint.Application")
        return ppt
    except Exception as e:
        print(f"[LOI] Khong the ket noi PowerPoint: {e}")
        return None

def bring_ppt_to_front(ppt=None):
    """Tìm và đẩy cửa sổ PowerPoint lên trên cùng"""
    try:
        import win32api
        # Mẹo qua mặt Windows Foreground Lock bằng cách giả lập ấn nhả phím ALT
        win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
        win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)

        def enum_windows(hwnd, lParam):
            class_name = win32gui.GetClassName(hwnd)
            title = win32gui.GetWindowText(hwnd)

            if win32gui.IsWindowVisible(hwnd):
                # Class 'screenClass' là cửa sổ Fullscreen của Slide Show
                # Class 'PPTFrameClass' là cửa sổ Editor
                if class_name == "screenClass" or "Slide Show" in title or "Trình chiếu" in title:
                    win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
                    win32gui.SetForegroundWindow(hwnd)
        win32gui.EnumWindows(enum_windows, None)
    except Exception as e:
        print(f"[LOI] Loi khi kich hoat cua so: {e}")

@app.route('/slide/start', methods=['GET'])
def start_slide():
    """Lệnh bắt đầu chiếu Slide và hiện PPT lên"""
    pythoncom.CoInitialize()
    ppt = get_ppt_app()
    if not ppt: return jsonify({"status": "error", "message": "PowerPoint is not running"}), 500
    try:
        # Nếu chưa có file nào đang mở, tự động mở file cứng
        if ppt.Presentations.Count == 0:
            if os.path.exists(PPT_FILE_PATH):
                ppt.Presentations.Open(PPT_FILE_PATH)
            else:
                return jsonify({"status": "error", "message": f"Khong tim thay file {PPT_FILE_PATH}"}), 404

        # Bắt đầu chiếu
        presentation = ppt.ActivePresentation
        presentation.SlideShowSettings.Run()
        bring_ppt_to_front(ppt)
        return jsonify({"status": "success", "message": "Started Slideshow"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/slide/next', methods=['GET'])
def next_slide():
    """Lệnh chuyển trang tiếp theo"""
    pythoncom.CoInitialize()
    ppt = get_ppt_app()
    if not ppt: return jsonify({"status": "error", "message": "PowerPoint is not running"}), 500
    try:
        if ppt.SlideShowWindows.Count > 0:
            ppt.SlideShowWindows(1).View.Next()
        bring_ppt_to_front(ppt)
        return jsonify({"status": "success", "message": "Next Slide"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/slide/prev', methods=['GET'])
def prev_slide():
    """Lệnh lùi lại trang trước"""
    pythoncom.CoInitialize()
    ppt = get_ppt_app()
    if not ppt: return jsonify({"status": "error", "message": "PowerPoint is not running"}), 500
    try:
        if ppt.SlideShowWindows.Count > 0:
            ppt.SlideShowWindows(1).View.Previous()
        bring_ppt_to_front(ppt)
        return jsonify({"status": "success", "message": "Previous Slide"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/slide/dashboard', methods=['GET'])
def back_to_dashboard():
    """Thu nhỏ PPT và mở Chrome/Edge (Dashboard) lên trên cùng"""
    try:
        def enum_windows(hwnd, lParam):
            title = win32gui.GetWindowText(hwnd)
            if win32gui.IsWindowVisible(hwnd):
                # Đổi thành "Digital Twin Fire Safety" để không bị nhầm với thư mục Windows Explorer
                if "Digital Twin Fire Safety" in title:
                    # Giả lập phím ALT để giành quyền Foreground
                    win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
                    win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
                    win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
                    win32gui.SetForegroundWindow(hwnd)
        win32gui.EnumWindows(enum_windows, None)
        return jsonify({"status": "success", "message": "Switched to Dashboard"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Tắt log quá dài của werkzeug
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    print("\n" + "="*60)
    print("MINI-SERVER DIEU KHIEN POWERPOINT KHOI DONG THANH CONG")
    print("API chay tai: http://localhost:5005")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=5005, debug=False)
