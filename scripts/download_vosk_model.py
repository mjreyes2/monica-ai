"""Download Vosk model for speech recognition"""
import urllib.request
import zipfile
from pathlib import Path

model_url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
model_dir = Path("models/vosk")
model_dir.mkdir(parents=True, exist_ok=True)

zip_path = model_dir / "vosk-model-small-en-us-0.15.zip"

print(f"Downloading Vosk model (~40MB)...")
print(f"From: {model_url}")
print(f"To: {zip_path}")

urllib.request.urlretrieve(model_url, zip_path)
print("Download complete!")

print("Extracting...")
with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(model_dir)

zip_path.unlink()  # Delete zip file
print(f" Model ready at: {model_dir / 'vosk-model-small-en-us-0.15'}")
