# Custom Object Detection — Adding Your Own Objects
## How It Works

Monica uses YOLOv8 for real-time object detection. By default she recognizes
80 common objects (person, car, bottle, laptop, etc.). You can teach her to
recognize **new** objects by adding training data here.

## Quick Start

### 1. Organize your images

Put images and YOLO-format labels in `datasets/`:

```
models/yolo/custom/datasets/
├── images/
│   ├── train/          ← training images (80%+)
│   │   ├── img001.jpg
│   │   └── img002.jpg
│   └── val/            ← validation images (20%)
│       └── img003.jpg
├── labels/
│   ├── train/          ← matching label files
│   │   ├── img001.txt
│   │   └── img002.txt
│   └── val/
│       └── img003.txt
└── data.yaml           ← dataset config (see below)
```

### 2. Create `datasets/data.yaml`

```yaml
path: ./models/yolo/custom/datasets
train: images/train
val: images/val

nc: 2                      # number of new classes
names: ['my_object_1', 'my_object_2']
```

### 3. Label format (YOLO)

Each `.txt` label file has one line per object:
```
<class_id> <x_center> <y_center> <width> <height>
```
All values normalized 0–1 relative to image size. Use [Label Studio](https://labelstud.io/)
or [Roboflow](https://roboflow.com) to label interactively.

### 4. Train

```bash
cd C:\Users\Marvi\OneDrive\monica_project
C:\Users\Marvi\monica_venv\Scripts\python.exe -m ultralytics yolo detect train \
    data=models/yolo/custom/datasets/data.yaml \
    model=yolov8n.pt \
    epochs=50 imgsz=640 batch=8 \
    project=models/yolo/custom name=train
```

### 5. Deploy

Copy the best weights to the expected location:
```bash
copy models\yolo\custom\train\weights\best.pt models\yolo\custom\best.pt
```

Monica auto-loads `models/yolo/custom/best.pt` on startup if it exists.

## Tips

- **Minimum ~50 images per class** for decent results; 200+ is better.
- Include varied lighting, angles, and backgrounds.
- You can download ready-made datasets from [Roboflow Universe](https://universe.roboflow.com/).
- Fine-tuning from `yolov8n.pt` (pretrained COCO) is much faster than training from scratch.
