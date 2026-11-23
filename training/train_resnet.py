"""KrishiNetra Deep Learning Model: ResNet50 Transfer Learning & Fine-Tuning.

Workflow:
1. Initialize ResNet50 with ImageNet pretrained weights.
2. Freeze conv1, layer1, layer2, layer3.
3. Replace fully connected head with agricultural diagnostic classification head.
4. Fine-tune layer4 and classification head with Adam optimizer and ReduceLROnPlateau.
5. Save model weights and training logs.
"""

import os
import sys
import json
import time
import argparse
import logging
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import ReduceLROnPlateau
import torchvision.models as models

from dataset.dataset_loader import create_dataloaders
from training.utils import set_seed, get_device, EarlyStopping, ModelCheckpoint

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("KrishiNetra.TrainResNet50")


def build_resnet50(num_classes: int, fine_tune_layer4: bool = True) -> nn.Module:
    """Instantiate ResNet50 with ImageNet weights and tailored classifier head."""
    weights = models.ResNet50_Weights.DEFAULT
    model = models.resnet50(weights=weights)

    # Freeze base layers
    for param in model.parameters():
        param.requires_grad = False

    # Optionally unfreeze layer4 for deep representation fine-tuning
    if fine_tune_layer4:
        for param in model.layer4.parameters():
            param.requires_grad = True

    in_features = model.fc.in_features  # 2048
    model.fc = nn.Sequential(
        nn.Dropout(p=0.4),
        nn.Linear(in_features, 512),
        nn.BatchNorm1d(512),
        nn.ReLU(inplace=True),
        nn.Dropout(p=0.3),
        nn.Linear(512, num_classes)
    )
    return model


def train_epoch(model, loader, criterion, optimizer, device) -> tuple[float, float]:
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for inputs, labels in loader:
        inputs = inputs.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * inputs.size(0)
        _, preds = torch.max(outputs, 1)
        correct += torch.sum(preds == labels.data).item()
        total += labels.size(0)

    epoch_loss = running_loss / max(1, total)
    epoch_acc = correct / max(1, total)
    return epoch_loss, epoch_acc


def validate_epoch(model, loader, criterion, device) -> tuple[float, float]:
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for inputs, labels in loader:
            inputs = inputs.to(device)
            labels = labels.to(device)

            outputs = model(inputs)
            loss = criterion(outputs, labels)

            running_loss += loss.item() * inputs.size(0)
            _, preds = torch.max(outputs, 1)
            correct += torch.sum(preds == labels.data).item()
            total += labels.size(0)

    epoch_loss = running_loss / max(1, total)
    epoch_acc = correct / max(1, total)
    return epoch_loss, epoch_acc


def train(
    data_dir: str = "dataset/data",
    output_dir: str = "models",
    batch_size: int = 32,
    epochs: int = 8,
    lr: float = 3e-4,
    patience: int = 4,
    seed: int = 42
):
    set_seed(seed)
    device = get_device()

    out_path = Path(output_dir)
    weights_path = out_path / "weights" / "resnet50.pth"
    history_path = out_path / "reports" / "resnet50_history.json"
    weights_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Setting up ResNet50 DataLoaders (224x224 input resolution)...")
    train_loader, val_loader, test_loader, class_names, class_weights = create_dataloaders(
        data_dir=data_dir,
        arch="resnet50",
        batch_size=batch_size,
        balance_classes=True
    )
    num_classes = len(class_names)

    model = build_resnet50(num_classes=num_classes, fine_tune_layer4=True).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights.to(device))
    optimizer = optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=lr, weight_decay=1e-4)
    scheduler = ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=2)
    checkpoint = ModelCheckpoint(filepath=weights_path, monitor="val_loss", mode="min")
    early_stopping = EarlyStopping(patience=patience, mode="min")

    history = {
        "architecture": "ResNet50",
        "num_classes": num_classes,
        "class_names": class_names,
        "total_epochs": epochs,
        "train_loss": [],
        "val_loss": [],
        "train_acc": [],
        "val_acc": [],
        "learning_rates": []
    }

    start_time = time.time()
    logger.info(f"=== Starting ResNet50 Transfer Learning ({epochs} epochs, lr={lr}) ===")
    for epoch in range(1, epochs + 1):
        t_loss, t_acc = train_epoch(model, train_loader, criterion, optimizer, device)
        v_loss, v_acc = validate_epoch(model, val_loader, criterion, device)
        current_lr = optimizer.param_groups[0]["lr"]

        history["train_loss"].append(t_loss)
        history["val_loss"].append(v_loss)
        history["train_acc"].append(t_acc)
        history["val_acc"].append(v_acc)
        history["learning_rates"].append(current_lr)

        logger.info(
            f"[ResNet50 Epoch {epoch}/{epochs}] Train Loss: {t_loss:.4f} | Train Acc: {t_acc*100:.2f}% | "
            f"Val Loss: {v_loss:.4f} | Val Acc: {v_acc*100:.2f}% | LR: {current_lr:.6f}"
        )

        improved = checkpoint.step(v_loss, model, optimizer=optimizer, epoch=epoch, extra_info={"classes": class_names, "arch": "resnet50"})
        scheduler.step(v_loss)

        if early_stopping(v_loss):
            logger.info(f"Early stopping triggered at epoch {epoch}.")
            break

    elapsed = time.time() - start_time
    history["training_time_seconds"] = round(elapsed, 2)
    history["best_val_loss"] = checkpoint.best_val

    with open(history_path, "w") as f:
        json.dump(history, f, indent=2)

    logger.info(f"ResNet50 training complete in {elapsed:.1f}s. Best Val Loss: {checkpoint.best_val:.4f}. Saved: {weights_path}")
    return history


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train ResNet50 on KrishiNetra Dataset")
    parser.add_argument("--data_dir", type=str, default="dataset/data")
    parser.add_argument("--output_dir", type=str, default="models")
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--lr", type=float, default=3e-4)
    args = parser.parse_args()

    train(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        epochs=args.epochs,
        lr=args.lr
    )
