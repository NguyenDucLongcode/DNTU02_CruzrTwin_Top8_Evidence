import time
import numpy as np
from src.ai.detector import detect_anomaly

def main():
    print("=" * 60)
    print("BENCHMARKING DETECTOR INFERENCE LATENCY")
    print("=" * 60)
    
    test_sensor = {
        "temperature": 25.0,
        "humidity": 60.0,
        "smoke": 50.0,
        "co2": 400.0,
        "power": 50.0
    }
    
    # Warmup
    for _ in range(10):
        detect_anomaly(test_sensor)
        
    num_runs = 1000
    latencies = []
    
    for _ in range(num_runs):
        start_time = time.perf_counter()
        detect_anomaly(test_sensor)
        end_time = time.perf_counter()
        # Convert to milliseconds
        latencies.append((end_time - start_time) * 1000.0)
        
    latencies = np.array(latencies)
    
    print(f"Total Runs:    {num_runs}")
    print(f"Min Latency:   {np.min(latencies):.4f} ms")
    print(f"Max Latency:   {np.max(latencies):.4f} ms")
    print(f"Average:       {np.mean(latencies):.4f} ms")
    print(f"Median:        {np.median(latencies):.4f} ms")
    print(f"95th Percent:  {np.percentile(latencies, 95):.4f} ms")
    print("=" * 60)

if __name__ == "__main__":
    main()
