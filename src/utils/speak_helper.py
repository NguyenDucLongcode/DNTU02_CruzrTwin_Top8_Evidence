"""
Robot Speak Helper - Hỗ trợ speak tuần tự với ước lượng thời gian
"""

import time
import re
from typing import List, Dict, Any, Optional


def estimate_speak_duration(text: str, language: str = "vi") -> float:
    """
    Ước lượng thời gian robot nói.

    Công thức:
    - Tiếng Việt: ~0.55 giây / từ
    - Tiếng Anh: ~0.45 giây / từ
    - Cộng thêm thời gian khởi động TTS
    - Cộng thêm thời gian ngắt nghỉ theo dấu câu
    """

    # Đếm số từ
    word_count = len(text.split())

    # Tốc độ nói thực tế của robot thường chậm hơn người
    if language.lower() == "vi":
        seconds_per_word = 0.55
    else:
        seconds_per_word = 0.45

    # Thời gian khởi động engine TTS
    startup_overhead = 1.5

    # Thời gian cơ bản
    estimated_time = (word_count * seconds_per_word) + startup_overhead

    # Đếm dấu câu để cộng thời gian ngắt nghỉ
    punctuation_count = len(
        re.findall(r"[.,!?;:\-()]", text)
    )

    estimated_time += punctuation_count * 0.3

    # Tối thiểu 2 giây
    estimated_time = max(2.0, estimated_time)

    return round(estimated_time, 1)


def wait_for_robot_ready(
    robot_client,
    timeout: float = 10.0,
    check_interval: float = 0.5,
    verbose: bool = True
) -> bool:
    """
    Kiểm tra robot đã sẵn sàng chưa (gửi lệnh ping)
    
    Args:
        robot_client: Robot client instance
        timeout: Thời gian chờ tối đa (giây)
        check_interval: Khoảng cách kiểm tra (giây)
        verbose: In log hay không
    
    Returns:
        bool: True nếu robot sẵn sàng, False nếu timeout
    """
    start_time = time.time()
    attempt = 0
    
    while time.time() - start_time < timeout:
        attempt += 1
        try:
            # Gửi lệnh kiểm tra trạng thái
            status = robot_client.send_command("current_location", timeout=2)
            
            # Kiểm tra response
            if status and status.get("success", False):
                if verbose:
                    print(f"   ✅ Robot ready (attempt {attempt})")
                return True
                
        except Exception as e:
            if verbose:
                print(f"   ⚠️ Check attempt {attempt} failed: {e}")
        
        time.sleep(check_interval)
    
    if verbose:
        print(f"   ⚠️ Robot not ready after {timeout}s")
    return False


def speak_and_wait(
    robot_client,
    message: str,
    language: str = "vi",
    max_wait: float = 60.0,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Gửi lệnh speak và đợi robot nói xong
    
    Args:
        robot_client: Robot client instance
        message: Nội dung cần nói
        language: Ngôn ngữ ('vi' hoặc 'en')
        max_wait: Thời gian chờ tối đa (giây)
        verbose: In log hay không
    
    Returns:
        dict: {
            "success": bool,
            "message": str,
            "language": str,
            "word_count": int,
            "estimated_duration": float,
            "actual_duration": float,
            "robot_ready": bool,
            "response": dict
        }
    """
    if verbose:
        print(f"\n   🗣️ Speaking ({language}): {message[:60]}...")
    
    # 1. Gửi lệnh speak
    start_time = time.time()
    result = robot_client.speak(message, language=language)
    send_time = time.time() - start_time
    
    if verbose:
        print(f"   📡 Speak sent in {send_time:.2f}s")
        print(f"   📡 Response: success={result.get('success', False)}")
    
    if not result.get("success", False):
        if verbose:
            print(f"   ❌ Speak failed!")
        return {
            "success": False,
            "message": message,
            "language": language,
            "word_count": len(message.split()),
            "estimated_duration": 0,
            "actual_duration": send_time,
            "robot_ready": False,
            "error": result.get("message", "Unknown error"),
            "response": result
        }
    
    # 2. Ước lượng thời gian nói
    estimated_time = estimate_speak_duration(message, language)
    word_count = len(message.split())
    
    if verbose:
        print(f"   ⏳ Ước lượng {estimated_time:.1f}s ({word_count} từ)...")
    
    # Chờ toàn bộ thời gian ước lượng + 1 giây buffer
    wait_time = estimated_time + 1.0
    if verbose:
      print(
        f"   📊 Words={word_count}, "
        f"Estimated={estimated_time:.1f}s"
    )
    
    # 4. Kiểm tra robot đã sẵn sàng chưa
    remaining_time = max_wait - (time.time() - start_time)
    robot_ready = False
    
    if remaining_time > 0:
        if verbose:
            print(f"   ⏳ Kiểm tra robot (timeout: {min(remaining_time, 10):.1f}s)...")
        robot_ready = wait_for_robot_ready(
            robot_client,
            timeout=min(remaining_time, 10),
            verbose=verbose
        )
        if verbose and robot_ready:
            print(f"   ✅ Robot ready!")
        elif verbose:
            print(f"   ⚠️ Robot not ready, continuing...")
    else:
        if verbose:
            print(f"   ⚠️ Timeout, continuing...")
    
    total_time = time.time() - start_time
    
    return {
        "success": True,
        "message": message,
        "language": language,
        "word_count": word_count,
        "estimated_duration": estimated_time,
        "actual_duration": total_time,
        "robot_ready": robot_ready,
        "response": result
    }


def speak_sequence(
    robot_client,
    messages: List[str],
    languages: List[str],
    wait_between: float = 1.0,
    max_wait: float = 60.0,
    verbose: bool = True,
    stop_on_error: bool = True
) -> List[Dict[str, Any]]:
    """
    Speak nhiều message tuần tự
    
    Args:
        robot_client: Robot client instance
        messages: List message cần nói
        languages: List ngôn ngữ tương ứng
        wait_between: Thời gian chờ giữa các lệnh (giây)
        max_wait: Thời gian chờ tối đa cho mỗi lệnh
        verbose: In log hay không
        stop_on_error: Dừng nếu có lỗi
    
    Returns:
        list: Kết quả từng lệnh
    """
    if len(messages) != len(languages):
        raise ValueError("messages and languages must have same length")
    
    results = []
    
    if verbose:
        print(f"\n{'='*50}")
        print(f"🗣️ SPEAK SEQUENCE ({len(messages)} messages)")
        print(f"{'='*50}")
    
    for i, (message, language) in enumerate(zip(messages, languages)):
        if verbose:
            print(f"\n📢 [{i+1}/{len(messages)}] Language: {language.upper()}")
        
        # Speak và đợi
        result = speak_and_wait(
            robot_client,
            message,
            language,
            max_wait=max_wait,
            verbose=verbose
        )
        results.append(result)
        
        # Dừng nếu lỗi
        if not result.get("success", False) and stop_on_error:
            if verbose:
                print(f"   ❌ Stop sequence due to error")
            break
        
        # Chờ thêm giữa các lệnh
        if i < len(messages) - 1:
            if verbose:
                print(f"   ⏳ Chờ {wait_between}s trước lệnh tiếp theo...")
            time.sleep(wait_between)
    
    # Tổng kết
    if verbose:
        success_count = sum(1 for r in results if r.get("success", False))
        print(f"\n{'='*50}")
        print(f"📊 KẾT QUẢ: {success_count}/{len(results)} thành công")
        print(f"{'='*50}")
        
        # Chi tiết
        for r in results:
            status = "✅" if r.get("success") else "❌"
            lang = r.get("language", "??").upper()
            words = r.get("word_count", 0)
            duration = r.get("actual_duration", 0)
            print(f"   {status} {lang}: {words} từ, {duration:.1f}s")
    
    return results


def speak_single(
    robot_client,
    message: str,
    language: str = "vi",
    wait_after: float = 1.0,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Speak một message duy nhất
    
    Args:
        robot_client: Robot client instance
        message: Nội dung cần nói
        language: Ngôn ngữ ('vi' hoặc 'en')
        wait_after: Thời gian chờ sau khi nói xong
        verbose: In log hay không
    
    Returns:
        dict: Kết quả speak
    """
    result = speak_and_wait(robot_client, message, language, verbose=verbose)
    
    if wait_after > 0 and result.get("success", False):
        if verbose:
            print(f"   ⏳ Chờ {wait_after}s sau khi nói...")
        time.sleep(wait_after)
    
    return result


# ============================================
# PHIÊN BẢN ĐƠN GIẢN NHẤT (dùng cho code của bạn)
# ============================================

def speak_simple(robot_client, message: str, language: str = "vi") -> dict:
    """
    Phiên bản đơn giản nhất: speak và đợi ước lượng
    
    Args:
        robot_client: Robot client instance
        message: Nội dung cần nói
        language: Ngôn ngữ ('vi' hoặc 'en')
    
    Returns:
        dict: Kết quả speak
    """
    return speak_and_wait(robot_client, message, language, verbose=True)


# ============================================
# TEST
# ============================================

if __name__ == "__main__":
    # Test ước lượng thời gian
    test_texts = [
        ("Phát hiện bất thường môi trường trong phòng A101. Vui lòng làm theo hướng dẫn.", "vi"),
        ("Critical indoor-environment anomaly detected in Room A101.", "en"),
    ]
    
    print("🧪 TEST ESTIMATE DURATION")
    print("=" * 50)
    for text, lang in test_texts:
        duration = estimate_speak_duration(text, lang)
        words = len(text.split())
        print(f"   {lang.upper()}: {words} từ → {duration:.1f}s")
        print(f"      {text[:60]}...")