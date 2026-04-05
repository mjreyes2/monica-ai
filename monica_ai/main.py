#!/usr/bin/env python3
"""
Monica AI - Main Entry Point
Run this file to start Monica AI.
"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.app import main

if __name__ == "__main__":
    main()
