import os
import sys
import random
import argparse
import pandas as pd
from datetime import datetime, timedelta, timezone

# Ensure project root is in path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

def generate_sensor_data(days=30, interval_minutes=5, output_path="data/sensor_data.csv"):
    print("=" * 60)
    print(f"GENERATING {days}-DAY SENSOR DATASET ({interval_minutes}-minute interval)")
    print("=" * 60)

    # Calculate steps
    total_steps = int(days * 24 * (60 / interval_minutes))
    
    # Base configuration: end at 2026-06-08 12:00:00 UTC
    end_time = datetime(2026, 6, 8, 12, 0, 0, tzinfo=timezone.utc)
    start_time = end_time - timedelta(days=days)
    
    zone_id = "DNTU_ROOM_A101"
    random.seed(42)

    rows = []
    
    # State tracking for anomaly generation to ensure contiguous blocks
    anomaly_state = "normal"  # normal, warning, critical
    anomaly_timer = 0
    scenario_counter = {"warning": 0, "critical": 0}
    current_scenario_id = ""

    for i in range(total_steps):
        current_time = start_time + timedelta(minutes=i * interval_minutes)
        timestamp_str = current_time.isoformat(timespec="seconds").replace("+00:00", "Z")
        hour = current_time.hour
        day_of_week = current_time.weekday()
        is_weekend = day_of_week >= 5

        # If currently in an anomaly, decrement timer
        if anomaly_timer > 0:
            anomaly_timer -= 1
            if anomaly_timer == 0:
                anomaly_state = "normal"
                current_scenario_id = ""

        # If normal, check if we should trigger a new anomaly event
        if anomaly_state == "normal":
            # Don't trigger right at the very start or end
            if 50 < i < total_steps - 50:
                # Trigger a critical event with small probability
                # Duration: 3 to 5 steps (15-25 mins)
                if random.random() < 0.0025:
                    anomaly_state = "critical"
                    anomaly_timer = random.randint(3, 5)
                    scenario_counter["critical"] += 1
                    current_scenario_id = f"SCN_CRITICAL_{scenario_counter['critical']:03d}"
                # Trigger a warning event
                # Duration: 5 to 8 steps (25-40 mins)
                elif random.random() < 0.0085:
                    anomaly_state = "warning"
                    anomaly_timer = random.randint(5, 8)
                    scenario_counter["warning"] += 1
                    current_scenario_id = f"SCN_WARNING_{scenario_counter['warning']:03d}"

        # Generate base values based on state and temporal factors
        if anomaly_state == "normal":
            # With 35% probability, generate a uniform normal point to cover the feature space
            is_uniform_mix = random.random() < 0.35
            
            if is_uniform_mix:
                base_temp = random.uniform(22.5, 26.8)
                base_hum = random.uniform(45.5, 68.5)
                base_co2 = random.uniform(370.0, 515.0)
                base_energy = random.uniform(22.0, 84.0)
                base_smoke_raw = random.uniform(15.0, 48.0)
            else:
                if is_weekend:
                    # Weekend - low standby activity
                    base_temp = 22.5 + random.uniform(0.5, 1.5)
                    base_hum = 60.0 + random.uniform(-3.0, 4.0)
                    base_co2 = 390.0 + random.uniform(-10.0, 20.0)
                    base_energy = 28.0 + random.uniform(-3.0, 5.0)
                    base_smoke_raw = 22.0 + random.uniform(-5.0, 15.0)
                else:
                    # Weekday
                    if 22 <= hour or hour < 6:
                        # Night phase
                        base_temp = 22.0 + random.uniform(0.5, 1.5)
                        base_hum = 65.0 + random.uniform(-2.0, 4.0)
                        base_co2 = 380.0 + random.uniform(-10.0, 20.0)
                        base_energy = 25.0 + random.uniform(-3.0, 5.0)
                        base_smoke_raw = 20.0 + random.uniform(-5.0, 15.0)
                    elif 8 <= hour < 18:
                        # Working hours
                        base_temp = 25.0 + random.uniform(0.5, 2.0)
                        base_hum = 48.0 + random.uniform(-3.0, 5.0)
                        base_co2 = 480.0 + random.uniform(-20.0, 40.0)
                        base_energy = 75.0 + random.uniform(-5.0, 10.0)
                        base_smoke_raw = 30.0 + random.uniform(-8.0, 20.0)
                    else:
                        # Transition
                        base_temp = 23.5 + random.uniform(0.5, 1.5)
                        base_hum = 55.0 + random.uniform(-3.0, 4.0)
                        base_co2 = 420.0 + random.uniform(-15.0, 25.0)
                        base_energy = 45.0 + random.uniform(-4.0, 6.0)
                        base_smoke_raw = 25.0 + random.uniform(-6.0, 15.0)

            expected_label = "normal"
            scenario_id = f"SCN_NORMAL_{i+1:03d}"
            smoke_status = 0
            raw_smoke_value = base_smoke_raw

        elif anomaly_state == "warning":
            # Warning values (elevated temperature, co2, energy, smoke raw, but smoke status=0)
            base_temp = 32.2 + random.uniform(-0.6, 0.8)
            base_hum = 58.0 + random.uniform(-3.0, 3.0)
            base_co2 = 740.0 + random.uniform(-30.0, 50.0)
            base_energy = 95.0 + random.uniform(-6.0, 10.0)
            base_smoke_raw = 150.0 + random.uniform(-15.0, 20.0)
            
            expected_label = "warning"
            scenario_id = current_scenario_id
            smoke_status = 0
            raw_smoke_value = base_smoke_raw

        elif anomaly_state == "critical":
            # Critical values (very high temperature, low humidity, high co2, high energy, smoke status=1)
            base_temp = 42.5 + random.uniform(-1.5, 2.0)
            base_hum = 18.0 + random.uniform(-3.0, 3.0)
            base_co2 = 1020.0 + random.uniform(-40.0, 80.0)
            base_energy = 520.0 + random.uniform(-80.0, 150.0)
            base_smoke_raw = 380.0 + random.uniform(-30.0, 50.0)
            
            expected_label = "critical"
            scenario_id = current_scenario_id
            smoke_status = 1
            raw_smoke_value = base_smoke_raw

        rows.append({
            "timestamp": timestamp_str,
            "zone_id": zone_id,
            "temperature": round(base_temp, 2),
            "humidity": round(base_hum, 2),
            "co2": round(base_co2, 2),
            "smoke_status": smoke_status,
            "raw_smoke_value": round(raw_smoke_value, 2),
            "energy_consumption": round(base_energy, 2),
            "expected_label": expected_label,
            "scenario_id": scenario_id
        })

    df = pd.DataFrame(rows)

    # Sanity checks
    assert not (df["humidity"] < 0).any() and not (df["humidity"] > 100).any(), "Humidity range violated!"
    assert not (df["co2"] < 0).any(), "CO2 negative!"
    assert not (df["energy_consumption"] < 0).any(), "Energy consumption negative!"
    assert df["timestamp"].is_unique, "Timestamps not unique!"
    assert len(df) == total_steps, f"Rows count is {len(df)}, expected {total_steps}!"
    assert not (df["smoke_status"].isin([0, 1]).all() == False), "smoke_status not binary!"

    # Create directories
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)

    total = len(df)
    normal_cnt = (df["expected_label"] == "normal").sum()
    warning_cnt = (df["expected_label"] == "warning").sum()
    critical_cnt = (df["expected_label"] == "critical").sum()

    print(f"Total Rows Generated: {total}")
    print(f"Normal Rows: {normal_cnt} ({normal_cnt/total*100:.2f}%)")
    print(f"Warning Rows: {warning_cnt} ({warning_cnt/total*100:.2f}%)")
    print(f"Critical Rows: {critical_cnt} ({critical_cnt/total*100:.2f}%)")
    print(f"Saved dataset to {output_path}")
    print("=" * 60)
    
    return {
        "output_path": output_path,
        "total_rows": total,
        "normal_rows": normal_cnt,
        "warning_rows": warning_cnt,
        "critical_rows": critical_cnt
    }

def main():
    parser = argparse.ArgumentParser(description="Generate 1-month sensor dataset")
    parser.add_argument("--days", type=int, default=30, help="Number of days to generate")
    parser.add_argument("--interval-minutes", type=int, default=5, help="Sampling interval in minutes")
    parser.add_argument("--output", type=str, default="data/sensor_data.csv", help="Output CSV path")
    args = parser.parse_args()
    
    generate_sensor_data(
        days=args.days,
        interval_minutes=args.interval_minutes,
        output_path=args.output
    )

if __name__ == "__main__":
    main()
