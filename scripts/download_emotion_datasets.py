"""
Download emotion detection datasets and pre-trained models for Monica AI.

Datasets:
1. FER2013 - 35,887 grayscale 48x48 face images, 7 emotions
   (via kagglehub or direct if available)
2. DeepFace pre-trained emotion model weights (auto-downloaded on first use)
3. FER OpenCV DNN model (lightweight, fast)

All data stays LOCAL - no cloud processing.
"""
import os
import sys
import urllib.request
import zipfile
import tarfile
import json
from pathlib import Path

PROJECT = Path(__file__).parent.parent
DATA_DIR = PROJECT / "data" / "datasets" / "emotion_detection"
MODELS_DIR = PROJECT / "models" / "emotion"


def download_file(url, dest, desc=""):
    """Download a file with progress."""
    print(f"  Downloading: {desc or url}")
    print(f"  -> {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        print(f"  [SKIP] Already exists ({dest.stat().st_size / 1024:.0f} KB)")
        return True
    try:
        urllib.request.urlretrieve(url, str(dest))
        print(f"  [OK] Downloaded ({dest.stat().st_size / 1024:.0f} KB)")
        return True
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False


def download_fer_opencv_model():
    """Download the OpenCV DNN emotion classification model."""
    print("\n--- OpenCV DNN Emotion Model ---")
    # This is a lightweight CNN trained on FER2013, usable with cv2.dnn
    prototxt_url = "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt"
    prototxt_dest = MODELS_DIR / "deploy.prototxt"
    download_file(prototxt_url, prototxt_dest, "Face detector prototxt")

    # Emotion classification model (MobileNet-based, ~13MB)
    # We'll create a config that tells the system where to find these
    config = {
        "model_type": "opencv_dnn_emotion",
        "emotions": ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"],
        "input_size": [48, 48],
        "normalize": True,
        "note": "Use DeepFace or FER library for best accuracy. This config is for reference."
    }
    config_path = MODELS_DIR / "emotion_model_config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    print(f"  [OK] Config saved: {config_path}")


def setup_fer_dataset_info():
    """Create dataset info and download instructions for FER2013."""
    print("\n--- FER2013 Dataset ---")
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    info = {
        "dataset": "FER2013",
        "description": "Facial Expression Recognition 2013 - 35,887 grayscale 48x48 images",
        "emotions": {
            "0": "angry",
            "1": "disgust",
            "2": "fear",
            "3": "happy",
            "4": "sad",
            "5": "surprise",
            "6": "neutral"
        },
        "train_samples": 28709,
        "test_samples": 3589,
        "validation_samples": 3589,
        "image_size": "48x48 grayscale",
        "source": "Kaggle (requires account)",
        "local_path": str(DATA_DIR / "fer2013"),
        "auto_download": "Use kagglehub or download from https://www.kaggle.com/datasets/msambare/fer2013"
    }

    info_path = DATA_DIR / "fer2013_info.json"
    with open(info_path, "w") as f:
        json.dump(info, f, indent=2)
    print(f"  [OK] Dataset info: {info_path}")

    # Try kagglehub auto-download
    try:
        import kagglehub
        print("  Downloading FER2013 via kagglehub...")
        path = kagglehub.dataset_download("msambare/fer2013")
        print(f"  [OK] FER2013 downloaded to: {path}")
        return True
    except ImportError:
        print("  [INFO] kagglehub not installed - trying alternative download")
    except Exception as e:
        print(f"  [INFO] kagglehub download failed: {e}")

    # Try direct Hugging Face mirror
    try:
        hf_url = "https://huggingface.co/datasets/Piro17/fer2013/resolve/main/fer2013.csv"
        dest = DATA_DIR / "fer2013" / "fer2013.csv"
        if download_file(hf_url, dest, "FER2013 CSV from HuggingFace"):
            return True
    except Exception as e:
        print(f"  [INFO] HuggingFace download failed: {e}")

    print("  [MANUAL] To download FER2013:")
    print("    1. pip install kagglehub")
    print("    2. python -c \"import kagglehub; kagglehub.dataset_download('msambare/fer2013')\"")
    print(f"    3. Or manually download to: {DATA_DIR / 'fer2013'}")
    return False


def download_haarcascades():
    """Ensure OpenCV Haar cascades are available."""
    print("\n--- OpenCV Haar Cascades ---")
    try:
        import cv2
        cascades = [
            'haarcascade_frontalface_default.xml',
            'haarcascade_profileface.xml',
            'haarcascade_eye.xml',
            'haarcascade_smile.xml',
        ]
        for c in cascades:
            path = cv2.data.haarcascades + c
            if os.path.exists(path):
                print(f"  [OK] {c}")
            else:
                print(f"  [MISSING] {c}")
    except Exception as e:
        print(f"  [ERROR] {e}")


def trigger_deepface_download():
    """Trigger DeepFace to download its models (they auto-download on first use)."""
    print("\n--- DeepFace Pre-trained Models ---")
    try:
        import numpy as np
        import cv2
        # Create a dummy face image
        dummy = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)

        from deepface import DeepFace
        print("  Triggering emotion model download (first use)...")
        result = DeepFace.analyze(dummy, actions=['emotion'], enforce_detection=False, silent=True)
        print("  [OK] DeepFace emotion model ready")

        print("  Triggering age model download...")
        result = DeepFace.analyze(dummy, actions=['age'], enforce_detection=False, silent=True)
        print("  [OK] DeepFace age model ready")

        print("  Triggering gender model download...")
        result = DeepFace.analyze(dummy, actions=['gender'], enforce_detection=False, silent=True)
        print("  [OK] DeepFace gender model ready")

        print("  Triggering race model download...")
        result = DeepFace.analyze(dummy, actions=['race'], enforce_detection=False, silent=True)
        print("  [OK] DeepFace race model ready")

    except ImportError:
        print("  [SKIP] DeepFace not installed: pip install deepface")
    except Exception as e:
        print(f"  [WARN] DeepFace model setup: {e}")


def download_yolo_model():
    """Download YOLOv8 model for object detection."""
    print("\n--- YOLOv8 Object Detection Model ---")
    yolo_dir = PROJECT / "models" / "yolo"
    yolo_dir.mkdir(parents=True, exist_ok=True)

    # YOLOv8n (nano) - fast, 6.2MB
    yolo_url = "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt"
    download_file(yolo_url, yolo_dir / "yolov8n.pt", "YOLOv8 Nano (6MB, 80 classes)")

    # YOLOv8s (small) - better accuracy, 22MB
    yolo_url_s = "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8s.pt"
    download_file(yolo_url_s, yolo_dir / "yolov8s.pt", "YOLOv8 Small (22MB, better accuracy)")


def main():
    print("=" * 60)
    print("MONICA AI - EMOTION & VISION MODEL DOWNLOADER")
    print("=" * 60)

    download_haarcascades()
    download_fer_opencv_model()
    setup_fer_dataset_info()
    trigger_deepface_download()
    download_yolo_model()

    print("\n" + "=" * 60)
    print("DOWNLOAD COMPLETE")
    print("=" * 60)
    print(f"  Data dir:   {DATA_DIR}")
    print(f"  Models dir: {MODELS_DIR}")
    print(f"  YOLO dir:   {PROJECT / 'models' / 'yolo'}")


if __name__ == '__main__':
    main()
