import subprocess
import sys

def main():
    result = subprocess.run([sys.executable, "scripts/ai/generate_sensor_data.py"])
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
