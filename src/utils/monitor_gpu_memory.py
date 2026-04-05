#!/usr/bin/env python3
"""
GPU Memory Monitor for Monica Training
Run this in a separate terminal while training to watch memory usage.

Usage:
    python monitor_gpu_memory.py
"""

import time
import subprocess
import sys
from datetime import datetime

def get_gpu_memory():
    """Get GPU memory usage using nvidia-smi."""
    try:
        result = subprocess.check_output(
            [
                'nvidia-smi',
                '--query-gpu=index,name,memory.used,memory.total,utilization.gpu,temperature.gpu',
                '--format=csv,noheader,nounits'
            ],
            encoding='utf-8'
        )
        return result.strip()
    except Exception as e:
        return f"Error getting GPU info: {e}"

def main():
    print("=" * 80)
    print("GPU Memory Monitor for Monica Voice Training")
    print("=" * 80)
    print("\nPress Ctrl+C to stop monitoring\n")

    try:
        while True:
            timestamp = datetime.now().strftime("%H:%M:%S")
            gpu_info = get_gpu_memory()

            # Clear screen (optional)
            # print("\033[2J\033[H", end="")

            print(f"[{timestamp}]")
            print("-" * 80)

            if "Error" not in gpu_info:
                lines = gpu_info.split('\n')
                for line in lines:
                    parts = line.split(',')
                    if len(parts) >= 6:
                        gpu_id, gpu_name, mem_used, mem_total, gpu_util, temp = [p.strip() for p in parts]
                        mem_used_gb = float(mem_used) / 1024
                        mem_total_gb = float(mem_total) / 1024
                        mem_percent = (float(mem_used) / float(mem_total)) * 100

                        print(f"GPU {gpu_id}: {gpu_name}")
                        print(f"  Memory: {mem_used_gb:.2f} GB / {mem_total_gb:.2f} GB ({mem_percent:.1f}%)")
                        print(f"  Utilization: {gpu_util}%")
                        print(f"  Temperature: {temp}°C")

                        # Warning if memory is high
                        if mem_percent > 90:
                            print("  [WARN]  WARNING: Memory usage >90%!")
                        elif mem_percent > 80:
                            print("  [WARN]  High memory usage")

                        # Create a visual memory bar
                        bar_length = 50
                        filled = int(bar_length * mem_percent / 100)
                        bar = '█' * filled + '░' * (bar_length - filled)
                        print(f"  [{bar}]")
            else:
                print(gpu_info)

            print("-" * 80)
            print()

            # Update every 2 seconds
            time.sleep(2)

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")
        sys.exit(0)

if __name__ == "__main__":
    main()
