import os
import sys
import argparse

# Ensure project root is in path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from orchestration.pipeline import process_sensor_event

def get_interactive_input(prompt, default_val):
    val = input(f"{prompt} (Default: {default_val}): ").strip()
    if not val:
        return default_val
    try:
        return float(val)
    except ValueError:
        print("Invalid number. Using default value.")
        return default_val

def main():
    parser = argparse.ArgumentParser(description="Test custom sensor values on the AI + Rule Layer pipeline.")
    parser.add_argument("--temp", type=float, help="Room temperature")
    parser.add_argument("--humidity", type=float, help="Room humidity")
    parser.add_argument("--smoke", type=float, help="Smoke level")
    parser.add_argument("--co2", type=float, help="CO2 level")
    parser.add_argument("--power", type=float, help="Power value")
    
    args = parser.parse_args()
    
    # If no arguments are passed, use interactive mode
    if all(v is None for v in [args.temp, args.humidity, args.smoke, args.co2, args.power]):
        print("=" * 60)
        print("INTERACTIVE SENSOR TEST MODE")
        print("Enter sensor values to see AI detection and Alert Event outcomes.")
        print("=" * 60)
        temp = get_interactive_input("Enter temperature (e.g. 25 or 34 or 45)", 25.0)
        humidity = get_interactive_input("Enter humidity (e.g. 60 or 15)", 60.0)
        smoke = get_interactive_input("Enter smoke (e.g. 50 or 180 or 400)", 50.0)
        co2 = get_interactive_input("Enter CO2 (e.g. 400 or 750 or 1000)", 400.0)
        power = get_interactive_input("Enter power (e.g. 50 or 90 or 8)", 50.0)
    else:
        temp = args.temp if args.temp is not None else 25.0
        humidity = args.humidity if args.humidity is not None else 60.0
        smoke = args.smoke if args.smoke is not None else 50.0
        co2 = args.co2 if args.co2 is not None else 400.0
        power = args.power if args.power is not None else 50.0

    sensor_data = {
        "temperature": temp,
        "humidity": humidity,
        "smoke": smoke,
        "co2": co2,
        "power": power
    }
    
    print("\n" + "=" * 60)
    print("RUNNING PIPELINE FOR INPUT DATA:")
    print(f"  {sensor_data}")
    print("=" * 60)
    
    try:
        res = process_sensor_event(sensor_data)
        ai_res = res["ai_result"]
        alert = res["alert_event"]
        
        print(f"AI Detection outcome:")
        print(f"  Predicted Anomaly Flag: {ai_res['predicted_anomaly']} (0=normal, 1=anomaly)")
        print(f"  Anomaly Score:          {ai_res['anomaly_score']:.4f}")
        print(f"  Severity Level:         {ai_res['predicted_level'].upper()}")
        print(f"  Rationale:              \"{ai_res['rationale']}\"")
        if ai_res["rule_hits"]:
            print(f"  Triggered Rules:        {ai_res['rule_hits']}")
            
        print("\nAlert Event outcome:")
        if alert:
            print(f"  ALERT CREATED!")
            print(f"  Alert ID:           {alert['alert_id']}")
            print(f"  Level:              {alert['level'].upper()}")
            print(f"  Status:             {alert['status']}")
            print(f"  Recommended Action: {alert['recommended_action']}")
            print(f"  Message:            \"{alert['message']}\"")
        else:
            print("  No alert event created (Normal state).")
            
    except Exception as e:
        print(f"FAIL: Pipeline execution failed: {e}")
        
    print("=" * 60)

if __name__ == "__main__":
    main()
