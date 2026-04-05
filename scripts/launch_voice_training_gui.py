#!/usr/bin/env python3
"""
Launch Monica Voice Training GUI with Recording and Training Capabilities

This GUI lets you:
1. Record voice samples for training
2. Monitor recording progress
3. Start the optimized training process (22 epochs, FP16, memory-optimized)
4. View training results

Usage:
    python launch_voice_training_gui.py
"""

import sys
import os
from pathlib import Path

# Fix Windows console encoding issues
if sys.platform == 'win32':
    # Set UTF-8 encoding for stdout/stderr
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    # Set console to UTF-8 mode
    os.system('chcp 65001 >nul 2>&1')

def main():
    # Add monica_ai to Python path
    monica_ai_path = Path(__file__).parent / "monica_ai"
    if monica_ai_path.exists():
        sys.path.insert(0, str(monica_ai_path))

    try:
        # Import and run the voice recorder GUI
        from voice_training.record_voice import main as record_main

        print("=" * 80)
        print("MONICA VOICE TRAINING GUI")
        print("=" * 80)
        print("\nFeatures:")
        print("   Record voice samples")
        print("  [CHART] Track progress")
        print("  [ROCKET] Start optimized training (22 epochs, FP16)")
        print("  [OK] Memory-optimized for 8GB VRAM")
        print("\nTraining optimizations enabled:")
        print("  • Mixed precision (FP16)")
        print("  • Gradient accumulation (4x)")
        print("  • Gradient checkpointing")
        print("  • Aggressive memory management")
        print("\n" + "=" * 80)
        print()

        # Launch the GUI
        record_main()

    except ImportError as e:
        print(f"\n[X] Error: Could not import voice training module")
        print(f"Details: {e}")
        print("\nPlease ensure monica_ai/voice_training/record_voice.py exists")
        sys.exit(1)
    except Exception as e:
        print(f"\n[X] Error starting voice training GUI: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
