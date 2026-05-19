"""
Evaluation script for aesthetic image classification.
"""

import torch
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
    NUM_CLASSES,
)


def evaluate():
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
        shuffle=False,
        num_workers=2,
    )

    model = build_baseline_model(
        num_classes=NUM_CLASSES,
        pretrained=False,
    ).to(device)

    checkpoint_path = CHECKPOINT_DIR / "baseline_resnet18.pth"
    model.load_state_dict(torch.load(checkpoint_path, map_location=device))

    model.eval()

    correct = 0
    total = 0

    with torch.no_grad():
        for images, labels in dataloader:
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)
            _, predicted = torch.max(outputs, 1)

            correct += (predicted == labels).sum().item()
            total += labels.size(0)

    accuracy = correct / total

    print(f"Evaluation Accuracy: {accuracy:.4f}")


if __name__ == "__main__":
    evaluate()