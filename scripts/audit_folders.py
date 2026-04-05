"""Audit project folders for duplicates, empty dirs, and path issues."""
import os

root = r'C:\Monica'

print("=" * 60)
print("FOLDER AUDIT")
print("=" * 60)

# Check empty dirs
print("\n--- EMPTY ROOT DIRS ---")
for d in sorted(os.listdir(root)):
    full = os.path.join(root, d)
    if os.path.isdir(full) and not d.startswith('.'):
        try:
            items = os.listdir(full)
            if len(items) == 0:
                print(f"  [EMPTY] {d}/")
        except:
            pass

# Potential duplicates
print("\n--- POTENTIAL DUPLICATES ---")
checks = [
    ("personal_voice_model/", "monica_ai/personal_voice_model/"),
    ("resources/", "monica_ai/resources/"),
    ("sounds/", "monica_ai/resources/sounds/"),
    ("kenlm/", "data/kenlm/"),
    ("models/", "data/models/"),
]
for a, b in checks:
    pa = os.path.join(root, a)
    pb = os.path.join(root, b)
    a_items = len(os.listdir(pa)) if os.path.exists(pa) else -1
    b_items = len(os.listdir(pb)) if os.path.exists(pb) else -1
    print(f"  {a} ({a_items} items) vs {b} ({b_items} items)")

# stt_friend_package
sfp = os.path.join(root, "stt_friend_package")
if os.path.exists(sfp):
    print(f"\n  stt_friend_package/: {os.listdir(sfp)}")

# Check data subfolders for similar names
print("\n--- DATA SUBFOLDERS ---")
data_dir = os.path.join(root, "data")
for d in sorted(os.listdir(data_dir)):
    full = os.path.join(data_dir, d)
    if os.path.isdir(full):
        items = len(os.listdir(full))
        print(f"  data/{d}/ ({items} items)")

# Check what references empty root dirs
print("\n--- REFERENCE CHECK ---")
empty_suspects = ["sounds", "resources", "kenlm", "artifacts", "personal_voice_model"]
import subprocess
for suspect in empty_suspects:
    # grep for references
    try:
        result = subprocess.run(
            ["python", "-m", "grep_search", suspect],  # won't work, just count
            capture_output=True, text=True, cwd=root
        )
    except:
        pass
    # Manual check: scan py files
    count = 0
    for dirpath, dirnames, filenames in os.walk(os.path.join(root, "src")):
        for fn in filenames:
            if fn.endswith(".py"):
                try:
                    content = open(os.path.join(dirpath, fn), "r", encoding="utf-8", errors="replace").read()
                    # Check for direct reference to root-level suspect folder (not inside monica_ai or data)
                    if f'"{suspect}/' in content or f"'{suspect}/" in content:
                        count += 1
                except:
                    pass
    if count > 0:
        print(f"  '{suspect}/' referenced in {count} src/ .py files")
    else:
        print(f"  '{suspect}/' NOT referenced in src/ (safe to ignore)")

print("\n--- DONE ---")
