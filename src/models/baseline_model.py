"""
Baseline model for aesthetic image classification.

This model uses ResNet18 transfer learning.
The final classification layer is replaced for binary classification.
"""

import torch.nn as nn
from torchvision import models


def build_baseline_model(num_classes=2, pretrained=True):
    if pretrained:
        weights = models.ResNet18_Weights.IMAGENET1K_V1
    else:
        weights = None

    model = models.resnet18(weights=weights)

    in_features = model.fc.in_features
    model.fc = nn.Linear(in_features, num_classes)

    return model