import json
import os
import subprocess
import threading

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SIMULATION_JSON_PATH = os.path.join(ROOT_DIR, "docker", "simulator", "config", "simulation.json")
STATE_FILE_PATH = os.path.join(ROOT_DIR, "docker", "simulator", "config", "room_states.json")

ROOMS = ["L1-A1", "L1-A2", "L1-A3", "L1-A4", "L1-A5"]
ROOM_TO_CODE = {f"L1-A{index}": f"A{100 + index}" for index in range(1, 13)}
CODE_TO_ROOM = {code: room for room, code in ROOM_TO_CODE.items()}

def normalize_room_id(room_id: str) -> str:
    return ROOM_TO_CODE.get(room_id, CODE_TO_ROOM.get(room_id, room_id))

def resolve_room_state(room_id: str) -> str:
    states = get_room_states()
    return states.get(room_id, states.get(normalize_room_id(room_id), "empty"))

def get_room_states():
    if os.path.exists(STATE_FILE_PATH):
        try:
            with open(STATE_FILE_PATH, 'r') as f:
                return json.load(f)
        except:
            pass
    return {room: "empty" for room in ROOMS}

def save_room_states(states):
    with open(STATE_FILE_PATH, 'w') as f:
        json.dump(states, f)

def generate_simulation_json():
    states = get_room_states()
    
    config = {
        "domain": {
            "service": "cruzrtwin",
            "subservice": "/asean/buildings"
        },
        "contextBroker": {
            "protocol": "http",
            "host": "orion",
            "port": 1026,
            "ngsiVersion": "2.0"
        },
        "mqtt": {
            "protocol": "mqtt",
            "host": "mosquitto",
            "port": 1883
        },
        "entities": []
    }
    
    for room in ROOMS:
        state = resolve_room_state(room)
        
        # Mặc định (Empty / Phòng Trống)
        temp_func = "attribute-function-interpolator(module.exports = { result: Math.random() * (26 - 24) + 24 };)"
        smoke_func = "attribute-function-interpolator(module.exports = { result: 0 };)"
        co2_func = "attribute-function-interpolator(module.exports = { result: Math.random() * (450 - 400) + 400 };)"
        presence_func = "attribute-function-interpolator(module.exports = { result: 0 };)"
        
        if state == "active":
            temp_func = "attribute-function-interpolator(module.exports = { result: Math.random() * (28 - 25) + 25 };)"
            presence_func = "attribute-function-interpolator(module.exports = { result: 1 };)"
        elif state == "fire":
            temp_func = "attribute-function-interpolator(module.exports = { result: Math.random() * (85 - 60) + 60 };)"
            smoke_func = "attribute-function-interpolator(module.exports = { result: 1 };)"
            co2_func = "attribute-function-interpolator(module.exports = { result: Math.random() * (4000 - 1500) + 1500 };)"
            presence_func = "attribute-function-interpolator(module.exports = { result: 1 };)"
            
        config["entities"].extend([
            {
                "entity_name": f"Device:TEMP_{room}",
                "entity_type": "TemperatureSensor",
                "schedule": "*/5 * * * * *",
                "active": [
                    {"name": "temperature", "type": "Number", "value": temp_func},
                    {"name": "TimeInstant", "type": "DateTime", "value": "date-increment-interpolator({\"origin\": \"now\", \"increment\": 0})"}
                ]
            },
            {
                "entity_name": f"Device:SMOKE_{room}",
                "entity_type": "SmokeDetector",
                "schedule": "*/5 * * * * *",
                "active": [
                    {"name": "smoke_status", "type": "Number", "value": smoke_func},
                    {"name": "TimeInstant", "type": "DateTime", "value": "date-increment-interpolator({\"origin\": \"now\", \"increment\": 0})"}
                ]
            },
            {
                "entity_name": f"Device:AIR_{room}",
                "entity_type": "AirQualitySensor",
                "schedule": "*/5 * * * * *",
                "active": [
                    {"name": "co2", "type": "Number", "value": co2_func},
                    {"name": "TimeInstant", "type": "DateTime", "value": "date-increment-interpolator({\"origin\": \"now\", \"increment\": 0})"}
                ]
            },
            {
                "entity_name": f"Device:PRESENCE_{room}",
                "entity_type": "PresenceSensor",
                "schedule": "*/5 * * * * *",
                "active": [
                    {"name": "presence", "type": "Number", "value": presence_func},
                    {"name": "TimeInstant", "type": "DateTime", "value": "date-increment-interpolator({\"origin\": \"now\", \"increment\": 0})"}
                ]
            }
        ])
        
    with open(SIMULATION_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)

def set_room_state(room_id, state):
    states = get_room_states()
    states[room_id] = state
    save_room_states(states)
    
    generate_simulation_json()
    
    docker_dir = os.path.join(ROOT_DIR, "docker")
    print(f"[SIMULATOR] Restarting device-simulator container for {room_id} -> {state}...")
    subprocess.run(["docker", "restart", "device-simulator"], cwd=docker_dir)

# ==========================================
# Giao tiếp với Webhook API
# ==========================================

def simulate_fire_gradually(room_id="L1-A1", severity="large"):
    def run_simulation():
        set_room_state(room_id, "fire")
    threading.Thread(target=run_simulation, daemon=True).start()

def reset_simulation(room_id="L1-A1"):
    def run_reset():
        set_room_state(room_id, "empty")
    threading.Thread(target=run_reset, daemon=True).start()

def set_active_simulation(room_id="L1-A1"):
    def run_active():
        set_room_state(room_id, "active")
    threading.Thread(target=run_active, daemon=True).start()
