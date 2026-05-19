"""
Project configuration for aesthetic image classification.

This file stores common paths and hyperparameters.
Actual data paths can be changed when running experiments on Colab.
"""

from pathlib import Path


# Project root
ROOT_DIR = Path(__file__).resolve().parents[2]

# Local default paths
DATA_DIR = ROOT_DIR / "data"
LABEL_PATH = DATA_DIR / "labels.csv"
IMAGE_DIR = DATA_DIR / "images"

# Output paths
CHECKPOINT_DIR = ROOT_DIR / "checkpoints"
RESULT_DIR = ROOT_DIR / "results"

# Training settings
IMAGE_SIZE = 224
BATCH_SIZE = 32
NUM_EPOCHS = 10
LEARNING_RATE = 1e-4
NUM_CLASSES = 2

# Label rule
# 0: low aesthetic
# 1: high aesthetic
SCORE_THRESHOLD = 5.0

# Reproducibility
SEED = 42