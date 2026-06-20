import os
import sys
import time

# Ensure project root is in path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.orchestration.pipeline import process_sensor_event

def main():
    print("=" * 60)
    print("RUNNING REAL-TIME EVENT STREAM SIMULATION...")
    print("=" * 60)
    
    # 5 simulated rooms events
    events = [
        {
            "room": "Room 101",
            "data": {"temperature": 24.5, "humidity": 55.0, "smoke": 35.0, "co2": 420.0, "power": 45.0}
        },
        {
            "room": "Room 102",
            "data": {"temperature": 33.2, "humidity": 62.0, "smoke": 140.0, "co2": 720.0, "power": 85.0}
        },
        {
            "room": "Room 103",
            "data": {"temperature": 25.1, "humidity": 50.0, "smoke": 30.0, "co2": 390.0, "power": 52.0}
        },
        {
            "room": "Room 104",
            "data": {"temperature": 44.8, "humidity": 12.0, "smoke": 450.0, "co2": 1100.0, "power": 6.0}
        },
        {
            "room": "Room 105",
            "data": {"temperature": 23.9, "humidity": 58.0, "smoke": 40.0, "co2": 410.0, "power": 48.0}
        }
    ]
    
    for ev in events:
        room_name = ev["room"]
        sensor_data = ev["data"]
        
        print(f"\n[STREAM] Incoming sensor reading from: {room_name}")
        print(f"         Data: {sensor_data}")
        
        res = process_sensor_event(sensor_data)
        ai_res = res["ai_result"]
        alert = res["alert_event"]
        
        print(f"         AI Decision:   {ai_res['predicted_level'].upper()} (Anomaly Score: {ai_res['anomaly_score']:.4f})")
        if alert:
            print(f"         ALERT CREATED: Status={alert['status']} | Severity={alert['level']} | Action={alert['recommended_action']}")
            print(f"         Message:       \"{alert['message']}\"")
        else:
            print(f"         ALERT:         No alert generated.")
            
        time.sleep(0.5)
        
    print("\n" + "=" * 60)
    print("SIMULATION COMPLETED.")
    print("=" * 60)

if __name__ == "__main__":
    main()
