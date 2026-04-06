"""
Monica AI - Laptop Setup Script
================================
Role: Control / Mind (orchestration, inference testing, config, dataset prep)
Run this once on the laptop after cloning the repo.

Usage:
    python scripts/setup_laptop.py
"""

import os
import sys
import subprocess
import platform

REQUIRED_PYTHON = (3, 10)
REPO_URL = "https://github.com/mjreyes2/monica-ai.git"
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Folders that must exist locally on the laptop for artifact storage
# Point these at your external drive or D:\ if available
ARTIFACT_BASE = "D:\\Monica_Datasets" if os.path.exists("D:\\") else os.path.join(os.path.expanduser("~"), "Monica_Datasets")
ARTIFACT_DIRS = [
    os.path.join(ARTIFACT_BASE, "datasets"),
    os.path.join(ARTIFACT_BASE, "models"),
    os.path.join(ARTIFACT_BASE, "training"),
    os.path.join(ARTIFACT_BASE, "backups"),
    os.path.join(ARTIFACT_BASE, "logs"),
]


def check(label, ok, detail=""):
    status = "OK" if ok else "FAIL"
    print(f"  [{status}] {label}" + (f": {detail}" if detail else ""))
    return ok


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def run(cmd, capture=True):
    if capture:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    else:
        result = subprocess.run(cmd, shell=True)
        return result.returncode == 0, "", ""


# ── 1. Python version ──────────────────────────────────────────
section("1. Python Version")
major, minor = sys.version_info[:2]
ok = (major, minor) >= REQUIRED_PYTHON
check(f"Python {major}.{minor}", ok,
      f"Need {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}+ — get it from https://python.org")
if not ok:
    sys.exit(1)

# ── 2. Git ─────────────────────────────────────────────────────
section("2. Git")
ok, out, _ = run("git --version")
check("git installed", ok, out or "Install from https://git-scm.com")

# ── 3. Pip dependencies ────────────────────────────────────────
section("3. Installing Dependencies")
req = os.path.join(PROJECT_ROOT, "requirements.txt")
if os.path.exists(req):
    print(f"  Installing from {req} ...")
    ok, _, err = run(f'"{sys.executable}" -m pip install -r "{req}" --quiet', capture=False)
    check("pip install -r requirements.txt", ok, err[:200] if err else "")
else:
    check("requirements.txt found", False, req)

# Extra packages needed for full functionality
extras = ["deepface", "tf-keras", "sentence-transformers"]
for pkg in extras:
    ok, out, _ = run(f'"{sys.executable}" -m pip show {pkg}')
    if not ok:
        print(f"  Installing {pkg} ...")
        run(f'"{sys.executable}" -m pip install {pkg} --quiet', capture=False)
    ok, _, _ = run(f'"{sys.executable}" -m pip show {pkg}')
    check(f"{pkg} installed", ok)

# ── 4. Artifact directories ────────────────────────────────────
section("4. Artifact Storage Directories")
print(f"  Base: {ARTIFACT_BASE}")
for d in ARTIFACT_DIRS:
    os.makedirs(d, exist_ok=True)
    check(d, os.path.isdir(d))

# ── 5. Environment file ────────────────────────────────────────
section("5. Environment File (.env)")
env_path = os.path.join(PROJECT_ROOT, ".env")
env_example = os.path.join(PROJECT_ROOT, ".env.example")
if not os.path.exists(env_path):
    if os.path.exists(env_example):
        import shutil
        shutil.copy(env_example, env_path)
        check(".env created from .env.example", True, "Fill in your API keys in .env")
    else:
        check(".env file", False, "Create .env manually from .env.example")
else:
    check(".env exists", True)

# ── 6. Smoke test ──────────────────────────────────────────────
section("6. Running Smoke Test")
smoke = os.path.join(PROJECT_ROOT, "tests", "smoke_test_imports.py")
if os.path.exists(smoke):
    ok, out, err = run(f'"{sys.executable}" "{smoke}"')
    lines = (out + err).splitlines()
    for line in lines[-10:]:
        print(f"  {line}")
    check("Smoke test", ok)
else:
    check("Smoke test script", False, smoke)

# ── Summary ────────────────────────────────────────────────────
section("Setup Complete")
print(f"""
  Laptop role:   Control / Mind
  Desktop role:  Compute / Muscle (GPU training)

  Workflow:
    - Pull latest code:    git pull
    - Run inference/tests: python main.py
    - Transfer artifacts:  copy D:\\Monica_Datasets via USB to/from desktop

  GitHub repo:   {REPO_URL}
  Project root:  {PROJECT_ROOT}
  Artifacts:     {ARTIFACT_BASE}
""")
