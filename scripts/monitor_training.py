#!/usr/bin/env python3
"""
Training Monitor - Checks if Monica's voice training is complete
"""

import time
import subprocess
import os
import sys

def check_training_running():
    """Check if training process is still running"""
    try:
        result = subprocess.run(
            ['tasklist'],
            capture_output=True,
            text=True
        )
        # Look for python processes using significant memory (>1GB = training)
        for line in result.stdout.split('\n'):
            if 'python.exe' in line.lower():
                parts = line.split()
                if len(parts) >= 5:
                    # Memory is in KB format like "2,270,848 K"
                    mem_str = parts[4].replace(',', '').replace('K', '')
                    try:
                        mem_kb = int(mem_str)
                        if mem_kb > 1000000:  # More than 1GB
                            return True
                    except ValueError:
                        continue
        return False
    except Exception as e:
        print(f"Error checking process: {e}")
        return None

def check_log_completion():
    """Check if training log shows completion"""
    log_file = "monica_training.log"
    if not os.path.exists(log_file):
        return False, "Log file not found"

    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            # Read last 50 lines
            lines = f.readlines()
            last_lines = ''.join(lines[-50:])

            if "TRAINING COMPLETE!" in last_lines:
                return True, "Training completed successfully!"

            # Check for epoch 50
            if "epoch: 50" in last_lines:
                return True, "Reached epoch 50 - training complete!"

            # Check for errors
            if "Error:" in last_lines or "Exception:" in last_lines:
                return True, "Training stopped with errors - check log"

            # Extract current epoch
            for line in reversed(lines[-20:]):
                if "epoch:" in line and "Going into epoch" not in line:
                    return False, line.strip()

        return False, "Training in progress"
    except Exception as e:
        return False, f"Error reading log: {e}"

def main():
    print("=" * 60)
    print("MONICA TRAINING MONITOR")
    print("=" * 60)
    print("\nMonitoring training status...")
    print("Press Ctrl+C to stop monitoring\n")

    check_interval = 60  # Check every 60 seconds

    try:
        while True:
            is_running = check_training_running()
            is_complete, status_msg = check_log_completion()

            timestamp = time.strftime("%H:%M:%S")

            if is_complete:
                print("\n" + "=" * 60)
                print(f"*** TRAINING COMPLETE! [{timestamp}] ***")
                print("=" * 60)
                print(f"\nStatus: {status_msg}")
                print("\nModel saved to: models/monica_finetuned/1986/save/")
                print("\nCheck results with:")
                print("  tail -50 monica_training.log")
                print("\nOr view detailed stats:")
                print("  type models\\monica_finetuned\\1986\\train_log.txt")
                print("\n" + "=" * 60)

                # Play a beep sound
                print('\a')  # System beep
                break

            if is_running is False:
                print(f"\n[{timestamp}] WARNING: Training process not detected")
                print("Either training completed or stopped unexpectedly")
                print("Check the log file:")
                print("  tail -30 monica_training.log")
                break

            print(f"[{timestamp}] Training in progress - {status_msg}")

            time.sleep(check_interval)

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")
        print("Training is still running in the background")
        print("\nTo check status manually:")
        print("  tail -20 monica_training.log")

if __name__ == "__main__":
    main()
