"""KrishiNetra Primary Deep Learning Model: EfficientNetB3 Transfer Learning & Fine-Tuning.

Workflow:
1. Initialize EfficientNetB3 with ImageNet pretrained weights.
2. Freeze base feature extractor.
3. Train custom classification head with Adam optimizer and Dropout.
4. Unfreeze deeper feature stages (stage 6, 7) for fine-tuning at lower LR.
5. Apply Early Stopping, Learning Rate Scheduling (ReduceLROnPlateau), and Checkpointing.
6. Save best model weights and training logs.
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
logger = logging.getLogger("KrishiNetra.TrainEfficientNet")


def build_efficientnet_b3(num_classes: int, freeze_backbone: bool = True) -> nn.Module:
    """Instantiate EfficientNetB3 with ImageNet weights and tailored classifier head."""
    weights = models.EfficientNet_B3_Weights.DEFAULT
    model = models.efficientnet_b3(weights=weights)

    if freeze_backbone:
        for param in model.features.parameters():
            param.requires_grad = False

    # In_features for EfficientNetB3 is 1536
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.3, inplace=True),
        nn.Linear(in_features, 512),
        nn.BatchNorm1d(512),
        nn.ReLU(inplace=True),
        nn.Dropout(p=0.4),
        nn.Linear(512, num_classes)
    )
    return model


def unfreeze_deeper_layers(model: nn.Module, num_stages_to_unfreeze: int = 2):
    """Unfreeze the top deeper stages of EfficientNet feature extractor for fine-tuning."""
    # EfficientNet features has 9 blocks (0 to 8). Unfreeze stages 6, 7, 8
    total_blocks = len(model.features)
    start_idx = max(0, total_blocks - num_stages_to_unfreeze)
    logger.info(f"Unfreezing EfficientNetB3 feature blocks from index {start_idx} to {total_blocks - 1} for fine-tuning.")
    for i in range(start_idx, total_blocks):
        for param in model.features[i].parameters():
            param.requires_grad = True


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
    batch_size: int = 16,
    warmup_epochs: int = 5,
    finetune_epochs: int = 10,
    lr: float = 1e-3,
    finetune_lr: float = 1e-4,
    patience: int = 4,
    seed: int = 42
):
    set_seed(seed)
    device = get_device()

    out_path = Path(output_dir)
    weights_path = out_path / "weights" / "efficientnet_b3.pth"
    history_path = out_path / "reports" / "efficientnet_b3_history.json"
    weights_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Create DataLoaders
    logger.info("Setting up EfficientNetB3 DataLoaders (300x300 input resolution)...")
    train_loader, val_loader, test_loader, class_names, class_weights = create_dataloaders(
        data_dir=data_dir,
        arch="efficientnet_b3",
        batch_size=batch_size,
        balance_classes=True
    )
    num_classes = len(class_names)
    logger.info(f"Initialized training for {num_classes} agricultural diagnostic classes.")

    # 2. Build Model with Frozen Pretrained Layers
    model = build_efficientnet_b3(num_classes=num_classes, freeze_backbone=True).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights.to(device))

    # Optimizer for Classification Head
    optimizer = optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=lr, weight_decay=1e-4)
    scheduler = ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=2)
    checkpoint = ModelCheckpoint(filepath=weights_path, monitor="val_loss", mode="min")
    early_stopping = EarlyStopping(patience=patience, mode="min")

    history = {
        "architecture": "EfficientNetB3",
        "num_classes": num_classes,
        "class_names": class_names,
        "warmup_epochs": warmup_epochs,
        "finetune_epochs": finetune_epochs,
        "train_loss": [],
        "val_loss": [],
        "train_acc": [],
        "val_acc": [],
        "learning_rates": []
    }

    start_time = time.time()
    logger.info(f"=== STAGE 1: Training Classification Head ({warmup_epochs} epochs, lr={lr}) ===")
    for epoch in range(1, warmup_epochs + 1):
        t_loss, t_acc = train_epoch(model, train_loader, criterion, optimizer, device)
        v_loss, v_acc = validate_epoch(model, val_loader, criterion, device)
        current_lr = optimizer.param_groups[0]["lr"]

        history["train_loss"].append(t_loss)
        history["val_loss"].append(v_loss)
        history["train_acc"].append(t_acc)
        history["val_acc"].append(v_acc)
        history["learning_rates"].append(current_lr)

        logger.info(
            f"[Stage 1 Epoch {epoch}/{warmup_epochs}] Train Loss: {t_loss:.4f} | Train Acc: {t_acc*100:.2f}% | "
            f"Val Loss: {v_loss:.4f} | Val Acc: {v_acc*100:.2f}% | LR: {current_lr:.6f}"
        )

        checkpoint.step(v_loss, model, optimizer=optimizer, epoch=epoch, extra_info={"classes": class_names, "arch": "efficientnet_b3"})
        scheduler.step(v_loss)

    # === STAGE 2: Fine-Tuning Deeper Layers ===
    logger.info(f"=== STAGE 2: Fine-Tuning Deeper Layers ({finetune_epochs} epochs, lr={finetune_lr}) ===")
    unfreeze_deeper_layers(model, num_stages_to_unfreeze=3)
    optimizer = optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=finetune_lr, weight_decay=1e-5)
    scheduler = ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=2)

    total_epochs = warmup_epochs + finetune_epochs
    for epoch in range(warmup_epochs + 1, total_epochs + 1):
        t_loss, t_acc = train_epoch(model, train_loader, criterion, optimizer, device)
        v_loss, v_acc = validate_epoch(model, val_loader, criterion, device)
        current_lr = optimizer.param_groups[0]["lr"]

        history["train_loss"].append(t_loss)
        history["val_loss"].append(v_loss)
        history["train_acc"].append(t_acc)
        history["val_acc"].append(v_acc)
        history["learning_rates"].append(current_lr)

        logger.info(
            f"[Stage 2 Epoch {epoch}/{total_epochs}] Train Loss: {t_loss:.4f} | Train Acc: {t_acc*100:.2f}% | "
            f"Val Loss: {v_loss:.4f} | Val Acc: {v_acc*100:.2f}% | LR: {current_lr:.6f}"
        )

        improved = checkpoint.step(v_loss, model, optimizer=optimizer, epoch=epoch, extra_info={"classes": class_names, "arch": "efficientnet_b3"})
        scheduler.step(v_loss)

        if early_stopping(v_loss):
            logger.info(f"Early stopping triggered at epoch {epoch} due to plateau in validation loss.")
            break

    elapsed = time.time() - start_time
    history["training_time_seconds"] = round(elapsed, 2)
    history["best_val_loss"] = checkpoint.best_val

    with open(history_path, "w") as f:
        json.dump(history, f, indent=2)

    logger.info(f"EfficientNetB3 training complete in {elapsed:.1f}s. Best Val Loss: {checkpoint.best_val:.4f}. Saved: {weights_path}")
    return history


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train EfficientNetB3 on KrishiNetra Dataset")
    parser.add_argument("--data_dir", type=str, default="dataset/data")
    parser.add_argument("--output_dir", type=str, default="models")
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--warmup_epochs", type=int, default=3)
    parser.add_argument("--finetune_epochs", type=int, default=5)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--finetune_lr", type=float, default=1e-4)
    args = parser.parse_args()

    train(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        warmup_epochs=args.warmup_epochs,
        finetune_epochs=args.finetune_epochs,
        lr=args.lr,
        finetune_lr=args.finetune_lr
    )
