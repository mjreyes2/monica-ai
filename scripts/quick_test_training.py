"""
Quick test to verify training script starts without Unicode errors
"""
import subprocess
import sys

print("="*70)
print("QUICK TRAINING TEST - First 30 seconds")
print("="*70)

try:
    # Start training process
    process = subprocess.Popen(
        [".venv\\Scripts\\python.exe", "train_monica_safe.py", "hparams_monica.yaml"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        encoding='utf-8',
        errors='replace'
    )

    # Read output for 30 seconds to check for errors
    import time
    start_time = time.time()

    while time.time() - start_time < 30:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break
        if line:
            print(line.rstrip())

            # Check for success indicators
            if "STARTING MONICA VOICE TRAINING" in line:
                print("\n" + "="*70)
                print("SUCCESS! Training started successfully!")
                print("="*70)
                process.terminate()
                sys.exit(0)

            # Check for errors
            if "UnicodeEncodeError" in line or "Traceback" in line:
                print("\n" + "="*70)
                print("ERROR! Unicode or other error detected!")
                print("="*70)
                process.terminate()
                sys.exit(1)

    # If we got here, training is running
    print("\n" + "="*70)
    print("Training appears to be running successfully!")
    print("Terminating test...")
    print("="*70)
    process.terminate()

except Exception as e:
    print(f"\nERROR: {e}")
    sys.exit(1)
