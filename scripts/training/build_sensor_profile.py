import os
import sys
import json
import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timezone

def calculate_stats(series: pd.Series) -> dict:
    """
    Calculate statistics for a pandas Series.
    """
    if series.empty:
        return {}
        
    desc = series.describe()
    p05 = float(np.percentile(series, 5))
    p25 = float(np.percentile(series, 25))
    p75 = float(np.percentile(series, 75))
    p90 = float(np.percentile(series, 90))
    p95 = float(np.percentile(series, 95))
    p99 = float(np.percentile(series, 99))
    iqr = p75 - p25

    mean_val = float(desc["mean"])
    std_val = float(desc["std"]) if not pd.isna(desc["std"]) else 0.0
    min_val = float(desc["min"])
    max_val = float(desc["max"])
    median_val = float(np.median(series))

    # Avoid zero std issues
    std_adj = max(std_val, 1.0)

    # Dynamic Threshold Rules based on normal rows' statistics
    name = series.name
    if name == "temperature":
        normal_low = mean_val - 2.0 * std_adj
        normal_high = mean_val + 2.0 * std_adj
        warning_low = mean_val - 3.5 * std_adj
        warning_high = mean_val + 4.5 * std_adj
        strong_risk_high = mean_val + 6.0 * std_adj
        strong_risk_low = mean_val - 5.0 * std_adj
        critical_low = mean_val - 5.0 * std_adj
        critical_high = mean_val + 8.0 * std_adj
    elif name == "co2":
        normal_low = mean_val - 2.0 * std_adj
        normal_high = mean_val + 2.0 * std_adj
        warning_low = mean_val - 3.0 * std_adj
        warning_high = mean_val + 4.5 * std_adj
        strong_risk_high = mean_val + 10.0 * std_adj
        strong_risk_low = mean_val - 4.0 * std_adj
        critical_low = mean_val - 4.0 * std_adj
        critical_high = mean_val + 11.0 * std_adj
    elif name == "energy_consumption":
        normal_low = max(15.0, mean_val - 1.8 * std_adj)
        normal_high = mean_val + 1.8 * std_adj
        warning_low = max(10.0, mean_val - 2.2 * std_adj)
        warning_high = mean_val + 2.8 * std_adj
        strong_risk_low = 10.0
        strong_risk_high = mean_val + 3.0 * std_adj
        critical_low = 10.0
        critical_high = mean_val + 4.5 * std_adj
    elif name == "raw_smoke_value" or name == "smoke":
        normal_low = 0.0
        normal_high = mean_val + 2.5 * std_adj
        warning_low = 0.0
        warning_high = mean_val + 6.0 * std_adj
        strong_risk_low = 0.0
        strong_risk_high = mean_val + 20.0 * std_adj
        critical_low = 0.0
        critical_high = mean_val + 24.0 * std_adj
    else:
        # Default fallback rules (e.g. humidity, smoke_status)
        normal_low = max(0.0, mean_val - 2.0 * std_adj)
        normal_high = min(100.0, mean_val + 2.0 * std_adj)
        warning_low = max(0.0, mean_val - 3.0 * std_adj)
        warning_high = min(100.0, mean_val + 3.0 * std_adj)
        strong_risk_low = max(0.0, mean_val - 4.0 * std_adj)
        strong_risk_high = min(100.0, mean_val + 4.0 * std_adj)
        critical_low = max(0.0, mean_val - 4.5 * std_adj)
        critical_high = min(100.0, mean_val + 4.5 * std_adj)

    return {
        "min": min_val,
        "max": max_val,
        "mean": mean_val,
        "std": std_val,
        "median": median_val,
        "p05": p05,
        "p25": p25,
        "p75": p75,
        "p90": p90,
        "p95": p95,
        "p99": p99,
        "iqr": iqr,
        "normal_low": normal_low,
        "normal_high": normal_high,
        "warning_low": warning_low,
        "warning_high": warning_high,
        "strong_risk_low": strong_risk_low,
        "strong_risk_high": strong_risk_high,
        "critical_low": critical_low,
        "critical_high": critical_high
    }

def main():
    parser = argparse.ArgumentParser(description="Build sensor baseline profile from dataset")
    parser.add_argument("--input", type=str, default="data/sensor_data.csv", help="Input CSV path")
    parser.add_argument("--output", type=str, default="models/sensor_profile.json", help="Output JSON path")
    args = parser.parse_args()

    print("=" * 60)
    print("BUILDING SENSOR BASELINE PROFILE")
    print("=" * 60)

    csv_path = args.input
    profile_path = args.output
        
    print(f"Reading CSV from: {csv_path}")
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} does not exist!")
        sys.exit(1)

    df = pd.read_csv(csv_path)

    if "power" in df.columns and "energy_consumption" not in df.columns:
        df = df.rename(columns={"power": "energy_consumption"})
    if "smoke" in df.columns and "smoke_status" not in df.columns:
        df = df.rename(columns={"smoke": "smoke_status"})

    if "expected_label" not in df.columns:
        if "label" in df.columns:
            df["expected_label"] = df["label"].map({0: "normal", 1: "warning"})
        else:
            df["expected_label"] = "normal"
            
    if "raw_smoke_value" not in df.columns:
        df["raw_smoke_value"] = df["smoke_status"]

    df["dt"] = pd.to_datetime(df["timestamp"])
    df["hour"] = df["dt"].dt.hour
    df["weekday"] = df["dt"].dt.weekday
    df["day_type"] = df["weekday"].apply(lambda w: "weekend" if w >= 5 else "working_day")

    normal_df = df[df["expected_label"] == "normal"].copy()
    
    total_rows = len(df)
    normal_cnt = len(normal_df)
    warning_cnt = (df["expected_label"] == "warning").sum()
    critical_cnt = (df["expected_label"] == "critical").sum()

    print(f"Total rows in dataset: {total_rows}")
    print(f"Normal rows for baseline: {normal_cnt}")

    canonical_fields = ["temperature", "humidity", "co2", "smoke_status", "raw_smoke_value", "energy_consumption"]

    global_stats = {}
    for field in canonical_fields:
        if field in normal_df.columns:
            global_stats[field] = calculate_stats(normal_df[field])

    hourly_baseline = {}
    for hour in range(24):
        hour_df = normal_df[normal_df["hour"] == hour]
        hourly_baseline[str(hour)] = {}
        for field in canonical_fields:
            if field in normal_df.columns:
                hour_field_series = hour_df[field] if not hour_df.empty else normal_df[field]
                stats = calculate_stats(hour_field_series)
                stats["sample_count"] = len(hour_df)
                hourly_baseline[str(hour)][field] = stats

    day_type_baseline = {}
    for dt_name in ["working_day", "weekend"]:
        dt_df = normal_df[normal_df["day_type"] == dt_name]
        day_type_baseline[dt_name] = {}
        for field in canonical_fields:
            if field in normal_df.columns:
                dt_field_series = dt_df[field] if not dt_df.empty else normal_df[field]
                stats = calculate_stats(dt_field_series)
                stats["sample_count"] = len(dt_df)
                day_type_baseline[dt_name][field] = stats

    # Time coverage calculations
    time_coverage_hours = 0.0
    time_coverage_days = 0.0
    if not df.empty:
        dt_min = df["dt"].min()
        dt_max = df["dt"].max()
        duration_td = dt_max - dt_min
        time_coverage_hours = duration_td.total_seconds() / 3600.0
        time_coverage_days = round(time_coverage_hours / 24.0, 2)
        
    profile = {
        "metadata": {
            "version": "1.1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "source_csv": csv_path,
            "row_count": total_rows,
            "normal_row_count": int(normal_cnt),
            "warning_row_count": int(warning_cnt),
            "critical_row_count": int(critical_cnt),
            "time_coverage_days": time_coverage_days,
            "time_coverage_hours": time_coverage_hours,
            "sampling_interval_minutes": 5,
            "canonical_fields": canonical_fields,
            "label_field": "expected_label"
        },
        "global_statistics": global_stats,
        "hourly_baseline": hourly_baseline,
        "day_type_baseline": day_type_baseline,
        "safety_guardrails": {
            "temperature": {
                "critical_floor": 37.0,
                "warning_floor": 30.0,
                "strong_risk_floor": 32.0,
                "source": "safety_guardrail",
                "description": "Minimum absolute temperature floor for critical/warning escalation, preventing over-escalation from tight hourly standard deviations."
            },
            "co2": {
                "critical_floor": 900.0,
                "warning_floor": 600.0,
                "strong_risk_floor": 800.0,
                "source": "safety_guardrail",
                "description": "Minimum absolute CO2 floor for critical/warning escalation."
            },
            "raw_smoke_value": {
                "critical_floor": 250.0,
                "warning_floor": 100.0,
                "strong_risk_floor": 200.0,
                "source": "safety_guardrail",
                "description": "Minimum absolute raw smoke value floor for critical/warning escalation."
            },
            "energy_consumption": {
                "strong_risk_floor": 110.0,
                "source": "safety_guardrail",
                "description": "Minimum absolute energy consumption floor for strong risk escalation."
            }
        },
        "notes": [
            "This profile is built strictly from normal rows (expected_label == 'normal') to establish the normal baseline.",
            "Warning and critical rows are excluded from baseline calculations and are reserved for validation/evaluation.",
            "Rebuild this profile when the underlying CSV grows (e.g. to 48h, 72h, 30 days, or more)."
        ]
    }

    os.makedirs(os.path.dirname(profile_path) or ".", exist_ok=True)
    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)

    print(f"Successfully saved sensor baseline profile to {profile_path}")

if __name__ == "__main__":
    main()
