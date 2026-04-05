# Keras Built-in Datasets Cheat Sheet

Adapted from the July 2025 GeeksforGeeks roundup, this note lists the datasets
exposed through `keras.datasets` that pair well with our CNN tooling:

| Dataset | Task | Domain | Classes | Input Shape | Notes |
|---------|------|--------|---------|-------------|-------|
| `mnist` | classification | grayscale digits | 10 | (28, 28) | 60k train / 10k test handwritten digits |
| `fashion_mnist` | classification | grayscale apparel | 10 | (28, 28) | clothing replacement for MNIST (default in `fashion_mnist_cnn.py`) |
| `cifar10` | classification | RGB photos | 10 | (32, 32, 3) | 50k train / 10k test everyday objects |
| `cifar100` | fine-grained classification | RGB photos | 100 | (32, 32, 3) | exposes `label_mode="fine"` or `"coarse"` |
| `imdb` | sentiment | text | 2 | variable length | sequences of word indices for 25k reviews |
| `reuters` | topic classification | text | 46 | variable length | 11,228 newswire articles |
| `boston_housing` | regression | tabular | — | (13,) | 404/102 split predicting median price |

Each loader returns a `(train, test)` tuple. The new `keras_datasets_catalog.py`
helper can be invoked to print shapes and sample label mappings:

```bash
python keras_datasets_catalog.py --dataset fashion_mnist --describe
python keras_datasets_catalog.py --dataset cifar10 --sample-grid
```

Use this cheat sheet when deciding which dataset to feed through Monica's
training suite or when you need a quick sanity check on shapes/classes during
future experiments.
