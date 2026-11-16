import psutil
import time
from datetime import datetime
import pandas as pd

def record_metrics(frame_start, frame_number):
    """
    Record the metric per frame
    """
    # Treatment time
    frame_time = time.time() - frame_start
    fps = 1 / frame_time if frame_time > 0 else 0
    # System Metrics
    cpu = psutil.cpu_percent()
    memory = psutil.virtual_memory().percent
    return (datetime.now(), frame_time, cpu, memory, frame_number)

def save_report(video_benchmark_metrics, start_time):
    """
    Calculate the mean of metrics properties
    """
    total_time = time.time() - start_time
    df = pd.DataFrame(video_benchmark_metrics)
    
    # Mean estimation
    avg_fps = 1 / df['frame_times'].mean()
    avg_cpu = df['cpu_usage'].mean()
    avg_mem = df['memory_usage'].mean()
    
    # Price estimation
    cost_per_hour = 0.50  # $ par heure pour un instance type
    cost_per_minute = (cost_per_hour / 60) * (total_time / 60)
    
    # Saving results
    # with open("benchmark_report.txt", "w") as f:
    #     f.write(f"=== BENCHMARK REPORT ===\n")
    #     f.write(f"Durée totale: {total_time:.2f} secondes\n")
    #     f.write(f"FPS moyen: {avg_fps:.2f}\n")
    #     f.write(f"CPU moyen: {avg_cpu:.2f}%\n")
    #     f.write(f"Mémoire moyenne: {avg_mem:.2f}%\n")
    #     f.write(f"Coût estimé: ${cost_per_minute:.4f}\n")
    #     f.write(f"\nDétails par frame:\n")
    #     df.to_string(f, index=False)
    # df.to_csv("benchmark_data.csv", index=False)
    print("Rapport de benchmark sauvegardé.")