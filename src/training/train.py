"""
Training script for aesthetic image classification.

This is a minimal baseline training script.
Data paths should be adjusted depending on local or Colab environment.
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import transforms

from src.data.dataset import AestheticDataset
from src.models.baseline_model import build_baseline_model
from src.utils.config import (
    LABEL_PATH,
    IMAGE_DIR,
    CHECKPOINT_DIR,
    IMAGE_SIZE,
    BATCH_SIZE,
    NUM_EPOCHS,
    LEARNING_RATE,
    NUM_CLASSES,
)


def train():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    transform = transforms.Compose([
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])

    dataset = AestheticDataset(
        label_path=LABEL_PATH,
        image_dir=IMAGE_DIR,
        transform=transform,
    )

    dataloader = DataLoader(
        dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=2,
    )

    model = build_baseline_model(
        num_classes=NUM_CLASSES,
        pretrained=True,
    ).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=LEARNING_RATE,
    )

    model.train()

    for epoch in range(NUM_EPOCHS):
        total_loss = 0.0
        correct = 0
        total = 0

        for images, labels in dataloader:
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)
            loss = criterion(outputs, labels)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

            _, predicted = torch.max(outputs, 1)
            correct += (predicted == labels).sum().item()
            total += labels.size(0)

        avg_loss = total_loss / len(dataloader)
        accuracy = correct / total

        print(
            f"Epoch [{epoch + 1}/{NUM_EPOCHS}] "
            f"Loss: {avg_loss:.4f} "
            f"Accuracy: {accuracy:.4f}"
        )

    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), CHECKPOINT_DIR / "baseline_resnet18.pth")

    print("Training finished.")
    print(f"Model saved to: {CHECKPOINT_DIR / 'baseline_resnet18.pth'}")


if __name__ == "__main__":
    train()