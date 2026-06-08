import os
import sys
import importlib

def run_check():
    print("=" * 60)
    print("CHECKING ENVIRONMENT...")
    print("=" * 60)
    
    passed = True
    
    # 1. Python version check
    py_ver = sys.version_info
    print(f"Python Version: {sys.version.split()[0]}")
    if py_ver.major == 3 and py_ver.minor >= 10:
        print("-> Python version check: PASS")
    else:
        print("-> Python version check: FAIL (Requires Python >= 3.10)")
        passed = False
        
    # 2. Package checks
    required_packages = ["pandas", "numpy", "sklearn", "joblib", "pytest", "dotenv"]
    print("\nChecking imports:")
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"-> import {package}: PASS")
        except ImportError:
            print(f"-> import {package}: FAIL")
            passed = False
            
    # 3. File checks
    print("\nChecking root configuration files:")
    for filepath in ["requirements.txt", ".env.example"]:
        if os.path.isfile(filepath):
            print(f"-> File {filepath}: PASS")
        else:
            print(f"-> File {filepath}: FAIL")
            passed = False
            
    # 4. Folder creation checks
    required_folders = ["data", "models", "logs", "evidence"]
    print("\nChecking directory structures:")
    for folder in required_folders:
        try:
            os.makedirs(folder, exist_ok=True)
            print(f"-> Directory {folder}: PASS")
        except Exception as e:
            print(f"-> Directory {folder}: FAIL (Error: {e})")
            passed = False
            
    print("=" * 60)
    if passed:
        print("OVERALL RESULT: PASS")
        print("=" * 60)
        sys.exit(0)
    else:
        print("OVERALL RESULT: FAIL")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    run_check()
