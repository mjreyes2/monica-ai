# Fashion-MNIST CNN Notes

This document distills the GeeksforGeeks walkthroughs on Fashion-MNIST image
classification and CNN fundamentals into a quick-reference that matches the
`fashion_mnist_cnn.py` helper we just added.

## Dataset recap
- 70k grayscale images (28×28) split into 60k train / 10k test
- Ten wardrobe classes: `t_shirt`, `trouser`, `pullover`, `dress`, `coat`,
  `sandal`, `shirt`, `sneaker`, `bag`, `ankle_boots`
- We expand the channel dimension to get tensors shaped `(N, 28, 28, 1)` and
  normalize pixel values to `[0, 1]`

## CNN architecture (mirrors the GfG article)
1. Conv2D 64 filters, 5×5 kernel, ReLU, same padding
2. MaxPool 2×2
3. Conv2D 128 filters, 5×5, ReLU → MaxPool 2×2
4. Conv2D 256 filters, 5×5, ReLU → MaxPool 2×2
5. Flatten → Dense 256 ReLU → Dense 10 softmax

The network is compiled with `Adam(learning_rate=1e-3)` and
`sparse_categorical_crossentropy`.

## Training pipeline
- Optional 3×3 matplotlib grid helps visualize the raw samples
- Training uses a configurable epoch/batch schedule with validation split
- History objects are saved under `artifacts/fashion_mnist/` as
  `history.json`, `accuracy.png`, `loss.png`
- Weights land in `fashion_mnist_cnn.weights.h5` and the textual summary in
  `summary.txt`
- Predictions on a handful of test images are rendered for quick sanity checks

## Monica memory integration
If `monica_ai` is available and `--memory-log` is passed, the trainer logs its
latest train/validation/test accuracy snapshot into the Excel ledger. This gives
Monica conversational context when describing her AI training sessions.

## Usage
```
python fashion_mnist_cnn.py --epochs 10 --batch-size 128 --visualize --memory-log
```
Outputs are written to `artifacts/fashion_mnist/` by default; override via
`--output-dir`. Use `--no-train --weights <path>` to re-run prediction and
plotting using previously-saved weights without retraining.
