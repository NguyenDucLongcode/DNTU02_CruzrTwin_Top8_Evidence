"""
Translation utilities - Dịch ngôn ngữ
Support: English ↔ Vietnamese
"""

import os
import sys
from pathlib import Path

# Thêm đường dẫn
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR))

try:
    from deep_translator import GoogleTranslator
    HAS_TRANSLATOR = True
except ImportError:
    HAS_TRANSLATOR = False
    print("⚠️ deep-translator not installed. Install: pip install deep-translator")

# Cache để tránh dịch lại nhiều lần
_translation_cache = {}

# Khởi tạo translator
_translator = None
if HAS_TRANSLATOR:
    _translator = GoogleTranslator(source='en', target='vi')


def translate_to_vietnamese(text: str, use_cache: bool = True) -> str:
    """
    Dịch tiếng Anh sang tiếng Việt
    
    Args:
        text: Văn bản tiếng Anh cần dịch
        use_cache: Sử dụng cache để tránh dịch lại
    
    Returns:
        str: Văn bản đã dịch sang tiếng Việt
    """
    if not text:
        return text
    
    # Kiểm tra cache
    if use_cache and text in _translation_cache:
        return _translation_cache[text]
    
    if not HAS_TRANSLATOR or _translator is None:
        print(f"   ⚠️ Translator not available, using original: {text[:50]}...")
        return text
    
    try:
        result = _translator.translate(text)
        # Lưu cache
        if use_cache:
            _translation_cache[text] = result
        return result
    except Exception as e:
        print(f"   ⚠️ Translation error: {e}, using original")
        return text


def translate_to_english(text: str, use_cache: bool = True) -> str:
    """
    Dịch tiếng Việt sang tiếng Anh
    
    Args:
        text: Văn bản tiếng Việt cần dịch
        use_cache: Sử dụng cache để tránh dịch lại
    
    Returns:
        str: Văn bản đã dịch sang tiếng Anh
    """
    if not text:
        return text
    
    # Kiểm tra cache
    if use_cache and text in _translation_cache:
        return _translation_cache[text]
    
    if not HAS_TRANSLATOR or _translator is None:
        print(f"   ⚠️ Translator not available, using original: {text[:50]}...")
        return text
    
    try:
        # Tạo translator mới cho target là en
        en_translator = GoogleTranslator(source='vi', target='en')
        result = en_translator.translate(text)
        if use_cache:
            _translation_cache[text] = result
        return result
    except Exception as e:
        print(f"   ⚠️ Translation error: {e}, using original")
        return text


def translate(text: str, source: str = 'en', target: str = 'vi', use_cache: bool = True) -> str:
    """
    Dịch văn bản giữa các ngôn ngữ
    
    Args:
        text: Văn bản cần dịch
        source: Ngôn ngữ nguồn (mặc định: 'en')
        target: Ngôn ngữ đích (mặc định: 'vi')
        use_cache: Sử dụng cache
    
    Returns:
        str: Văn bản đã dịch
    """
    if not text:
        return text
    
    # Nếu không cần dịch
    if source == target:
        return text
    
    cache_key = f"{source}_{target}_{text}"
    if use_cache and cache_key in _translation_cache:
        return _translation_cache[cache_key]
    
    if not HAS_TRANSLATOR:
        print(f"   ⚠️ Translator not available, using original")
        return text
    
    try:
        translator = GoogleTranslator(source=source, target=target)
        result = translator.translate(text)
        if use_cache:
            _translation_cache[cache_key] = result
        return result
    except Exception as e:
        print(f"   ⚠️ Translation error: {e}, using original")
        return text


def clear_cache():
    """Xóa cache dịch"""
    global _translation_cache
    _translation_cache = {}
    print("🗑️ Translation cache cleared")


def get_cache_size() -> int:
    """Lấy số lượng cache đang lưu"""
    return len(_translation_cache)


def is_translator_available() -> bool:
    """Kiểm tra translator có sẵn sàng không"""
    return HAS_TRANSLATOR and _translator is not None


def test_translator():
    """Test translator"""
    print("\n🧪 TEST TRANSLATOR")
    print("=" * 50)
    
    test_texts = [
        "Critical indoor-environment anomaly detected in Room A101.",
        "Please follow staff guidance and move calmly to the safe waiting area.",
        "Emergency evacuation in progress."
    ]
    
    print(f"📝 Translator available: {is_translator_available()}")
    print()
    
    for text in test_texts:
        translated = translate_to_vietnamese(text)
        print(f"EN: {text}")
        print(f"VI: {translated}")
        print()


if __name__ == "__main__":
    test_translator()