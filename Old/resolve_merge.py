import subprocess
import re
import sys

def run_cmd(cmd):
    print(f"Running: {cmd}")
    subprocess.run(cmd, shell=True, check=True)

# 1. Accept THEIRS for everything that doesn't affect our core AI/Pipeline logic
theirs_files = [
    "docker/tuya-bridge/Dockerfile",
    "docker/tuya-bridge/entrypoint.py",
    "docker/tuya2mqtt.yaml",
    "requirements.txt",
    "src/fiware/__init__.py",
    "src/iot/devices.py",
    "src/tuya/__init__.py",
    "src/tuya/commands.py",
    "src/tuya/config.py",
    "src/utils/mqtt_helper.py"
]

for f in theirs_files:
    run_cmd(f"git checkout --theirs {f}")

# 2. Accept OURS for our AI data
ours_files = [
    "data/replay_test_set/critical_001.json"
]

for f in ours_files:
    run_cmd(f"git checkout --ours {f}")

# 3. Manually fix .env.example (combine)
try:
    with open('.env.example', 'r', encoding='utf-8') as file:
        content = file.read()
    # Replace the conflict block with origin/main's block which is a superset
    content = re.sub(r'<<<<<<< HEAD.*?=======\n(.*?)\n>>>>>>> origin/main', r'\1', content, flags=re.DOTALL)
    with open('.env.example', 'w', encoding='utf-8') as file:
        file.write(content)
except Exception as e:
    print(f"Error fixing .env.example: {e}")

# 4. Manually fix docker-compose.yml
try:
    with open('docker/docker-compose.yml', 'r', encoding='utf-8') as file:
        content = file.read()
    # We want to keep BOTH dashboard-web and tuya-bridge
    content = re.sub(r'<<<<<<< HEAD\n(.*?)\n=======\n(.*?)\n>>>>>>> origin/main', r'\1\n\2', content, flags=re.DOTALL)
    with open('docker/docker-compose.yml', 'w', encoding='utf-8') as file:
        file.write(content)
except Exception as e:
    print(f"Error fixing docker-compose: {e}")

# 5. Manually fix src/fiware/entities/query.py
try:
    with open('src/fiware/entities/query.py', 'r', encoding='utf-8') as file:
        content = file.read()
    # Remove the conflict markers and keep just one get_entity_by_type
    content = re.sub(r'<<<<<<< HEAD\n=======\n\n\ndef get_entity_by_type\(.*?return entities\n>>>>>>> origin/main\n\n\n', r'', content, flags=re.DOTALL)
    with open('src/fiware/entities/query.py', 'w', encoding='utf-8') as file:
        file.write(content)
except Exception as e:
    print(f"Error fixing query.py: {e}")

print("Done resolving.")
