import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone

def generate_dataset(output_path: str) -> dict:
    """
    Generate sensor data and save to CSV.
    Total: 1200 rows.
    Normal (label 0): 1000 rows.
    Anomaly (label 1): 200 rows (100 warning-like, 100 critical-like).
    """
    np.random.seed(42)
    
    # Base timestamp
    start_time = datetime(2026, 6, 8, 12, 0, 0, tzinfo=timezone.utc)
    
    # 1. Normal rows (1000 rows, label=0)
    num_normal = 1000
    normal_temp = np.random.uniform(22, 30, num_normal)
    normal_hum = np.random.uniform(45, 70, num_normal)
    normal_smoke = np.random.uniform(20, 80, num_normal)
    normal_co2 = np.random.uniform(350, 500, num_normal)
    normal_power = np.random.uniform(30, 80, num_normal)
    normal_labels = np.zeros(num_normal, dtype=int)
    
    # 2. Warning-like anomaly rows (100 rows, label=1)
    num_warning = 100
    warn_temp = np.random.uniform(31, 37, num_warning)
    warn_hum = np.random.uniform(30, 80, num_warning)
    warn_smoke = np.random.uniform(100, 250, num_warning)
    warn_co2 = np.random.uniform(600, 850, num_warning)
    warn_power = np.random.uniform(15, 120, num_warning)
    warn_labels = np.ones(num_warning, dtype=int)
    
    # 3. Critical-like anomaly rows (100 rows, label=1)
    num_critical = 100
    crit_temp = np.random.uniform(38, 50, num_critical)
    crit_hum = np.random.uniform(10, 25, num_critical)
    crit_smoke = np.random.uniform(300, 500, num_critical)
    crit_co2 = np.random.uniform(900, 1200, num_critical)
    crit_power = np.random.uniform(5, 15, num_critical)
    crit_labels = np.ones(num_critical, dtype=int)
    
    # Combine
    temp = np.concatenate([normal_temp, warn_temp, crit_temp])
    hum = np.concatenate([normal_hum, warn_hum, crit_hum])
    smoke = np.concatenate([normal_smoke, warn_smoke, crit_smoke])
    co2 = np.concatenate([normal_co2, warn_co2, crit_co2])
    power = np.concatenate([normal_power, warn_power, crit_power])
    labels = np.concatenate([normal_labels, warn_labels, crit_labels])
    
    total_rows = num_normal + num_warning + num_critical
    
    # Timestamps
    timestamps = []
    for i in range(total_rows):
        t = start_time + timedelta(seconds=i * 10)
        timestamps.append(t.isoformat(timespec="seconds").replace("+00:00", "Z"))
        
    df = pd.DataFrame({
        "timestamp": timestamps,
        "temperature": temp,
        "humidity": hum,
        "smoke": smoke,
        "co2": co2,
        "power": power,
        "label": labels
    })
    
    # Shuffle or keep order? Keeping normal, then warnings, then criticals is fine, 
    # but let's make sure it is saved in a structured way.
    # The requirement didn't specify shuffling, let's keep it sorted by timestamp.
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    
    return {
        "output_path": output_path,
        "normal_rows": num_normal,
        "anomaly_rows": num_warning + num_critical,
        "warning_like": num_warning,
        "critical_like": num_critical,
        "total_rows": total_rows
    }
