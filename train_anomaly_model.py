import subprocess
import sys

def main():
    result = subprocess.run([sys.executable, "scripts/ai/train_anomaly_model.py"])
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
