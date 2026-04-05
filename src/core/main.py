# main.py (alternate entry point inside src/core/)
import sys
from pathlib import Path

# Add src/ and project root to path
_src_dir = str(Path(__file__).parent.parent)
_project_root = str(Path(__file__).parent.parent.parent)
for _p in [_src_dir, _project_root]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from core.monica_services_launcher import launch_monica

if __name__ == '__main__':
    launch_monica()